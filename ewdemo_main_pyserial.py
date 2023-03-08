import json
import time
import math

import serial
#from RPi.GPIO import GPIO
from RPiSim  import GPIO



TOPIC = "/temperature/sensor/"
RANGE = 5
BASETEMPERATURE=25.0
TEMPRANGE1=5
TEMPRANGE2=1
INTERVAL=15

SERIAL_DEVICE="/dev/ttyS0"
PINOUT= {"tx": 15,
         "rx": 14,
         "reset": 23,
         "event":27,
         "wake": 22}

ser=serial.Serial(SERIAL_DEVICE)
print("Main::Initializing script...")
#time.sleep(2)

def el_send(cmd):
    ser.write(cmd.strip()+"\r")
    return ser.readlines()

print("Main::Bravo AWS ExpressLink starting...")


print("Main::Infinite loop starting")
try:
    ser.write("AT+CONNECT\r")
except:
    print("Exception captured" )

print("ExpressLink Started")

led = DigitalInOut(board.G10)
led.direction = Direction.OUTPUT

response = el.sendCommand('AT+CONF? ThingName')
thingName = response[3:]
response = el.sendCommand("AT+CONF Topic1="+ TOPIC + thingName)


while True:
    current_time = round(time.time()) 
    var_time = current_time % 86400
    #print( "Time is '{}': {}".format(current_time, (var_time %360) ))
    
    temperature = BASETEMPERATURE+TEMPRANGE1*(var_time % 3600)/3600 + TEMPRANGE2*math.sin(var_time %360 /180.0*math.pi)
    data = {"Temperature" : temperature}
    #mqtt_connection.publish(topic=TOPIC, payload=json.dumps(message), qos=mqtt.QoS.AT_LEAST_ONCE)
    el.sendCommand("AT+SEND1 " + data)
    print("....Published: '{}' to topic '{}'".format(json.dumps(message) ,TOPIC ))
    time.sleep(INTERVAL)
    