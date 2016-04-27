# Creation Date: 2016-04-13
# Author(s):
#		Peter J. Ersts (ersts@amnh.org)
#	
# This file is part of Photo Monitoring Toolkit (PMT).
#
# PMT is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# PMT is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PMT.  If not, see <http://www.gnu.org/licenses/>.
import numpy as np

from PyQt5 import QtCore, QtGui
from pmt import CalibrationIndiciesProcessor

class CalibrationIndiciesProcessorQt(QtCore.QObject, CalibrationIndiciesProcessor):
	progress = QtCore.pyqtSignal(int)
	message = QtCore.pyqtSignal(str)

	def __init__(self, theCalibrator=None):
		QtCore.QObject.__init__(self)
		CalibrationIndiciesProcessor.__init__(self)
		self.radiometricCalibrator = theCalibrator

	def log(self, theMessage, **kwargs):
		if 'progress' in kwargs:
			self.progress.emit(kwargs['progress'])
		self.message.emit(theMessage)

	def process(self, theSourceDir, theDestinationDir):
		#TODO: This needs to be spawned off in new thread
		CalibrationIndiciesProcessor.process(self, theSourceDir, theDestinationDir)