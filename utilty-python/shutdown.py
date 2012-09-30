import serial
ser = serial.Serial('/dev/ttyACM0', 115200)
ser.write('s\n')
import os
os.system("sudo shutdown -h now")
