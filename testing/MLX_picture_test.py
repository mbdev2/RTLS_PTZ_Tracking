# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""This example is for Raspberry Pi (Linux) only!
   It will not work on microcontrollers running CircuitPython!"""


import os
import math
import time
import argparse
from PIL import Image
import pygame
import board
import busio

import adafruit_mlx90640

INTERPOLATE = 10

# MUST set I2C freq to 1MHz in /boot/config.txt
i2c = busio.I2C(board.SCL, board.SDA)

# low range of the sensor (this will be black on the screen)
MINTEMP =20.0
# high range of the sensor (this will be white on the screen)
MAXTEMP = 36.0

# initialize the sensor
mlx = adafruit_mlx90640.MLX90640(i2c)
print("MLX addr detected on I2C, Serial #", [hex(i) for i in mlx.serial_number])
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
print(mlx.refresh_rate)
print("Refresh rate: ", pow(2, (mlx.refresh_rate - 1)), "Hz")

frame = [0] * 768
for samplesNum in range(168,600):
    try:
        mlx.getFrame(frame)
    except ValueError:
        print("Happens")
        continue  # these happen, no biggie - retry

    pixels = [0] * 768
    for i, pixel in enumerate(frame):
        if pixel < MINTEMP:
            pixels[i]=MINTEMP
        pixels[i] = int((pixel-MINTEMP)*(255/(MAXTEMP-MINTEMP)))

    # pixelrgb = [colors[constrain(int(pixel), 0, COLORDEPTH-1)] for pixel in pixels]
    if samplesNum%2==0:
        img = Image.new("L", (32, 24))
        img.putdata(pixels)
        img = img.resize((32 * INTERPOLATE, 24 * INTERPOLATE), Image.BICUBIC)
        name="2sample "+str(samplesNum/2)+".png"
        img.save(name)
        print("Saved sample ", samplesNum)
