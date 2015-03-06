"""
    Support for DM3 and DM4 I/O.
"""

# standard libraries
import gettext

# third party libraries
# None

# local libraries
import dm3_image_utils

from nion.swift import Facade


_ = gettext.gettext


class DM3IODelegate(object):

    def __init__(self, api):
        self.__api = api
        self.io_handler_name = _("DigitalMicrograph Files")
        self.io_handler_extensions = ["dm3", "dm4"]

    def read_data_and_metadata(self, extension, file_path):
        data, calibrations, title, properties = dm3_image_utils.load_image(file_path)
        data_element = dict()
        data_element["data"] = data
        dimensional_calibrations = list()
        for calibration in calibrations:
            origin, scale, units = calibration[0], calibration[1], calibration[2]
            scale = 1.0 if scale == 0.0 else scale  # sanity check
            dimensional_calibrations.append(self.__api.create_calibration(-origin * scale, scale, units))
        # data_element["title"] = title
        intensity_calibration = self.__api.create_calibration()
        metadata = dict()
        metadata["hardware_source"] = properties
        timestamp = None
        return self.__api.create_data_and_metadata_from_data(data, intensity_calibration, dimensional_calibrations, metadata, timestamp)

    def can_write_data_and_metadata(self, data_and_metadata, extension):
        return extension == "dm3" and data_and_metadata.is_data_2d

    def write_data_and_metadata(self, data_and_metadata, file_path, extension):
        data = data_and_metadata.data
        with open(file_path, 'wb') as f:
            dm3_image_utils.save_image(data, f)


def load_image(file_path):
    return dm3_image_utils.load_image(file_path)


api_manifest = {
    "main": "1",
}

api = Facade.load(api_manifest)
api.create_data_and_metadata_io_handler(DM3IODelegate(api))

# TODO: How should IO delegate handle title when reading using read_data_and_metadata
