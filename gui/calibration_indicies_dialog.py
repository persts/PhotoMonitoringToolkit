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
import os, glob, datetime
from PyQt5 import QtCore, QtGui, QtWidgets, uic

INDICIES_WIDGET, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'calibration_indicies_dialog.ui'))

class CalibrationIndiciesDialog(QtWidgets.QWidget, INDICIES_WIDGET):
	def __init__(self, theProcessor, parent=None):
		QtWidgets.QWidget.__init__(self)
		self.setupUi(self)
		self.processor = theProcessor
		self.fileExtension = 'JPG'
		self.source = ''
		self.destination = ''
		self.filesToProcess = 0

		self.textBrowser.setFontPointSize(8)
		self.progressBar.setRange(0, 1)
		self.progressBar.setValue(0)

		self.processor.message.connect(self.log)
		self.processor.progress.connect(self.progressBar.setValue)

		self.setWindowTitle('Calibration & Indicies')
		self.checkBoxRadiometricCalibration.stateChanged.connect(self.toggleCalibration)
		self.spinBoxMin.valueChanged.connect(self.setMin)
		self.spinBoxMax.valueChanged.connect(self.setMax)
		self.comboBoxLut.currentIndexChanged.connect(self.setLut)
		self.comboBoxIndex.currentIndexChanged.connect(self.setIndex)
		self.comboBoxRedBand.currentIndexChanged.connect(self.setRedBand)
		self.comboBoxNirBand.currentIndexChanged.connect(self.setNirBand)
		self.lineEditFileExtension.editingFinished.connect(self.updateFileExtension)
		self.pushButtonSource.clicked.connect(self.setSource)
		self.pushButtonDestination.clicked.connect(self.setDestination)
		self.pushButtonRun.clicked.connect(self.run)

	def checkDirectories(self):
		if self.source == '' or self.destination == '':
			self.pushButtonRun.setEnabled(False)
		elif self.source == self.destination:
			self.pushButtonRun.setEnabled(False)
			QtWidgets.QMessageBox.warning(self, 'Warning!', 'Source and Destination folders can not be the same')
			return False
		elif self.getFileCount() > 0:
			self.pushButtonRun.setEnabled(True)
		return True

	def getFileCount(self):
		if self.source != '':
			fileList = glob.glob(self.source+'/*.'+self.fileExtension)
			count = len(fileList)
			if count > 0:
				self.progressBar.setMaximum(count)	 
			else:
				self.progressBar.setMaximum(1)
			return count
		return 0

	def log(self, theMessage):
		self.textBrowser.append(datetime.datetime.now().isoformat()+': '+theMessage)

	def run(self):
		self.progressBar.setValue(0)
		self.processor.process(self.source, self.destination)

	def setDestination(self):
		self.destination = QtWidgets.QFileDialog.getExistingDirectory(self)
		if self.destination != '' and self.checkDirectories():
			self.log("Destination Directory: "+self.destination)
		else:
			self.destination = ''

	def setIndex(self, theIndex):
		index = self.comboBoxIndex.currentText()
		self.processor.index = self.comboBoxIndex.currentText()
		if index == 'None':
			self.comboBoxRedBand.setEnabled(False)
			self.comboBoxNirBand.setEnabled(False)
		else:			
			self.comboBoxRedBand.setEnabled(True)
			self.comboBoxNirBand.setEnabled(True)
		self.toggleLut()
	def setLut(self, theIndex):
		self.processor.lut = self.comboBoxLut.currentText()

	def setMax(self, theValue):
		self.processor.scaleTo = theValue
		self.toggleLut()

	def setMin(self, theValue):
		self.processor.scaleFrom = theValue

	def setNirBand(self, theIndex):
		self.processor.nirBand = theIndex + 1

	def setRedBand(self, theIndex):
		self.processor.redBand = theIndex + 1

	def setSource(self):
		self.source = QtWidgets.QFileDialog.getExistingDirectory(self)
		if self.source != '' and self.checkDirectories():
			self.log('[ '+str(self.getFileCount())+' ] '+self.fileExtension+' files found in '+self.source)
		else: 
			self.source = ''

	def toggleCalibration(self, theState):
		if theState == QtCore.Qt.Checked:
			self.processor.radiometricCalibration = True
		else:
			self.processor.radiometricCalibration = False

	def toggleLut(self):
		if self.comboBoxIndex.currentText() == 'None':
			self.comboBoxLut.setEnabled(False)
		elif self.spinBoxMax.value() <= 1 or self.spinBoxMax.value() > 255:
			self.comboBoxLut.setEnabled(False)
		else:
			self.comboBoxLut.setEnabled(True)

	def updateFileExtension(self):
		self.fileExtension = self.lineEditFileExtension.text()
		if self.source != '':
			self.log('[ '+str(self.getFileCount())+' ] '+self.fileExtension+' files found in '+self.source)
			