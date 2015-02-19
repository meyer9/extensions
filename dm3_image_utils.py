# ParseDM3File reads in a DM3 file and translates it into a dictionary
# this module treats that dictionary as an image-file and extracts the
# appropriate image data as numpy arrays.
# It also tries to create files from numpy arrays that DM can read.
#
# Some notes:
# Only complex64 and complex128 types are converted to structarrays,
# ie they're arrays of structs. Everything else, (including RGB) are
# standard arrays.
# There is a seperate DatatType and PixelDepth stored for images different
# from the tag file datatype. I think these are used more than the tag
# datratypes in describing the data.
from parse_dm3 import *
import numpy as np

structarray_to_np_map = {
    ('d', 'd'): np.complex128,
    ('f', 'f'): np.complex64}

np_to_structarray_map = {v: k for k, v in structarray_to_np_map.iteritems()}

# we want to amp any image type to a single np array type
# but a sinlge np array type could map to more than one dm type.
# For the moment, we won't be strict about, eg, discriminating
# int8 from bool, or even unit32 from RGB. In the future we could
# convert np bool type eg to DM bool and treat y,x,3 int8 images
# as RGB.

# note uint8 here returns the same data type as int8 0 could be that the
# only way they're differentiated is via this type, not the raw type
# in the tag file? And 8 is missing!
dm_image_dtypes = {
    1: ("int16", np.int16),
    2: ("float32", np.float32),
    3: ("Complex64", np.complex64),
    6: ("uint8", np.int8),
    7: ("int32", np.int32),
    9: ("int8", np.int8),
    10: ("uint16", np.uint16),
    11: ("uint32", np.uint32),
    12: ("float64", np.float64),
    13: ("Complex128", np.complex128),
    14: ("Bool", np.int8),
    23: ("RGB", np.int32)
}


def imagedatadict_to_ndarray(imdict):
    """
    Converts the ImageData dictionary, imdict, to an nd image.
    """
    arr = imdict['Data']
    im = None
    if isinstance(arr, array.array):
        im = np.asarray(arr, dtype=arr.typecode)
    elif isinstance(arr, structarray):
        t = tuple(arr.typecodes)
        im = np.frombuffer(
            arr.raw_data,
            dtype=structarray_to_np_map[t])
    elif isinstance(arr, types.UnicodeType):
        im = np.frombuffer(arr, dtype=np.uint16)
    # print "Image has dmimagetype", imdict["DataType"], "numpy type is", im.dtype
    assert dm_image_dtypes[imdict["DataType"]][1] == im.dtype
    assert imdict['PixelDepth'] == im.dtype.itemsize
    return im.reshape(imdict['Dimensions'][::-1])


def ndarray_to_imagedatadict(nparr):
    """
    Convert the numpy array nparr into a suitable ImageList entry dictionary.
    Returns a dictionary with the appropriate Data, DataType, PixelDepth
    to be inserted into a dm3 tag dictionary and written to a file.
    """
    ret = {}
    dm_type = (k for k, v in dm_image_dtypes.iteritems() if v[1] == nparr.dtype.type).next()
    ret["DataType"] = dm_type
    ret["PixelDepth"] = nparr.dtype.itemsize
    ret["Dimensions"] = list(nparr.shape[::-1])
    if nparr.dtype.type in np_to_structarray_map:
        types = np_to_structarray_map[nparr.dtype.type]
        ret["Data"] = structarray(types)
        ret["Data"].raw_data = str(nparr.data)
    else:
        ret["Data"] = array.array(nparr.dtype.char, nparr.flatten())
    return ret


import types
def display_keys(tag, indent=None):
    indent = indent if indent is not None else str()
    if isinstance(tag, types.ListType) or isinstance(tag, types.TupleType):
        for i, v in enumerate(tag):
            logging.debug("%s %s:", indent, i)
            display_keys(v, indent + "..")
    elif isinstance(tag, types.DictType):
        for k, v in tag.iteritems():
            logging.debug("%s key: %s", indent, k)
            display_keys(v, indent + "..")
    elif isinstance(tag, types.BooleanType):
        logging.debug("%s bool: %s", indent, tag)
    elif isinstance(tag, types.IntType):
        logging.debug("%s int: %s", indent, tag)
    elif isinstance(tag, types.LongType):
        logging.debug("%s long: %s", indent, tag)
    elif isinstance(tag, types.FloatType):
        logging.debug("%s float: %s", indent, tag)
    elif isinstance(tag, types.StringType):
        logging.debug("%s string: %s", indent, tag)
    elif isinstance(tag, types.UnicodeType):
        logging.debug("%s unicode: %s", indent, tag)
    else:
        logging.debug("%s %s: DATA", indent, type(tag))


def load_image(file):
    """
    Loads the image from the file-like object or string file.
    If file is a string, the file is opened and then read.
    Returns a numpy ndarray of our best guess for the most important image
    in the file.
    """
    if isinstance(file, str) or isinstance(file, unicode):
        with open(file, "rb") as f:
            return load_image(f)
    dmtag = parse_dm_header(file)
    #display_keys(dmtag)
    img_index = -1
    image_tags = dmtag['ImageList'][img_index]
    data = imagedatadict_to_ndarray(image_tags['ImageData'])
    calibrations = []
    calibration_tags = image_tags['ImageData'].get('Calibrations', dict())
    for dimension in calibration_tags.get('Dimension', list()):
        calibrations.append((dimension['Origin'], dimension['Scale'], dimension['Units']))
    title = image_tags.get('Name')
    properties = dict()
    voltage = None
    if 'ImageTags' in image_tags:
        properties["imported_properties"] = image_tags['ImageTags']
        voltage = image_tags['ImageTags'].get('ImageScanned', dict()).get('EHT', dict())
        if voltage:
            properties["autostem"] = { "high_tension_v": float(voltage) }
            properties["extra_high_tension"] = float(voltage)  # TODO: file format: remove extra_high_tension
    return data, tuple(reversed(calibrations)), title, properties


def save_image(image, file):
    """
    Saves the nparray image to the file-like object (or string) file.
    If file is a string the file is created and written to
    """
    if isinstance(file, str):
        with open(file, "wb") as f:
            return save_image(n, f)
    # we need to create a basic DM tree suitable for an imge
    # we'll try the minimum: just an image list
    # doesn't work. Do we need a ImageSourceList too?
    # and a DocumentObjectList?
    image = ndarray_to_imagedatadict(image)
    ret = {}
    ret["ImageList"] = [{"ImageData": image}]
    # I think ImageSource list creates a mapping between ImageSourceIds and Images
    ret["ImageSourceList"] = [{"ClassName": "ImageSource:Simple", "Id": [0], "ImageRef": 0}]
    # I think this lists the sources for the DocumentObjectlist. The source number is not
    # the indxe in the imagelist but is either the index in the ImageSourceList or the Id
    # from that list. We also need to set the annotation type to identify it as an image
    ret["DocumentObjectList"] = [{"ImageSource": 0, "AnnotationType": 20}]
    # finally some display options
    ret["Image Behavior"] = {"ViewDisplayID": 8}
    ret["InImageMode"] = 1
    parse_dm_header(file, ret)
