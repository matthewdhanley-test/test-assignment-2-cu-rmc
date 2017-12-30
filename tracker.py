import numpy as np
import cv2
import math
import ConfigParser
import sys
import re


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
        self.apparentMass = 0
        self.neighbors = {}

        # read in config file settings
        try:
            self.settings = ConfigSectionMap(color)
        except ConfigParser.NoSectionError as err:
            print("ERROR: Could not find profile in config.ini: \"" + color + "\"")
            sys.exit(1)
        self.hLow = self.settings['hlow']
        self.hHigh = self.settings['hhigh']
        self.sLow = self.settings['slow']
        self.sHigh = self.settings['shigh']
        self.vLow = self.settings['vlow']
        self.vHigh = self.settings['vhigh']
        self.area = self.settings['area']
        self.blur = self.settings['blur']
        self.calibrateMass = self.settings['calibratemass']

    def percent_visible(self):
        percent = float(self.apparentMass)/self.calibrateMass
        return percent

    def add_neighbor(self, blob):
        n = Neighbor(self, blob)
        self.neighbors[blob] = n

    def remove_neighbor(self, blob):
        self.neighbors.pop(blob,None)

    def find_neighbor(self, blob):
        if blob in self.neighbors:
            return True
        else:
            return False


class Neighbor(object):
    def __init__(self, blob1, blob2):
        self.angle = self.calc_angle(blob1, blob2)
        self.home = blob1.color
        self.neighbor = blob2.color
        self.distance = self.calc_distance(blob1, blob2)
        self.xdist = blob1.cx - blob2.cx
        self.ydist = blob1.cy - blob2.cy

    @staticmethod
    def calc_angle(blob1, blob2):
        xdist = blob1.cx - blob2.cx
        ydist = blob1.cy - blob2.cy
        try:
            angle = math.atan(float(ydist) / xdist)
        except ZeroDivisionError:
            angle = math.atan(float(ydist) / 0.00001)
        return angle

    @staticmethod
    def calc_distance(blob1, blob2):
        xdist = abs(blob1.cx - blob2.cx)
        ydist = (blob1.cy - blob2.cy)
        distance = math.sqrt(xdist ** 2 + ydist ** 2)
        return distance


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
    Config.set(profile, 'calibratemass', blob.calibrateMass)
    with open(r'config.ini', 'wb') as configfile:
        Config.write(configfile)
    print "Updated config.ini"


def add_section(color):
    Config = ConfigParser.RawConfigParser()
    Config.read("config.ini")
    profile = color
    Config.add_section(profile)
    Config.set(profile, 'hhigh', 255)
    Config.set(profile, 'hlow', 0)
    Config.set(profile, 'slow', 0)
    Config.set(profile, 'shigh', 255)
    Config.set(profile, 'vhigh', 255)
    Config.set(profile, 'vlow', 0)
    Config.set(profile, 'area', 0)
    Config.set(profile, 'blur', 0)
    Config.set(profile, 'calibratemass', 10)
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
    blurimg = cv2.GaussianBlur(image,(blob.blur, blob.blur), 0)

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

            # set what the camera is seeing
            blob.apparentMass = cv2.contourArea(c)

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

            magnitude = control(x, y, image.shape[0:2])

            if not magnitude == 0:
                cv2.arrowedLine(image, (cx, cy), (cx+magnitude, cy), (255, 0, 0), 2)
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


def blob_graph(bloblist):
    for blob1 in bloblist:
        for blob2 in bloblist:
            if blob1 != blob2 and not blob1.tracked:
                if blob1.find_neighbor(blob2):
                    blob1.remove_neighbor(blob2)
            elif blob1 != blob2 and blob1.tracked and blob2.tracked:
                if not blob1.find_neighbor(blob2):
                    blob1.add_neighbor(blob2)


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

        blob_graph(bloblist)

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
    for arg in sys.argv:
        if arg[0] == '-':
            if tmp:
                argdict[key] = tmp
                tmp = []
            key = arg
            if re.match('-\w',key):
                try:
                    argdict[key] = sys.argv[sys.argv.index(key) + 1]
                except IndexError:
                    print sys.argv[0] + ": Unexpected or incorrect command line argument"
                    sys.exit(1)
            continue
        tmp.append(arg)
    return argdict


def main():

    # Get any input arguements
    argdict = parseargs()
    try:
        filename = argdict['-f']
    except KeyError:
        filename = -1

    # This is a list of blobs
    bloblist = [Blob("Skin"), Blob("Red")]

    if filename != -1:
        phototracking(filename, bloblist)
    else:
        cameratracking(bloblist)


if __name__ == '__main__':
    main()
