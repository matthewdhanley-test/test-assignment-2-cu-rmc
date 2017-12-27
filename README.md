# blob_tracking
Using simple blob tracking to achieve localization. This was a project created at HackCU Local Hack Day. It is very much so a work in progress. The purpose is to achieve localization using simple markers such as a cluster of multicolored blobs. It is inteneded to be simple so that it is easily manipulated. This program will eventually be transistioned to be implemented with ROS. It's inteneded use is for localization of CU's NASA Robotic Mining Competition Club's robot as a part of autonomy.

## Dependent upon:
[cv2](https://docs.opencv.org/2.4/doc/tutorials/introduction/linux_install/linux_install.html), [numpy](https://www.scipy.org/install.html), and ConfigParser

## Use calibrate.py to optimize tracking parameters. 
calibrate.py will update the \[Calibrate] section of "config.ini"
The user can then choose to save this profile as another name, such as \[Pink] as seen in my config.ini
### How this would flow:
1. Run calibrate.py
```
python calibrate.py
```
2. Adjust parameters until color is being tracked accurately in the tracking window. Use the theshold and calibrate windows to help optimize.

3. Once satisfied, tap "s" on your keyboard. This will save the variables into the \[Calibrate] section of "config.ini"

4. Open config.ini in your favorite text editor. Copy and paste all the entries in the \[Calibrate] section, then rename to a custom name. Example:
```
  \[Calibrate]
  hlow = 0
  hhigh = 13
  slow = 41
  shigh = 255
  vlow = 58
  vhigh = 186
  area = 2982
  blur = 31
  ```
  
  
**Copy -> Paste** (and change section name)


  ```
  [Orange]
  hlow = 0
  hhigh = 13
  slow = 41
  shigh = 255
  vlow = 58
  vhigh = 186
  area = 2982
  blur = 31
```


You now have a new profile ready for use in tracker.py!!!!! The name in brackets (i.e. "Orange") is what should be used in tracker.py as seen in the next step.


## tracker.py
Change these lines to custom profiles to track two colors (i.e. a color you created using calibrate.py, procedure above). These lines are currently found in main():
```
image,cx1,cy1 = tracking(image,"Green2")
image,cx2,cy2 = tracking(image,"Pink")
```
where Green2 and Pink are profiles found in config.ini

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
