# -*- coding: utf-8 -*-
"""
/***************************************************************************
 IDESCaliWebServices
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, pyqtSignal, QEvent, Qt
from qgis.PyQt.QtGui import QIcon, QTextCursor
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QTableWidgetItem, QHeaderView, QAbstractItemView, QProgressBar, QProgressDialog, QCheckBox, QWidget, QHBoxLayout, QComboBox
from qgis._core import Qgis, QgsRasterLayer, QgsProject,QgsMessageLog
from .info_dialog import InfoDialog
from .com.map.ServiceUrlMap import service_url_map
from .com.enum.Service import Service
from .com.enum.ServiceType import ServiceType
from .com.map.ServiceTextMap import service_text_map
from .com.map.ServiceTypeMap import service_type_map
from .resources import *
from .idescaliws_dialog import IDESCaliWebServicesDialog
import os.path
from owslib.wms import WebMapService
from owslib.wmts import WebMapTileService
from collections import OrderedDict


class IDESCaliWebServices:

    def __init__(self, iFace):
        self.iFace = iFace
        self.plugin_dir = os.path.dirname(__file__)
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'IDESCaliWebServices_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.dlg = IDESCaliWebServicesDialog()
        self.dlginfo = InfoDialog()
        self.generatedService = None
        self.bar = QProgressBar()
        self.bar.setRange(0, 0)
        self.bar.setGeometry(950, 500, 200, 25)
        self.actions = []
        self.menu = self.tr(u'&Servicios WMS - Geoportal IDESC')
        self.first_start = None
        self.all_contents = OrderedDict()  # Almacenar todas las capas sin filtrar
        self.selected_layers = set()  # Almacenar las capas seleccionadas (por nombre)

    def tr(self, message):
        return QCoreApplication.translate('IDESCaliWebServices', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iFace.addToolBarIcon(action)

        if add_to_menu:
            self.iFace.addPluginToWebMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        self.add_all_action()
        self.dlg.table_widget.itemSelectionChanged.connect(self.updateDesc)
        self.dlg.help_button.clicked.connect(self.openDlgInfo)
        self.dlg.close_button.clicked.connect(self.closeDlg)
        self.dlg.search_box.textEdited.connect(self.search)
        self.dlg.workspace_combo.currentTextChanged.connect(self.filterByWorkspace)
        self.dlg.add_button.released.connect(self.loadWebService)
        self.dlg.clear_button.released.connect(self.clearSelectedLayers)
        self.dlginfo.ok_dialog.released.connect(self.closeAbout)
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iFace.removePluginWebMenu(
                self.tr(u'&Servicios WMS - Geoportal IDESC'),
                action)
            self.iFace.removeToolBarIcon(action)

    def run(self):
        if self.generatedService.web_map_service is not None:
            self.dlg.search_box.clear()
            self.dlg.workspace_combo.setCurrentIndex(0)  # Resetear a "Todos"
            self.fill_table(self.generatedService.web_map_service.contents)
            self.dlg.show()
            result = self.dlg.exec_()
            if result:
                pass

    def run_0(self):
        self.loadServiceList(Service.IDESCaliDataset.value)
        self.run()

    def add_all_action(self):
        icon_path = ':/plugins/idescali_ws/icon.png'

        self.add_action(icon_path,
                        text=self.tr(service_text_map[Service.IDESCaliDataset.value]),
                        callback=self.run_0,
                        whats_this=str(Service.IDESCaliDataset.value),
                        parent=self.iFace.mainWindow())

    def loadServiceList(self, service_id: int):
        self.generatedService = WebMapServiceClass(service_id)
        url = self.generatedService.service_url
        self.bar.show()
        if self.generatedService.service_type == ServiceType.WebMapService.value:
            try:
                wms = WebMapService(url)
                self.generatedService.setWebMapService(wms)
            except Exception as e:
                QMessageBox.information(None, "ERROR:", 'No se puede cargar este servicio en este momento.' + str(e))
        elif self.generatedService.service_type == ServiceType.WebMapTileService.value:
            try:
                wmts = WebMapTileService(url)
                self.generatedService.setWebMapService(wmts)
            except Exception as e:
                QMessageBox.information(None, "ERROR:", 'No se puede acceder a este servicio en este momento.' + str(e))
        self.bar.close()

    def openDlgInfo(self):
        self.dlginfo.show()

    def closeDlg(self):
        self.generatedService = None
        self.dlg.search_box.clear()
        self.dlg.table_widget.setRowCount(0)
        self.dlg.table_widget.setColumnCount(0)
        self.dlg.layer_name_box.clear()
        self.selected_layers.clear()  # Limpiar selecciones al cerrar
        self.dlg.close()
        if self.dlginfo:
            self.dlginfo.close()
	
    def closeAbout(self):
        if self.dlginfo:
            self.dlginfo.close()

    def extract_workspace(self, layer_name):
        """Extrae el espacio de trabajo del nombre de la capa (formato: espaciotrabajo:nombre capa)"""
        if ':' in layer_name:
            return layer_name.split(':')[0]
        return ""

    def get_unique_workspaces(self, contentOrderedDict):
        """Obtiene los espacios de trabajo únicos de las capas"""
        workspaces = set()
        for content in contentOrderedDict:
            name = contentOrderedDict[content].name
            workspace = self.extract_workspace(name)
            if workspace:
                workspaces.add(workspace)
        return sorted(list(workspaces))

    def fill_table(self, contentOrderedDict):
        # Guardar todas las capas para filtrado
        self.all_contents = contentOrderedDict
        
        # Extraer y poblar espacios de trabajo únicos
        workspaces = self.get_unique_workspaces(contentOrderedDict)
        self.dlg.workspace_combo.blockSignals(True)  # Bloquear señales para evitar filtrado durante la carga
        self.dlg.workspace_combo.clear()
        self.dlg.workspace_combo.addItem("Todos")  # Opción para mostrar todos
        for workspace in workspaces:
            self.dlg.workspace_combo.addItem(workspace)
        self.dlg.workspace_combo.blockSignals(False)
        
        # Llenar la tabla
        self.dlg.table_widget.setRowCount(0)
        count = self.dlg.table_widget.rowCount()
        self.dlg.table_widget.setColumnCount(5)

        for content in contentOrderedDict:
            index = count
            name = contentOrderedDict[content].name
            title = contentOrderedDict[content].title
            abstract = contentOrderedDict[content].abstract
            self.dlg.table_widget.insertRow(index)
            
            # Columna 0: Checkbox
            checkbox = QCheckBox()
            # Restaurar el estado del checkbox si la capa estaba seleccionada
            if name in self.selected_layers:
                checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.updateSelectedLayers)
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.dlg.table_widget.setCellWidget(index, 0, checkbox_widget)
            
            # Columna 1: ID (oculta)
            self.dlg.table_widget.setItem(index, 1, QTableWidgetItem(str(content)))
            # Columna 2: Capa
            self.dlg.table_widget.setItem(index, 2, QTableWidgetItem(str(name)))
            # Columna 3: Nombre
            self.dlg.table_widget.setItem(index, 3, QTableWidgetItem(str(title)))
            # Columna 4: Resumen
            self.dlg.table_widget.setItem(index, 4, QTableWidgetItem(str(abstract)))

        self.dlg.table_widget.setHorizontalHeaderLabels(["", "ID", "Capa", "Nombre", "Resumen"])
        self.dlg.label_conteo.setText("Capas disponibles: "+str(len(contentOrderedDict)))
        self.setTableWidgetBehaviour()
        
        # Actualizar la lista de capas seleccionadas después de restaurar
        self.updateSelectedLayers()

    def setTableWidgetBehaviour(self):
        self.dlg.table_widget.setColumnWidth(0, 50)
        self.dlg.table_widget.setColumnWidth(1, 0)
        self.dlg.table_widget.setColumnWidth(2, 180)
        self.dlg.table_widget.setColumnWidth(3, 180)
        self.dlg.table_widget.setColumnWidth(4, 180)
        self.dlg.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.dlg.table_widget.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

        self.dlg.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.dlg.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dlg.table_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def filterByWorkspace(self):
        """Filtra las capas por espacio de trabajo seleccionado"""
        self.applyFilters()

    def applyFilters(self):
        """Aplica los filtros de espacio de trabajo y búsqueda por nombre"""
        # Actualizar las selecciones actuales antes de filtrar (sin borrar las que no están visibles)
        self._updateSelectedLayersFromTable()
        
        if not hasattr(self, 'all_contents') or not self.all_contents:
            # Si no hay contenido guardado, usar el contenido original
            if self.generatedService and self.generatedService.web_map_service:
                contents = self.generatedService.web_map_service.contents
            else:
                return
        else:
            contents = self.all_contents
        
        # Obtener filtros
        selected_workspace = self.dlg.workspace_combo.currentText()
        search_criteria = self.dlg.search_box.text().lower()
        
        wms_filtered_contents = OrderedDict()
        for content in contents:
            name = contents[content].name
            workspace = self.extract_workspace(name)
            
            # Filtrar por espacio de trabajo
            workspace_match = (selected_workspace == "Todos" or workspace == selected_workspace)
            
            # Filtrar por búsqueda de nombre
            name_match = (not search_criteria or search_criteria in name.lower())
            
            if workspace_match and name_match:
                wms_filtered_contents[content] = contents[content]
        
        # Actualizar tabla sin repoblar el ComboBox
        self.dlg.table_widget.setRowCount(0)
        count = 0
        self.dlg.table_widget.setColumnCount(5)

        for content in wms_filtered_contents:
            index = count
            name = wms_filtered_contents[content].name
            title = wms_filtered_contents[content].title
            abstract = wms_filtered_contents[content].abstract
            self.dlg.table_widget.insertRow(index)
            
            # Columna 0: Checkbox
            checkbox = QCheckBox()
            # Restaurar el estado del checkbox si la capa estaba seleccionada
            if name in self.selected_layers:
                checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.updateSelectedLayers)
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.dlg.table_widget.setCellWidget(index, 0, checkbox_widget)
            
            # Columna 1: ID (oculta)
            self.dlg.table_widget.setItem(index, 1, QTableWidgetItem(str(content)))
            # Columna 2: Capa
            self.dlg.table_widget.setItem(index, 2, QTableWidgetItem(str(name)))
            # Columna 3: Nombre
            self.dlg.table_widget.setItem(index, 3, QTableWidgetItem(str(title)))
            # Columna 4: Resumen
            self.dlg.table_widget.setItem(index, 4, QTableWidgetItem(str(abstract)))
            
            count += 1

        self.dlg.table_widget.setHorizontalHeaderLabels(["", "ID", "Capa", "Nombre", "Resumen"])
        self.dlg.label_conteo.setText("Capas disponibles: "+str(len(wms_filtered_contents)))
        self.setTableWidgetBehaviour()
        
        # Actualizar la lista de capas seleccionadas después de restaurar
        self.updateSelectedLayers()

    def search(self):
        """Filtra las capas por nombre"""
        self.applyFilters()

    def getSelectedItemsFromTable(self):
        # Usar self.selected_layers que contiene todas las capas seleccionadas,
        # incluso las que no están visibles en el filtro actual
        rowNames = list(self.selected_layers)

        selectedServices = OrderedDict()
        contents = self.generatedService.web_map_service.contents
        for rowName in rowNames:
            for content in contents:
                name_itr = contents[content].name
                if name_itr == rowName:
                    selectedServices[content] = contents[content]

        return selectedServices

    def updateDesc(self):
        try:
            selectedServices = self.getSelectedItemsFromTable()
            self.dlg.layer_name_box.clear()
            names = ''
            for selectedService in selectedServices:
                name_itr = selectedServices[selectedService].name
                names += name_itr + ','
            names = names[:-1]
            self.dlg.layer_name_box.setText(names)
            self.dlg.layer_name_box.setReadOnly(True)
        except:
            QgsMessageLog.logMessage("No selecciono ninguna capa WMS para cargar")

    def _updateSelectedLayersFromTable(self):
        """Actualiza las selecciones basándose en la tabla actual, preservando las que no están visibles"""
        # Obtener las capas visibles actualmente
        visible_layers = set()
        for row in range(self.dlg.table_widget.rowCount()):
            checkbox_widget = self.dlg.table_widget.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    name = self.dlg.table_widget.item(row, 2).text()
                    visible_layers.add(name)
                    if checkbox.isChecked():
                        self.selected_layers.add(name)
                    else:
                        # Solo remover si está visible y desmarcada
                        self.selected_layers.discard(name)
        
        # Mantener las capas seleccionadas que no están visibles (no las removemos)
    
    def updateSelectedLayers(self):
        """Actualiza la lista de capas seleccionadas cuando cambia el estado de un checkbox"""
        try:
            # Actualizar solo las capas visibles en la tabla, preservando las que no están visibles
            for row in range(self.dlg.table_widget.rowCount()):
                checkbox_widget = self.dlg.table_widget.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox:
                        name = self.dlg.table_widget.item(row, 2).text()
                        if checkbox.isChecked():
                            self.selected_layers.add(name)
                        else:
                            # Solo remover si está visible y desmarcada
                            self.selected_layers.discard(name)
            
            selectedServices = self.getSelectedItemsFromTable()
            self.dlg.layer_name_box.clear()
            if len(selectedServices) > 0:
                names = ''
                for selectedService in selectedServices:
                    name_itr = selectedServices[selectedService].name
                    names += name_itr + ','
                names = names[:-1]
                self.dlg.layer_name_box.setText(names)
            else:
                self.dlg.layer_name_box.clear()
            self.dlg.layer_name_box.setReadOnly(True)
        except Exception as e:
            QgsMessageLog.logMessage("Error al actualizar capas seleccionadas: " + str(e))

    def clearSelectedLayers(self):
        """Limpia todas las capas seleccionadas"""
        # Limpiar el conjunto de capas seleccionadas
        self.selected_layers.clear()
        
        # Desmarcar todos los checkboxes visibles en la tabla
        for row in range(self.dlg.table_widget.rowCount()):
            checkbox_widget = self.dlg.table_widget.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(False)
        
        # Limpiar el cuadro de texto
        self.dlg.layer_name_box.clear()

    def loadWebService(self):
        # get selected items and add to the map
        self.bar.show()
        EPSG_CODE_4326 = 'EPSG:4326'
        selectedServices = self.getSelectedItemsFromTable()
        web_map_service = self.generatedService.web_map_service
        for selectedService in selectedServices:
            if self.generatedService.service_url is not None:
                layer_name = selectedServices[selectedService].name
                url = 'contextualWMSLegend=0'
                if hasattr(web_map_service[layer_name], 'crsOptions'):
                    if len(web_map_service[layer_name].crsOptions) > 0:
                        if EPSG_CODE_4326 in web_map_service[layer_name].crsOptions:
                            url += '&crs=' + EPSG_CODE_4326
                            if self.generatedService.service_type == ServiceType.WebMapTileService.value:
                                    url += '&tileMatrixSet=' + EPSG_CODE_4326
                        else:
                            url += '&crs=' + web_map_service[layer_name].crsOptions[0]
                            if self.generatedService.service_type == ServiceType.WebMapTileService.value:
                                    url += '&tileMatrixSet=' + web_map_service[layer_name].crsOptions[0]
                else:
                    url += '&crs=' + EPSG_CODE_4326
                    if self.generatedService.service_type == ServiceType.WebMapTileService.value:
                        url += '&tileMatrixSet=' + EPSG_CODE_4326
                url += '&dpiMode=7&featureCount=10&format=image/png&styles' + \
                       '&layers=' + layer_name + \
                       '&url=' + str(self.generatedService.service_url)
                rlayer = QgsRasterLayer(url, selectedServices[selectedService].title, 'wms')
                if not rlayer.isValid():
                    QMessageBox.information(None, "ERROR:", 'Imposible cargar las capas ' +
                                            selectedServices[selectedService].title +
                                            ' en este momento.')
                else:
                    QgsProject.instance().addMapLayer(rlayer)
                    self.iFace.messageBar().pushMessage("Mensaje:", "Fueron cargadas las capas WMS con exito", level=Qgis.Success, duration=3)
            else:
                QMessageBox.information(None, "ERROR:", 'No selecciono ninguna capa WMS para cargar')
        self.bar.close()


class WebMapServiceClass:
    def __init__(self, service_id):
        self.service_id = service_id
        self.service_type = service_type_map[service_id]
        self.service_text = service_text_map[service_id]
        self.service_url = service_url_map[service_id]
        self.web_map_service = None

    def setWebMapService(self, map_service):
        self.web_map_service = map_service
