#!/usr/bin/python

# Python Standard Library Imports
import time

# External Imports
pass

# Custom Imports
from pycomms import PyComms

# ===========================================================================
# Adafruit BMP085 Class (slightly modified)
# ===========================================================================

class BMP085:
    i2c = None

    # Operating Modes
    __BMP085_ULTRALOWPOWER     = 0
    __BMP085_STANDARD          = 1
    __BMP085_HIGHRES           = 2
    __BMP085_ULTRAHIGHRES      = 3

    # BMP085 Registers
    __BMP085_CAL_AC1           = 0xAA  # R   Calibration data (16 bits)
    __BMP085_CAL_AC2           = 0xAC  # R   Calibration data (16 bits)
    __BMP085_CAL_AC3           = 0xAE  # R   Calibration data (16 bits)
    __BMP085_CAL_AC4           = 0xB0  # R   Calibration data (16 bits)
    __BMP085_CAL_AC5           = 0xB2  # R   Calibration data (16 bits)
    __BMP085_CAL_AC6           = 0xB4  # R   Calibration data (16 bits)
    __BMP085_CAL_B1            = 0xB6  # R   Calibration data (16 bits)
    __BMP085_CAL_B2            = 0xB8  # R   Calibration data (16 bits)
    __BMP085_CAL_MB            = 0xBA  # R   Calibration data (16 bits)
    __BMP085_CAL_MC            = 0xBC  # R   Calibration data (16 bits)
    __BMP085_CAL_MD            = 0xBE  # R   Calibration data (16 bits)
    __BMP085_CONTROL           = 0xF4
    __BMP085_TEMPDATA          = 0xF6
    __BMP085_PRESSUREDATA      = 0xF6
    __BMP085_READTEMPCMD       = 0x2E
    __BMP085_READPRESSURECMD   = 0x34

    # Private Fields
    _cal_AC1 = 0
    _cal_AC2 = 0
    _cal_AC3 = 0
    _cal_AC4 = 0
    _cal_AC5 = 0
    _cal_AC6 = 0
    _cal_B1 = 0
    _cal_B2 = 0
    _cal_MB = 0
    _cal_MC = 0
    _cal_MD = 0

    def __init__(self, address = 0x77, mode = 3):
        self.i2c = PyComms(address)
        self.address = address

        # Make sure the specified mode is in the appropriate range
        if ((mode < 0) | (mode > 3)):
            self.mode = self.__BMP085_STANDARD
        else:
            self.mode = mode
            
        # Read the calibration data
        self.readCalibrationData()

    def readCalibrationData(self):
        # Reads the calibration data from the IC
        self._cal_AC1 = self.i2c.readS16(self.__BMP085_CAL_AC1)   # INT16
        self._cal_AC2 = self.i2c.readS16(self.__BMP085_CAL_AC2)   # INT16
        self._cal_AC3 = self.i2c.readS16(self.__BMP085_CAL_AC3)   # INT16
        self._cal_AC4 = self.i2c.readU16(self.__BMP085_CAL_AC4)   # UINT16
        self._cal_AC5 = self.i2c.readU16(self.__BMP085_CAL_AC5)   # UINT16
        self._cal_AC6 = self.i2c.readU16(self.__BMP085_CAL_AC6)   # UINT16
        self._cal_B1 = self.i2c.readS16(self.__BMP085_CAL_B1)     # INT16
        self._cal_B2 = self.i2c.readS16(self.__BMP085_CAL_B2)     # INT16
        self._cal_MB = self.i2c.readS16(self.__BMP085_CAL_MB)     # INT16
        self._cal_MC = self.i2c.readS16(self.__BMP085_CAL_MC)     # INT16
        self._cal_MD = self.i2c.readS16(self.__BMP085_CAL_MD)     # INT16

    def readRawTemp(self):
        # Reads the raw (uncompensated) temperature from the sensor
        self.i2c.write8(self.__BMP085_CONTROL, self.__BMP085_READTEMPCMD)
        time.sleep(0.005)  # Wait 5ms
        raw = self.i2c.readU16(self.__BMP085_TEMPDATA)
        
        return raw

    def readRawPressure(self):
        # Reads the raw (uncompensated) pressure level from the sensor
        self.i2c.write8(self.__BMP085_CONTROL, self.__BMP085_READPRESSURECMD + (self.mode << 6))
        if (self.mode == self.__BMP085_ULTRALOWPOWER):
            time.sleep(0.005)
        elif (self.mode == self.__BMP085_HIGHRES):
            time.sleep(0.014)
        elif (self.mode == self.__BMP085_ULTRAHIGHRES):
            time.sleep(0.026)
        else:
          time.sleep(0.008)
          
        msb = self.i2c.readU8(self.__BMP085_PRESSUREDATA)
        lsb = self.i2c.readU8(self.__BMP085_PRESSUREDATA + 1)
        xlsb = self.i2c.readU8(self.__BMP085_PRESSUREDATA + 2)
        
        raw = ((msb << 16) + (lsb << 8) + xlsb) >> (8 - self.mode)
        
        return raw

    def readTemperature(self):
        # Gets the compensated temperature in degrees celcius
        UT = 0
        X1 = 0
        X2 = 0
        B5 = 0
        temp = 0.0

        # Read raw temp before aligning it with the calibration values
        UT = self.readRawTemp()
        X1 = ((UT - self._cal_AC6) * self._cal_AC5) >> 15
        X2 = (self._cal_MC << 11) / (X1 + self._cal_MD)
        B5 = X1 + X2
        temp = ((B5 + 8) >> 4) / 10.0
        
        return temp

    def readPressure(self):
        # Gets the compensated pressure in pascal
        UT = 0
        UP = 0
        B3 = 0
        B5 = 0
        B6 = 0
        X1 = 0
        X2 = 0
        X3 = 0
        p = 0
        B4 = 0
        B7 = 0

        UT = self.readRawTemp()
        UP = self.readRawPressure()

        # True Temperature Calculations
        X1 = ((UT - self._cal_AC6) * self._cal_AC5) >> 15
        X2 = (self._cal_MC << 11) / (X1 + self._cal_MD)
        B5 = X1 + X2

        # Pressure Calculations
        B6 = B5 - 4000
        X1 = (self._cal_B2 * (B6 * B6) >> 12) >> 11
        X2 = (self._cal_AC2 * B6) >> 11
        X3 = X1 + X2
        B3 = (((self._cal_AC1 * 4 + X3) << self.mode) + 2) / 4

        X1 = (self._cal_AC3 * B6) >> 13
        X2 = (self._cal_B1 * ((B6 * B6) >> 12)) >> 16
        X3 = ((X1 + X2) + 2) >> 2
        B4 = (self._cal_AC4 * (X3 + 32768)) >> 15
        B7 = (UP - B3) * (50000 >> self.mode)

        if (B7 < 0x80000000):
            p = (B7 * 2) / B4
        else:
            p = (B7 / B4) * 2

        X1 = (p >> 8) * (p >> 8)
        X1 = (X1 * 3038) >> 16
        X2 = (-7375 * p) >> 16

        p = p + ((X1 + X2 + 3791) >> 4)

        return p

    def readAltitude(self, seaLevelPressure = 101325):
        # Calculates the altitude in meters
        altitude = 0.0
        pressure = float(self.readPressure())
        altitude = 44330.0 * (1.0 - pow(pressure / seaLevelPressure, 0.1903))
        
        return altitude
        return 0