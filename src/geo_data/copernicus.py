from math import ceil, floor
from pathlib import Path
import tempfile

import numpy as np
import requests
import rasterio
from rasterio.features import geometry_mask
from rasterio.merge import merge
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject
from shapely.geometry import mapping

from geo_data.area import Area


BASE_URL = "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com"
NODATA = -9999.0
RESOLUTION_M = 30.0


def _tile_part(degree: int, latitude: bool) -> str:
    direction = ("S" if degree < 0 else "N") if latitude else ("W" if degree < 0 else "E")
    width = 2 if latitude else 3
    return f"{direction}{abs(degree):0{width}d}_00"


def _tile_url(latitude_degree: int, longitude_degree: int) -> str:
    latitude = _tile_part(latitude_degree, latitude=True)
    longitude = _tile_part(longitude_degree, latitude=False)
    tile = f"Copernicus_DSM_COG_10_{latitude}_{longitude}_DEM"
    return f"{BASE_URL}/{tile}/{tile}.tif"


def download_copernicus(area: Area, output_dir: Path) -> tuple[Path, Path]:
    """Download Copernicus GLO-30, clip to the UTM square, and derive slope."""
    output_dir.mkdir(parents=True, exist_ok=True)
    west, south, east, north = area.bounds_wgs84
    source_paths: list[Path] = []

    with tempfile.TemporaryDirectory(dir=output_dir) as temporary_dir:
        temporary_path = Path(temporary_dir)
        tile_degrees = [
            (latitude, longitude)
            for latitude in range(floor(south), floor(north) + 1)
            for longitude in range(floor(west), floor(east) + 1)
        ]

        for index, (latitude, longitude) in enumerate(tile_degrees):
            url = _tile_url(latitude, longitude)
            tile_path = temporary_path / f"tile_{index}.tif"
            print(f"Copernicus: baixando tile {latitude}, {longitude}...")
            with requests.get(url, stream=True, timeout=120) as response:
                if response.status_code == 404:
                    print("  tile não disponível (pode ser área oceânica ou tile GLO-30 não público)")
                    continue
                response.raise_for_status()
                with tile_path.open("wb") as tile_file:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            tile_file.write(chunk)
            source_paths.append(tile_path)

        if not source_paths:
            raise RuntimeError("Nenhum tile Copernicus GLO-30 foi encontrado para a área.")

        with rasterio.open(source_paths[0]) as first_tile:
            source_crs = first_tile.crs
            source_nodata = first_tile.nodata
        with rasterio.Env():
            sources = [rasterio.open(path) for path in source_paths]
            try:
                mosaic, mosaic_transform = merge(sources, nodata=source_nodata)
            finally:
                for source in sources:
                    source.close()

        xmin, ymin, xmax, ymax = area.bounds_utm
        width = ceil((xmax - xmin) / RESOLUTION_M)
        height = ceil((ymax - ymin) / RESOLUTION_M)
        output_transform = from_origin(xmin, ymax, RESOLUTION_M, RESOLUTION_M)
        elevation = np.full((height, width), NODATA, dtype=np.float32)

        reproject(
            source=mosaic[0],
            destination=elevation,
            src_transform=mosaic_transform,
            src_crs=source_crs,
            src_nodata=source_nodata,
            dst_transform=output_transform,
            dst_crs=area.crs,
            dst_nodata=NODATA,
            resampling=Resampling.bilinear,
        )

        inside_area = geometry_mask(
            [mapping(area.polygon_utm)],
            out_shape=elevation.shape,
            transform=output_transform,
            invert=True,
        )
        elevation_for_slope = elevation.copy()
        elevation[~inside_area] = NODATA

    elevation_path = output_dir / "elevation.tif"
    slope_path = output_dir / "slope.tif"
    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": "float32",
        "crs": area.crs,
        "transform": output_transform,
        "nodata": NODATA,
        "compress": "deflate",
    }

    with rasterio.open(elevation_path, "w", **profile) as raster:
        raster.write(elevation, 1)

    # Slope is calculated from the projected elevation grid, so x/y are in metres.
    elevation_for_slope = elevation_for_slope.astype(np.float32)
    elevation_for_slope[elevation_for_slope == NODATA] = np.nan
    gradient_y, gradient_x = np.gradient(elevation_for_slope, RESOLUTION_M, RESOLUTION_M)
    slope = np.degrees(np.arctan(np.hypot(gradient_x, gradient_y))).astype(np.float32)
    slope[~inside_area | ~np.isfinite(slope)] = NODATA

    with rasterio.open(slope_path, "w", **profile) as raster:
        raster.write(slope, 1)

    return elevation_path, slope_path
