# blob_tracking
Using simple blob tracking to achieve localization. This was a project created at HackCU Local Hack Day. It is very much so a work in progress. The purpose is to achieve localization using simple markers such as a cluster of multicolored blobs. It is inteneded to be simple so that it is easily manipulated. 

## Dependent upon:
cv2
numpy
ConfigParser

## Use calibrate.py to optimize tracking parameters. 
calibrate.py will update the \[Calibrate] section of "config.ini"
The user can then choose to save this profile as another name, such as \[Pink] as seen in my config.ini

## tracker.py
change these lines to custom profiles to track two colors:
'''
image,cx1,cy1 = tracking(image,"Green2")
image,cx2,cy2 = tracking(image,"Pink")
'''
where Green2 and Pink are profiles found in config.ini

## Usage
simply run by ensuring config.ini, tracker.py, and calibrate.py are in the same directory.

Run calibrate.py simply by inputting:
'''
python calibrate.py
'''

Run tracker.py simply by inputting:
'''
python tracker.py
'''
