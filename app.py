from flask import Flask, render_template, redirect, request
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
import scipy.ndimage

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

#globalna spremenljivka za upravljanje avtonomnega threada
avtonomijaONOFF = False

#inicializaicja termalne kamere MLX90640 na I2C vmesniku
i2c = busio.I2C(board.SCL, board.SDA, frequency=800000)
mlx = adafruit_mlx90640.MLX90640(i2c)
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ

#spremenimo flask app v socketio app
socketio = SocketIO(app, async_mode=None, logger=True, engineio_logger=True)

#omogocimo uporabo threada z knjizico
thread = None
thread_stop_event = Event()

def rtlsRun():
    global avtonomijaONOFF
    global mlx

    while not thread_stop_event.isSet():
        frame = [0] * 768 #array za naso termalno sliko
        #error-catching nacin zavzetja slike
        try:
            mlx.getFrame(frame)
        except ValueError:
            continue # these happen, no biggie - retry
        print(frame)
        frame = scipy.ndimage.zoom(frame, 20, order=1)
        print(frame)
        break
        if avtonomijaONOFF:
            socketio.emit('koordinate', {'number': number}, namespace='/rtls')
        sleep(1)

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
    socketio.run(app)
