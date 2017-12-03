import numpy as np
import matplotlib.pyplot as pyplot
import cv2
import glob
import time
import sys
import io
import math
import ConfigParser

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
    #-------------------------------------------------------------------------------
    # FUNCTION - mask
    # Input Parameters:
    #      rgbimg - red, blue, green channels of an image
    #      hl - low range for hue in hsv
    #      hh - high value for hue in hsv
    #      sl - low for saturation
    #      sh - high for saturation
    #      vl - low for v
    #      vh - high for v
    #-------------------------------------------------------------------------------
    #convert to hsv
    hsv = cv2.cvtColor(rgbimg,cv2.COLOR_BGR2HSV)

    #define lower and upper color limits
    blueLow = np.array([hl,sl,vl])
    blueHigh = np.array([hh,sh,vh])

    #create a mask by selecting pixels that fall within range
    mask = cv2.inRange(hsv,blueLow,blueHigh)

    #use the mask to reveal the image
    res = cv2.bitwise_and(rgbimg,rgbimg,mask=mask)

    return res,mask

def momentXY(c):
    #find center of countour
    M = cv2.moments(c)
    cx = int(M['m10']/M['m00'])
    cy = int(M['m01']/M['m00'])
    return cx,cy

def calibrate():
    #set up the camera feed w/builtin webcam
    camera = cv2.VideoCapture(0)

    # make and place a window
    cv2.namedWindow('calibrate')
    cv2.moveWindow('calibrate',700,0)

    # make and place a window
    cv2.namedWindow('thresh')
    cv2.moveWindow('thresh',1200,0)

    # read in settings from config file
    settings = ConfigSectionMap("Calibrate")
    hl = settings['hlow']
    hh = settings['hhigh']
    sl = settings['slow']
    sh = settings['shigh']
    vl = settings['vlow']
    vh = settings['vhigh']
    a = settings['area']
    b = settings['blur']

    # make the trackbars for calibration
    cv2.createTrackbar('HueLow','calibrate',hl,255,nothing)
    cv2.createTrackbar('HueHigh','calibrate',hh,255,nothing)
    cv2.createTrackbar('satLow','calibrate',sl,255,nothing)
    cv2.createTrackbar('satHigh','calibrate',sh,255,nothing)
    cv2.createTrackbar('vLow','calibrate',vl,255,nothing)
    cv2.createTrackbar('vHigh','calibrate',vh,255,nothing)
    cv2.createTrackbar('area','calibrate',a,100000,nothing)
    cv2.createTrackbar('blur','calibrate',b,30,nothing)
    #start up stream loop
    while(1):
        ret,image = camera.read()

        # Get values from the endless trackbars
        hLow = cv2.getTrackbarPos('HueLow','calibrate')
        hHigh = cv2.getTrackbarPos('HueHigh','calibrate')
        sLow = cv2.getTrackbarPos('satLow','calibrate')
        sHigh = cv2.getTrackbarPos('satHigh','calibrate')
        vLow = cv2.getTrackbarPos('vLow','calibrate')
        vHigh = cv2.getTrackbarPos('vHigh','calibrate')
        area = cv2.getTrackbarPos('area','calibrate')
        blur = cv2.getTrackbarPos('blur','calibrate')
        if blur % 2 == 0:
            blur = blur + 1


        blurimg = cv2.GaussianBlur(image,(blur,blur),0)
        cal,mas = mask(blurimg,hLow,hHigh,sLow,sHigh,vLow,vHigh)
        #threshold the image
        ret, thresh = cv2.threshold(mas,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

        save_text = 's - Save settings to config.ini'
        quit_text = 'q - quit'
        cv2.putText(cal,save_text,(0,20),cv2.FONT_HERSHEY_PLAIN,0.9,(0,0,255))
        cv2.putText(cal,quit_text,(0,40),cv2.FONT_HERSHEY_PLAIN,0.9,(0,0,255))

        #find any countours in the thresholded image
        im2,contours,hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, \
                                                  cv2.CHAIN_APPROX_NONE)
        found_prev = 0
        found_area = 0
        if len(contours) != 0:
            # draw in blue the contours that were found
            cv2.drawContours(cal, contours, -1, 255, 3)

            #find the biggest area
            c = max(contours, key = cv2.contourArea)
            if cv2.contourArea(c) > area:
                found_prev = found_area
                found_area = 1
                #draw a rectangle around the largest contour
                x,y,w,h = cv2.boundingRect(c)
                cv2.putText(image,'Tracking',(x,y-10),cv2.FONT_HERSHEY_PLAIN,\
                            2,(0,0,255),2,cv2.LINE_AA)

                # get the center of the largest centroid as it's probably the object
                # that we are tracking
                cx,cy = momentXY(c)

                #plot the center of the countour
                cv2.circle(image, (cx, cy), 7, (255, 255, 255), -1)
                # draw the book contour (in green)
                cv2.rectangle(image,(x,y),(x+w,y+h),(0,255,0),2)
            else:
                found_area = 0
                found_prev = found_area


        # Show the image
        cv2.imshow("thresh",thresh)
        cv2.imshow("Live feed",image)
        cv2.imshow("calibrate",cal)


        #check for input to quit or save
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            cv2.destroyAllWindows()
            break
        elif key == ord("s"):
            cv2.destroyAllWindows()
            print "Updating Config File"
            updateConfig("Calibrate",hLow,hHigh,sLow,sHigh,vLow,vHigh,area,blur)
            break

    return 1

def control(x,y,imgshape):
    #imgshape - [x,y] shape of the image
    gain = ConfigSectionMap("Controller")['gain']
    middle = imgshape[0]/2
    mag = int(float(middle-x)/middle * gain)


    return mag

def tracking(image,profile):

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
    cx = 0
    cy = 0

    #set up the camera feed w/builtin webcam

    #start up stream loop
    blurimg = cv2.GaussianBlur(image,(blur,blur),0)
    res,mas = mask(blurimg,hLow,hHigh,sLow,sHigh,vLow,vHigh)

    #threshold the image using otsu
    ret, thresh = cv2.threshold(mas,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

    #find any countours in the thresholded image
    im2,contours,hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    found_prev = 0
    found_area = 0
    if len(contours) != 0:
        # draw in blue the contours that were found
        cv2.drawContours(res, contours, -1, 255, 3)

        #find the biggest area
        c = max(contours, key = cv2.contourArea)
        if cv2.contourArea(c) > area:
            found_prev = found_area
            found_area = 1

            #draw a rectangle around the largest contour
            x,y,w,h = cv2.boundingRect(c)
            cv2.putText(image,'Tracking',(x,y-10),cv2.FONT_HERSHEY_PLAIN,2,(0,0,255),2,cv2.LINE_AA)


            # looking at the moment
            cx,cy = momentXY(c)

            # controlling left and right camera movement
            magnitude = control(x,y,image.shape[0:2])
            if not magnitude == 0:
                cv2.arrowedLine(image,(cx,cy),(cx+magnitude,cy),(255,0,0),2)

            #plot the center of the countour
            cv2.circle(image, (cx, cy), 7, (255, 255, 255), -1)

            # draw the book contour (in green)
            cv2.rectangle(image,(x,y),(x+w,y+h),(0,255,0),2)
        else:
            found_area = 0
            found_prev = found_area


    return image,cx,cy

def connectCentroid(image,cx1,cx2,cy1,cy2):
    cv2.line(image, (cx1,cy1), (cx2,cy2), (255,255,0), 2)

def calcLocalize(theta1,theta2,err):
    # this function calculates location based on camera angles

    # calculate the third angle in the triangle
    theta3 = 180 - theta1 - theta2
    x = ConfigSectionMap("PhysicalProps")["cameraseperation"]
    d1 = math.sin(theta2)/math.sin(theta3)*x
    d2 = math.sin(theta1)/math.sin(theta3)*x
    #---------------------------------------------------------------------------
    # STOPPED HERE 12/2/17-13:00:00
    #---------------------------------------------------------------------------

def calcAngle(cx1,cx2,cy1,cy2):
    xdist = abs(cx1-cx2)
    ydist = abs(cy1-cy2)
    x = ConfigSectionMap("PhysicalProps")["blobseperation"]
    try:
        ratio = float(x)/xdist
    except:
        ratio = 1
    print ratio
    return ratio


def main():
    calibrate()

    camera = cv2.VideoCapture(0)

    while(1):
        ret,image = camera.read()
        image,cx1,cy1 = tracking(image,"Green2")
        image,cx2,cy2 = tracking(image,"Pink")
        if cx1 and cx2 and cy1 and cy2:
            connectCentroid(image,cx1,cx2,cy1,cy2)
            calcAngle(cx1,cx2,cy1,cy2)
        cv2.imshow("Live",image)
        #check for input to quit
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            cv2.destroyAllWindows()
            break


if __name__ == '__main__':
    main()
