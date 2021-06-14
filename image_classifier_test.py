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
INTERPOLATE = 10
# MUST set I2C freq to 1MHz in /boot/config.txt
i2c = busio.I2C(board.SCL, board.SDA)
# low range of the sensor (this will be black on the screen)
MINTEMP =20.0
# high range of the sensor (this will be white on the screen)
MAXTEMP = 36.0

def help():
    print('python classify.py <path_to_model.eim>')

def main():
    for poskusi in range (0,600):
        model = "python idk.py /home/pi/RTLS_FindMyProfessor/modelfile.eim"

        dir_path = os.path.dirname(os.path.realpath(__file__))
        modelfile = os.path.join(dir_path, model)

        # initialize the sensor
        mlx = adafruit_mlx90640.MLX90640(i2c)
        print("MLX addr detected on I2C, Serial #", [hex(i) for i in mlx.serial_number])
        mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
        print(mlx.refresh_rate)
        print("Refresh rate: ", pow(2, (mlx.refresh_rate - 1)), "Hz")

        print('MODEL: ' + modelfile)

        with ImageImpulseRunner("/home/pi/RTLS_FindMyProfessor/modelfile.eim") as runner:
            try:
                model_info = runner.init()
                print('Loaded runner for "' + model_info['project']['owner'] + ' / ' + model_info['project']['name'] + '"')
                labels = model_info['model_parameters']['labels']

                frame = [0] * 768
                while True:
                    try:
                        mlx.getFrame(frame)
                        break
                    except Exception:
                        print(traceback.format_exc())
                        mlx = adafruit_mlx90640.MLX90640(i2c)
                        mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
                        continue  # these happen, no biggie - retry

                pixels = [0] * 768
                for i, pixel in enumerate(frame):
                    if pixel < MINTEMP:
                        pixels[i]=MINTEMP
                    pixels[i] = int((pixel-MINTEMP)*(255/(MAXTEMP-MINTEMP)))

                # pixelrgb = [colors[constrain(int(pixel), 0, COLORDEPTH-1)] for pixel in pixels]
                img2 = Image.new("L", (32, 24))
                img2.putdata(pixels)
                img2 = img2.resize((32 * INTERPOLATE, 24 * INTERPOLATE), Image.BICUBIC)
                img= np.array(img2)
                print(img)
                #img = cv2.imread('/Users/janjongboom/Desktop/jan.jpg')

                features = []

                EI_CLASSIFIER_INPUT_WIDTH = runner.dim[0]
                EI_CLASSIFIER_INPUT_HEIGHT = runner.dim[1]

                in_frame_cols = img.shape[1]
                in_frame_rows = img.shape[0]

                factor_w = EI_CLASSIFIER_INPUT_WIDTH / in_frame_cols
                factor_h = EI_CLASSIFIER_INPUT_HEIGHT / in_frame_rows

                largest_factor = factor_w if factor_w > factor_h else factor_h

                resize_size_w = int(largest_factor * in_frame_cols)
                resize_size_h = int(largest_factor * in_frame_rows)
                resize_size = (resize_size_w, resize_size_h)

                resized = cv2.resize(img, resize_size, interpolation = cv2.INTER_AREA)

                crop_x = int((resize_size_w - resize_size_h) / 2) if resize_size_w > resize_size_h else 0
                crop_y = int((resize_size_h - resize_size_w) / 2) if resize_size_h > resize_size_w else 0

                crop_region = (crop_x, crop_y, EI_CLASSIFIER_INPUT_WIDTH, EI_CLASSIFIER_INPUT_HEIGHT)

                cropped = resized[crop_region[1]:crop_region[1]+crop_region[3], crop_region[0]:crop_region[0]+crop_region[2]]

                if runner.isGrayscale:
                    cropped = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
                    pixels = np.array(cropped).flatten().tolist()
                    for p in pixels:
                        features.append((p << 16) + (p << 8) + p)
                else:
                    cv2.imwrite('test.jpg', cropped)
                    pixels = np.array(cropped).flatten().tolist()
                    for ix in range(0, len(pixels)):
                        b = pixels[ix]
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
