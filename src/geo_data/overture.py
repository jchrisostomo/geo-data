from pathlib import Path

from overturemaps import geodataframe

from geo_data.area import Area


# Feature types documented by Overture, grouped by theme.
OVERTURE_TYPES = {
    "addresses": ("address",),
    "base": ("bathymetry", "infrastructure", "land", "land_cover", "land_use", "water"),
    "buildings": ("building", "building_part"),
    "divisions": ("division", "division_area", "division_boundary"),
    "places": ("place",),
    "transportation": ("connector", "segment"),
}


def download_overture(area: Area, output_dir: Path) -> list[Path]:
    """Download Overture feature types intersecting the area and clip them to it."""
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[Path] = []
    errors: list[str] = []
    west, south, east, north = area.bounds_wgs84
    bbox = (west, south, east, north)

    for theme, feature_types in OVERTURE_TYPES.items():
        for feature_type in feature_types:
            print(f"Overture: baixando {theme}/{feature_type}...")
            try:
                features = geodataframe(feature_type, bbox=bbox)
                if features is None or features.empty:
                    print(f"  sem dados para {feature_type}")
                    continue

                if features.crs is None:
                    features = features.set_crs("EPSG:4326")
                features = features.to_crs(area.crs)
                features = features[
                    features.geometry.notna() & ~features.geometry.is_empty
                ]
                if features.empty:
                    continue

                # The bbox limits the download; this intersection applies the actual square.
                features.geometry = features.geometry.intersection(area.polygon_utm)
                features = features[
                    features.geometry.notna() & ~features.geometry.is_empty
                ].copy()
                if features.empty:
                    print(f"  sem feições dentro do quadrado para {feature_type}")
                    continue

                path = output_dir / f"{theme}_{feature_type}.gpkg"
                features.to_file(path, layer=feature_type, driver="GPKG")
                downloaded.append(path)
                print(f"  salvo: {path}")
            except Exception as error:
                errors.append(f"{theme}/{feature_type}: {error}")

    if errors:
        details = "\n".join(f"- {error}" for error in errors)
        raise RuntimeError(f"Falha ao baixar alguns tipos Overture:\n{details}")

    return downloaded
