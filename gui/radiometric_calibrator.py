# Creation Date: 2016-03-15
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
from pmt import RadiometricCalibrator

class RadiometricCalibratorQt(QtCore.QObject, RadiometricCalibrator):
	modelCreated = QtCore.pyqtSignal(list)
	pixmapCreated = QtCore.pyqtSignal(QtGui.QPixmap)
	roisLoaded = QtCore.pyqtSignal(list)

	def __init__(self):
		QtCore.QObject.__init__(self)
		RadiometricCalibrator.__init__(self)

	def generateModel(self):
		if RadiometricCalibrator.generateModel(self):
			self.modelCreated.emit(self.model)
	def loadImage(self, theImage):
		if RadiometricCalibrator.loadImage(self, theImage):
			imageArray = np.array(self.image)
			qImage = QtGui.QImage(imageArray, imageArray.shape[1], imageArray.shape[0], QtGui.QImage.Format_RGB888)
			self.pixmapCreated.emit(QtGui.QPixmap.fromImage(qImage))
			self.roisLoaded.emit(self.rois)
		else:
			return False
		return True