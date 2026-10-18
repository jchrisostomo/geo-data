from dataclasses import dataclass, field
from math import sqrt

from pyproj import CRS, Transformer
from shapely.geometry import Polygon, box
from shapely.ops import transform

# EPSG:4326 - WGS 84 (Geográfico)
CRS_WGS84 = CRS.from_epsg(4326)


@dataclass
class Area:
    name: str
    latitude: float
    longitude: float
    area_km2: float = 1.0

    crs: CRS = field(init=False)
    bounds_utm: tuple[float, float, float, float] = field(init=False)
    bounds_wgs84: tuple[float, float, float, float] = field(init=False)
    polygon_utm: Polygon = field(init=False, repr=False)   
    polygon_wgs84: Polygon = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not -80 <= self.latitude <= 84:
            raise ValueError("Latitude must be between -80.0 and 84.0 for UTM.")
        if not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180.0 and 180.0.")
        if self.area_km2 <= 0:
            self.area_km2 = 1
            raise ValueError("Area must be greater then zero.")

        
        utm_zone = min(60, max(1, int((self.longitude + 180) // 6) + 1))
        epsg = (32700 if self.latitude < 0 else 32600) + utm_zone
        
        self.crs = CRS.from_epsg(epsg) # Coordinate Reference System

        transform_to_meters = Transformer.from_crs(
            CRS_WGS84, # default value
            self.crs, # calculated
            always_xy=True,
        )

        transform_to_wgs84 = Transformer.from_crs(
            self.crs, # calculated
            CRS_WGS84, # default value
            always_xy=True,
        )
        
        x_utm, y_utm = transform_to_meters.transform(self.longitude, self.latitude)

        side_length_m = sqrt(self.area_km2) * 1000
        half_side_length_m = side_length_m / 2

        xmin_utm = x_utm - half_side_length_m
        ymin_utm = y_utm - half_side_length_m
        xmax_utm = x_utm + half_side_length_m
        ymax_utm = y_utm + half_side_length_m

        self.bounds_utm = (xmin_utm, ymin_utm, xmax_utm, ymax_utm)
        self.polygon_utm = box(xmin_utm, ymin_utm, xmax_utm, ymax_utm)

        polygon_utm_densified = self.polygon_utm.segmentize(250)

        self.polygon_wgs84 = transform(transform_to_wgs84.transform, polygon_utm_densified)
        self.bounds_wgs84 = self.polygon_wgs84.bounds



