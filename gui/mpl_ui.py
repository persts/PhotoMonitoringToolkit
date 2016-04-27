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
from PyQt5 import QtWidgets
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MplCanvas(FigureCanvas):
	#Taken from http://matplotlib.org/devdocs/examples/user_interfaces/embedding_in_qt5.html
	def __init__(self, parent=None, width=4, height=4, dpi=60):
		fig = Figure(figsize=(width, height), dpi=dpi)
		self.plot = fig.add_subplot(111)
		# We want the axes cleared every time plot() is called
		self.plot.hold(False)

		self.compute_initial_figure()

		FigureCanvas.__init__(self, fig)
		self.setParent(parent)

		FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		FigureCanvas.updateGeometry(self)

	def compute_initial_figure(self):
		pass

class MplLinearRegressionCanvas(MplCanvas):
	def plotModel(self, theModelBand, theColor):
		y = []
		for x in theModelBand['data']['x']:
			y.append((theModelBand['slope']*x) + theModelBand['intercept'])
		self.plot.plot(theModelBand['data']['x'], theModelBand['data']['y'], 'gs', theModelBand['data']['x'], y, color=theColor, linewidth=2)
		self.plot.set_title('R-value: '+str(theModelBand['r-value']))
		self.plot.locator_params(nbins=5)
		self.plot.set_xlim(xmin=0)
		self.plot.set_ylim(ymin=0)
		self.draw()


class MplLinearRegressionWidget(QtWidgets.QWidget):
	def __init__(self, parent=None):
		QtWidgets.QWidget.__init__(self, parent)

		layout = QtWidgets.QVBoxLayout(self)
		self.canvas = MplLinearRegressionCanvas()
		layout.addWidget(self.canvas)

	def plotModel(self, theModel, theColor):
		self.canvas.plotModel(theModel, theColor)
