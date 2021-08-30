# RTLS_PTZ_tracking - Real-Time Indoor Speaker Tracking System

## _Change your flow with thermal camera-based RTLS Speaker Tracking!_

RTLS_PTZ_tracking is a DIY take on expensive and often unadaptable speaker tracking technologies like Panasonic AW-SF100 software, AVer DL30, HuddleCamHD SimplTrack2, and Cisco Telepresence. 

Developed by Mark Breznik for a final graduation project in the undergraduate study program Multimedia at the Faculty of Electrical Engineering, University of Ljubljana.

A diploma thesis based on the project is available here: 

## Features

- Presenter tracking during movement and writing on the board
- Intuitive web-based user interface
- Compatible with any PTZ camera brand (dependent on API)
- Inexpensive 
<img width="991" alt="RTLS_PTZ_tracking UI" src="https://user-images.githubusercontent.com/72226231/131320463-b5e1c7f9-6d3d-4ea7-a6d5-093cbbd97f8c.png">



## Tech

- Operates on a Raspberry Pi Model 4 B microcontroller and an MLX90640 thermal camera system (Adafruit recommended, but not required)
- Flask with SocketIO base
- Panasonic PTZ API implementation
- Adafruit CircuitPython and MLX90640 drivers


## Installation

- install Raspberry Pi OS (Raspbian) Buster or later on your RPi board (required: support for Python 3.6 or later)
- Instal CircuitPython for Raspbian (available here: https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi)
_ Install I2C drivers:
a.	sudo pip3 install adafruit-circuitpython-mlx90640
b.	sudo pip3 install adafruit-circuitpython-busdevice
c.	sudo pip3 install adafruit-circuitpython-register
- Restart your board
- Run »python3 app.py« from the cloned folder
- (optional) Move app.py, /template, /static to »/etc/init.d/« if you want it to start on boot



## Development

For now, the development is finished. May revisit and explore new features in the future.

## License
TBD
