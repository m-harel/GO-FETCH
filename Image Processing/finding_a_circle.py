import numpy as np
import cv2
import sys
#import rospy

cam = cv2.VideoCapture(0)

while(True):
    # Capture frame-by-frame
    _, frame = cam.read()

    frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cv2.imshow('tracker',frame)

    gray = cv2.medianBlur(frameGray, 5)
    circles = cv2.HoughCircles(frameGray, cv2.HOUGH_GRADIENT, 1, 70,
                              param1=100, param2=100,
                              minRadius=5, maxRadius=200)

    if circles is not None:
        circles = np.uint16(np.around(circles))
        maxrad=0
        for i in circles[0, :]:
            if i[2]>maxrad:
                center = (i[0], i[1])
                maxrad=i[2]
        # circle center
        cv2.circle(frame, center, 1, (0, 100, 100), 3)
        # circle outline
        cv2.circle(frame, center, maxrad, (255, 0, 255), 3)
        cv2.imshow("detected circles", frame)
        print("center at: ", center)
        print("radius is: ",maxrad)


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


# When everything done, release the capture
cam.release()
cv2.destroyAllWindows()


