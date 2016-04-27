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
import sys

from PyQt5.QtWidgets import QApplication

import pmt
import gui

if __name__ == '__main__':
	app = QApplication(sys.argv)

	rc = gui.RadiometricCalibratorQt()
	rcd = gui.RadiometricCalibrationDialog(rc)

	cip = gui.CalibrationIndiciesProcessorQt(rc)
	cid = gui.CalibrationIndiciesDialog(cip)
	cid.show()
	rcd.show()

	sys.exit(app.exec_())