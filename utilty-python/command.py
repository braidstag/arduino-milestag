import serial

count = 0

while count < 5:
	value = raw_input("Command? : ")


	ser = serial.Serial('/dev/ttyACM0', 115200)
	
	ser.write(value + '\n') #Line-Ends the communication, speeds up responses
