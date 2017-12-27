import numpy as np
import cv2
import math
import ConfigParser
import sys

def nothing(x):
    pass


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


def updateConfig(profile,hLow,hHigh,sLow,sHigh,vLow,vHigh,area,blur):
    Config = ConfigParser.RawConfigParser()
    Config.read("config.ini")
    Config.set('Calibrate','hhigh',hHigh)
    Config.set('Calibrate','hlow',hLow)
    Config.set('Calibrate','slow',sLow)
    Config.set('Calibrate','shigh',sHigh)
    Config.set('Calibrate','vhigh',vHigh)
    Config.set('Calibrate','vlow',vLow)
    Config.set('Calibrate','area',area)
    Config.set('Calibrate','blur',blur)
    with open(r'config.ini', 'wb') as configfile:
        Config.write(configfile)
    print "Updated config.ini"


def mask(rgbimg,hl,hh,sl,sh,vl,vh):
    # -------------------------------------------------------------------------------
    # FUNCTION - mask
    # Input Parameters:
    #      rgbimg - red, blue, green channels of an image
    #      hl - low range for hue in hsv
    #      hh - high value for hue in hsv
    #      sl - low for saturation
    #      sh - high for saturation
    #      vl - low for v
    #      vh - high for v
    # -------------------------------------------------------------------------------
    # convert to hsv
    hsv = cv2.cvtColor(rgbimg, cv2.COLOR_BGR2HSV)

    # define lower and upper color limits
    blueLow = np.array([hl, sl, vl])
    blueHigh = np.array([hh, sh, vh])

    # create a mask by selecting pixels that fall within range
    mask = cv2.inRange(hsv, blueLow, blueHigh)

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


def tracking(image,profile):
    # this function takes in an image and a profile from the config file.
    # the profile should be created using the calibrate program
    # this function returns a centroid and an image with a bounding box and the
    # centroid marked

    # read in config file settings
    settings = ConfigSectionMap(profile)

    hLow = settings['hlow']
    hHigh = settings['hhigh']
    sLow = settings['slow']
    sHigh = settings['shigh']
    vLow = settings['vlow']
    vHigh = settings['vhigh']
    area = settings['area']
    blur = settings['blur']

    # init the centroid
    cx = 0
    cy = 0

    # blur the image
    blurimg = cv2.GaussianBlur(image,(blur,blur),0)

    # mask to the parameters defined in config.ini
    res,mas = mask(blurimg,hLow,hHigh,sLow,sHigh,vLow,vHigh)

    # threshold the image using otsu (binary vision)
    ret, thresh = cv2.threshold(mas,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

    # find any countours in the thresholded image
    im2,contours,hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if len(contours) != 0:
        # draw in blue the contours that were found
        cv2.drawContours(res, contours, -1, 255, 3)

        # find the biggest area
        c = max(contours, key=cv2.contourArea)

        # see if contour is large enough to be significant. witout this check,
        # random noise would be enough to trigger the tracker
        if cv2.contourArea(c) > area:
            # draw a rectangle around the largest contour
            x, y, w, h = cv2.boundingRect(c)

            # plot the center of the countour
            cv2.circle(image, (cx, cy), 7, (255, 255, 255), -1)

            # draw the book contour (in green)
            cv2.rectangle(image,(x,y),(x+w,y+h),(0,255,0),2)

            # label the rectangle
            cv2.putText(image,'Tracking',(x,y-10),cv2.FONT_HERSHEY_PLAIN,2,\
                        (0,0,255),2,cv2.LINE_AA)

            # get the moment of the blob
            cx, cy = momentXY(c)

            # controlling left and right camera movement
            # simulate gain with an arrow

            magnitude = control(x,y,image.shape[0:2])

            if not magnitude == 0:
                cv2.arrowedLine(image,(cx,cy),(cx+magnitude,cy),(255,0,0),2)
        else:
            pass


    return image,cx,cy


def connectCentroid(image, cx1, cx2, cy1, cy2):
    # draws a line between centroids
    cv2.line(image, (cx1, cy1), (cx2, cy2), (255, 255, 0), 2)


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


def cameratracking():
    # init the camera
    print "Running with webcam..."
    try:
        camera = cv2.VideoCapture(0)
    except:
        print "Could not set up camera. Exiting..."
        return

    # video loop
    while True:
        # get an image
        ret, image = camera.read()

        if not ret:
            print "Failed to read from camera. Exiting..."
            break

        # track colors from config.ini
        image, cx1, cy1 = tracking(image, "Skin")
        image, cx2, cy2 = tracking(image, "Red")

        # if tracking the two colors, connect the centroids and do math
        if cx1 and cx2 and cy1 and cy2:
            connectCentroid(image, cx1, cx2, cy1, cy2)
            calcAngle(cx1, cx2, cy1, cy2)

        # visualize the data
        cv2.imshow("Live", image)

        # check for input to quit
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            cv2.destroyAllWindows()
            break


def phototracking(filename):
    image = cv2.imread(filename)
    image = cv2.resize(image, (0, 0), fx=0.2, fy=0.2)
    # track colors from config.ini
    image, cx1, cy1 = tracking(image, "Yellow")
    image, cx2, cy2 = tracking(image, "Red")
    image, cx3, cy3 = tracking(image, "Orange")
    image, cx4, cy4 = tracking(image, "Green")


    # if tracking the two colors, connect the centroids and do math
    if cx1 and cx2 and cy1 and cy2:
        connectCentroid(image, cx1, cx2, cy1, cy2)
        connectCentroid(image, cx2, cx3, cy2, cy3)
        connectCentroid(image, cx3, cx4, cy3, cy4)
        connectCentroid(image, cx4, cx1, cy4, cy1)

        calcAngle(cx1, cx2, cy1, cy2)


    while True:
        # visualize the data
        cv2.imshow(filename, image)

        # check for input to quit
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            cv2.destroyAllWindows()
            break

def main():
    dict = {}
    tmp = []
    key = ''
    filename = -1
    for arg in sys.argv:
        if arg[0] == '-':
            if tmp != []:
                dict[key] = tmp
                tmp = []
            key = arg
            if key == '-f':
                dict[key] = sys.argv[sys.argv.index(key)+1]
                filename = dict[key]
                print "Using file: "
                print filename
                break
            continue
        tmp.append(arg)
    if filename != -1:
        phototracking(filename)
    else:
        cameratracking()

if __name__ == '__main__':
    main()
