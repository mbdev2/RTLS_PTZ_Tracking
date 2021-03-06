import cv2
import os
import time
import argparse
from PIL import Image
import sys, getopt
import numpy as np
from edge_impulse_linux.image import ImageImpulseRunner
import board
import busio
import adafruit_mlx90640
import traceback

# image interpolation factor
INTERPOLATE = 10
# MUST set I2C freq to 1MHz in /boot/config.txt
i2c = busio.I2C(board.SCL, board.SDA)
# low range of the sensor (this will be black on the screen)
MINTEMP =20.0
# high range of the sensor (this will be white on the screen)
MAXTEMP = 38.0

def help():
 print('python image_collection_test.py')

def main():
    # initialize the sensor
    mlx = adafruit_mlx90640.MLX90640(i2c)
    print("MLX addr detected on I2C, Serial #", [hex(i) for i in mlx.serial_number])
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
    print(mlx.refresh_rate)
    print("Refresh rate: ", pow(2, (mlx.refresh_rate - 1)), "Hz")

    for poskusi in range (400,480):
        # capture thermal frame
        frame = [0] * 768
        while True:
         try:
             mlx.getFrame(frame)
             break
         except Exception:
             #in case we get a traceback error, we just retry the connection and go again, no biggie
             print(traceback.format_exc())
             mlx = adafruit_mlx90640.MLX90640(i2c)
             mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
             continue

        #Limit the temp range between MINTEMP and MAXTEMP for higher accuracy
        pixels = [0] * 1024
        for i in range(0,1023):
            if i<128 or i>895:
                pixels[i]=MINTEMP
            elif frame[i-128] < MINTEMP:
                pixels[i]=MINTEMP
            elif frame[i-128] > MAXTEMP:
                pixels[i]=MAXTEMP
            else:
                pixels[i]=frame[i-128]
            pixels[i] = int((pixels[i]-MINTEMP)*(255/(MAXTEMP-MINTEMP)))

        #use PIL library to interpolate by a factor of INTERPOLATE -> increasing resolution to 320x240 and smoothing out the mosaicing effect
        base = Image.new("L", (32, 32)) #the frame should actually be 32x24, but our Object Detection on Edge Impulse is limted to squares
        base.putdata(pixels)
        base = base.resize((32 * INTERPOLATE, 32 * INTERPOLATE), Image.BICUBIC)
        img_mirror= base.transpose(method=Image.FLIP_LEFT_RIGHT)
        img= np.array(img_mirror) #since CV uses numpy arrays for image manipulation, we convert our PIL image to an array

        #save images to disk
        name="/home/pi/Desktop/RTLS_FindMyProfessor/testing/pics/collection_"+str(poskusi)+".png"
        cv2.imwrite(name, img)
        print("Saved image ", poskusi)


if __name__ == "__main__":
    main()
