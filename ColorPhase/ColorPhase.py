#ColorPhase, by Zeno Dellby
#installed by putting it into a folder in the PlugIns directory,
#along with a file named __init__.py whose only contents are
#
#import ColorPhase
#

import gettext
import math

import numpy as np


# local libraries
from nion.swift import Application
from nion.swift.model import Image
from nion.swift.model import Operation

_ = gettext.gettext  # for translation

#The operation class. Functions in it are called by Swift.
class ColorPhaseOperation(Operation.Operation):
    def __init__(self):
        super(ColorPhaseOperation, self).__init__(_("Color Phase"), "color-phase-operation")

    #This is called whenever Swift wants to update the Color Phase image
    def get_processed_data(self, data_sources, values):
        img = data_sources[0].data
        if img is None:
            return None
        grad = np.zeros(img.shape+(3L,),dtype=np.uint8) # rgb format
        # grad will be returned at the end, then Swift will identify it as rgb and display it as such.
        w = img.shape[0] #w and h are much shorter to read than img.shape[0] and img.shape[1]
        h = img.shape[1]
        if Image.is_data_complex_type(img): #If it's complex, we want to show the phase data, otherwise just a color map
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
        return grad #Return an image to Swift either way, because that's what it wants


#The following is code for making this into a process you can click on in the processing menu

def processing_color_phase(document_controller):
    display_specifier = document_controller.selected_display_specifier
    return document_controller.add_processing_operation_by_id(display_specifier.buffered_data_source_specifier,
                                                              "color-phase-operation", prefix=_("Color Phase of "))

def build_menus(document_controller): #makes the Show Color Phase Button
    document_controller.processing_menu.add_menu_item(_("Color Phase"), lambda: processing_color_phase(document_controller))

Application.app.register_menu_handler(build_menus) #called on import to make the Show Color Phase Button

Operation.OperationManager().register_operation("color-phase-operation", lambda: ColorPhaseOperation())
