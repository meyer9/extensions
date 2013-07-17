from dm3_image_utils import load_image, save_image

from nion.swift import Application

Application.app.import_export_manager.register_io(
    name="DM3",
    extensions=["dm3"],
    load_func=load_image,
    save_func=save_image)
