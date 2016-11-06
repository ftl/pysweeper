# Copyright (c) Florian Thienel/DL3NEY.
# 
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html 

import serial, re
from PySide.QtCore import *

class SweepInfo:
    def __init__(self, start_frequency, stop_frequency, steps):
        self.start_frequency = start_frequency
        self.stop_frequency = stop_frequency
        self.steps = steps

class DataPoint:
    PATTERN = re.compile('(\d+\.\d{2}), 0, (\d+\.\d{5}), (\d+), (\d+)')
    def __init__(self, frequency, vswr, forward, reverse):
        self.frequency = frequency
        self.vswr = vswr
        self.forward = forward
        self.reverse = reverse

class Sweeper(QObject):
    connection_opened = Signal()
    connection_closed = Signal()
    data_point_received = Signal(float, float, int, int)

    def __init__(self):
        QObject.__init__(self)
        self.serial = None

    def open_connection(self, serialPort):
        if self.is_connected(): return
        self.serial = serial.Serial(
            port = serialPort,
            baudrate = 57600,
            parity = serial.PARITY_NONE,
            stopbits = serial.STOPBITS_ONE,
            bytesize = serial.EIGHTBITS
        )
        print 'Connecting to ' + self.serial.port
        print self._read_until(r"Build Date\s+:.*\n")
        print 'Connected to ' + self.serial.port
        self.connection_opened.emit()

    def close_connection(self):
        if not(self.is_connected()): return
        self.serial.close()
        self.serial = None
        print 'Disconnected'
        self.connection_closed.emit()

    def is_connected(self):
    	return not(self.serial is None)

    def get_version_info(self):
        if not(self.is_connected()): return
        self.serial.write('v')
        self.serial.flush()
        print self._read_until(r"Build Date\s+:.*\n")

    def get_sweep_info(self):
        if not(self.is_connected()): return
        self.serial.write('?')
        self.serial.flush()
        print self._read_until(r"Num Steps:\s+.*\n")

    def sweep(self, start_frequency, stop_frequency, steps):
        if not(self.is_connected()): return
        self.serial.write(str(start_frequency) + 'a' + str(stop_frequency) + 'b' + str(steps) + 'ns')
        self.serial.flush()
        data_point = self._read_next_data_point()
        while data_point:
            self.data_point_received.emit(data_point.frequency, data_point.vswr, data_point.forward, data_point.reverse)            
            data_point = self._read_next_data_point()

    def _read_next_data_point(self):
        line = ''
        while True:
            c = self.serial.read(1)
            line += c
            if c == '\n':
                m = DataPoint.PATTERN.match(line)
                if m:
                    frequency = float(m.group(1))
                    vswr = float(m.group(2)) / 1000
                    forward = int(m.group(3))
                    reverse = int(m.group(4))
                    return DataPoint(frequency, vswr, forward, reverse)
                elif line.startswith('End'):
                    return None
                else: 
                    line = ''        

    def _read_until(self, expectedResponse):
        responsePattern = re.compile(expectedResponse, re.DOTALL)
        response = ''
        while True:
            response += self.serial.read(1)
            if responsePattern.search(response):
                break
        return response
