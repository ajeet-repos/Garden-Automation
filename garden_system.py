from plant_watering_system import *

initGPIO()
sendRestartEmail("Program Restarted")
#initLCD()
logInfo("************************************")
logInfo("*                                  *")
logInfo("* Automated Watering System Active *")
logInfo("*                                  *")
logInfo("* Author: Ajeet Kumar              *")
logInfo("* Licence: GNU                     *")
logInfo("*                                  *")
logInfo("*                                  *")
logInfo("************************************")

logInfo("***************Automated Watering System = ON*************")

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
            logInfo("sending job email")
            sendEmail(humidity, temperature, lightIntensity)
            
            turnOnGreenLED(False)

        sleep(3600)
    except:
        GPIO.cleanup()
        initGPIO()

