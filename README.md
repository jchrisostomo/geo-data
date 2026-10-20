# geo-data

Downloads Overture vector layers and Copernicus elevation data for a square area of interest.

Run `geo-data` and enter the area's name, center coordinates, and total area in km². The area limit enforced by the current validation is 1,000 km². Outputs are written under `downloads/<area-name>/`:

- `overture/`: one GeoPackage per Overture feature type, clipped to the area square.
- `copernicus/elevation.tif`: Copernicus GLO-30 elevation, clipped to the square and projected to the area's UTM CRS.
- `copernicus/slope.tif`: slope in degrees derived from the elevation raster and clipped to the same square.

The Copernicus source is the public GLO-30 COG collection. Overture is queried with the WGS84 bounding box, then its vector features are intersected with the exact UTM square.

## Running the program

Requirements: Python 3.11 or newer, [uv](https://docs.astral.sh/uv/getting-started/installation/), and an internet connection to download the datasets.

From the project directory, install the dependencies and start the program:

```bash
uv sync
uv run geo-data
```

You can also start it directly with `uv run geo-data`; uv will create the project environment and install the dependencies when needed.

The program interactively asks for:

1. An area name, used to name the output folder.
2. The center latitude and longitude in decimal degrees, using a period (`.`) as the decimal separator (for example, `-23.5505`).
3. The total area in km². The current validation accepts values up to 1,000 km².

Use a period (`.`) as the decimal separator for coordinates and area values. The results are saved in `downloads/<area-name>/`, inside `overture/` and `copernicus/` subfolders.

## Data sources and attribution

The downloaded datasets are provided by third parties and have terms that are separate from this project's GPL-3.0 license. Check the applicable terms before redistributing or publishing downloaded data.

### Overture Maps

Vector data is queried from [Overture Maps](https://overturemaps.org/). Overture themes can include data from multiple upstream providers, and attribution and license terms vary by theme and source. When using or redistributing the generated GeoPackages, consult the current [Overture attribution and licensing documentation](https://docs.overturemaps.org/attribution/) and comply with the requirements for the themes and sources present in the data. For publications, Overture suggests the citation: “Overture Maps Foundation, overturemaps.org”, together with the date accessed.

### Copernicus DEM GLO-30

The elevation raster is clipped and reprojected, and the slope raster is derived from it. For these adapted products, Copernicus requires this notice:

> Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved.

See the [Copernicus DEM product and licensing information](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM) for the source and applicable terms. The Copernicus page also provides the dataset DOI for research citations: [10.5270/ESA-c5d3d65](https://doi.org/10.5270/ESA-c5d3d65).
