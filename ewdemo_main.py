import json
import time
import math
import board

from expresslink import ExpressLink


TOPIC = "TempCheckerTopic"
RANGE = 5
BASETEMPERATURE=25.0
TEMPRANGE1=5
TEMPRANGE2=1
INTERVAL=15




el = ExpressLink(uart, DigitalInOut(board.G5), DigitalInOut(board.G2), DigitalInOut(board.G6) )

try:
    el.begin()
except:
    print("Exception captured")

print("ExpressLink Started")

led = DigitalInOut(board.G10)
led.direction = Direction.OUTPUT



while True:
    current_time = round(time.time()) 
    var_time = current_time % 86400
    #print( "Time is '{}': {}".format(current_time, (var_time %360) ))
    
    temperature = BASETEMPERATURE+TEMPRANGE1*(var_time % 3600)/3600 + TEMPRANGE2*math.sin(var_time %360 /180.0*math.pi)
    message = {"Temperature" : temperature}
    mqtt_connection.publish(topic=TOPIC, payload=json.dumps(message), qos=mqtt.QoS.AT_LEAST_ONCE)
    print("....Published: '{}' to topic '{}'".format(json.dumps(message) ,TOPIC ))
    time.sleep(INTERVAL)
    