# blob_tracking
Using simple blob tracking to achieve localization. This was a project created at HackCU Local Hack Day. It is very much so a work in progress. The purpose is to achieve localization using simple markers such as a cluster of multicolored blobs. It is inteneded to be simple so that it is easily manipulated. This program will eventually be transistioned to be implemented with ROS. It's inteneded use is for localization of CU's NASA Robotic Mining Competition Club's robot as a part of autonomy.

## Dependent upon:
[cv2](https://docs.opencv.org/2.4/doc/tutorials/introduction/linux_install/linux_install.html), [numpy](https://www.scipy.org/install.html), and ConfigParser

## Use calibrate.py to optimize tracking parameters. 
calibrate.py will update the \[Calibrate] (unless otherwise specified with command line arguments) section of "config.ini"
### How this would flow:
### 1. Run calibrate.py
```
python calibrate.py
```
### 2. Adjust parameters until color is being tracked accurately in the tracking window. Use the theshold and calibrate windows to help optimize.

### 3. Once satisfied, tap "s" on your keyboard. This will save the variables into the \[Calibrate] section of "config.ini"

### Updating/Adding profiles
To add a profile to the config file, use the command argument \-n. For example, to add a "Blue" section:
```
python calibrate.py -n Blue
```

To update a profile in the config file, use the command line argument \-u. For example, to update "Red" section:
```
python calibrate.py -u Red
```

You now have a new profile ready for use in tracker.py!!!!!


## tracker.py

To specify profiles to be tracked, change this line to include profiles (i.e. a color you created using calibrate.py, procedure above). This line is currently found in main():
```
# this is a list of blobs
bloblist = [Blob("Blue"), Blob("Red")]
```
where Blue and Red are profiles found in config.ini. You can add as many profiles (as long as they exist in config.ini) as you would like!

## Usage
Simply run by ensuring config.ini, tracker.py, and calibrate.py are in the same directory.

Run calibrate.py simply by inputting:
```
python calibrate.py
```
for the built-in webcam or:
```
python calibrate.py -f [filename]
```
for a photo specified using a filepath.


Run tracker.py simply by inputting:
```
python tracker.py
```
for the built-in webcam or:
```
python tracker.py -f [filename]
```
for an image file specified using a filepath.

**Please contact me with errors and/or questions. This is very much so still a WIP.**
