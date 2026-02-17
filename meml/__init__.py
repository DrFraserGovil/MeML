
# from meml.people import *
import meml.util
import meml.meeting_object as main
import meml.output

def Initialise():
    file,modes,output = meml.util.parseArgs()
    obj = main.Meeting(file)

    for mode in modes:
        meml.output.ToTex(obj,mode,file,output)