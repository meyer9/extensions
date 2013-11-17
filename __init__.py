from dm3_image_utils import load_image, save_image

from nion.swift import ImportExportManager

class DM3ImportExportHandler(ImportExportManager.ImportExportHandler):

    def __init__(self):
        super(DM3ImportExportHandler, self).__init__("DigitalMicrograph Files", ["dm3", "dm4"])

    def read_data(self, extension, f):
        data, calibrations, title, properties = load_image(f)
        data_element = dict()
        data_element["data"] = data
        data_element["spatial_calibration"] = calibrations
        data_element["title"] = title
        data_element["properties"] = properties
        return [data_element]

    def can_write(self, data_item, extension):
        return extension == "dm3" and len(data_item.spatial_shape) == 2

    def write_data(self, data, extension, f):
        save_image(data, f)

ImportExportManager.ImportExportManager().register_io_handler(DM3ImportExportHandler())
