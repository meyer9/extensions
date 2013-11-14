from dm3_image_utils import load_image, save_image

from nion.swift import ImportExportManager

class DM3ImportExportHandler(ImportExportManager.ImportExportHandler):

    def __init__(self):
        super(DM3ImportExportHandler, self).__init__("DigitalMicrograph 3", ["dm3"])

    def read_data(self, extension, f):
        return load_image(f)

    def can_write(self, data_item, extension):
        return len(data_item.spatial_shape) == 2

    def write_data(self, data, extension, f):
        save_image(data, f)

ImportExportManager.ImportExportManager().register_io_handler(DM3ImportExportHandler())
