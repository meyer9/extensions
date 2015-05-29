# ColorPhase, by Zeno Dellby

# system imports
import gettext
import math

# library imports
import numpy as np

# local libraries
# None


_ = gettext.gettext  # for translation


# The operation class. Functions in it are called by Swift.
class ColorPhaseOperationDelegate(object):

    def __init__(self, api):
        self.__api = api
        self.operation_id = "color-phase-operation"
        self.operation_name = _("Color Phase")
        self.operation_prefix = _("Color Phase of ")

    def can_apply_to_data(self, data_and_metadata):
        return data_and_metadata.is_data_2d

    def get_processed_data_and_metadata(self, data_and_metadata, parameters):
        api = self.__api
        img = data_and_metadata.data
        grad = np.zeros(img.shape+(3,),dtype=np.uint8) # rgb format
        # grad will be returned at the end, then Swift will identify it as rgb and display it as such.
        w = img.shape[0] #w and h are much shorter to read than img.shape[0] and img.shape[1]
        h = img.shape[1]
        if img.is_data_complex_type: #If it's complex, we want to show the phase data, otherwise just a color map
            ave_intensity = np.median(np.log(abs(img))) #To see the colors in the cool parts more clearly, ignore the noise in the dark
            max_intensity = max(np.log(abs(img[0:w/2-2])).max(), np.log(abs(img[w/2+2:])).max(),       #not counting
                                np.log(abs(img[0:,0:h/2-2])).max(), np.log(abs(img[0:,h/2+2:])).max()) #center pixels
            simgpx = img[range(1,w)+[0,]]       #shift image plus in x. It's a new view on the image, shifted one pixel
            simgmx = img[[w-1,]+range(0,w-1)]   #over.
            simgpy = img[:,range(1,h)+[0,]]
            simgmy = img[:,[h-1,]+range(0,h-1)]

            nplusx  = np.sqrt(1/abs(img) + 1/abs(simgpx)) #Implicit looping lets it calculate an nplusx array in a
            nminusx = np.sqrt(1/abs(img) + 1/abs(simgmx)) #single line
            nplusy  = np.sqrt(1/abs(img) + 1/abs(simgpy))
            nminusy = np.sqrt(1/abs(img) + 1/abs(simgmy))

            arcimg = np.arctan2(img.imag,img.real) #for SPEED, not that it helps as much as I hoped
            dlambdaplusx  = (np.arctan2(simgpx.imag,simgpx.real)-arcimg) % 6.2831
            dlambdaminusx = (arcimg-np.arctan2(simgmx.imag,simgmx.real)) % 6.2831
            dlambdaplusy  = (np.arctan2(simgpy.imag,simgpy.real)-arcimg) % 6.2831
            dlambdaminusy = (arcimg-np.arctan2(simgmy.imag,simgmy.real)) % 6.2831

            dlambdax = (dlambdaplusx + ((dlambdaminusx-dlambdaplusx+3.1415)%6.2831-3.1415)*nplusx / (nplusx+nminusx)) % 6.2831
            dlambday = (dlambdaplusy + ((dlambdaminusy-dlambdaplusy+3.1415)%6.2831-3.1415)*nplusy / (nplusy+nminusy)) % 6.2831

            X = (dlambdax/math.pi)/2     #The realspace location, as a number from 0 to 1
            Y = (dlambday/math.pi)/2
            magnitude = np.log(abs(img)) #Putting the FFT on a log scale to see the dark parts more easily
            I = np.maximum(np.minimum((magnitude-ave_intensity)/(max_intensity-ave_intensity),1),0) #Intensity
            H = np.arctan2(X-0.5,Y-0.5)  #Hue
            S = np.sqrt(np.square(X-0.5)+np.square(Y-0.5)) #Saturation
            grad[:,:,0] = (S*(np.cos(H)+1)*127.5+(1-S)*127.5)*I           #Blue
            grad[:,:,1] = (S*(np.cos(H-np.pi*2/3)+1)*127.5+(1-S)*127.5)*I #Green
            grad[:,:,2] = (S*(np.cos(H+np.pi*2/3)+1)*127.5+(1-S)*127.5)*I #Red
        else: #just overlay a color map onto it
            min_intensity = img.min()
            intensity_range = img.max() - min_intensity
            irow,icol = np.ogrid[0:w,0:h] #Makes 2 arrays, one of size w and one of size h
            H = np.arctan2(w/2.0-irow,h/2.0-icol) #Makes a hue map from the direction to point irow,icol from point w/2,h/2
            S = np.sqrt(np.square((irow-w/2)*np.sqrt(2)/w)+np.square((icol-h/2)*np.sqrt(2)/h)) #Saturation
            I = (img*1.0 - min_intensity)/intensity_range #Intensity
            grad[:,:,0] = (S*(np.cos(H)+1)*127.5+(1-S)*127.5)*I           #Blue
            grad[:,:,1] = (S*(np.cos(H-np.pi*2/3)+1)*127.5+(1-S)*127.5)*I #Green
            grad[:,:,2] = (S*(np.cos(H+np.pi*2/3)+1)*127.5+(1-S)*127.5)*I #Red

        intensity_calibration = data_and_metadata.intensity_calibration
        dimensional_calibrations = data_and_metadata.dimensional_calibrations
        metadata = data_and_metadata.metadata
        return api.create_data_and_metadata_from_data(grad, intensity_calibration, dimensional_calibrations, metadata)


class ColorPhaseExtension(object):

    # required for Swift to recognize this as an extension class.
    extension_id = "nion.swift.extensions.color_phase"

    def __init__(self, api_broker):
        # grab the api object.
        api = api_broker.get_api(version="1", ui_version="1")
        # be sure to keep a reference or it will be closed immediately.
        self.__operation_ref = api.create_unary_operation(ColorPhaseOperationDelegate(api))

    def close(self):
        # close will be called when the extension is unloaded. in turn, close any references so they get closed. this
        # is not strictly necessary since the references will be deleted naturally when this object is deleted.
        self.__operation_ref.close()
        self.__operation_ref = None
