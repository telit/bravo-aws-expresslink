 #!/usr/bin/env python

import json
import time
import math

import threading
import serial, io
import RPi.GPIO as GPIO
import signal, sys

############# AWS Specific parameters
TOPIC_TEMP = "TempCheckerTopic/"
TOPIC_LED = "ledSetTopic/"
ENDPOINT="<YOUR_AWS_ENDPOINT>"

############# Temperature simulator parameters
RANGE = 5
BASETEMPERATURE=25.0
TEMPRANGE1=5
TEMPRANGE2=1

############# Update interval time
INTERVAL=60


############# ExpressLink specific parameters
BAUDRATE  = 115200          # baud rate for serial port
SERIAL_DEVICE="/dev/ttyS0"

PINOUT= {
         "led": 6,
         "tx": 15,
         "rx": 14,
         "reset": 23,
         "event":27,
         "wake": 22
         }


print ("Opening COM port %s" % SERIAL_DEVICE)
pt = serial.Serial(SERIAL_DEVICE, BAUDRATE, timeout = 0)
sbp = io.TextIOWrapper(io.BufferedRWPair(pt, pt, 1),
                               newline = '\n',
                               encoding='ascii',
                               line_buffering = True)

def el_send(cmd, timeout=10):
    try:
        print("sending command " + str(cmd))
        """ send AT command to ExpressLink and return output - blocking call"""
        sbp.write(cmd.strip()+"\r")
    except:
        print("exception")

    resp = ''
    max_count = timeout * 10
    count = 0
    while True:
        try:
            resp += sbp.readline()  # read one line of text from serial port and decode it as a string
            if len(resp) > 0:
                #print("resp: " + str(resp) )
                if "OK" in resp:
                    return [0, resp]
                elif "ERR" in resp:
                    return [1, resp]

            time.sleep(0.1)
        except KeyboardInterrupt:
            print("break")
            break
        except:
            print("exception")
            continue
        # todo better timeout ?
        count += 1
        if count > max_count:
            print("too many loops")
            break
    return [2, ""]



def blink_led(cycles= 2, delay=0.2, off_mult=1):
    for n in range(cycles):
        GPIO.output(PINOUT["led"], 1)
        time.sleep(delay)
        GPIO.output(PINOUT["led"], 0)
        time.sleep(delay * off_mult)

def parse_event_led(response):
    data = json.loads(response)
    status = data["led"]
    if status == "on":
        GPIO.output(PINOUT["led"], 1)
    else:
        GPIO.output(PINOUT["led"], 0)

def check_events():
    [rc, response] = el_send("AT+EVENT?")
    if rc == 0:
        print("events: " + str(response))
        arr = response.split(" ")
        #print(str(arr))
        if(len(arr) > 1):
            type = int(arr[1])
            if type == 1:
                topic = arr[2]
                [rc, response] = el_send("AT+GET" + str(topic))
                if rc == 0:
                    response = response[3:].replace("\A", "\n")
                    print("message: " + str(response))
                    parse_event_led(response)

def wait_event_gpio(timeout=30):
    count = 0
    while True:
        count += 1
        val = int(GPIO.input(PINOUT["event"]))

        if val == 1:
            print("--event pin is high")
            return 0
        time.sleep(1)

        if count >= timeout:
            print("return with timeout!!")
            return 1
        else:
            return 0

def check_event_gpio():
    while True:
        val = int(GPIO.input(PINOUT["event"]))
        if val == 1:
            print("event pin is high")
            check_events()
        else:
            print("event pin is low")
            break
        time.sleep(1)

def event_pin_callback(channel):
    print("Event pin interrupt!")
    check_event_gpio()

def config_device():
    [rc, response] = el_send("AT+CONF Endpoint="+ENDPOINT)
    if rc == 0:
        print("endpoint set:" + str(response))
    else:
        return 1
    [rc, response] = el_send('AT+CONF? ThingName')
    if rc == 0:
        print("thingname read ok:" + str(response))
    else:
        return 1

    thingName = response[3:]
    print(thingName)
    [rc, response]  = el_send("AT+CONF Topic1=" + TOPIC_TEMP + thingName)
    if rc == 0:
        print("topic set: " + str(response))
    else:
        return 1

    [rc, response]  = el_send("AT+CONF Topic2=" + TOPIC_LED + thingName)
    if rc == 0:
        print("topic set: " + str(response))
    else:
        return 1

    [rc, response] = el_send("AT+DISCONNECT", 20)
    if rc != 0:
        print("disconnect failed")

    check_event_gpio()

    return 0

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)






def second_thread():
    time.sleep(2)
    print("Main::Bravo AWS IoT ExpressLink starting...")


    if( 0 != wait_event_gpio()):
        print("Event pin not found within timeout!")
        sys.exit(1)

    time.sleep(2)

    #flush everything
    #pt.readlines()

    print("Main::Initializing script...")

    if config_device() != 0:
        blink_led(10, 0.05, 5)
        print("cannot configure device!!!")
        sys.exit()
    else:
        blink_led(3, 0.8)

        print("Main::Infinite loop starting")

        while True:
            """ make an infinite loop on connecting"""
            [rc, response] = el_send("AT+CONNECT", 20)
            if rc != 0:
                print("Cannot connect to bravo AWS IoT ExpressLink: " + response)
                blink_led(5, 0.05, 5)
                print("Retrying...")
                time.sleep(15)
            else:
                print("ExpressLink Started")
                blink_led(2, 0.5)

                [rc, response] = el_send("AT+SUBSCRIBE2", 20)
                if rc != 0:
                    print("Cannot subscribe topic 2 " + response)
                    blink_led(5, 0.05, 5)

                while True:
                    try:
                        current_time = round(time.time())
                        var_time = current_time % 86400
                        # print( "Time is '{}': {}".format(current_time, (var_time %360) ))

                        temperature = BASETEMPERATURE + TEMPRANGE1 * (var_time % 3600) / 3600 + TEMPRANGE2 * math.sin(
                            var_time % 360 / 180.0 * math.pi)
                        data = {"Temperature": temperature}

                        payload = json.dumps(data)
                        print(payload)
                        [rc, response] = el_send("AT+SEND1 " + str(payload))
                        if rc == 0:
                            print("....Published: '{}' to topic '{}'".format(json.dumps(payload), TOPIC_TEMP))
                            blink_led(2, 0.8)
                        else:
                            print("publish failed: " + str(response))
                            blink_led(10, 0.05, 5)
                    except:
                        time.sleep(INTERVAL)
                        continue
                    time.sleep(INTERVAL)



if __name__ == '__main__':

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    print("set RST HIGH")
    GPIO.setup(PINOUT["reset"], GPIO.OUT)
    GPIO.output(PINOUT["reset"], 1)

    GPIO.setup(PINOUT["led"], GPIO.OUT, initial=0)

    print("set RST LOW...")
    GPIO.output(PINOUT["reset"], 0)
    time.sleep(2)

    print("set RST HIGH")
    GPIO.output(PINOUT["reset"], 1)

    time.sleep(10)

    GPIO.setup(PINOUT["event"], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(PINOUT["event"], GPIO.RISING, callback=event_pin_callback)


    #GPIO.add_event_detect(PINOUT["event"], GPIO.RISING,callback=event_pin_callback, bouncetime=100)

    threading1 = threading.Thread(target=second_thread)
    threading1.daemon = True
    threading1.start()

    #try:
    #    print("waiting for events on pin")
    #    GPIO.wait_for_edge(PINOUT["event"], GPIO.RISING)

    #except KeyboardInterrupt:
    #    GPIO.cleanup()  # clean up GPIO on CTRL+C exit
    #GPIO.cleanup()  # clean up GPIO on normal exit

    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()


 
 