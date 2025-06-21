import cv2
import numpy as np

image = cv2.imread('dcz.jpg')
h, w = image.shape[:2]
r = cv2.getRotationMatrix2D([w // 2, h // 2], -30, 0.75)
r_img = cv2.warpAffine(image, r, (w, h))
f_img = cv2.flip(r_img, 1)
t_img = cv2.warpAffine(f_img, np.float32([1, 0, 50], [0, 1, -20]), (w, h))
cv2.imshow('i', image)
cv2.imshow('t', t_img)
cv2.waitKey(0)
cv2.destroyWindow()


import cv2
import numpy as np

image = cv2.imread('yingbi.jpg')
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (9, 9), 2)
e = cv2.Canny(blurred, 30, 60)
c = cv2.HoughCircles(e, cv2.HOUGH_GRADIENT, 1, 20, param1=60, param2=30, minRadius=30, maxRadius=60)

if c is not None:
    cir = np.uint16(np.around(c))
    for i in cir[0]:
        x, y, r = i[0], i[1], i[2]
        cv2.circle(image, (x, y), r, (0, 255, 0), 2)

    print(len(cir[0]))

cv2.imshow('circles', image)
cv2.waitKey(0)
cv2.destroyAllWindows()


