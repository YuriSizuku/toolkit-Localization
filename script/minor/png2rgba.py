import cv2
import os
import numpy as np

outdir = "out"
if not os.path.exists(outdir): os.os.mkdir(outdir)
for file in os.listdir("./"):
    if os.path.splitext(file)[1] != '.png':
        continue
    img = cv2.imread(file, cv2.IMREAD_UNCHANGED)
    if img.shape[2] < 4:
        imgb, imgg, imgr = cv2.split(img)
        imga = np.ones(imgb.shape, dtype=imgb.dtype) * 255
        img = cv2.merge((imgb, imgg, imgr, imga))
    cv2.imwrite(os.path.join(outdir, file), img[:, : , [2,1,0,3]])
    print(f"convert {file} done!")