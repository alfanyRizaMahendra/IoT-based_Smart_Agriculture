#import paho.mqtt.client as mqtt
from Adafruit_IO import Client, Feed
import random
import time
import os

# for scheduling
from apscheduler.schedulers.background import BackgroundScheduler

mqtt_Username = "ichsan27"
mqtt_Password = "aio_RRwa27ppd8piInU1p2qV3Mom5ERA"

# publish
humidity = "plant-slash-humidity"
lux = "plant-slash-lux"
temp = "plant-slash-temp"
update_condition = "plant-slash-result"
note = "plant-slash-note"

# subscribe
lamp_state = "plant-slash-onlamp"
pump_state = "plant-slash-onpump"

condition_value = "Tidak Ideal"
note_value = "Kelembaban, Suhu air, dan insitas cahaya tidak ideal  "

aio = Client(mqtt_Username, mqtt_Password)

def publish():
    humudity_value = random.randint(0, 100)
    lux_value = random.randint(0, 255)
    temp_value = random.randint(0, 100)
    
    aio.send_data(humidity, humudity_value)

    #luxfeed = aio.Feed(lux)
    aio.send_data(lux, lux_value)

    #tempfeed = aio.Feed(temp)
    aio.send_data(temp, temp_value)

    #conditionfeed = aio.Feed(update_condition)
    aio.send_data(update_condition, condition_value)
    
    aio.send_data(note, note_value)
    
    print("Data berhasil terkirim")
    #time.sleep(5)
        
def subscribe():
    lampfeed = aio.receive(lamp_state).value
    pumpfeed = aio.receive(pump_state).value
    
    print("lamp feed = {0} \npump feed = {1}".format(lampfeed, pumpfeed))    
        
if __name__ == '__main__':
    while True:
        scheduler = BackgroundScheduler()
        scheduler.add_job(publish, 'interval', seconds = 10)
        scheduler.add_job(subscribe, 'interval', seconds = 3)
        scheduler.start()
        print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
        try:
            # This is here to simulate application activity (which keeps the main thread alive)
            while True:
                time.sleep(2)
        except:
            # Not strictly necessary if daemonic mode is enabled but should be done if possible
            scheduler.shutdown()
