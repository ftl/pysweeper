# -*- coding: utf-8 -*-

# Copyright (c) Florian Thienel/DL3NEY.
# 
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html 

import sys
from PySide.QtCore import *
from PySide.QtGui import *
import pyqtgraph as pg

class MainWindow(QMainWindow):
    def __init__(self, app, sweeper):
        QMainWindow.__init__(self, None)

        self.qt_app = app
        self.sweeper = sweeper

        self.setWindowTitle('DDS Sweeper')
        self.setMinimumSize(800, 600)

        root_frame = QFrame(self)
        self.setCentralWidget(root_frame)
 
        sidebar = QFrame(root_frame)
        port_label = QLabel('Port', sidebar)
        self.port_edit = QLineEdit('/dev/ttyUSB0', sidebar)
        self.connect_button = QPushButton('&Connect', sidebar)
        self.connect_button.clicked.connect(self.connect_sweeper)
        self.disconnect_button = QPushButton('&Disconnect', sidebar)
        self.disconnect_button.clicked.connect(self.disconnect_sweeper)

        start_frequency_label = QLabel('Start Frequency [Hz]', sidebar)
        self.start_frequency_edit = QSpinBox(sidebar)
        self.start_frequency_edit.setRange(1000000, 30000000)
        self.start_frequency_edit.setValue(13500000)
        stop_frequency_label = QLabel('Stop Frequency [Hz]', sidebar)
        self.stop_frequency_edit = QSpinBox(sidebar)
        self.stop_frequency_edit.setRange(1000000, 30000000)
        self.stop_frequency_edit.setValue(14500000)
        steps_label = QLabel('Steps', sidebar)
        self.steps_edit = QSpinBox(sidebar)
        self.steps_edit.setRange(10, 9999)
        self.steps_edit.setValue(100)
        self.sweep_button = QPushButton('&Start Sweep', sidebar)
        self.sweep_button.clicked.connect(self.sweep)

        self.plotter = SweepPlotter(app, root_frame)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.addWidget(port_label)
        sidebar_layout.addWidget(self.port_edit)
        sidebar_layout.addWidget(self.connect_button)
        sidebar_layout.addWidget(self.disconnect_button)
        sidebar_layout.addWidget(start_frequency_label)
        sidebar_layout.addWidget(self.start_frequency_edit)
        sidebar_layout.addWidget(stop_frequency_label)
        sidebar_layout.addWidget(self.stop_frequency_edit)
        sidebar_layout.addWidget(steps_label)
        sidebar_layout.addWidget(self.steps_edit)
        sidebar_layout.addWidget(self.sweep_button)
        sidebar_layout.addStretch(100)
        sidebar.setLayout(sidebar_layout)
 
        root_layout = QHBoxLayout()
        root_layout.addWidget(sidebar, 20)
        root_layout.addWidget(self.plotter, 80)
        root_frame.setLayout(root_layout)

        self.sweeper.connection_opened.connect(self.sweeper_connected)
        self.sweeper.connection_closed.connect(self.sweeper_disconnected)
        self.sweeper.data_point_received.connect(self.plotter.add_data_point)

        self._update_enablement(self.sweeper.is_connected())

 
    def connect_sweeper(self):
        self.sweeper.open_connection(self.port_edit.text())

    def disconnect_sweeper(self):
        self.sweeper.close_connection()

    def sweep(self):
        start_frequency = self.start_frequency_edit.value()
        stop_frequency = self.stop_frequency_edit.value()
        steps = self.steps_edit.value()

        self.plotter.sweep(start_frequency, stop_frequency)
        self.sweeper.sweep(start_frequency, stop_frequency, steps)

    def sweeper_connected(self):
        self._update_enablement(True)

    def sweeper_disconnected(self):
        self._update_enablement(False)

    def _update_enablement(self, sweeper_connected):
    	self.connect_button.setEnabled(not(sweeper_connected))
    	self.disconnect_button.setEnabled(sweeper_connected)
    	self.sweep_button.setEnabled(sweeper_connected)

class SweepPlotter(pg.PlotWidget):
    def __init__(self, app, parent):
        pg.PlotWidget.__init__(self, parent)
        self.disableAutoRange(pg.ViewBox.XAxis)
        self.getAxis('bottom').setLabel('f [Hz]')
        self.getAxis('left').setLabel('VSWR')
        self.sweep_plot = self.plot()
        self.min_line = self.addLine(x=0)
        self.qt_app = app
        self._reset_data()

    def sweep(self, start_frequency, stop_frequency):
        self._reset_data()
        self.setXRange(start_frequency, stop_frequency)

    def add_data_point(self, frequency, vswr, forward, reverse):
        self.x_values.append(frequency)
        self.y_values.append(vswr)
        if (self.min_vswr > vswr):
            self.min_vswr = vswr
            self.min_vswr_frequency = frequency
            self.min_line.setValue(frequency)
        self.sweep_plot.setData(self.x_values, self.y_values)
        self.qt_app.processEvents()

    def _reset_data(self):
        self.x_values = []
        self.y_values = []
        self.min_vswr = sys.maxsize
        self.min_vswr_frequency = 0
