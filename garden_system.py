from plant_watering_system import *

initGPIO()
sendRestartEmail("Program Restarted")
#initLCD()
logging.info("************************************")
logging.info("*                                  *")
logging.info("* Automated Watering System Active *")
logging.info("*                                  *")
logging.info("* Author: Ajeet Kumar              *")
logging.info("* Licence: GNU                     *")
logging.info("*                                  *")
logging.info("*                                  *")
logging.info("************************************")

print("***************Automated Watering System = ON*************")

while(True):

    try:
        humidity, temperature = getHumidityAndTemperature()
        lightIntensity = getLightIntensity()
        pumpState = shouldTurnOnPump()

        updateLCDDisplay(humidity, temperature, lightIntensity, pumpState)
        if pumpState:

            turnOnGreenLED(True) 

            turnOnPump(PUMP_1_ON_DURATION, IN3)
            turnOnPump(PUMP_2_ON_DURATION, IN1)
            logging.info("sending job email")
            sendEmail(humidity, temperature, lightIntensity)
            
            turnOnGreenLED(False)

        sleep(3600)
    except:
        GPIO.cleanup()
        initGPIO()

