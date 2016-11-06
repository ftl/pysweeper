# Copyright (c) Florian Thienel/DL3NEY.
# 
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html 

import sys
from PySide.QtCore import *
from gui import *
from sweeper import *

app = QApplication(sys.argv)
sweeper = Sweeper()

mainWindow = MainWindow(app, sweeper)
mainWindow.show()

app.exec_()

sweeper.close_connection()
