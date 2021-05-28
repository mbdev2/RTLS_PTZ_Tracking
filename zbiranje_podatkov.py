# First, install the dependencies via:
#    $ pip3 install requests
import json
import hmac, hashlib
import requests
import re, uuid
import math
import time
import board
import busio
import adafruit_mlx90640

# Your API & HMAC keys can be found here (go to your project > Dashboard > Keys to find this)
HMAC_KEY = "4fa093e33fec9cafc6e98ed4ad75f4c3"
API_KEY = "ei_725635cec1610d803dca79065fc88bfad571f30abe2e68a8df1a79f661ac7418"

# empty signature (all zeros). HS256 gives 32 byte signature, and we encode in hex, so we need 64 characters here
emptySignature = ''.join(['0'] * 64)

# use MAC address of network interface as deviceId
device_name =":".join(re.findall('..', '%012x' % uuid.getnode()))

# image array capture using the MLX90640 and adafruit_mlx90640 drivers
i2c = busio.I2C(board.SCL, board.SDA, frequency=800000)
mlx = adafruit_mlx90640.MLX90640(i2c)
print("MLX addr detected on I2C")
print([hex(i) for i in mlx.serial_number])
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ

frame = [0] * 768
try:
    mlx.getFrame(frame)
except ValueError:
    # these happen, no biggie - retry
    print("Error with capture")
    continue

# prepare data frame to send to edgeimpulse
data = {
    "protected": {
        "ver": "v1",
        "alg": "HS256",
        "iat": time.time() # epoch time, seconds since 1970
    },
    "signature": emptySignature,
    "payload": {
        "device_name":  device_name,
        "device_type": "MLX_TEST",
        "interval_ms": 500,
        "sensors": [
            { "name": "Temparature", "units": "celsius" }
        ],
        "values": frame # our temperature data
    }
}

# encode in JSON
encoded = json.dumps(data)

# sign message
signature = hmac.new(bytes(HMAC_KEY, 'utf-8'), msg = encoded.encode('utf-8'), digestmod = hashlib.sha256).hexdigest()

# set the signature again in the message, and encode again
data['signature'] = signature
encoded = json.dumps(data)

# and upload the file
res = requests.post(url='https://ingestion.edgeimpulse.com/api/training/data',
                    data=encoded,
                    headers={
                        'Content-Type': 'application/json',
                        'x-file-name': 'idle01',
                        'x-api-key': API_KEY
                    })
if (res.status_code == 200):
    print('Uploaded file to Edge Impulse', res.status_code, res.content)
else:
    print('Failed to upload file to Edge Impulse', res.status_code, res.content)
