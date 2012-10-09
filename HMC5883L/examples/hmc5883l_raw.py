import time
import math
import hmc5883l

# Sensor initialization
mag = hmc5883l.HMC5883L()
mag.initialize()

while True:
    data = mag.getHeading()
    
    print(data['x']),
    print(data['y']),
    print(data['z'])
