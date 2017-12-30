import numpy as np
import cv2
import sys
import math
import ConfigParser
from tracker import *


def nothing(nothing):
    """
    doesn't do anything
    used with trackbars
    """
    pass


def calibrate(blob, filename):

    if filename == -1:
        # set up the camera feed w/builtin webcam
        print "using builtin webcam..."
        camera = cv2.VideoCapture(0)
    else:
        camera = -1

    # make and place a window
    cv2.namedWindow('calibrate')
    cv2.moveWindow('calibrate', 700, 0)

    # make and place a window
    cv2.namedWindow('thresh')
    cv2.moveWindow('thresh', 1200, 0)

    # make the trackbars for calibration
    cv2.createTrackbar('HueLow', 'calibrate', blob.hLow, 255, nothing)
    cv2.createTrackbar('HueHigh', 'calibrate', blob.hHigh, 255, nothing)
    cv2.createTrackbar('satLow', 'calibrate', blob.sLow, 255, nothing)
    cv2.createTrackbar('satHigh', 'calibrate', blob.sHigh, 255, nothing)
    cv2.createTrackbar('vLow', 'calibrate', blob.vLow, 255, nothing)
    cv2.createTrackbar('vHigh', 'calibrate', blob.vHigh, 255, nothing)
    cv2.createTrackbar('area', 'calibrate', blob.area, 100000, nothing)
    cv2.createTrackbar('blur', 'calibrate', blob.blur, 30, nothing)

    # create a temp blob object for updating
    tmpBlob = Blob(blob.color)

    # start up stream loop
    while True:
        if filename == -1:
            ret, image = camera.read()
            if not ret:
                print "Camera not started. Exiting..."
                return
        else:
            image = cv2.imread(filename)
            image = cv2.resize(image, (0, 0), fx=0.2, fy=0.2)

        # Get values from the trackbars
        tmpBlob.hLow = cv2.getTrackbarPos('HueLow', 'calibrate')
        tmpBlob.hHigh = cv2.getTrackbarPos('HueHigh', 'calibrate')
        tmpBlob.sLow = cv2.getTrackbarPos('satLow', 'calibrate')
        tmpBlob.sHigh = cv2.getTrackbarPos('satHigh', 'calibrate')
        tmpBlob.vLow = cv2.getTrackbarPos('vLow', 'calibrate')
        tmpBlob.vHigh = cv2.getTrackbarPos('vHigh', 'calibrate')
        tmpBlob.area = cv2.getTrackbarPos('area', 'calibrate')
        tmpBlob.blur = cv2.getTrackbarPos('blur', 'calibrate')

        # can't have an even kernel size for blurring so make it odd.
        if tmpBlob.blur % 2 == 0:
            tmpBlob.blur = tmpBlob.blur + 1

        blurimg = cv2.GaussianBlur(image, (tmpBlob.blur, tmpBlob.blur), 0)
        cal, mas = mask(blurimg, tmpBlob)

        # threshold the image
        ret, thresh = cv2.threshold(mas, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)

        # User interface text
        save_text = 's - Save settings to config.ini'
        quit_text = 'q - quit'
        cv2.putText(cal, save_text, (0, 20), cv2.FONT_HERSHEY_PLAIN, 0.9, (0, 0, 255))
        cv2.putText(cal, quit_text, (0, 40), cv2.FONT_HERSHEY_PLAIN, 0.9, (0, 0, 255))

        # find any countours in the thresholded image
        im2, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                                                  cv2.CHAIN_APPROX_NONE)
        if len(contours) != 0:
            # draw in blue the contours that were found
            cv2.drawContours(cal, contours, -1, 255, 3)

            # find the biggest area
            c = max(contours, key=cv2.contourArea)
            if cv2.contourArea(c) > tmpBlob.area:

                # set calibrate area
                tmpBlob.calibrateMass = cv2.contourArea(c)

                # draw a rectangle around the largest contour
                x, y, w, h = cv2.boundingRect(c)
                cv2.putText(image,'Tracking',(x,y-10),cv2.FONT_HERSHEY_PLAIN,
                            2, (0, 0, 255), 2, cv2.LINE_AA)

                # get the center of the largest centroid as it's probably the object
                # that we are tracking
                cx, cy = momentXY(c)

                # plot the center of the countour
                cv2.circle(image, (cx, cy), 7, (255, 255, 255), -1)
                # draw the book contour (in green)
                cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)

        # Show the image
        cv2.imshow("thresh", thresh)
        cv2.imshow("Live feed", image)
        cv2.imshow("calibrate", cal)

        # check for input to quit or save
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            cv2.destroyAllWindows()
            break
        elif key == ord("s"):
            cv2.destroyAllWindows()
            print "Updating Config File"
            updateConfig(tmpBlob)
            break

    return 0


def main():

    argdict = parseargs()

    try:
        filename = argdict['-f']
    except KeyError:
        filename = -1

    profilename = "Calibrate"

    try:
        profilename = argdict['-u']
    except KeyError:
        pass
    try:
        profilename = argdict['-n']
        add_section(profilename)
    except KeyError:
        pass

    # Create a Blob object to calibrate
    blob = Blob(profilename)

    calibrate(blob, filename)


if __name__ == '__main__':
    main()
