import logging

from nion.swift import ImportExportManager
from nion.imaging import Image

from dm3_image_utils import load_image, save_image

class DM3ImportExportHandler(ImportExportManager.ImportExportHandler):

    def __init__(self):
        super(DM3ImportExportHandler, self).__init__("DigitalMicrograph Files", ["dm3", "dm4"])

    def read_data_elements(self, ui, extension, file_path):
        data, calibrations, title, properties = load_image(file_path)
        data_element = dict()
        data_element["data"] = data
        spatial_calibrations = list()
        for calibration in calibrations:
            origin, scale, units = calibration[0], calibration[1], calibration[2]
            scale = 1.0 if scale == 0.0 else scale  # sanity check
            spatial_calibrations.append({ "origin": origin, "scale": scale, "units": units })
        data_element["spatial_calibrations"] = spatial_calibrations
        data_element["title"] = title
        data_element["properties"] = properties
        return [data_element]

    def can_write(self, data_item, extension):
        return extension == "dm3" and len(data_item.spatial_shape) == 2

    def write_data(self, data, extension, f):
        save_image(data, f)

ImportExportManager.ImportExportManager().register_io_handler(DM3ImportExportHandler())
