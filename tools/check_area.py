from geo_data.area import Area

area = Area(
    name="Minha área",
    latitude=-23.55,
    longitude=-46.63,
    area_km2=4,
)

print("Nome:", area.name)
print("CRS:", area.crs)
print("Limites UTM:", area.bounds_utm)
print("Limites WGS84:", area.bounds_wgs84)
print("Polígono UTM válido:", area.polygon_utm.is_valid)
print("Área UTM em km²:", area.polygon_utm.area / 1_000_000)

assert area.name == "Minha área"
assert area.polygon_utm.is_valid