"""
    Double Gaussian Filter.

    Implemented as an operation that can be applied to data items.

    This code is experimental, meaning that it works with the current version
    but will probably not work "as-is" with future versions of the software.

"""

# standard libraries
import gettext
import math

# third party libraries
import numpy
import scipy.fftpack

# local libraries
from nion.swift import Application
from nion.swift.model import Image
from nion.swift.model import Operation


_ = gettext.gettext


class DoubleGaussianFilterOperation(Operation.Operation):
    def __init__(self):

        # provide a description of the parameters to this operation. these parameters will
        # be placed in the processing panel as user interface elements.
        description = [{"name": _("Sigma 1"), "property": "sigma1", "type": "scalar", "default": 0.3},
                       {"name": _("Sigma 2"), "property": "sigma2", "type": "scalar", "default": 0.3},
                       {"name": _("Weight 2"), "property": "weight2", "type": "scalar", "default": 0.3}, ]
        super(DoubleGaussianFilterOperation, self).__init__(_("Double Gaussian Filter"),
                                                            "double-gaussian-filter-operation", description)

    # process is called to process the data. this version does not change the data shape
    # or data type. if it did, we would need to provide another function to describe the
    # change in shape or data type.
    def get_processed_data(self, data_sources, values):

        data = data_sources[0].data
        if data is None:
            return None

        # only works with 2d, scalar data
        if Image.is_data_2d(data) and Image.is_data_scalar_type(data):

            # make a copy of the data so that other threads can use data while we're processing
            # otherwise numpy puts a lock on the data.
            data_copy = data.copy()

            # grab our parameters. ideally this could just access the member variables directly,
            # but it doesn't work that way (yet).
            sigma1 = values.get("sigma1")
            sigma2 = values.get("sigma2")
            weight2 = values.get("weight2")

            # first calculate the FFT
            fft_data = scipy.fftpack.fftshift(scipy.fftpack.fft2(data_copy))

            # next, set up xx, yy arrays to be linear indexes for x and y coordinates ranging
            # from -width/2 to width/2 and -height/2 to height/2.
            yy_min = int(math.floor(-data.shape[0] / 2))
            yy_max = int(math.floor(data.shape[0] / 2))
            xx_min = int(math.floor(-data.shape[1] / 2))
            xx_max = int(math.floor(data.shape[1] / 2))
            xx, yy = numpy.meshgrid(numpy.linspace(yy_min, yy_max, data.shape[0]),
                                    numpy.linspace(xx_min, xx_max, data.shape[1]))

            # calculate the pixel distance from the center
            rr = numpy.sqrt(numpy.square(xx) + numpy.square(yy)) / (data.shape[0] * 0.5)

            # finally, apply a filter to the Fourier space data.
            filter = numpy.exp(-0.5 * numpy.square(rr / sigma1)) - (1.0 - weight2) * numpy.exp(
                -0.5 * numpy.square(rr / sigma2))
            filtered_fft_data = fft_data * filter

            # and then do invert FFT and take the real value.
            return scipy.fftpack.ifft2(scipy.fftpack.ifftshift(filtered_fft_data)).real

        else:
            # not 2d data.
            raise NotImplementedError()


# The following is code for making this into a process you can access from the processing menu

def processing_double_gaussian_filter(document_controller):
    display_specifier = document_controller.selected_display_specifier
    return document_controller.add_processing_operation_by_id(display_specifier.buffered_data_source_specifier,
                                                              "double-gaussian-filter-operation",
                                                              prefix=_("Double Gaussian Filter of "))


def build_menus(document_controller):
    document_controller.processing_menu.add_menu_item(_("Double Gaussian Filter"),
                                                      lambda: processing_double_gaussian_filter(document_controller))


Application.app.register_menu_handler(build_menus)  # called on import to make the Show Color Phase Button

Operation.OperationManager().register_operation("double-gaussian-filter-operation",
                                                lambda: DoubleGaussianFilterOperation())
