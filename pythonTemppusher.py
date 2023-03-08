# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder
import time as t
import math
import json
import time

# Define ENDPOINT, CLIENT_ID, PATH_TO_CERTIFICATE, PATH_TO_PRIVATE_KEY, PATH_TO_AMAZON_ROOT_CA_1, MESSAGE, TOPIC, and RANGE
ENDPOINT = "a2lfhk74nngow4-ats.iot.eu-west-1.amazonaws.com"
CLIENT_ID = "telit-demo-1"
PATH_TO_CERTIFICATE = "certificates/telit-demo-1/6a3612923c6be8a7cac0e28eeb056bbf5fdd88c8ed1e861d22cebf1cc52e0d30-certificate.pem.crt"
PATH_TO_PRIVATE_KEY = "certificates/telit-demo-1/6a3612923c6be8a7cac0e28eeb056bbf5fdd88c8ed1e861d22cebf1cc52e0d30-private.pem.key"
PATH_TO_AMAZON_ROOT_CA_1 = "certificates/AmazonRootCA1.pem"

TOPIC = "TempCheckerTopic"
RANGE = 5
BASETEMPERATURE=25.0
TEMPRANGE1=5
TEMPRANGE2=1
INTERVAL=15

io.init_logging(io.LogLevel.Warn, 'stderr')
# Spin up resources
event_loop_group = io.EventLoopGroup(1)
host_resolver = io.DefaultHostResolver(event_loop_group)
client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=ENDPOINT,
            cert_filepath=PATH_TO_CERTIFICATE,
            pri_key_filepath=PATH_TO_PRIVATE_KEY,
            client_bootstrap=client_bootstrap,
            ca_filepath=PATH_TO_AMAZON_ROOT_CA_1,
            client_id=CLIENT_ID,
            clean_session=True,
            keep_alive_secs=6
            )
print("Connecting to {} with client ID '{}'...".format(ENDPOINT, CLIENT_ID))
# Make the connect() call
connect_future = mqtt_connection.connect()
# Future.result() waits until a result is available
connect_future.result()
print("Connected!")

# Publish message to server desired number of times.
print('Begin Publish')
current_time=0
while True:
    current_time = round(time.time()) 
    #current_time=current_time+1  
    var_time = current_time % 86400
    print( "Time is '{}': {}".format(current_time, (var_time %360) ))
    data = BASETEMPERATURE+TEMPRANGE1*(var_time % 3600)/3600 + TEMPRANGE2*math.sin(var_time %360 /180.0*math.pi)
    message = {"Temperature" : data}
    mqtt_connection.publish(topic=TOPIC, payload=json.dumps(message), qos=mqtt.QoS.AT_LEAST_ONCE)
    print("....Published: '{}' to topic '{}'".format(json.dumps(message) ,TOPIC ))
    t.sleep(INTERVAL)
    print('Publish End')
disconnect_future = mqtt_connection.disconnect()
disconnect_future.result()