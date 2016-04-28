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
import glob, re, os
import numpy as np
import pyexiv2
from skimage import io
from skimage.external.tifffile import TiffWriter

class CalibrationIndiciesProcessor():
	def __init__(self, theCalibrator=None):
		self.radiometricCalibrator = theCalibrator
		self.scaleFrom = 0
		self.scaleTo = 255
		self.fileExtension = 'JPG'
		self.radiometricCalibration = False
		self.index = 'None'
		self.lut = 'None'
		self.redBand = 1
		self.nirBand = 3
		self.currentMin = 0
		self.currentMax = 255
	
	def indexNdvi(self, theImage):
		#Put each band into its own array
		bands = np.split(theImage, 3, axis=2)
		image = (bands[self.nirBand - 1] - bands[self.redBand - 1]) / (bands[self.nirBand - 1] + bands[self.redBand - 1])
		self.currentMin = -1.0
		self.currentMax = 1.0
		return image

	def log(self, theMessage, **kwargs):
		pass

	def process(self, theSourceDir, theDestinationDir, **kwargs):
		for key, value in kwargs.items():
			setattr(self, key, value)

		if theSourceDir == theDestinationDir:
			self.log("Input and output directories cannot be the same.")
			return False
		fileList = glob.glob(theSourceDir+'/*.'+self.fileExtension)
		if len(fileList) == 0:
			self.log(" Zero files to process in source directory.")
			return False

		fileList = glob.glob(theSourceDir+'/*.'+self.fileExtension)
		self.log('Processing %i images' % len(fileList))
		progress = 0
		for file in fileList:
			#Load image
			data = io.imread(file).astype('float')
			self.currentMax = 0

			#Load original EXIF data
			inExif = pyexiv2.metadata.ImageMetadata(file)
			inExif.read()
			
			#Radiometric Calibration
			if self.radiometricCalibrator != None and self.radiometricCalibration:
				data = self.radiometricCalibrator.calibrate(data)
				self.currentMax = 1

			#compute index
			if self.index == 'NDVI':
				data = self.indexNdvi(data)

			#Scale
			if self.currentMax != 0:
				percentOfRange = (data - self.currentMin) / (self.currentMax - self.currentMin)
				data = (self.scaleFrom * (1 - percentOfRange)) + (self.scaleTo * percentOfRange)
			
			#Set dtype
			if self.scaleTo == 1:
				if data.dtype.name != 'float32':
					data = data.astype('float32')
			elif self.scaleTo > 255:
				#unsigned int (I:16)
				data = data.astype('uint16')
			elif self.index != 'None':
				if self.lut == 'None':
					#bit image (L)
					data = data.astype('uint8')
					pass
				else:
					#Paletted
					pass
			else:
				#RGB (RGB)
				data = data.astype('uint8')

			#Save processed data to new file
			path, baseName = os.path.split(file)
			baseName = re.sub(r''+re.escape(self.fileExtension)+'$', 'tiff', baseName)
			if self.index != 'None':
				baseName = self.index+'-'+baseName
			tif = TiffWriter(theDestinationDir+'/'+baseName)
			tif.save(data, compress=6)
			tif = None
			
			#Transfer EXIF data to new file
			outExif = pyexiv2.metadata.ImageMetadata(theDestinationDir+'/'+baseName)
			outExif.read()
			#inExif.copy(outExif, comment=False)
			#outExif.write()

			#Log and progress
			progress += 1
			self.log('%s created' % (baseName), progress=progress)