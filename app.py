#App with local maximums
#External libraries
from flask import Flask, render_template, redirect, request
import numpy
import asyncio
from flask_socketio import SocketIO, emit
import logging
import threading
import time
import board
import busio
import adafruit_mlx90640
import requests
import random
from time import sleep
from threading import Thread, Event
import functools
import cv2
import os
import argparse
from PIL import Image
import sys, getopt
import numpy as np
import traceback
import math

#test flask setup with debugging
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

avtonomijaONOFF = False #global variable to control stop/ start of autonomous tracking
INTERPOLATE = 10 #image interpolation factor
MINTEMP =22.0 #low range of the sensor (this will be black on the screen)
MAXTEMP = 38.0 #high range of the sensor (this will be white on the screen)
DEBUG=True
starX=0 #previous X coordinate (used to elimiante jitter i.e. motion within a certain amount of pixels)
starY=0 #previous Y coordinate

socketio = SocketIO(app, async_mode=None, logger=True, engineio_logger=True) #enables our flask server to use websockets for dynamic updates

#enable threading
thread = None
thread_stop_event = Event()


def api_call_PT(pan_val_hex, tilt_val_hex):
    # Request API for Pan and Tilt axis with slow speed limit for smoother motion
    # GET http://212.101.141.80/cgi-bin/aw_ptz
    try:
        response = requests.get(
            url="http://212.101.141.80/cgi-bin/aw_ptz",
            params={
                "cmd": "#APS"+str(pan_val_hex)+str(tilt_val_hex)+"0E0",
                "res": "1",
            },
            headers={
                "Cookie": "Session=0",
            },
        )
        print('Response HTTP Status Code: {status_code}'.format(
            status_code=response.status_code))
        print('Response HTTP Response Body: {content}'.format(
            content=response.content))
    except requests.exceptions.RequestException:
        print('HTTP Request failed')

def api_call_PT_fast(pan_val_hex, tilt_val_hex):
    # Request API for Pan and Tilt axis with no speed limit
    # GET http://212.101.141.80/cgi-bin/aw_ptz
    try:
        response = requests.get(
            url="http://212.101.141.80/cgi-bin/aw_ptz",
            params={
                "cmd": "#APC"+str(pan_val_hex)+str(tilt_val_hex),
                "res": "1",
            },
            headers={
                "Cookie": "Session=0",
            },
        )
        print('Response HTTP Status Code: {status_code}'.format(
            status_code=response.status_code))
        print('Response HTTP Response Body: {content}'.format(
            content=response.content))
    except requests.exceptions.RequestException:
        print('HTTP Request failed')

def api_call_Z(zoom_val_hex):
    # Request APi for Zoom axis
    # GET http://212.101.141.80/cgi-bin/aw_ptz
    print(zoom_val_hex)
    try:
        response = requests.get(
            url="http://212.101.141.80/cgi-bin/aw_ptz",
            params={
                "cmd": "#AXZ"+str(zoom_val_hex),
                "res": "1",
            },
            headers={
                "Cookie": "Session=0",
            },
        )
        print('Response HTTP Status Code: {status_code}'.format(
            status_code=response.status_code))
        print('Response HTTP Response Body: {content}'.format(
            content=response.content))
    except requests.exceptions.RequestException:
        print('HTTP Request failed')

def rtlsRun():
    global avtonomijaONOFF
    global starX
    global starY
    global DEBUG
    #initialize the MLX90640 sensor
    i2c = busio.I2C(board.SCL, board.SDA) #MUST set I2C freq to 1MHz in /boot/config.txt
    mlx = adafruit_mlx90640.MLX90640(i2c) #initialize I2C connection with the camera
    print("MLX addr detected on I2C, Serial #", [hex(i) for i in mlx.serial_number])
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ #set the camera refresh rate to 4Hz
    print(mlx.refresh_rate)
    print("Refresh rate: ", pow(2, (mlx.refresh_rate - 1)), "Hz")

    while not thread_stop_event.isSet(): #ifinite loop until the thread is killed
        #capture thermal frame
        frame = [0] * 768 #1D array consisting of 32x24 pixels - will transform it later
        while True: #try to read the sensor values until success
             try:
                 mlx.getFrame(frame) #reads the frame
                 break #if successful, break the while loop
             except Exception: #če slučajno dobimo traceback error zaradi ne sinhronizacije I2C
                 print(traceback.format_exc())
                 mlx = adafruit_mlx90640.MLX90640(i2c) #reastablished I2C connection
                 mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ #set the camera refresh rate to 4Hz - prolly don't need it, but just to be sure
                 continue

        #Limit the temp range between MINTEMP and MAXTEMP for higher accuracy
        pixels = [0] * 768
        for i in range(0,767):
            if frame[i] < MINTEMP:
                pixels[i]=MINTEMP
            else:
                pixels[i]=frame[i]
            pixels[i] = int((pixels[i]-MINTEMP)*(255/(MAXTEMP-MINTEMP)))

        #use PIL library to interpolate by a factor of INTERPOLATE -> increasing resolution to 320x240 and smoothing out the mosaicing effect
        img2 = Image.new("L", (32, 24))
        img2.putdata(pixels)
        img2 = img2.resize((32 * INTERPOLATE, 24 * INTERPOLATE), Image.BICUBIC)
        img= np.array(img2) #since numpy arrays are easier to use, no particular other reason

        #preset conditions for a certain room (currently our lab)
        robYspredaj=45 #front Y-axis limit for blackout
        robXlevo=45 #left X-axis limit for blackout
        robXdesno=265 #right X-axis limit for blackout
        robKatederX=205 #table X-axis limit for blackout
        robKatederY=72 #table Y-axis limit for blackout
        Bkamere=295 #distance from start point to PTZ camera in cm
        deltaRAD=5835 #value change per radian of rotation (see paper for calculation details)
        Bpolja=280 #Y-axis length in cm
        Apolja=340 #X-axis lenght in cm
        Xsr=310 #X-axis center
        Xzl=530 #front left-cordner X-axis
        Yzl=420 #front left-cordner Y-axis
        Xsl=530 #back left-cordner X-axis
        Ysl=90 #back left-cordner Y-axis
        mejaTableY=350 #Y-axis threshold for detecting as writing board
        mejaKatederY=190 #Y-axis limit for our table
        Xsd=90 #front right-cordner X-axis
        mejaKatederXdesno=230 #X-axis limit for our table

        #blackout certain parts of the image (borders + table with hot laptop)
        for x in range(0,319):
            for y in range(0,239):
                if y < robKatederY and x > robKatederX:
                    img[y][x]=0
                if y < robYspredaj or x < robXlevo or x > robXdesno:
                    img[y][x]=0

        if avtonomijaONOFF and np.amax(img)>140: #check if detection is desired + if it's warmer than 34 degrees Celsius mapped on a scale between 0 and 255. (MIN and MAX temp)
            result = np.where(img == np.amax(img)) #finds highest temp in scene
            #since our web interface is 640x480 we double the coordinates for accurate repesentation on the website
            cordX=int(320-result[1][0])*2 #we also invert the X-axis
            cordY=int(result[0][0])*2
            if cordY>mejaTableY: #check borders for writing boards
                if cordX>Xsr:
                    #the left board
                    PAN=33952
                    TILT=32816
                    ZOOM=2500
                else:
                    #the right board
                    PAN=31968
                    TILT=32816
                    ZOOM=2500
            elif cordX<mejaKatederXdesno and cordX>Xsd and cordY<mejaKatederY: #check borders for our desk table
                # static values for professors desk
                PAN=30720
                TILT=33700
                ZOOM=2300
            else:
                #otherwise try to track - for formula explanations, check out my paper (same names for variables)
                Aosebe=(abs(cordX-Xsr)*Apolja/2)/(Xsl-Xsr)
                Bosebe=Bkamere+(abs(cordY-90)*Bpolja/(Yzl-Ysl))
                C=math.sqrt(int(Bosebe)^2+int(Aosebe)^2)
                alpha=np.arctan(Aosebe/Bosebe)
                TILT=32768+C*50/260
                ZOOM=2200
                if cordX > 310:
                    PAN=32768+(alpha*deltaRAD)
                else:
                    PAN=32768-(alpha*deltaRAD)

            razdaljaStarNov=math.sqrt(math.pow((cordX-starX),2)+math.pow((cordY-starY),2)) #calculate the distance between current and previous X, Y coordinates
            if razdaljaStarNov<300 and razdaljaStarNov>15: #if the subject moved less than 15 points, we ignore it, as it only introduces jitter + if the subject moves more than half the frame (300px), it's prolly an error "shrug"
                api_call_PT("%X" % int(PAN), "%X" % int(TILT)) #call our function to set PAN and TILT
                api_call_Z("%X" % int(ZOOM)) #call function to set ZOOM
                #emit required variables for JS to render our scene
                koordinate=[1.0, cordX, cordY, 10, 10, robYspredaj*2, robXlevo*2, robXdesno*2, robKatederX*2, robKatederY*2, Xsr, mejaTableY, mejaKatederY, mejaKatederXdesno, Xsd]
                if DEBUG: #emit debug info only if desired
                    socketio.emit('koordinate', {'koordinate': koordinate}, namespace='/rtls')
            starX=cordX
            starY=cordY
            sleep(0.01) #if left at 0, it crashes, prolly cause of thread schedulers

@app.route("/") #route to home website
def home():
    global avtonomijaONOFF
    avtonomijaONOFF = False #we don't want tracking from the get go
    return render_template('findmyprofessor.html') #generates an HTML based on our template

@app.route("/preset", methods=["POST"]) #route for static presets (1=Full frame, 2=Left board, 3=Right board, 4=Desk)
def nastaviPresetPTZ():
    izbranPreset = int(request.form["preset"]) #save the preset value
    global avtonomijaONOFF
    avtonomijaONOFF = False #we don't want tracking in static preset mode
    #check which preset is in use, prolly could have used a switch for it to be cleaner
    if izbranPreset == 1:
        PAN=32768
        TILT=32768
        ZOOM=1365
    elif izbranPreset == 2:
        PAN=33952
        TILT=32816
        ZOOM=2500
    elif izbranPreset == 3:
        PAN=31968
        TILT=32816
        ZOOM=2500
    elif izbranPreset == 4:
        PAN=30720
        TILT=33700
        ZOOM=2300
    api_call_PT_fast("%X" % int(PAN), "%X" % int(TILT)) #set PAN, TILT with no speed limit
    api_call_Z("%X" % int(ZOOM)) #set ZOOM
    return render_template('findmyprofessor.html', status=izbranPreset) #render template with current selection highlighted

@app.route("/auto", methods=["POST"]) #route to start autonomous tracking
def zagonAvtonomnegaSistema():
    global avtonomijaONOFF
    avtonomijaONOFF = True #let's turn our baby on, yessir
    return render_template('findmyprofessor.html', status=5)

@socketio.on('connect', namespace='/rtls')
def test_connect(): #connects to our websocket space named rtls
    global thread
    global thread_stop_event
    #if there is no current thread for tracking, initialize it
    if not thread or not thread.is_alive():
        print("Starting Thread from ",threading.current_thread().ident,threading.current_thread().name)
        thread_stop_event.clear()
        thread = Thread(target=functools.partial(rtlsRun),name="RTLSthread")
        thread.start()

@socketio.on('disconnect', namespace='/rtls')
def test_disconnect(): #on disconnect, kill thread
    global thread_stop_event
    global avtonomijaONOFF
    if not avtonomijaONOFF:
        thread_stop_event.set()


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
