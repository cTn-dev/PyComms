from bmp085 import BMP085

bmp = BMP085()

temp = bmp.readTemperature()
pressure = bmp.readPressure()
altitude = bmp.readAltitude()

print ("Temperature: %.2f C" % temp)
print ("Pressure:    %.2f hPa" % (pressure / 100.0))
print ("Altitude:    %.2f" % altitude)
