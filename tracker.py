import numpy as np
import cv2
import math
import ConfigParser
import sys


class Blob(object):
    def __init__(self, color):
        '''
        :param color: string profile name found in config.ini
        '''
        self.cx = 0
        self.cy = 0
        self.color = color
        self.distance = 0.0
        self.tracked = 0  # flag for if being tracked or not

        # read in config file settings
        self.settings = ConfigSectionMap(color)
        self.hLow = self.settings['hlow']
        self.hHigh = self.settings['hhigh']
        self.sLow = self.settings['slow']
        self.sHigh = self.settings['shigh']
        self.vLow = self.settings['vlow']
        self.vHigh = self.settings['vhigh']
        self.area = self.settings['area']
        self.blur = self.settings['blur']


def ConfigSectionMap(section):
    # helper function to get values from the config file
    Config = ConfigParser.ConfigParser()
    Config.read("config.ini")
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.getint(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1


def updateConfig(blob):
    Config = ConfigParser.RawConfigParser()
    Config.read("config.ini")
    profile = blob.color
    Config.set(profile, 'hhigh', blob.hHigh)
    Config.set(profile, 'hlow', blob.hLow)
    Config.set(profile, 'slow', blob.sLow)
    Config.set(profile, 'shigh', blob.sHigh)
    Config.set(profile, 'vhigh', blob.vHigh)
    Config.set(profile, 'vlow', blob.vLow)
    Config.set(profile, 'area', blob.area)
    Config.set(profile, 'blur', blob.blur)
    with open(r'config.ini', 'wb') as configfile:
        Config.write(configfile)
    print "Updated config.ini"


def mask(rgbimg, blob):
    """
    :param rgbimg: red, blue, green channels of an image
    :param blob: Blob object
    :return: res and mask numpy arrays
    """
    # convert to hsv
    hsv = cv2.cvtColor(rgbimg, cv2.COLOR_BGR2HSV)

    # define lower and upper color limits
    colorLow = np.array([blob.hLow, blob.sLow, blob.vLow])
    colorHigh = np.array([blob.hHigh, blob.sHigh, blob.vHigh])

    # create a mask by selecting pixels that fall within range
    mask = cv2.inRange(hsv, colorLow, colorHigh)

    # use the mask to reveal the image
    res = cv2.bitwise_and(rgbimg, rgbimg, mask=mask)

    return res, mask


def momentXY(c):
    # find center of contour
    m = cv2.moments(c)
    cx = int(m['m10']/m['m00'])
    cy = int(m['m01']/m['m00'])
    return cx, cy


def control(x, y, imgshape):
    # imgshape - [x,y] shape of the image
    # this will eventually be used to provide control for a motor mounted webcam
    gain = ConfigSectionMap("Controller")['gain']
    middle = imgshape[0]/2
    mag = int(float(middle-x)/middle * gain)

    return mag


def tracking(image, blob):
    """
    this function takes in an image and a profile from the config file.
    the profile should be created using the calibrate program
    this function returns a centroid and an image with a bounding box and the
    centroid marked
    :param image: image file
    :param profile: profile that is being tracked
    :return: image, x and y locations of centroid
    """


    # init the centroid
    cx = blob.cx
    cy = blob.cy

    # blur the image
    blurimg = cv2.GaussianBlur(image,(blob.blur,blob.blur),0)

    # mask to the parameters defined in config.ini
    res, mas = mask(blurimg, blob)

    # threshold the image using otsu (binary vision)
    ret, thresh = cv2.threshold(mas,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

    # find any countours in the thresholded image
    im2, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    if len(contours) != 0:
        # draw in blue the contours that were found
        cv2.drawContours(res, contours, -1, 255, 3)

        # find the biggest area
        c = max(contours, key=cv2.contourArea)

        # see if contour is large enough to be significant. witout this check,
        # random noise would be enough to trigger the tracker
        if cv2.contourArea(c) > blob.area:
            # draw a rectangle around the largest contour
            x, y, w, h = cv2.boundingRect(c)

            # plot the center of the countour
            cv2.circle(image, (cx, cy), 7, (255, 255, 255), -1)

            # draw the outlining contour (in green)
            cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)

            # label the rectangle
            cv2.putText(image,'Tracking',(x,y-10),cv2.FONT_HERSHEY_PLAIN,2,\
                        (0,0,255),2,cv2.LINE_AA)

            # get the moment of the blob
            cx, cy = momentXY(c)

            # update the object
            blob.cx = cx
            blob.cy = cy
            blob.tracked = 1

            # controlling left and right camera movement
            # simulate gain with an arrow

            magnitude = control(x,y,image.shape[0:2])

            if not magnitude == 0:
                cv2.arrowedLine(image,(cx,cy),(cx+magnitude,cy),(255,0,0),2)
        else:
            # not being tracked
            blob.tracked = 0

    return image


def connectCentroid(image, bloblist):
    # draws a line between centroids
    for blob1 in bloblist:
        for blob2 in bloblist:
            if blob1 != blob2 and blob1.tracked and blob2.tracked:
                cv2.line(image, (blob1.cx, blob1.cy), (blob2.cx, blob2.cy), (255, 255, 0), 2)



def calcLocalize(theta1, theta2, err):
    # this function calculates location based on camera angles
    # not currently used but will be used to localize the camera relative to the
    # blob beacon

    # calculate the third angle in the triangle
    theta3 = 180 - theta1 - theta2
    x = ConfigSectionMap("PhysicalProps")["cameraseperation"]
    d1 = math.sin(theta2)/math.sin(theta3)*x
    d2 = math.sin(theta1)/math.sin(theta3)*x
    # ---------------------------------------------------------------------------
    # STOPPED HERE 12/2/17-13:00:00
    # ---------------------------------------------------------------------------


def calcAngle(cx1, cx2, cy1, cy2):
    # this function is WIP
    # will be used to calculate the angle of the camera relative to the beacon
    xdist = abs(cx1-cx2)
    ydist = abs(cy1-cy2)
    x = ConfigSectionMap("PhysicalProps")["blobseperation"]
    try:
        ratio = float(x)/xdist
    except:
        # sometimes we divide by zero so big
        ratio = 100000
    return ratio


def cameratracking(bloblist):
    # init the camera
    print "Running with webcam..."
    try:
        camera = cv2.VideoCapture(0)
    except:
        RuntimeError('Cannot set up camera')

    # video loop
    while True:
        # get an image
        ret, image = camera.read()

        if not ret:
            print "Failed to read from camera. Exiting..."
            break

        # track colors from config.ini
        for blob in bloblist:
            image = tracking(image, blob)

        # if tracking the two colors, connect the centroids and do math
        connectCentroid(image, bloblist)

        # visualize the data
        cv2.imshow("Live", image)

        # check for input to quit
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            cv2.destroyAllWindows()
            break


def phototracking(filename,bloblist):
    image = cv2.imread(filename)
    image = cv2.resize(image, (0, 0), fx=0.2, fy=0.2)

    for blob in bloblist:
        image = tracking(image, blob)

    connectCentroid(image, bloblist)

    while True:
        # visualize the data
        cv2.imshow(filename, image)

        # check for input to quit
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            cv2.destroyAllWindows()
            break


def parseargs():
    argdict = {}
    tmp = []
    key = ''
    filename = -1
    for arg in sys.argv:
        if arg[0] == '-':
            if tmp:
                argdict[key] = tmp
                tmp = []
            key = arg
            if key == '-f':
                argdict[key] = sys.argv[sys.argv.index(key) + 1]
                filename = argdict[key]
                print "Using file: "
                print filename
                break
            continue
        tmp.append(arg)
    return filename


def main():

    # Get any input arguements
    filename = parseargs()

    # Create some Blob objects
    greenblob = Blob("Green")
    yellowblob = Blob("Yellow")
    redblob = Blob("Red")

    # this is a list of blobs created above
    bloblist = [greenblob, yellowblob, redblob]

    if filename != -1:
        phototracking(filename, bloblist)
    else:
        cameratracking(bloblist)


if __name__ == '__main__':
    main()
