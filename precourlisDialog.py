from PyQt4 import QtCore, QtGui 
from Ui_precourlis import Ui_precourlis
# create the dialog for precourlis
class precourlisDialog(QtGui.QDialog):
  def __init__(self,iface): 
    QtGui.QDialog.__init__(self,None, QtCore.Qt.WindowStaysOnTopHint) 
    # Set up the user interface from Designer. 
    self.ui = Ui_precourlis ()
    self.ui.setupUi(self,iface)
    