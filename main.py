import RPi.GPIO as GPIO
import serial
import time
from time import sleep
from datetime import datetime
import os
from Adafruit_IO import Client, Feed
import numpy as np
import pandas as pd

# for scheduling
from apscheduler.schedulers.background import BackgroundScheduler

# for machine learning purposed
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier

# for GUI purposed
import tkinter as tk
from tkinter import *
from tkinter import ttk
import tkinter.font as tkFont
from tkinter import messagebox

# -------------------- MQTT adafruit IO --------------------
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
pump_onDuration = "plant-slash-pumponduration"
pump_offDuration = "plant-slash-pumpoffduration"

# initial value
condition_value = "Tidak Ideal"
note_value = "Kelembaban, Suhu air, dan insitas cahaya tidak ideal"

aio = Client(mqtt_Username, mqtt_Password)

# -------------------- GPIO Define -----------------------------
GPIO.setmode(GPIO.BCM) # Broadcom chip-spesific pin number

ser = serial.Serial('/dev/ttyS0', # replace tty50 with AM0 for Pi1, Pi2, Pi0
                     baudrate = 38400,
                     parity = serial.PARITY_NONE,
                     stopbits = serial.STOPBITS_ONE,
                     bytesize = serial.EIGHTBITS,
                     timeout = 1)

convert_char_to_int = {
    "\\t" : 9,
    "\\n" : 10,
    '\\r' : 13,
    ' ' : 32,
    '!' : 33,
    '"' : 34,
    '#' : 35,
    '$' : 36,
    '%' : 37,
    '&' : 38,
    "\'": 39,
    '(' : 40,
    ')' : 41,
    '*' : 42,
    '+' : 43,
    ',' : 44,
    '-' : 45,
    '.' : 46,
    '/' : 47,
    '0' : 48,
    '1' : 49,
    '2' : 50,
    '3' : 51,
    '4' : 52,
    '5' : 53,
    '6' : 54,
    '7' : 55,
    '8' : 56,
    '9' : 57,
    ':' : 58,
    ';' : 59,
    '<' : 60,
    '=' : 61,
    '>' : 62,
    '?' : 63,
    '@' : 64,
    'A' : 65,
    'B' : 66,
    'C' : 67,
    'D' : 68,
    'E' : 69,
    'F' : 70,
    'G' : 71,
    'H' : 72,
    'I' : 73,
    'J' : 74,
    'K' : 75,
    'L' : 76,
    'M' : 77,
    'N' : 78,
    'O' : 79,
    "P" : 80,
    'Q' : 81,
    'R' : 82,
    'S' : 83,
    'T' : 84,
    'U' : 85,
    'V' : 86,
    'W' : 87,
    'X' : 88,
    'Y' : 89,
    'Z' : 90,
    '[' : 91,
    '\\\\': 92,
    ']' : 93,
    '^' : 94,
    '_' : 95,
    "`" : 96,
    'a' : 97,
    'b' : 98,
    'c' : 99,
    'd' : 100,
    'e' : 101,
    'f' : 102,
    'g' : 103,
    'h' : 104,
    'i' : 105,
    'j' : 106,
    'k' : 107,
    'l' : 108,
    'm' : 109,
    'n' : 110,
    'o' : 111,
    'p' : 112,
    'q' : 113,
    'r' : 114,
    's' : 115,
    't' : 116,
    'u' : 117,
    'v' : 118,
    'w' : 119,
    'x' : 120,
    'y' : 121,
    'z' : 122,
    '{' : 123,
    '|' : 124,
    '}' : 125,
    '~' : 126,
}

# ---------------------------- Conversion data ---------------------
convert_res = {
    0 : ["Ideal",""],
    1 : ["Tidak Ideal", "Suhu air tidak ideal"],
    2 : ["Tidak Ideal", "Kelembapan udara tidak ideal"],
    3 : ["Tidak Ideal", "Intensitas cahaya tidak ideal"],
    4 : ["Tidak Ideal", "Suhu air dan kelembapan tidak ideal"],
    5 : ["Tidak Ideal", "Kelembapan dan intensitas cahaya tidak ideal"],
    6 : ["Tidak Ideal", "Suhu air dan intensitas cahaya tidak ideal"],
    7 : ["Tidak Ideal", "Suhu air, kelembapan, dan intensitas cahaya tidak ideal"],
}

res_to_out = {
    0 : "-ON$\n",
    1 : "!ON$\n",
    2 : "@ON$\n",
    3 : "#ON$\n",
    4 : "%ON$\n",
    5 : "^ON$\n",
    6 : "&ON$\n",
    7 : "*ON$\n", 
}

def bytes_to_int(data):
    sign = str(data[:-1])[2:-1]
    if sign in convert_char_to_int:
        convert = convert_char_to_int[sign]
    else:
        convert = str(data[:-1])[4:-1]
        convert = int(convert, 16)
    return convert

# -------------------------- Machine learning Model Classification ----------------------
def classified(X):
    result = []
    load_rf = joblib.load("./ML_model/random_forest.joblib")
    load_knn = joblib.load("./ML_model/knn.joblib")
    result.append(load_rf.predict(X)[0])
    result.append(load_knn.predict(X)[0])
    return result

recheck = False
count_classification = 0 # classification flag

# ----------------------------- IoT and microcontroller communication ------------------------------------
def get_data():
    global recheck, count_classification
    ser.flushInput()
    var = "?luxData$\n"
    ser.write(var.encode())
    rx_data = ser.read_until('\n')
    lux_value = bytes_to_int(rx_data)
    time.sleep(1)
    
    var = "?humData$\n"
    ser.write(var.encode())
    rx_data = ser.read_until('\n')
    humidity_value = bytes_to_int(rx_data)
    time.sleep(1)
    
    var = "?temData$\n"
    ser.write(var.encode())
    rx_data = ser.read_until('\n')
    tempC_value = bytes_to_int(rx_data)
    time.sleep(1)
    
    print("\nlux = " + str(lux_value) + "\nhumidity = " + str(humidity_value) + "\nwater_temp = " + str(tempC_value))
    x = np.array([[lux_value, humidity_value, tempC_value]])
    input_x = pd.DataFrame(x, columns = ['Suhu(*C)', 'Kelembaban_Udara(%)', 'Intensitas_Cahaya(Lux)'])
    
    # classification section
    result = classified(input_x)
    
    # Checking result
    print(convert_res[result[0]][0])
    print(convert_res[result[0]][1])
    
    # Rescheduling to make the ideal result, exept for light intensity
    # for the second checked
    if result[0] != 0:
        if result[0] == 3:
            count_classification += 1
            if count_classification > 1:
                recheck = False
                count_classification = 0
            else:
                recheck = True
        else:
            recheck = True
    else:
        recheck = False
    
    #publishing knn result to web
    publish(x, result[0])
    
    #Send knn classification result for output driving purposed
    result_send = res_to_out[result[0]]
    ser.write(result_send.encode())

def publish(data, res):
    condition_value = convert_res[res][0]
    note_value = convert_res[res][1]
    aio.send_data(lux, int(data[0][0]))
    aio.send_data(humidity, int(data[0][1]))
    aio.send_data(temp, int(data[0][2]))
    aio.send_data(update_condition, condition_value)    
    aio.send_data(note, note_value)  
    print("Data berhasil terkirim")

previous_onDuration = 0
previous_offDuration = 0
previous_lampState = '0'
previous_pumpState = '0'
different_duration = False
different_lampState = False
different_pumpState = False

def subscribe():
    global previous_onDuration, previous_offDuration, previous_lampState, previous_pumpState, different_lampState, different_pumpState, different_duration
    lampfeed = aio.receive(lamp_state).value
    pumpfeed = aio.receive(pump_state).value
    onDuration = aio.receive(pump_onDuration).value
    offDuration = aio.receive(pump_offDuration).value
    print("lamp feed = {0}\npump feed = {1}\nonDuration_feed = {2}\noffDuration_feed = {3}".format(lampfeed, pumpfeed, onDuration, offDuration))
    if lampfeed == '1':
        lamp_state_send = "#ON$\n"
    if lampfeed == '0':
        lamp_state_send = "#OFF$\n"
    if pumpfeed == '1':
        pump_state_send = "+ON$\n"
    if pumpfeed == '0':
        pump_state_send = "+OFF$\n"
    
    # preventing repetition
    if onDuration != previous_onDuration:
        previous_onDuration = onDuration
        different_duration = True
    if offDuration != previous_offDuration:
        previous_offDuration = offDuration
        different_duration = True
    if pumpfeed != previous_pumpState:
        previous_pumpState = pumpfeed
        different_pumpState = True
    if lampfeed != previous_lampState:
        previous_lampState = lampfeed
        different_lampState = True
    
    # gate 
    if different_duration == True:
        duration_update = "~," + str(onDuration) + "," + str(offDuration) + "$\n"
        ser.write(duration_update.encode())
        different_duration = False
    if different_lampState == True:
        ser.write(lamp_state_send.encode())
        different_lampState = False
    if different_pumpState == True:
        ser.write(pump_state_send.encode())
        different_pumpState = False

# ------------------------------------------------------------------------------------------
# --------------------------------------------- GUI Section --------------------------------

white       = "#ffffff"
BlackSolid  = "#000000"
font        = "Constantia"
fontButtons = (font, 12)
maxWidth    = 640
maxHeight   = 480
colorChoice = {'putih' : '$255,255,255$\n',
               'kuning' : '$255,255,0$\n',
               'hijau' : '$0,255,0$\n',
               'biru' : '$0,255,255$\n',
               'merah' : '$255,0,0$\n'}

def _from_rgb(rgb):
    """translate an rgb tuple to hex"""
    return "#%02x%02x%02x" % rgb

# vanilla button class
class buttonL:
    def __init__(self, obj, size, position, text,font, fontSize, hoverColor,command=None):
        self.obj= obj
        self.size= size
        self.position= position
        self.font= font
        self.fontSize= fontSize
        self.hoverColor= hoverColor
        self.text= text
        self.command = command
        self.state = True
        self.Button_ = None

    def myfunc(self):
        print("Hello size :" , self.size)
        print("Hello position :" , self.position)
        print("Hello font :" , self.font)
        print("Hello fontSize :" , self.fontSize)
        print("Hello hoverState :" , self.hoverColor)
  
    def changeOnHover(self, obj,colorOnHover, colorOnLeave):
         obj.bind("<Enter>", func=lambda e: obj.config(
             background=colorOnHover))

         obj.bind("<Leave>", func=lambda e: obj.config(
             background=colorOnLeave))
            
    def buttonShow(self):
        fontStyle = tkFont.Font(family= self.font, size=self.fontSize,weight="bold")
        self.Button_ = Button(self.obj,text = self.text, font=fontStyle, width = self.size[0], height = self.size[1],  bg = self.hoverColor[1] if isinstance(self.hoverColor, list)  == True else  self.hoverColor, compound=TOP,command=self.command)         
        self.Button_.place(x=self.position[0],y=self.position[1])

        if isinstance(self.hoverColor, list) == True:
            self.changeOnHover(self.Button_, self.hoverColor[0], self.hoverColor[1])
        else:
            self.changeOnHover(self.Button_, self.hoverColor, self.hoverColor)
    
    def stateButton(self,st):
        self.st=st
        if not self.Button_ == None:
            self.Button_["state"]=self.st
    
    def buttonUpdate(self, textUpdate = "", colorUpdate = "#fff"):
        temp= [self.hoverColor[0], colorUpdate]
        self.hoverColor = temp
        self.Button_.config(text = textUpdate, bg = self.hoverColor[1] if isinstance(self.hoverColor, list)  == True else  self.hoverColor)
        if isinstance(self.hoverColor, list) == True:
            self.changeOnHover(self.Button_, self.hoverColor[0], self.hoverColor[1])
        else:
            self.changeOnHover(self.Button_, self.hoverColor, self.hoverColor)

# image button class
class buttonImg:
    def __init__(self, obj, imgDir, size, position, hoverColor, command=None):
        self.obj= obj
        self.imgDir= imgDir
        self.size= size
        self.position= position
        self.hoverColor = hoverColor
        self.command = command
        self.state = True
        self.Button_ = None
    
    def changeOnHover(self, obj,colorOnHover, colorOnLeave):
         obj.bind("<Enter>", func=lambda e: obj.config(
             background=colorOnHover))

         obj.bind("<Leave>", func=lambda e: obj.config(
             background=colorOnLeave))
         
    def buttonShow(self):
        self.Button_ = Button(self.obj, width = self.size[0], height = self.size[1], bg = self.hoverColor[1] if isinstance(self.hoverColor, list) == True else self.hoverColor, bd = 10, highlightthickness=4, highlightcolor="#000", highlightbackground="#000", borderwidth = 4, compound=TOP, command=self.command)         
        self.Button_.place(x=self.position[0],y=self.position[1])
        self.imageOpen = Image.open(self.imgDir)
        self.imageOpen = self.imageOpen.resize((self.size[0],self.size[1]), Image.ANTIALIAS)
        self.imageOpen = ImageTk.PhotoImage(self.imageOpen)
        self.Button_.config(image=self.imageOpen)
        
        if isinstance(self.hoverColor, list) == True:
            self.changeOnHover(self.Button_, self.hoverColor[0], self.hoverColor[1])
        else:
            self.changeOnHover(self.Button_, self.hoverColor, self.hoverColor)
    
    def stateButton(self,st):
        self.st=st
        if not self.Button_ == None:
            self.Button_["state"]=self.st
    
    def buttonUpdate(self, colorUpdate = "#fff"):
        temp= [self.hoverColor[0], colorUpdate]
        self.hoverColor = temp
        self.Button_.config(bg = self.hoverColor[1] if isinstance(self.hoverColor, list)  == True else  self.hoverColor)
        if isinstance(self.hoverColor, list) == True:
            self.changeOnHover(self.Button_, self.hoverColor[0], self.hoverColor[1])
        else:
            self.changeOnHover(self.Button_, self.hoverColor, self.hoverColor)

class framecontroller(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        
        #Graphics window
        self.mainWindow = self
        self.mainWindow.configure(bg=BlackSolid)
        self.mainWindow.geometry('%dx%d+%d+%d' % (maxWidth,maxHeight,0,0))
        self.mainWindow.resizable(0,0)
        self.mainWindow.title("Smart Agriculture")
        self.mainWindow.attributes("-fullscreen", True)
        
        # # creating a container
        container = tk.Frame(self.mainWindow) 
        container.configure(bg=BlackSolid)
        container.pack(side = "top", fill = "both", expand = True)
  
        container.grid_rowconfigure(0, weight = 1)
        container.grid_columnconfigure(0, weight = 1)
  
        frame = StartPage(container, self.mainWindow)
        frame.grid(row = 0, column = 0, sticky ="nsew")
        frame.tkraise()
    
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        # backgroud
        self.configure(bg="#444")
        
        # contain
        # Showing each sensor value
        fontStyleLabel= tkFont.Font(family="Arial", size=55, weight = "bold")
        
        self.condLabel = Label(self, text="Tidak Ideal", bg='#444', fg='#fff', font=fontStyleLabel)
        self.condLabel.pack()
        self.condLabel.place(x=120,y=40)
        
        fontStyleLabel= tkFont.Font(family="Arial", size=25)
        
        self.tempLabel = Label(self, text="Temperature", bg='#444', fg='#fff', font=fontStyleLabel)
        self.tempLabel.pack()
        self.tempLabel.place(x=20,y=150)
        
        fontStyleLabel= tkFont.Font(family="Arial", size=45)
        self.tempValue = Label(self, text="0", bg='#444', fg='#fff', font=fontStyleLabel)
        self.tempValue.pack()
        self.tempValue.place(x=20,y=190)
        
        fontStyleLabel= tkFont.Font(family="Arial", size=25)
        self.humLabel = Label(self, text="Kelembapan", bg='#444', fg='#fff', font=fontStyleLabel)
        self.humLabel.pack()
        self.humLabel.place(x=400,y=150)
        
        fontStyleLabel= tkFont.Font(family="Arial", size=45)
        self.humValue = Label(self, text="0", bg='#444', fg='#fff', font=fontStyleLabel)
        self.humValue.pack()
        self.humValue.place(x=400,y=190)
        
        fontStyleLabel= tkFont.Font(family="Arial", size=25)
        self.lightLabel = Label(self, text="Intensitas Cahaya", bg='#444', fg='#fff', font=fontStyleLabel)
        self.lightLabel.pack()
        self.lightLabel.place(x=180,y=275)
        
        fontStyleLabel= tkFont.Font(family="Arial", size=45)
        self.lightValue = Label(self, text="0", bg='#444', fg='#fff', font=fontStyleLabel)
        self.lightValue.pack()
        self.lightValue.place(x=180,y=315)
        
        # Showing each unit sensor values
        fontStyleLabel= tkFont.Font(family="Arial", size=45)
        self.tempUnit = Label(self, text="*C", bg='#444', fg='#fff', font=fontStyleLabel)
        self.tempUnit.pack()
        self.tempUnit.place(x=180,y=190)
        
        self.humUnit = Label(self, text="%", bg='#444', fg='#fff', font=fontStyleLabel)
        self.humUnit.pack()
        self.humUnit.place(x=570,y=190)
        
        self.lightUnit = Label(self, text="Lux", bg='#444', fg='#fff', font=fontStyleLabel)
        self.lightUnit.pack()
        self.lightUnit.place(x=370,y=315)
        
        # Actuator manually control button 
        fontStyle = tkFont.Font(family= "Arial", size=25,weight="bold")
        
        self.button = buttonL(self,[8,2],[5,400],"Pompa air",fontStyle,18,[BlackSolid,_from_rgb((244,239,140))],lambda : [])
        self.button.buttonShow()
        
        self.button2 = buttonL(self,[7,2],[185,400],"Lampu",fontStyle,18,[BlackSolid,_from_rgb((255,190,100))],lambda : [])
        self.button2.buttonShow()
        
        self.button3 = buttonL(self,[7,2],[338,400],"Peltier",fontStyle,18,[BlackSolid,_from_rgb((255,190,100))],lambda : [])
        self.button3.buttonShow()
        
        self.button4 = buttonL(self,[7,2],[490,400],"Humidifier",fontStyle,18,[BlackSolid,_from_rgb((255,190,100))],lambda : [])
        self.button4.buttonShow()
        
    def waterPump(self):

# -------------------------------------- Program Execution ------------------------------
if __name__ == '__main__':
    app = framecontroller()
    scheduler = BackgroundScheduler()
    if recheck is False:
        scheduler.add_job(get_data, 'interval', seconds = 30)
    else:
        scheduler.add_job(get_data, 'interval', seconds = 6)
    scheduler.add_job(subscribe, "interval", seconds = 3)
    scheduler.start()
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
    
    try:
        # This is here to simulate application activity (which keeps the main thread alive)
        while True:
            app.mainloop()
            time.sleep(1)
    except:
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        scheduler.shutdown()

    

        