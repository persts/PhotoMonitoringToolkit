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
import sys, os, math
import numpy as np
import pyexiv2, json
from PIL import Image
from scipy.stats import linregress as LinearRegression

class RadiometricCalibrator():
#Individual ROI entry format: [Label, [Calibration R,G,B], [ROI X, Y, width, height], [ROI Means R,G,B]]
	def __init__(self):
		self.rois = []
		self.fileName = ''
		self.image = None
		self.model = None
		self.gamma = 2.2
		self.minPixelValue = 0 
		self.maxPixelValue = 255
		self.subtractionPercent = 0
		self.subtractionSourceBand = 3
		self.subtractionFromBand = 1

	def calibrate(self, theImage):
		if self.model == None:
			return theImage
		image = self.preprocessPixels(theImage)
		bands = np.split(image, 3, axis=2)
		bands[0] = (self.model['1']['slope'] * bands[0]) + self.model['1']['intercept']
		bands[1] = (self.model['2']['slope'] * bands[1]) + self.model['2']['intercept']
		bands[2] = (self.model['3']['slope'] * bands[2]) + self.model['3']['intercept']
		image = np.dstack(bands)
		image[ image < 0] = 0.0
		image[ image > 1.0] = 1.0
		return image

	def generateModel(self):
		#TODO: Make model dynamic in size for > 3 bands -- based on bands or mode?
		if len(self.rois) > 1:
			self.model = {'1': {'data': {'x': [], 'y': []}, 'slope': 0, 'intercept': 0, 'r-value': 0}, '2': {'data': {'x': [], 'y': []}, 'slope': 0, 'intercept': 0, 'r-value': 0}, '3': {'data': {'x': [], 'y': []}, 'slope': 0, 'intercept': 0, 'r-value': 0}}
			for roi in self.rois:
				#If the width is not 0 we have means for the roi, so process
				if roi[2][2] != 0:
					array = np.reshape(np.array(roi[3]), (1,1,3))
					stack = self.preprocessPixels(array)
					self.model['1']['data']['x'].append(stack[0,0,0]) #X: pixel mean
					self.model['1']['data']['y'].append(roi[1][0]) #Y: calibration
					self.model['2']['data']['x'].append(stack[0,0,1])
					self.model['2']['data']['y'].append(roi[1][1])
					self.model['3']['data']['x'].append(stack[0,0,2])
					self.model['3']['data']['y'].append(roi[1][2])
			if len(self.model['1']['data']['x']) > 1:
				self.model['1']['slope'], self.model['1']['intercept'], self.model['1']['r-value'], _, _ = LinearRegression(self.model['1']['data']['x'], self.model['1']['data']['y'])
				self.model['2']['slope'], self.model['2']['intercept'], self.model['2']['r-value'], _, _ = LinearRegression(self.model['2']['data']['x'], self.model['2']['data']['y'])
				self.model['3']['slope'], self.model['3']['intercept'], self.model['3']['r-value'], _, _ = LinearRegression(self.model['3']['data']['x'], self.model['3']['data']['y'])
				return True
		return False

	def loadCalibrationData(self):
		#Reset defaults
		self.rois = []
		self.gamma = 2.2
		self.subtractionPercent = 0
		self.subtractionSourceBand = 3
		self.subtractionFromBand = 1
		#Read EXIF data
		inExif = pyexiv2.metadata.ImageMetadata(self.fileName)
		inExif.read()
		#Extract user comment field
		exifField = inExif['Exif.Photo.UserComment'].value
		if 'ROI' in exifField:
			calibration = json.loads(exifField)
			self.rois = calibration['ROI']
			self.gamma = calibration['GAMMA']
			self.subtractionPercent = calibration['SUBTRACTION'][0]
			self.subtractionSourceBand = calibration['SUBTRACTION'][1]
			self.subtractionFromBand = calibration['SUBTRACTION'][2]
			self.generateModel()
			
	def loadImage(self, theImage):
		self.rois = []
		try:
			self.image = Image.open(theImage)
		except IOError:
			self.image = None
			return False
		maxValue = -1
		#Get max pixel value
		for minMax in self.image.getextrema():
			maxValue = max(maxValue, minMax[1])
		if maxValue < 255:
			self.maxValue = 255
		else:
			self.maxValue = 65,535
		self.fileName = theImage
		self.loadCalibrationData()
		return True

	def preprocessPixels(self, theImage):
		image = (1.0/(self.maxPixelValue - self.minPixelValue)) * (theImage - self.minPixelValue)
		if self.gamma != 0.0:
			image = np.power(image, 1.0/self.gamma)
		if self.subtractionPercent != 0:
			bands = np.split(image, 3, axis=2)
			bands[self.subtractionFromBand-1] = bands[self.subtractionFromBand-1] - (bands[self.subtractionSourceBand-1] * (self.subtractionPercent/100))
			image = np.dstack(bands)
			image[ image < 0] = 0.0
		return image

	def save(self):
		#Make new calibration record to save in EXIF data
		exifData = {'ROI': self.rois, 'GAMMA': self.gamma, 'SUBTRACTION': [self.subtractionPercent, self.subtractionSourceBand, self.subtractionFromBand]}
		fileName = self.fileName
		#Load original EXIF data
		inExif = pyexiv2.metadata.ImageMetadata(fileName)
		inExif.read()
		#Update User Comment with calibration data
		inExif['Exif.Photo.UserComment'] = pyexiv2.ExifTag('Exif.Photo.UserComment', json.dumps(exifData))
		if not '-calibration.' in fileName:
			#Update filename since first time save
			path, baseName = os.path.split(self.fileName)
			baseName = baseName.split('.')[0] + '-calibration.jpg'
			fileName = os.path.join(path, baseName)
			#TODO: Check the self.maxValue to determine 8 or 16-bit then pick format
			self.image.save(fileName, 'jpeg', quality=95)
			#Transfer EXIF data to new file and reload
			outExif = pyexiv2.metadata.ImageMetadata(fileName)
			outExif.read()
			inExif.copy(outExif, comment=False)
			outExif.write()
			self.loadImage(fileName)
		else:
			#Save EXIF data and generate model
			inExif.write()
			self.generateModel()

	def setGamma(self, theValue):
		self.gamma = theValue
		self.generateModel()
		
	def setRois(self, theRois):
		self.rois = theRois
		self.generateModel()

	def setSubtractionParameters(self, thePercent, theSourceBand, theFromBand):
		self.subtractionPercent = thePercent
		self.subtractionSourceBand = theSourceBand
		self.subtractionFromBand = theFromBand
		self.generateModel()