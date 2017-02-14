import mraa
import time
import pyupm_i2clcd as lcd
import math
 
switch_pin_number=8
 
# Configuring the switch and buzzer as GPIO interfaces
switch = mraa.Gpio(switch_pin_number)


# Initialize Jhd1313m1 at 0x3E (LCD_ADDRESS) and 0x62 (RGB_ADDRESS)
myLcd = lcd.Jhd1313m1(0, 0x3E, 0x62)
 
myLcd.setCursor(0,0)
# RGB Blue
myLcd.setColor(53, 39, 249)
 
# RGB Red
# myLcd.setColor(255, 0, 0)
 

#myLcd.setCursor(1,2)
#myLcd.write('Hello World')


 
# Configuring the switch and buzzer as input & output respectively
switch.dir(mraa.DIR_IN)
 
print "Press Ctrl+C to escape..."
try:
        while (1):
                if (switch.read()):     # check if switch pressed
                	tempSensor = mraa.Aio(1)
    			# print (tempSensor.read()), "is the current temperature")
			temp = float (tempSensor.read())
			temp = 1023.0/(temp)-1.0;
			temp = 100000.0 * temp;
			temp = 1.0/(math.log(temp/100000.0)/4275+1/298.15)-273.15;
			myLcd.setCursor(0, 0)
			myLcd.write(str(temp))
    			#myLcd.setCursor(0, 0)
			#myLcd.write("a")
			time.sleep(0.2) # puts system to sleep for 0.2sec before switching
    				
    		else :
    			myLcd.write('')

except KeyboardInterrupt:
        exit
