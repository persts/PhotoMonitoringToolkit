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
import sys, os, csv
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets, uic

from gui.mpl_ui import MplLinearRegressionWidget



CALIBRATION_WIDGET, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'radiometric_calibration_dialog.ui'))

class RadiometricCalibrationDialog(QtWidgets.QWidget, CALIBRATION_WIDGET):
	def __init__(self, theCalibrator, parent=None):
		QtWidgets.QWidget.__init__(self)
		self.setupUi(self)
		self.currentRoi = None
		self.pixmap = None
		self.rois = []
		self.roiRects = []
		self.baseWindowTitle = "Target Calibration"
		self.setWindowTitle(self.baseWindowTitle)
		
		self.calibrator = theCalibrator
		self.loadRois(theCalibrator.rois)

		self.calibrator.pixmapCreated.connect(self.setPixmap)
		self.calibrator.roisLoaded.connect(self.loadRois)
		self.calibrator.modelCreated.connect(self.plotModel)

		self.cboxGammaCorrection.stateChanged.connect(self.toggleGamma)
		self.dsboxGamma.valueChanged.connect(self.calibrator.setGamma)

		self.cboxSubtraction.stateChanged.connect(self.toggleSubtraction)
		self.sboxPercent.valueChanged.connect(self.subtractionParametersChanged)
		self.cboxSourceBand.currentIndexChanged.connect(self.subtractionParametersChanged)
		self.cboxFromBand.currentIndexChanged.connect(self.subtractionParametersChanged)

		self.scene = QtWidgets.QGraphicsScene()
		self.graphicsView.setScene(self.scene)
		self.graphicsView.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
		self.graphicsView.rubberBandChanged.connect(self.recordRubberBand)

		self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
		self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
		self.tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
		self.tableWidget.cellClicked.connect(self.displayRoi)
		self.tableWidget.cellChanged.connect(self.cellChanged)

		self.pbuttonAddRow.clicked.connect(self.addRoi)
		self.pbuttonDeleteRow.clicked.connect(self.deleteRoi)
		self.pbuttonLoadFromFile.clicked.connect(self.loadFromFile)
		self.pbuttonLoadImage.clicked.connect(self.loadImage)
		self.pbuttonSaveRois.clicked.connect(self.saveRois)
		self.pbuttonZoomOut.clicked.connect(self.zoomOut)
		self.pbuttonZoomIn.clicked.connect(self.zoomIn)

		layout = QtWidgets.QVBoxLayout(self.frameRed)
		layout.setContentsMargins(0,0,0,0)
		self.mplWidgetRed = MplLinearRegressionWidget()
		layout.addWidget(self.mplWidgetRed)

		layout = QtWidgets.QVBoxLayout(self.frameGreen)
		layout.setContentsMargins(0,0,0,0)
		self.mplWidgetGreen = MplLinearRegressionWidget()
		layout.addWidget(self.mplWidgetGreen)

		layout = QtWidgets.QVBoxLayout(self.frameBlue)
		layout.setContentsMargins(0,0,0,0)
		self.mplWidgetBlue = MplLinearRegressionWidget()
		layout.addWidget(self.mplWidgetBlue)

	def addRoi(self, theRoi=None):
		rowCount = self.tableWidget.rowCount() + 1
		newRoi = ["ROI"+str(rowCount), [0.0,0.0,0.0], [0.0, 0.0, 0.0, 0.0], [0.0,0.0,0.0]]
		if theRoi != None and theRoi != False:
			newRoi = theRoi
		self.rois.append(newRoi)
		self.addRoiToTable(newRoi)
		self.tableWidget.selectRow(rowCount-1)
		self.calibrator.setRois(self.rois)

	def addRoiToTable(self, theRoi):
		self.roiRects.append(QtCore.QRectF(theRoi[2][0], theRoi[2][1], theRoi[2][2], theRoi[2][3]))
		rows = self.tableWidget.rowCount() + 1
		self.tableWidget.setRowCount(rows)
		
		self.tableWidget.blockSignals(True)
		self.tableWidget.setItem(rows-1, 0, QtWidgets.QTableWidgetItem(str(theRoi[0])))
		self.tableWidget.setItem(rows-1, 1, QtWidgets.QTableWidgetItem(str(theRoi[1][0])))
		self.tableWidget.setItem(rows-1, 2, QtWidgets.QTableWidgetItem(str(theRoi[1][1])))
		self.tableWidget.setItem(rows-1, 3, QtWidgets.QTableWidgetItem(str(theRoi[1][2])))
		self.tableWidget.setItem(rows-1, 4, QtWidgets.QTableWidgetItem(str.format('{0:.2f}', theRoi[3][0])+', '+str.format('{0:.2f}', theRoi[3][1])+', '+str.format('{0:.2f}', theRoi[3][2])))
		self.tableWidget.item(rows-1, 4).setFlags(self.tableWidget.item(rows-1, 4).flags() ^ QtCore.Qt.ItemIsEditable)
		self.tableWidget.blockSignals(False)

	def cellChanged(self, theRow, theColumn):
		item = self.tableWidget.item(theRow, theColumn)
		if item.text() != None and item.text() != '':
			if theColumn == 0:
				self.rois[theRow][theColumn] = item.text()
			else:
				calibrationData = self.rois[theRow][1]
				calibrationData[theColumn - 1] = float(item.text())
				self.calibrator.setRois(self.rois)

	def deleteRoi(self):
		currentRow = self.tableWidget.currentRow()
		if currentRow != -1:
			if len(self.scene.items()) == 2:
				self.scene.removeItem(self.scene.items()[0])
			self.tableWidget.removeRow(currentRow)
			self.rois.remove(self.rois[currentRow])
			self.roiRects.remove(self.roiRects[currentRow])
			self.tableWidget.setCurrentIndex(QtCore.QModelIndex())
			self.calibrator.setRois(self.rois)

	def displayRoi(self, theRow):
		if self.roiRects[theRow].width() != 0:
			if len(self.scene.items()) == 2:
				self.scene.removeItem(self.scene.items()[0])
			self.scene.addRect(QtCore.QRectF(self.roiRects[theRow]), QtGui.QPen(QtGui.QBrush(QtCore.Qt.yellow, QtCore.Qt.SolidPattern), 4))
			self.graphicsView.centerOn(self.roiRects[theRow].center())

	def loadFromFile(self):
		fileName = QtWidgets.QFileDialog.getOpenFileName(self, 'Open CSV file')
		if fileName[0] != '':
			with open(fileName[0], 'r') as file:
				reader = csv.reader(file, delimiter=',')
				for row in reader:
					if len(row) == 4:
						newRoi = [row[0], [float(row[1]),float(row[2]),float(row[3]) ], [0.0, 0.0, 0.0, 0,0], [0.0,0.0,0.0]]
						self.addRoi(newRoi)

	def loadImage(self):
		self.scene.clear()
		fileName = QtWidgets.QFileDialog.getOpenFileName(self, 'Open Image')
		if not fileName[0] == '':		
			self.calibrator.loadImage(fileName[0])

	def loadRois(self, theRois):
		self.rois = theRois
		self.tableWidget.setRowCount(0)
		for roi in theRois:
			self.addRoiToTable(roi)

	def plotModel(self, theModel):
		self.mplWidgetRed.plotModel(theModel['1'], 'red')
		self.mplWidgetGreen.plotModel(theModel['2'], 'green')
		self.mplWidgetBlue.plotModel(theModel['3'], 'blue')

	def recordRubberBand(self, theRect, fromScenePoint, toSceenPoint):
		if theRect.width() == 0 and theRect.height() == 0:
			newRoi = QtCore.QRectF(self.currentRoi)
			newRoi.setTopLeft(self.graphicsView.mapToScene(self.currentRoi.topLeft()))
			newRoi.setBottomRight(self.graphicsView.mapToScene(self.currentRoi.bottomRight()))
			
			qImage = self.pixmap.copy(newRoi.toRect()).toImage()
			pixels = []
			for y in range(qImage.height()):
				for x in range(qImage.width()):
					pixel = QtGui.QColor(qImage.pixel(x, y))
					pixels.append([pixel.red(), pixel.green(), pixel.blue()])
			means = np.mean(pixels, axis=0).tolist()

			currentRow = self.tableWidget.currentRow()
			if currentRow != -1:
				self.roiRects[self.tableWidget.currentRow()] = newRoi
				roi = self.rois[self.tableWidget.currentRow()]
				roi[2] = []
				roi[2].append(newRoi.topLeft().x())
				roi[2].append(newRoi.topLeft().y())
				roi[2].append(newRoi.width())
				roi[2].append(newRoi.height())
				roi[3] = means
				self.displayRoi(self.tableWidget.currentRow())
				self.tableWidget.blockSignals(True)
				self.tableWidget.item(currentRow, 4).setText(str.format('{0:.2f}', roi[3][0])+', '+str.format('{0:.2f}', roi[3][1])+', '+str.format('{0:.2f}', roi[3][2]))
				self.tableWidget.blockSignals(False)
				self.calibrator.setRois(self.rois)
		else:
			self.currentRoi = theRect

	def saveRois(self):
		self.calibrator.save()

	@QtCore.pyqtSlot(QtGui.QPixmap, str)
	def setPixmap(self, thePixmap):
		if thePixmap != None:
			self.scene.clear()
			self.pixmap = thePixmap
			self.scene.addPixmap(thePixmap)
			self.setWindowTitle(self.baseWindowTitle + " [ " + os.path.basename(self.calibrator.fileName) + " ]")

			#set the other gui components
			self.dsboxGamma.setValue(self.calibrator.gamma)
			if self.calibrator.gamma != 0.0:
				self.cboxGammaCorrection.setCheckState(QtCore.Qt.Checked)
			else:
				self.cboxGammaCorrection.setCheckState(QtCore.Qt.Unchecked)
			if self.calibrator.subtractionPercent != 0:
				self.cboxSourceBand.blockSignals(True)
				self.cboxFromBand.blockSignals(True)
				self.cboxSubtraction.setCheckState(QtCore.Qt.Checked)
				self.cboxSourceBand.setCurrentIndex(self.calibrator.subtractionSourceBand - 1)
				self.cboxFromBand.setCurrentIndex(self.calibrator.subtractionFromBand - 1)
			else:
				self.cboxSubtraction.setCheckState(QtCore.Qt.Unchecked)

	def subtractionParametersChanged(self):
		self.calibrator.setSubtractionParameters(self.sboxPercent.value(), self.cboxSourceBand.currentIndex()+1, self.cboxFromBand.currentIndex()+1)

	def toggleGamma(self, theState):
		if theState == QtCore.Qt.Checked:
			self.dsboxGamma.setValue(2.2)
			self.dsboxGamma.setEnabled(True)
		else:
			self.dsboxGamma.setValue(0.0)
			self.dsboxGamma.setEnabled(False)

	def toggleSubtraction(self, theState):
		if theState == QtCore.Qt.Checked:
			self.sboxPercent.setEnabled(True)
			self.cboxSourceBand.setEnabled(True)
			self.cboxFromBand.setEnabled(True)
		else:
			self.sboxPercent.setValue(0)
			self.sboxPercent.setEnabled(False)
			self.cboxSourceBand.setEnabled(False)
			self.cboxFromBand.setEnabled(False)

	def zoomIn(self):
		self.graphicsView.scale(2,2)

	def zoomOut(self):
		self.graphicsView.scale(0.5,0.5)


