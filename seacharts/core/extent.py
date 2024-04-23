"""
Contains the Extent class for defining the span of spatial data.
"""
import math
import re

from pyproj import Transformer, CRS
from pyproj import Proj, transform


# TODO size in extent for latlong needs  fixing
class Extent:
    def __init__(self, settings: dict):
        self.size = tuple(settings["enc"].get("size", (0, 0)))
        crs: str = settings["enc"].get("crs")

        if "origin" in settings["enc"]:
            self.origin = tuple(settings["enc"].get("origin", (0, 0)))
            self.center = self._center_from_origin()

        if "center" in settings["enc"]:
            self.center = tuple(settings["enc"].get("center", (0, 0)))
            self.origin = self._origin_from_center()

        if crs.__eq__("WGS84"):
            self.utm_zone = self.wgs2utm(self.center[0])
            self.southern_hemisphere = False if self.center[1] >= 0 else True
            self.size = self._size_from_lat_long()
            self.center = self.convert_lat_lon_to_utm(self.center[1], self.center[0], self.utm_zone)
            self.origin = self.convert_lat_lon_to_utm(self.origin[1], self.origin[0], self.utm_zone)

        elif re.match(r'^UTM\d{2}[NS]', crs):
            crs = re.search(r'\d+[A-Z]', crs).group(0)
            self.utm_zone = crs[0:2]
            self.southern_hemisphere = False if crs[2] == 'N' else True

        self.bbox = self._bounding_box_from_origin_size()
        self.area: int = self.size[0] * self.size[1]

    @staticmethod
    def wgs2utm(longitude):
        return str(math.floor(longitude / 6 + 31))

    def convert_lat_lon_to_utm(self, latitude, longitude, zone):
        in_proj = Proj(init='epsg:4326')  # WGS84
        # TODO find if hemisphere code variation is necessary
        hemisphere_code = '7' if self.southern_hemisphere is True else '6'
        out_proj = Proj(init='epsg:32' + hemisphere_code + zone)

        utm_east, utm_north = transform(in_proj, out_proj, longitude, latitude)
        utm_east = math.ceil(utm_east)
        utm_north = math.ceil(utm_north)
        return utm_east, utm_north

    def _origin_from_center(self) -> tuple[int, int]:
        return (
            int(self.center[0] - self.size[0] / 2),
            int(self.center[1] - self.size[1] / 2),
        )

    def _center_from_origin(self) -> tuple[int, int]:
        return (
            int(self.origin[0] + self.size[0] / 2),
            int(self.origin[1] + self.size[1] / 2),
        )

    def _bounding_box_from_origin_size(self) -> tuple[int, int, int, int]:
        x_min, y_min = self.origin
        x_max, y_max = x_min + self.size[0], y_min + self.size[1]
        return x_min, y_min, x_max, y_max

    def _size_from_lat_long(self) -> tuple[int, int]:
        x_min, y_min = self.origin
        x_max, y_max = x_min + self.size[0], y_min + self.size[1]
        converted_x_min, converted_y_min = self.convert_lat_lon_to_utm(y_min, x_min, self.utm_zone)
        converted_x_max, converted_y_max = self.convert_lat_lon_to_utm(y_max, x_max, self.utm_zone)
        return converted_x_max - converted_x_min, converted_y_max - converted_y_min

    def _bounding_box_from_origin_size_lat_long(self) -> tuple[int, int, int, int]:
        x_min, y_min = self.origin
        x_max, y_max = x_min + self.size[0], y_min + self.size[1]
        converted_x_min, converted_y_min = self.convert_lat_lon_to_utm(y_min, x_min, self.utm_zone)
        converted_x_max, converted_y_max = self.convert_lat_lon_to_utm(y_max, x_max, self.utm_zone)
        self.size = tuple([converted_x_max - converted_x_min, converted_y_max - converted_y_min])
        return converted_x_min, converted_y_min, converted_x_max, converted_y_max
