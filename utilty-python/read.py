import serial
ser = serial.Serial('/dev/ttyACM0', 115200)
while 1:
	print ser.readline()

