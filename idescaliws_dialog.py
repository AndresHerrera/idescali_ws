# -*- coding: utf-8 -*-
"""
/***************************************************************************
 IDESCaliWebServicesDialog
 Este plugin provee acceso a los servicios WMS de la Infraestructura de Datos Espaciales de Santiago de Cali (IDESC)
 Code based in Bhuvan ISRO's Geoportal QGIS plugin: https://github.com/brenykurien/bhuvan_web_services
        -------------------
        begin                : 2020-01-10
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Andres Herrera
        email                : fandresherrera@hotmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'idescaliws_dialog_base.ui'))


class IDESCaliWebServicesDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(IDESCaliWebServicesDialog, self).__init__(parent)
        self.setupUi(self)
