# -*- coding: utf-8 -*-

import os
from qgis.PyQt import QtGui, uic
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QDialog
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'info_dialog_base.ui'))

class InfoDialog(QDialog, FORM_CLASS):

    closingPlugin = pyqtSignal()
    
    def __init__(self, parent=None):
        """Constructor."""
        super(InfoDialog, self).__init__(parent)
        self.setupUi(self)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
