#App with ML components
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
from edge_impulse_linux.image import ImageImpulseRunner
import traceback

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

avtonomijaONOFF = False#globalna spremenljivka za upravljanje avtonomnega threada
runner = None #EdgeImpulse runner startup
INTERPOLATE = 10# image interpolation factor
MINTEMP =22.0 # low range of the sensor (this will be black on the screen)
MAXTEMP = 38.0 # high range of the sensor (this will be white on the screen)

socketio = SocketIO(app, async_mode=None, logger=True, engineio_logger=True) #spremenimo flask app v socketio app

#omogocimo uporabo threada z knjizico
thread = None
thread_stop_event = Event()
def api_call_PT(pan_val_hex, tilt_val_hex):
    # Request API for Pan and Tilt axis
    # GET http://212.101.141.51/cgi-bin/aw_ptz
    try:
        response = requests.get(
            url="http://212.101.141.51/cgi-bin/aw_ptz",
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
    # GET http://212.101.141.51/cgi-bin/aw_ptz
    print(zoom_val_hex)
    try:
        response = requests.get(
            url="http://212.101.141.51/cgi-bin/aw_ptz",
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

    model = "/home/pi/RTLS_FindMyProfessor/modelfile.eim"
    dir_path = os.path.dirname(os.path.realpath(__file__))
    modelfile = os.path.join(dir_path, model)
    print('MODEL: ' + modelfile)

    # initialize the sensor
    i2c = busio.I2C(board.SCL, board.SDA)# MUST set I2C freq to 1MHz in /boot/config.txt
    mlx = adafruit_mlx90640.MLX90640(i2c)
    print("MLX addr detected on I2C, Serial #", [hex(i) for i in mlx.serial_number])
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
    print(mlx.refresh_rate)
    print("Refresh rate: ", pow(2, (mlx.refresh_rate - 1)), "Hz")

    while not thread_stop_event.isSet():
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
                if avtonomijaONOFF:
                    pixels_proc = np.array(img).flatten().tolist()
                    for ix in range(0, len(pixels_proc)):
                        b = pixels_proc[ix]
                        features.append((b << 16) + (b << 8) + b)

                    res = runner.classify(features)

                    if "classification" in res["result"].keys():
                        #print('Result (%d ms.) ' % (res['timing']['dsp'] + res['timing']['classification']), end='')
                        for label in labels:
                            score = res['result']['classification'][label]
                            #print('%s: %.2f\t' % (label, score), end='')
                        #print('', flush=True)


                    elif "bounding_boxes" in res["result"].keys():
                        #print('Found %d bounding boxes (%d ms.)' % (len(res["result"]["bounding_boxes"]), res['timing']['dsp'] + res['timing']['classification']))
                        for bb in res["result"]["bounding_boxes"]:
                            #print('\t%s (%.2f): x=%d y=%d w=%d h=%d' % (bb['label'], bb['value'], bb['x'], bb['y'], bb['width'], bb['height']))
                            koordinate=[bb['value'], abs(320-bb['x'])*2, bb['y']*2-80, bb['width']*2, bb['height']*2]
                            cordX=koordinate[1]-koordinate[3]/2
                            cordY=koordinate[2]-koordinate[4]/2
                            if cordY>230:
                                if cordX>310:
                                    #the left board
                                    pan_val=33712
                                    tilt_val=32768
                                    zoom_val=2672
                                else:
                                    #the right board
                                    pan_val=31744
                                    tilt_val=32768
                                    zoom_val=2640
                            elif cordX<220 and cordX>95 and cordY<150:
                                # static values for professors desk
                                pan_val=30720
                                tilt_val=33700
                                zoom_val=2400
                            else:
                                #otherwise try to track
                                aY=300+(abs(cordY-35)*280/255)
                                bX=abs(cordX-310)*175/210
                                phi=np.arctan(bX/aY)
                                tilt_val=32768
                                zoom_val=2100
                                if koordinate[1] > 310:
                                    pan_val=32768+(phi*5500)
                                else:
                                    pan_val=32768-(phi*5500)
                            api_call_PT("%X" % int(pan_val), "%X" % int(tilt_val))
                            api_call_Z("%X" % int(zoom_val))
                            socketio.emit('koordinate', {'koordinate': koordinate}, namespace='/rtls')
                            break

            finally:
                if (runner):
                    runner.stop()
            sleep(0.01)

@app.route("/") # route za osnovno stran
def home():
    global avtonomijaONOFF #povemo sistemu da uporabljamo globalno srepemnljivko avtonomijaONOFF
    avtonomijaONOFF = False #ustavi avtonomno upravljanje kamere
    return render_template('findmyprofessor.html') #vzame HTML template iz zunanje datoteke

@app.route("/preset", methods=["POST"]) #route klici za presete PTZ 1=tabla1, 2=tabla2, 3=kateder
def nastaviPresetPTZ():
    izbranPreset = int(request.form["preset"]) #shranimo vrednost preseta (1-3)
    global avtonomijaONOFF #povemo sistemu da uporabljamo globalno srepemnljivko avtonomijaONOFF
    avtonomijaONOFF = False #ustavi avtonomno upravljanje kamere
    print("Izbrani preset za PTZ: ", izbranPreset) #izpisemo v terminal ker preset je
    return render_template('findmyprofessor.html', status=izbranPreset)

@app.route("/auto", methods=["POST"]) #route za zagon avtonomnega sistema sledenja
def zagonAvtonomnegaSistema():
    global avtonomijaONOFF #povemo sistemu da uporabljamo globalno srepemnljivko avtonomijaONOFF
    avtonomijaONOFF = True #ustavi avtonomno upravljanje kamere
    print("Zagon avtonomnega sistema MLX90640")
    return render_template('findmyprofessor.html', status=4)

@socketio.on('connect', namespace='/rtls')
def test_connect():
    global thread #zelimo uporabljati globalni thread
    global thread_stop_event

    if not thread or not thread.is_alive():
        print("Starting Thread from ",threading.current_thread().ident,threading.current_thread().name)
        thread_stop_event.clear()
        thread = Thread(target=functools.partial(rtlsRun),name="RTLSthread")
        thread.start()

@socketio.on('disconnect', namespace='/rtls')
def test_disconnect():
    global thread_stop_event
    global avtonomijaONOFF
    if not avtonomijaONOFF:
        thread_stop_event.set()


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
