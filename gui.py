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
        self.sweep_tab = SweepTab(sidebar)

        self.plotter = SweepPlotter(app, root_frame)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.addWidget(port_label)
        sidebar_layout.addWidget(self.port_edit)
        sidebar_layout.addWidget(self.connect_button)
        sidebar_layout.addWidget(self.disconnect_button)
        sidebar_layout.addWidget(self.sweep_tab)
        sidebar_layout.addStretch(100)
        sidebar.setLayout(sidebar_layout)
 
        root_layout = QHBoxLayout()
        root_layout.addWidget(sidebar, 20)
        root_layout.addWidget(self.plotter, 80)
        root_frame.setLayout(root_layout)

        self.sweep_tab.start_sweep.connect(self.plotter.sweep)
        self.sweep_tab.start_sweep.connect(self.sweeper.sweep)

        self.sweeper.connection_opened.connect(self.sweeper_connected)
        self.sweeper.connection_closed.connect(self.sweeper_disconnected)
        self.sweeper.data_point_received.connect(self.plotter.add_data_point)

        self._update_enablement(self.sweeper.is_connected())

 
    def connect_sweeper(self):
        self.sweeper.open_connection(self.port_edit.text())

    def disconnect_sweeper(self):
        self.sweeper.close_connection()

    def sweeper_connected(self):
        self._update_enablement(True)

    def sweeper_disconnected(self):
        self._update_enablement(False)

    def _update_enablement(self, sweeper_connected):
    	self.connect_button.setEnabled(not(sweeper_connected))
    	self.disconnect_button.setEnabled(sweeper_connected)
    	self.sweep_tab.setEnabled(sweeper_connected)

class SweepTab(QWidget):
    start_sweep = Signal(int, int, int)

    def __init__(self, parent = None):
        QWidget.__init__(self, parent)

        start_frequency_label = QLabel('Start Frequency [Hz]', self)
        self.start_frequency_edit = QSpinBox(self)
        self.start_frequency_edit.setRange(1000000, 30000000)
        self.start_frequency_edit.setValue(13500000)
        stop_frequency_label = QLabel('Stop Frequency [Hz]', self)
        self.stop_frequency_edit = QSpinBox(self)
        self.stop_frequency_edit.setRange(1000000, 30000000)
        self.stop_frequency_edit.setValue(14500000)
        steps_label = QLabel('Steps', self)
        self.steps_edit = QSpinBox(self)
        self.steps_edit.setRange(10, 9999)
        self.steps_edit.setValue(100)
        sweep_button = QPushButton('&Start Sweep', self)
        sweep_button.clicked.connect(self._sweep)

        layout = QVBoxLayout()
        layout.addWidget(start_frequency_label)
        layout.addWidget(self.start_frequency_edit)
        layout.addWidget(stop_frequency_label)
        layout.addWidget(self.stop_frequency_edit)
        layout.addWidget(steps_label)
        layout.addWidget(self.steps_edit)
        layout.addWidget(sweep_button)
        self.setLayout(layout)

    def _sweep(self):
        start_frequency = self.start_frequency_edit.value()
        stop_frequency = self.stop_frequency_edit.value()
        steps = self.steps_edit.value()

        self.start_sweep.emit(start_frequency, stop_frequency, steps)

class SweepPlotter(pg.PlotWidget):
    def __init__(self, app, parent):
        pg.PlotWidget.__init__(self, parent)
        self.getAxis('bottom').setLabel('f [Hz]')
        self.getAxis('left').setLabel('VSWR')
        self.sweep_plot = self.plot()
        self.max_vswr = 0
        self.min_vswr = sys.maxsize
        self.min_vswr_frequency = 0
        self.min_line = self.addLine(x=0)
        self.qt_app = app
        self._reset_data()

    def sweep(self, start_frequency, stop_frequency):
        self._reset_data()
        self.setXRange(start_frequency, stop_frequency)
        self.setYRange(0.9, 2.0)

    def add_data_point(self, frequency, vswr, forward, reverse):
        self.x_values.append(frequency)
        self.y_values.append(vswr)
        if (self.max_vswr < vswr):
            self.max_vswr = vswr
        if (self.max_vswr > self.viewRange()[1][1]):
            self.setYRange(0.9, self.max_vswr)
        if (self.min_vswr > vswr):
            self.min_vswr = vswr
            self.min_vswr_frequency = frequency
            self.min_line.setValue(frequency)
        self.sweep_plot.setData(self.x_values, self.y_values)
        self.qt_app.processEvents()

    def _reset_data(self):
        self.x_values = []
        self.y_values = []
        self.max_vswr = 0
        self.min_vswr = sys.maxsize
        self.min_vswr_frequency = 0
