import gettext

# third party libraries
# see http://docs.opencv.org/index.html
import cv2
import cv2.cv as cv
import numpy

# local libraries
from nion.data import Image
from nion.swift import Application
from nion.swift.Decorators import relative_file
from nion.swift.model import Operation

_ = gettext.gettext  # for translation


def draw_rects(img, rects, color):
    for x1, y1, x2, y2 in rects:
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)


def detect(img, cascade_fn, scaleFactor=1.3, minNeighbors=4, minSize=(20, 20), flags=cv.CV_HAAR_SCALE_IMAGE):

    cascade = cv2.CascadeClassifier(cascade_fn)
    rects = cascade.detectMultiScale(img, scaleFactor=scaleFactor, minNeighbors=minNeighbors, minSize=minSize, flags=flags)
    if len(rects) == 0:
        return []
    rects[:, 2:] += rects[:, :2]
    return rects


class FaceDetectionOperation(Operation.Operation):

    def __init__(self):
        super(FaceDetectionOperation, self).__init__(_("Face Detection"), "face-detection-operation")

    def get_processed_data(self, data_sources, values):
        data = data_sources[0].data
        if data is None:
            return None
        img = Image.create_rgba_image_from_array(data)  # inefficient since we're just converting back to gray
        if id(img) == id(data):
            img = img.copy()
        if id(img.base) == id(data):
            img = img.copy()
        img = img.view(numpy.uint8).reshape(img.shape + (4,))  # expand the color into uint8s
        img_gray = cv2.cvtColor(img, cv.CV_RGB2GRAY)
        img_gray = cv2.equalizeHist(img_gray)
        rects = detect(img_gray, relative_file(__file__, "haarcascade_frontalface_alt.xml"))
        draw_rects(img, rects, (0, 255, 0))
        return img


def processing_face_detect(document_controller):
    display_specifier = document_controller.selected_display_specifier
    return document_controller.add_processing_operation_by_id(display_specifier.buffered_data_source_specifier,
                                                              "face-detection-operation",
                                                              prefix=_("Face Detection of "))


def build_menus(document_controller):
    document_controller.processing_menu.add_menu_item(_("Face Detection"), lambda: processing_face_detect(document_controller))

Application.app.register_menu_handler(build_menus)

Operation.OperationManager().register_operation("face-detection-operation", lambda: FaceDetectionOperation())
