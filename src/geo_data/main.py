import re
from pathlib import Path

from geo_data.area import Area
from geo_data.copernicus import download_copernicus
from geo_data.overture import download_overture


def _ask_float(prompt: str) -> float:
    while True:
        try:
            return float(input(prompt).replace(",", "."))
        except ValueError:
            print("Digite um número válido.")


def _folder_name(name: str) -> str:
    return re.sub(r"[^\w.-]+", "_", name.strip(), flags=re.UNICODE).strip("._") or "area"


def main() -> None:
    print("Defina a área para baixar os dados geográficos. Área máxima: 100 km².\n")
    name = input("Nome do local/mapa/área: ").strip() or "area"
    latitude = _ask_float("Latitude: ")
    longitude = _ask_float("Longitude: ")
    area_km2 = _ask_float("Área total em km²: ")

    try:
        area = Area(name, latitude, longitude, area_km2)
    except ValueError as error:
        print(f"Não foi possível definir a área: {error}")
        return

    output_dir = Path("downloads") / _folder_name(name)
    print(f"\nCRS: {area.crs}")
    print(f"BBox WGS84: {area.bounds_wgs84}")
    print(f"Destino: {output_dir.resolve()}\n")

    try:
        paths = download_overture(area, output_dir / "overture")
        print(f"Overture: {len(paths)} camada(s) salva(s).\n")
    except Exception as error:
        print(f"Overture terminou com falhas: {error}\n")

    try:
        elevation, slope = download_copernicus(area, output_dir / "copernicus")
        print(f"Copernicus: elevação salva em {elevation}")
        print(f"Copernicus: slope salvo em {slope}")
    except Exception as error:
        print(f"Copernicus terminou com falha: {error}")
