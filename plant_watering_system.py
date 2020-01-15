import sys
from datetime import datetime, date, time

from time import sleep
from PIL import Image, ImageFont, ImageDraw

import RPi.GPIO as GPIO

import Adafruit_DHT as DHT
import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI

import smtplib
from email.message import EmailMessage

import pickle

from local import *
from remoteLogger import *

#DHT sensor(humdity, temporature) config:
DHT_PIN = 3

#LED sensor config:
LED_GREEN = 13 #Only turned on when pump is operating.
LED_YELLOW = 19 #LCD is updated with new information or data is synced with backend
LED_RED = 26 #always ON, indicates that program in running.

#LDR sensor  config:
LDR_PIN = 2

#Water pump pin config:
# Motor 1
ENA = 12 #white
IN1 = 5 #black, Turn high to start the motor
IN2 = 6 #red

# Motor 2
ENB = 21
IN3 = 16 #Turn HIGH to start the motor
IN4 = 20 
WATER_INTERVAL = 86400 #secs
PUMP_1_ON_DURATION = 30 #secs
PUMP_2_ON_DURATION = 40 #secs
PUMP_3_ON_DURATION = 50 #secs

# Motor 3
ENB_2 = 22
IN3_2 = 17 # turn on high to start the motor
IN4_2 = 27

#Raspberry Pi hardware SPI config:
DC = 23
RST = 24
SPI_PORT = 0
SPI_DEVICE = 0

display = None
image = None
draw = None
font = None

IS_FIRST_START = False

LOCAL_STORAGE_PATH = "/home/pi/Desktop/garden_automation/var.txt"



def getLastTimePumpWasOn():
    
    try:
        varFile = open(LOCAL_STORAGE_PATH,"rb")
        
        d = pickle.load(varFile)
        varFile.close()
        
        logInfo("datetime:{}\ncounter:{}".format(d["datetime"], d["counter"]))

        return d
    except Exception as e:

        IS_FIRST_START = True
        logInfo("is first start is true")

        d = {"datetime":"{}".format(datetime.timestamp(datetime.now())),"counter":0}
        varFile = open(LOCAL_STORAGE_PATH, "wb")
        pickle.dump(d, varFile)
        varFile.close()

        logError("Exception occured.")
        logException(e)

        return d



def initGPIO():

    mode = GPIO.getmode()
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    #LED
    GPIO.setup(LED_GREEN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(LED_YELLOW, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(LED_RED, GPIO.OUT, initial=GPIO.LOW)
    
    #WATER PUMP
    #Motor - 1
    GPIO.setup(ENB, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(IN3, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(IN4, GPIO.OUT, initial=GPIO.LOW)
    #Motor - 2
    GPIO.setup(ENA, GPIO.OUT,  initial=GPIO.LOW)
    GPIO.setup(IN1, GPIO.OUT,  initial=GPIO.LOW)
    GPIO.setup(IN2, GPIO.OUT,  initial=GPIO.LOW)
    #Motor - 3
    GPIO.setup(ENB_2, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(IN3_2, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(IN4_2, GPIO.OUT, initial=GPIO.LOW)
    
    #Turn on RED LED to show the code is working
    try:
        #RED LED
        GPIO.output(LED_RED, GPIO.HIGH)
        #ENABLE MOTOR 1 in L298 Micro-Controller
        GPIO.output(ENB, GPIO.HIGH)
        GPIO.output(ENA, GPIO.HIGH)
        GPIO.output(ENB_2, GPIO.HIGH)
    except:
        pass

def initLCD():

    global display
    global image
    global draw
    global font

    #Hardware SPI usage:
    display = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000))

    #Initialize library
    display.begin(contrast = 60)

    image = Image.new("1",(LCD.LCDWIDTH, LCD.LCDHEIGHT))
    draw=ImageDraw.Draw(image)

    font=ImageFont.load_default()
    mode = GPIO.getmode()
    
    
def sendEmail(humidity, temperature, lightIntensity):
    
    emailServer = smtplib.SMTP_SSL("smtp.gmail.com",465)
    emailServer.login(FROM_EMAIL_ADDR,FROM_EMAIL_PASS)

    currentDate = date.today()

    msg = EmailMessage()
    msg["Subject"] = "Garden Automation Update - %s"  % currentDate.strftime("%d/%m/%Y")
    msg["From"] = FROM_EMAIL_ADDR
    msg["To"] = TO_EMAIL_ADDR
    msg.add_header("Content-Type", "text/html")
    msg.set_payload("<h2>Update:</h2><ul><li>Humidity: {}</li><li>Temperature: {}</li><li>Light Intensity: {}</li></ul>".format(humidity, temperature, lightIntensity))

    emailServer.send_message(msg)
    emailServer.quit()
    logInfo("Email sent")

def sendRestartEmail(msg):
    
    emailServer = smtplib.SMTP_SSL("smtp.gmail.com",465)
    emailServer.login(FROM_EMAIL_ADDR,FROM_EMAIL_PASS)

    currentDate = date.today()

    msg = EmailMessage()
    msg["Subject"] = "Raspberry pi Restarted - %s"  % currentDate.strftime("%d/%m/%Y")
    msg["From"] = FROM_EMAIL_ADDR
    msg["To"] = TO_EMAIL_ADDR
    msg.set_content("Raspberry pi restart but the program is working fine.")
    emailServer.send_message(msg)
    emailServer.quit()

    logInfo("Restart email sent.")

    
def updateLCDDisplay(humidity, temperature, LDR, pumpState):

    initLCD()

    global display
    global image
    global draw
    global font

    #clear the display before displaying anything
    display.clear()
    display.display()
    #creating blank rectangle to clear the display
    draw.rectangle((0, 0, LCD.LCDWIDTH, LCD.LCDHEIGHT),  outline=255, fill=255)
    
    #draw.text((0, 0),"System Info",font=font)
    draw.text((0, 0), ('humi = %s' % humidity), font=font)
    draw.text((0, 10), ('temp = %s' % temperature), font=font)
    draw.text((0, 20), ('LDR = %d' % LDR), font=font)
    draw.text((0, 30), ('Pump = %s' % pumpState), font=font)
    display.image(image)
    display.display()

def getHumidityAndTemperature():
    humdity, temprature = DHT.read_retry(11, DHT_PIN)
    return humdity, temprature


def turnOnYellowLED(state):
    if state:
        GPIO.output(LED_YELLOW, GPIO.HIGH)
    else:
        GPIO.output(LED_YELLOW, GPIO.LOW)

def turnOnGreenLED(state):
    if state:
        GPIO.output(LED_GREEN, GPIO.HIGH)
    else:
        GPIO.output(LED_GREEN, GPIO.LOW)

def rcTime(pin):
    count = 0

    GPIO.setup(LDR_PIN, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)
    sleep(0.1)

    GPIO.setup(LDR_PIN, GPIO.IN)

    while(GPIO.input(pin) == GPIO.LOW):
        count += 1

    return count


def getLightIntensity():
    
    lightSensivity = 0 #Brightest Light

    try:
        lightSensivity = rcTime(LDR_PIN)
    except:
        pass

    return lightSensivity

def turnOnPump(duration, pin):


    GPIO.output(pin, GPIO.HIGH)
    sleep(duration) #in seconds
    GPIO.output(pin, GPIO.LOW)

def updateLocalStorage(timestamp, counter):
    
    global LAST_TIME_WATER_PUMP_WAS_ON
    
    try:
        LAST_TIME_WATER_PUMP_WAS_ON = {"datetime":"{}".format(timestamp),"counter":counter+1}

        varFile = open(LOCAL_STORAGE_PATH, "wb")
        pickle.dump(LAST_TIME_WATER_PUMP_WAS_ON, varFile)
        varFile.close()

        logInfo(LAST_TIME_WATER_PUMP_WAS_ON["datetime"])
    except Exception as e:
        logError("error writing to file")
        logException(e)

    
def shouldTurnOnPump():
  
    global LAST_TIME_WATER_PUMP_WAS_ON
    logInfo("LTWPWO: {}".format(LAST_TIME_WATER_PUMP_WAS_ON))

    now = datetime.now()
    logInfo("now   : {}".format(now))
    
    pastTime = datetime.fromtimestamp(float(LAST_TIME_WATER_PUMP_WAS_ON["datetime"])) 
    counter = LAST_TIME_WATER_PUMP_WAS_ON["counter"]

    #print(pastTime)

    if LAST_TIME_WATER_PUMP_WAS_ON["counter"] == 0:

        updateLocalStorage(datetime.timestamp(now), counter)
        logInfo("turn pump on")
        return True
    else:

        totalSecElapsed = (now - pastTime).total_seconds()
        logInfo("Time elapsed since last pump operation:  %d" % totalSecElapsed)

        if totalSecElapsed >= WATER_INTERVAL:
            #LAST_TIME_WATER_PUMP_WAS_ON = now

            updateLocalStorage(datetime.timestamp(now), counter)

            logInfo("turn pump on")
            return True
        else:
            return False
    

#Temp storatge
LAST_TIME_WATER_PUMP_WAS_ON = getLastTimePumpWasOn()




