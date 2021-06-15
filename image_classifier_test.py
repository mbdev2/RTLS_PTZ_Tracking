#!/usr/bin/env python

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


runner = None
# image interpolation factor
INTERPOLATE = 10
# MUST set I2C freq to 1MHz in /boot/config.txt
i2c = busio.I2C(board.SCL, board.SDA)
# low range of the sensor (this will be black on the screen)
MINTEMP =22.0
# high range of the sensor (this will be white on the screen)
MAXTEMP = 38.0

def help():
    print('python classify.py <path_to_model.eim>')

def main():
    model = "/home/pi/RTLS_FindMyProfessor/modelfile.eim"
    dir_path = os.path.dirname(os.path.realpath(__file__))
    modelfile = os.path.join(dir_path, model)
    print('MODEL: ' + modelfile)

    # initialize the sensor
    mlx = adafruit_mlx90640.MLX90640(i2c)
    print("MLX addr detected on I2C, Serial #", [hex(i) for i in mlx.serial_number])
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
    print(mlx.refresh_rate)
    print("Refresh rate: ", pow(2, (mlx.refresh_rate - 1)), "Hz")

    for poskusi in range (0,2000):
        with ImageImpulseRunner(model) as runner:
            try:
                model_info = runner.init()
                #print('Loaded runner for "' + model_info['project']['owner'] + ' / ' + model_info['project']['name'] + '"')
                labels = model_info['model_parameters']['labels']

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
                    else:
                        pixels[i]=frame[i-128]
                    pixels[i] = int((pixels[i]-MINTEMP)*(255/(MAXTEMP-MINTEMP)))

                #use PIL library to interpolate by a factor of INTERPOLATE -> increasing resolution to 320x240 and smoothing out the mosaicing effect
                img2 = Image.new("L", (32, 32)) #the frame should actually be 32x24, but our Object Detection on Edge Impulse is limted to squares
                img2.putdata(pixels)
                img2 = img2.resize((32 * INTERPOLATE, 32 * INTERPOLATE), Image.BICUBIC)
                img= np.array(img2) #since CV uses numpy arrays for image manipulation, we convert our PIL image to an array

                features = []

                cv2.imwrite('test.jpg', img)
                pixels_proc = np.array(img).flatten().tolist()
                for ix in range(0, len(pixels_proc)):
                    b = pixels_proc[ix]
                    features.append((b << 16) + (b << 8) + b)

                res = runner.classify(features)

                if "classification" in res["result"].keys():
                    print('Result (%d ms.) ' % (res['timing']['dsp'] + res['timing']['classification']), end='')
                    for label in labels:
                        score = res['result']['classification'][label]
                        print('%s: %.2f\t' % (label, score), end='')
                    print('', flush=True)


                elif "bounding_boxes" in res["result"].keys():
                    print('Found %d bounding boxes (%d ms.)' % (len(res["result"]["bounding_boxes"]), res['timing']['dsp'] + res['timing']['classification']))
                    for bb in res["result"]["bounding_boxes"]:
                        print('\t%s (%.2f): x=%d y=%d w=%d h=%d' % (bb['label'], bb['value'], bb['x'], bb['y'], bb['width'], bb['height']))
            finally:
                if (runner):
                    runner.stop()

if __name__ == "__main__":
   main()
