# -*- coding: utf-8 -*-
'''
Created on 14 janv. 2015

@author: quarre
'''
import os
from qgis.core import *
from functools import partial
from PyQt4.QtCore import QVariant
from PyQt4 import QtCore, QtGui 


from types import MethodType
from PyQt4.QtCore import QPyNullVariant

from PyQt4.Qt import QGridLayout
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from PyQt4.QtGui import QPushButton,QTableView,QTabWidget,QMessageBox,QComboBox,QGroupBox,QInputDialog,QCheckBox,QLineEdit,QLabel,QColorDialog,QColor,QButtonGroup,QRadioButton
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import math
from PyQt4.QtCore import QAbstractTableModel,Qt,QModelIndex
from preCourlisGeoRefWriter import preCourlisGeoRefWriter
from matplotlib.pyplot import Rectangle
import matplotlib.patches as patches
from preCourlisTools import preCourlisTools , Point, Polyligne
from math import isnan
from preCourlisLayersChooser import preCourlisLayersChooser 
from preCourlisCoucheSediGeoRefImport import preCourlisCoucheSediGeoRefImport


class preCourlisProfilEditor(QtGui.QFrame):
    
    def __init__(self,iface):
        QtGui.QFrame.__init__(self)
        self.iface = iface
        #self.listBiefs = listbiefs
        #self.bief_courant = bief
        self.tools = preCourlisTools()
        list_layer = [['Profils','layer_profils']]
        
        layChooser = preCourlisLayersChooser(list_layer)
        tab_ret = {}
        
        if layChooser.exec_():
            tab_ret = layChooser.tab_ret 
                 
            self.couche_choisi = self.tools.getLayerByName(tab_ret["Profils"])
            #self.axe = self.tools.getLayerByName(tab_ret['Axe'])              
        
        else:
            return
        
        #self.trace_axe = trace_axe
        
        self.setWindowTitle("Editeur de profils - Couche '"+tab_ret["Profils"]+"'")
        self.figure = plt.figure(figsize=(15, 7))
        self.canvas = FigureCanvas(self.figure) 
        #self.graph = plt.subplot(111,projection='3d') 
        self.graph = plt.subplot(111)
        #self.graph2 = plt.subplot(122,projection='3d') 
        self.x_valeur_min = 0;
        self.x_valeur_max = 0;
        
        self.y_valeur_min = 0;
        self.y_valeur_max = 0;
        
        self.x_valeur_zoom_min = 0;
        self.x_valeur_zoom_max = 0;
        
        self.y_valeur_zoom_min = 0;
        self.y_valeur_zoom_max = 0;
        
        self.gridL = QGridLayout()        
        self.gridL.addWidget(self.canvas, 1,6,8, 16)
        
        self.combo_profil = QComboBox()
        
        self.showverts = True
        self._ind = None
        self.epsilon = 5
        self.tabs = QTabWidget()
        
        self.coucheActiveEditable ="Fond"
        self.coucheActiveEditableIndex = 0
        
        
        self.all_tabs = []
        
        self.gridL.addWidget(self.combo_profil,1,1,1,5)
        self.gridL.addWidget(self.tabs,2,1,7,5)
        self.setLayout(self.gridL)
        self.nombreProfil = 0
        
        #self.couche_choisi = self.iface.mapCanvas().currentLayer()
        self.profils_ordonne = {}
        
        self.initDataProfilInBief()
        
        self.btn_export = QPushButton("Exporter")
        
        #Gestion des couches sedimentaires *************** 
        self.ajout_couche_sedi = QPushButton("Ajout")
        self.supp_couche_sedi = QPushButton("Supprimer")
        self.import_couche_sedi = QPushButton("Import .geo")
        
        
        self.combo_couche_sedi = QComboBox()
        
        
        
        
        radioGroup = QButtonGroup()
        self.btn_ponc = QRadioButton("Point par point")
        self.btn_ponc.setChecked(True)      
        self.interp_enable = QRadioButton("Interpolation")
        group_edit = QGroupBox("Edition")
        self.gridL_edit = QGridLayout()
        
        radioGroup.addButton(self.btn_ponc)
        radioGroup.addButton(self.interp_enable)
        
        self.gridL_edit.addWidget(self.combo_couche_sedi,1,1,1,2)
        self.gridL_edit.addWidget(self.btn_ponc,1,3)
        self.gridL_edit.addWidget(self.interp_enable,1,4)
        #self.edit_couche_sedi = QPushButton("Modif.")
        group_edit.setLayout(self.gridL_edit)
        #self.supp_couche_sedi = QPushButton("Supp.")
        
        self.gridL_sedi = QGridLayout()
        self.gridL_sedi.addWidget(self.ajout_couche_sedi, 1, 1, 1, 1) 
        self.gridL_sedi.addWidget(self.supp_couche_sedi, 1, 2, 1, 1)       
        self.gridL_sedi.addWidget(self.import_couche_sedi, 1, 3, 1, 1)
        
        
        #self.gridL_sedi.addWidget(self.combo_couche_sedi, 2, 1, 1, 3)
        self.gridL_sedi.addWidget(group_edit, 2, 1, 1, 4)       
        #self.gridL_sedi.addWidget(self.supp_couche_sedi, 2, 4, 1, 1)
        
        self.combo_fond_dur = QComboBox()
        #self.edit_couche_sedi.setEnabled(False)
        #self.supp_couche_sedi.setEnabled(False)
        self.updateComboSedi()
        group_sedi = QGroupBox("Couche(s) sedimentaire(s)")  
        group_sedi.setLayout(self.gridL_sedi)
        
        QtCore.QObject.connect(self.ajout_couche_sedi, QtCore.SIGNAL("clicked(bool)"), self.ajoutCoucheSedi)
        QtCore.QObject.connect(self.import_couche_sedi, QtCore.SIGNAL("clicked(bool)"), self.importCoucheSediGeoRef)
        QtCore.QObject.connect(self.supp_couche_sedi, QtCore.SIGNAL("clicked(bool)"), self.suppCoucheSedi)
        
        #***************************************************
        
        group_inter = QGroupBox("Interpolation")
        self.gridL_inter = QGridLayout()
        
        self.interp_launch = QPushButton("OK")
        self.raz_btn = QPushButton("R.A.Z")
        
        #self.interp_enable = QCheckBox("Active")
        self.pt1_len = QLineEdit()        
        self.pt1_tick = QLineEdit()
        
        self.pt2_len = QLineEdit()        
        self.pt2_tick = QLineEdit()
        
        
        
        #self.gridL_inter.addWidget(self.interp_enable,1,1,1,1)
        self.gridL_inter.addWidget(QLabel('Point 1 Abs. Curv. :'),1,1,1,1)
        self.gridL_inter.addWidget(self.pt1_len,1,2,1,1)
        self.gridL_inter.addWidget(QLabel('Delta Z :'),1,3,1,1)
        self.gridL_inter.addWidget(self.pt1_tick,1,4,1,1)
        
        self.gridL_inter.addWidget(QLabel('Point 2 Abs. Curv. :'),2,1,1,1)
        self.gridL_inter.addWidget(self.pt2_len,2,2,1,1)
        self.gridL_inter.addWidget(QLabel('Delta Z :'),2,3,1,1)
        self.gridL_inter.addWidget(self.pt2_tick,2,4,1,1)
        self.gridL_inter.addWidget(QLabel('Couche de fond dur :'),3,1,1,1)
        self.gridL_inter.addWidget(self.combo_fond_dur,3,2,1,1)
        self.gridL_inter.addWidget(self.raz_btn,1,5,1,1)
        self.gridL_inter.addWidget(self.interp_launch,2,5,1,1)
        
        self.pt1_len.setEnabled(False)
        self.pt1_tick.setEnabled(False)
        self.pt2_len.setEnabled(False)
        self.pt2_tick.setEnabled(False)
        #self.interp_launch.setEnabled(False)
        
        group_inter.setLayout(self.gridL_inter)
         
        
        QtCore.QObject.connect(self.tabs, QtCore.SIGNAL("currentChanged(int)"), self.changeTabEvent)
        QtCore.QObject.connect(self.combo_profil, QtCore.SIGNAL("currentIndexChanged(int)"), self.comboChangeEvent)
        QtCore.QObject.connect(self.combo_couche_sedi, QtCore.SIGNAL("currentIndexChanged(int)"), self.comboSediChangeEvent)
        QtCore.QObject.connect(self.btn_export, QtCore.SIGNAL("clicked(bool)"), self.export)
        QtCore.QObject.connect(self.interp_enable, QtCore.SIGNAL("toggled(bool)"), self.interpStateEvent)
        QtCore.QObject.connect(self.interp_launch, QtCore.SIGNAL("clicked(bool)"), self.launchInterpol)
        QtCore.QObject.connect(self.raz_btn, QtCore.SIGNAL("clicked(bool)"), self.raz_interp)
        
        
        
        self.gridL.addWidget(self.btn_export,9,1)
        self.gridL.addWidget(group_sedi,9,2,2,5)
        self.gridL.addWidget(group_inter,9,7,2,5)
        
        self.pointing_line = None
        self.courbe_principal = None
        self.background = None
        self.active_Zoom = True
        
        
        self.a = self.zoomRectangle(self.graph, self)
        #self.canvas.mpl_connect('draw_event', self.draw_callback)
        self.canvas.mpl_connect('pick_event', self.button_press_callback)
        
        self.canvas.mpl_connect('button_release_event', self.button_release_callback)
        self.canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)
        
        self.profil_courant = None       
        
        self.changeTabEvent()
        plt.tight_layout()
        
        
        self.show()
        
  
    
    def initDataProfilInBief(self):          
        
            
            self.couche_choisi.startEditing()
            self.couche_choisi.dataProvider().addAttributes([QgsField('abs_travers', QVariant.String)])
            #self.iface.mapCanvas().currentLayer().dataProvider().updateFields()
            self.couche_choisi.updateFields()
            features = self.couche_choisi.getFeatures()
                        
           
            #self.profils_ordonne = self.getProfilsOrdonnes()
                
            
            
        
            for f in features:
                
                #f = p_and_l[0]
                
                table_val = self.TableView()
                self.tabs.addTab(table_val,f.attribute('nom'))
                
                self.combo_profil.addItem(f.attribute('nom'))
                
                tabx = [float(x) for x in f.attribute('x').split(',')]
                taby = [float(y) for y in f.attribute('y').split(',')]
                tabz = [float(z) for z in f.attribute('z').split(',')]
                tab_len = [float(a) for a in f.attribute('abs_travers').split(',')]              
                                
                table_val.setModel(self.NumpyModel(self,self.iface,f,np.array(tab_len),np.array(tabz),self.couche_choisi,self)) 
                sel = table_val.selectionModel()
                sel.selectionChanged.connect(partial(self.rowChangeEvent,tab=table_val))
                self.all_tabs.append(table_val)
                
                self.nombreProfil = self.nombreProfil +1
                
            #self.iface.mapCanvas().currentLayer().updateFields()
            self.couche_choisi.commitChanges()
            
            
    def importCoucheSediGeoRef(self):
        """
        """
        self.imp_couche_geo = preCourlisCoucheSediGeoRefImport(self)
        
    def suppCoucheSedi(self):
        """
        suppression de couche sedimentaire
        """
        lst = []
        for f in self.couche_choisi.getFeatures():
            if(not f.attribute('liste_couche_sediment') is None and not isinstance(f.attribute('liste_couche_sediment'),QPyNullVariant) ):
                lst = [str(c) for c in f.attribute('liste_couche_sediment').split(',')]
                lst_color = [str(c) for c in f.attribute('liste_couche_sediment_couleur').split(',')]
            break
        name_couche_sedi,ok = QInputDialog.getItem(self, unicode("Suppression couche sédimentaire","utf-8"),"Couche :",lst)
        
        if(name_couche_sedi=="" or not ok):
            return
        
        self.couche_choisi.startEditing()
        #self.hide()
        
        new_list = []
        new_list_color = []
        i=0
        for c in lst:
            if(c!=name_couche_sedi):
                new_list.append(c)
                new_list_color.append(lst_color[i])
                
            i=i+1
                
        fied_index_lst = self.couche_choisi.fieldNameIndex("liste_couche_sediment")
        fied_index_lst_couleur = self.couche_choisi.fieldNameIndex("liste_couche_sediment_couleur")
        fied_index_id = self.couche_choisi.fieldNameIndex('couche_sedi_'+name_couche_sedi)
        for f in self.couche_choisi.getFeatures():
            if(len(new_list)==0):
                f[fied_index_lst] = None # Qui va se tranformer en qpynullvariant .... pffff
            else:    
                f[fied_index_lst] = ','.join([str(l) for l in new_list])
            f[fied_index_lst_couleur] = ','.join([str(l) for l in new_list_color])   
            self.couche_choisi.updateFeature(f) 
        self.graph.clear()
        
        self.couche_choisi.dataProvider().deleteAttributes([fied_index_id])
        self.couche_choisi.updateFields()
        
        self.couche_choisi.commitChanges()
        self.updateComboSedi()
        
        
        for tab in self.all_tabs: 
            tab.model().update()
            
        #self.show()
        
              
            
    def ajoutCoucheSedi(self):
        #Ajoute une couche sedimentaire
        name_couche_sedi,ok = QInputDialog.getText(self, unicode("Nouvelle couche sédimentaire","utf-8"), "Entrez un nom")
        if(name_couche_sedi=="" or not ok):
            return
        
        for f in self.couche_choisi.getFeatures():
            if(f.id()==self.profil_courant.id()):
                self.profil_courant = f 
                break;
        
        if(not self.profil_courant.attribute('liste_couche_sediment') is None and not isinstance(self.profil_courant.attribute('liste_couche_sediment'),QPyNullVariant) ):
            if(name_couche_sedi in self.profil_courant.attribute('liste_couche_sediment').split(',')):
                QMessageBox.critical(self, "Erreur", unicode("Ce nom est déjà utilisé","utf-8"), QMessageBox.Ok, QMessageBox.NoButton)
                self.ajoutCoucheSedi()
                return
        
        color = QColorDialog.getColor()
        if not color.isValid():
            return
        
        self.couche_choisi.startEditing()
        self.couche_choisi.dataProvider().addAttributes([QgsField('couche_sedi_'+name_couche_sedi, QVariant.String)])
        self.couche_choisi.updateFields()
        field = self.couche_choisi.pendingFields()
        
        
        
        #on recopie tout point Z des profils pour initialisé cette nouvelle couche
        for f in self.couche_choisi.getFeatures():
            
            fied_index_Z = -1 
            if(not f.attribute('liste_couche_sediment') is None and not isinstance(f.attribute('liste_couche_sediment'),QPyNullVariant) ):
                lst_couche_sedi = [str(c) for c in f.attribute('liste_couche_sediment').split(',')]
                lst_couche_sedi_couleur = [str(c) for c in f.attribute('liste_couche_sediment_couleur').split(',')]
                fied_index_Z = self.couche_choisi.fieldNameIndex('couche_sedi_'+lst_couche_sedi[-1]) #-1 retourne le dernier element d'une liste
            else:
                fied_index_Z = self.couche_choisi.fieldNameIndex("z")
                lst_couche_sedi = []
                lst_couche_sedi_couleur = []
            lst_couche_sedi.append(name_couche_sedi)
            lst_couche_sedi_couleur.append(color.rgb())
            
            
            
            fied_index_lst = self.couche_choisi.fieldNameIndex("liste_couche_sediment") 
            fied_index_lst_couleur = self.couche_choisi.fieldNameIndex("liste_couche_sediment_couleur")       
            fied_index_new_sedi = self.couche_choisi.fieldNameIndex('couche_sedi_'+name_couche_sedi)
            f[fied_index_new_sedi] = f[fied_index_Z]
            f[fied_index_lst] = ','.join([str(l) for l in lst_couche_sedi])
            f[fied_index_lst_couleur] = ','.join([str(l) for l in lst_couche_sedi_couleur])
            self.couche_choisi.updateFeature(f)
        
        self.couche_choisi.commitChanges()
        self.updateComboSedi()
        
        
        #Il faut maintenant recuperer les features de QGIS pour avoir la mise à jour. Du coup il faut de nouveau les reordonner
        #self.profils_ordonne = self.getProfilsOrdonnes()
        
        for tab in self.all_tabs: 
            tab.model().update()
        
    def raz_interp(self):
        #Vide les champs pour une nouvel interpolation
        
        self.pt1_len.setText('')
        self.pt1_tick.setText('')
        self.pt2_len.setText('')
        self.pt2_tick.setText('') 
        
    def updateComboSedi(self):
        
        self.combo_couche_sedi.clear()
        self.combo_fond_dur.clear()
        self.combo_couche_sedi.addItem("Fond")
        self.combo_fond_dur.addItem("Pas de fond dur")
        self.combo_fond_dur.addItem("Fond")
        for f in self.couche_choisi.getFeatures():
            if(not f.attribute('liste_couche_sediment') is None and not isinstance(f.attribute('liste_couche_sediment'),QPyNullVariant) ):
                lst_couche_sedi = [str(c) for c in f.attribute('liste_couche_sediment').split(',')]
            else:
                lst_couche_sedi = []
            for c in lst_couche_sedi:
                self.combo_couche_sedi.addItem(c)
                self.combo_fond_dur.addItem(c)
        
            break #Une seul iteration suffit
        
    def editCoucheSedit(self):
        
        self.btn_ponc.setChecked(True)
        self.coucheActiveEditable = self.combo_couche_sedi.currentText()
        self.coucheActiveEditableIndex = self.combo_couche_sedi.currentIndex()
        self.changeTabEvent()   
            
    def comboSediChangeEvent(self):
        #Appelé quand on selectionne une couche sedimentaire dans la liste deroulante
        #if(self.combo_couche_sedi.currentText()!='--Profil--'):
        #    self.edit_couche_sedi.setEnabled(True)
        #    self.supp_couche_sedi.setEnabled(True)
        
        self.coucheActiveEditable = self.combo_couche_sedi.currentText()
        self.coucheActiveEditableIndex = self.combo_couche_sedi.currentIndex()
        self.changeTabEvent() 
            
    def interpStateEvent(self):
        if(self.interp_enable.isChecked()):
            self.pt1_len.setEnabled(True)
            self.pt1_tick.setEnabled(True)
            self.pt2_len.setEnabled(True)
            self.pt2_tick.setEnabled(True)
            self.raz_btn.setEnabled(True)
            self.interp_launch.setEnabled(True)
        else:
            self.pt1_len.setEnabled(False)
            self.pt1_tick.setEnabled(False)
            self.pt2_len.setEnabled(False)
            self.pt2_tick.setEnabled(False)
            self.raz_btn.setEnabled(False)
            self.interp_launch.setEnabled(False)
            
                  
            
    def comboChangeEvent(self):
        #Appelé quand on selectionne un profil dans la liste deroulante
        self.tabs.setCurrentIndex(self.combo_profil.currentIndex())
        #self.changeTabEvent()
        
            
    def rowChangeEvent(self,tab):
        """
        """
        row = tab.currentIndex().row()
        
        model = tab.model()
        index = model.index(row, 0)
        
        abs_ = model.data(index,Qt.DisplayRole)
        self.rowChange(abs_)
        
             
    def rowChange(self,abs):
        ""
        ""
        if(self.pointing_line!=None):
            self.pointing_line.remove()     
            del self.pointing_line
        self.pointing_line = self.graph.axvline(float(abs), color='purple')
        self.canvas.draw()
            
    #def updateTab(self):
    #    table_val.setModel(self.NumpyModel(self,self.iface,f,np.array(tab_len),np.array(tabz),self.couche_choisi,self)) 
                               
    def changeTabEvent(self,index=-1,looseZoom=True):
        
        self.pointing_line = None
        
        self.all_tabs[self.tabs.currentIndex()].model().update()
        
        if(self.couche_choisi!=None):
            #features = self.iface.mapCanvas().currentLayer().getFeatures()       
                        
            self.graph.clear()
            axe_abs_curvN_m_1 = 0
            axe_abs_curvN = 0
            axe_abs_curvN_p_1 = 0
            
            tab_axe_abs_curv =[]
            selection=[]
            
            #calcul des abs_curv des point de passage de l'axe d'ecoulement.
            pts = []
            #===================================================================
            # for axe in self.trace_axe.getFeatures():                                
            #     geom= axe.geometry()
            #     if geom.type() == QGis.Point:
            #         pts.append(geom.asPoint())
            #     if geom.type() == QGis.Line:
            #         pts = geom.asPolyline()                  
            #===================================================================
            #self.profils_ordonne = self.getProfilsOrdonnes()
            
            
                
            i = 0
            for f in self.couche_choisi.getFeatures():
                
                #f = p_and_l[0]    
                taby = [float(y) for y in f.attribute('y').split(',')]
                tabx = [float(x) for x in f.attribute('x').split(',')]                  
                x1 = tabx[0]
                y1 = taby[0]
                #x2 = pts[i].x()
                #y2 = pts[i].y()
                x2 = float(f.attribute('intersection_axe').split(' ')[0])
                y2 = float(f.attribute('intersection_axe').split(' ')[1])
                
                axe_abs_curvN = math.sqrt (((x2-x1)*(x2-x1)) + ((y2-y1)*(y2-y1)))
                tab_axe_abs_curv.append(axe_abs_curvN+float(f.attribute('abs_travers').split(',')[0]))
                i = i +1
            
            #on affiche les features selectionnées
            i=0
            for f in self.couche_choisi.getFeatures():
                
                #f = p_and_l[0]           
                
                tabz = [float(z) for z in f.attribute('z').split(',')]
                taby = [float(y) for y in f.attribute('y').split(',')]
                tabx = [float(x) for x in f.attribute('x').split(',')]
                
                          
                #on dessine le precedent si il exite
                f_index=self.tabs.currentIndex()               
                
                
                
                if(i==f_index):
                    
                        pts = []
                        
                        #activation du profil selection sur la map
                        selection.append(f.id())
                        self.profil_courant = f
                        self.couche_choisi.setSelectedFeatures(selection)
                        
                        z0 = []
                        z1 = []
                        if(self.coucheActiveEditable=="Fond"):
                            self.courbe_principal, = self.graph.plot([float(l) for l in f.attribute('abs_travers').split(',')],tabz,color='red',marker=".",picker=self.line_picker,label=f.attribute('nom'),zorder = 10)
                        else:
                            self.graph.plot([float(l) for l in f.attribute('abs_travers').split(',')],tabz,color='red',label=f.attribute('nom'))
                        z0 = np.array(tabz)
                        if(not f.attribute('liste_couche_sediment') is None and not isinstance(f.attribute('liste_couche_sediment'),QPyNullVariant)):
                            
                            #On dessine chaque couche sedimentaire
                            j=0
                            
                            for name_couche_sedi in f.attribute('liste_couche_sediment').split(','):
                                tabz_sedi = [float(z) for z in f.attribute('couche_sedi_'+name_couche_sedi).split(',')]
                                tab_sedi_couleur = [str(c) for c in f.attribute('liste_couche_sediment_couleur').split(',')]
                                z1 = np.array(tabz_sedi)
                                colorR = None
                                colorG = None
                                colorB = None
                                if(self.coucheActiveEditable==name_couche_sedi):
                                    colorR = QColor.fromRgb(int(tab_sedi_couleur[self.coucheActiveEditableIndex-1])).redF()
                                    colorG = QColor.fromRgb(int(tab_sedi_couleur[self.coucheActiveEditableIndex-1])).greenF()
                                    colorB = QColor.fromRgb(int(tab_sedi_couleur[self.coucheActiveEditableIndex-1])).blueF()
                                    self.courbe_principal, = self.graph.plot([float(l) for l in f.attribute('abs_travers').split(',')],tabz_sedi,color=(colorR,colorG,colorB),marker=".",picker=self.line_picker,label=name_couche_sedi,zorder = 10)
                                else:
                                    colorR = QColor.fromRgb(int(tab_sedi_couleur[j])).redF()
                                    colorG = QColor.fromRgb(int(tab_sedi_couleur[j])).greenF()
                                    colorB = QColor.fromRgb(int(tab_sedi_couleur[j])).blueF()
                                    self.graph.plot([float(l) for l in f.attribute('abs_travers').split(',')],tabz_sedi,color=(colorR,colorG,colorB),label=name_couche_sedi,zorder = 1) 
                                    
                                j = j +1                                
                                self.graph.fill_between(np.array([float(l) for l in f.attribute('abs_travers').split(',')]),z0,z1,where=z1<=z0, facecolor=(colorR,colorG,colorB),alpha=0.3)
                                z0 = z1
                        
                        
                        
                            
                            
                        self.graph.axvline(tab_axe_abs_curv[f_index], color='black')
                        
                        #Affichage des berges
                        i_lit=0
                        berg_gauche_found = False
                        berg_droite_found = False
                        tablit = [lit for lit in f.attribute('lit').split(',')]  
                        abs_trav = [float(l) for l in f.attribute('abs_travers').split(',')]
                        for l in tablit:
                            if(l=="B" and berg_gauche_found == False):
                                self.graph.axvline(abs_trav[i_lit], color='red',linestyle='-.')
                                berg_gauche_found = True
                            if(l=="T" and berg_gauche_found ==True and berg_droite_found==False):
                                self.graph.axvline(abs_trav[i_lit-1], color='red',linestyle='-.')
                                berg_droite_found = True
                            i_lit=i_lit+1
                        if(berg_droite_found == False and berg_gauche_found == True ):                                
                                self.graph.axvline(abs_trav[i_lit-1], color='red',linestyle='-.')
                        
                if(f_index>0):
                    if(i==f_index-1):
                        
                        offset = -(tab_axe_abs_curv[f_index-1])+tab_axe_abs_curv[f_index]
                        self.graph.plot([(float(l)+offset) for l in f.attribute('abs_travers').split(',')],tabz,color='green',label=f.attribute('nom'),zorder = 1)
                        
                        #Affichage des berges
                        i_lit=0
                        berg_gauche_found = False
                        berg_droite_found = False
                        tablit = [lit for lit in f.attribute('lit').split(',')]  
                        abs_trav = [float(l) for l in f.attribute('abs_travers').split(',')]
                        for l in tablit:
                            if(l=="B" and berg_gauche_found == False):
                                self.graph.axvline(abs_trav[i_lit]+offset, color='green',linestyle='-.')
                                berg_gauche_found = True
                            if(l=="T" and berg_gauche_found ==True and berg_droite_found==False):
                                self.graph.axvline(abs_trav[i_lit-1]+offset, color='green',linestyle='-.')
                                berg_droite_found = True
                            i_lit=i_lit+1
                        if(berg_droite_found == False and berg_gauche_found == True ):
                                self.graph.axvline(abs_trav[i_lit-1]+offset, color='green',linestyle='-.')
                        
                        
                if(f_index<self.nombreProfil):
                    if(i==f_index+1):                          
                        
                        offset = -(tab_axe_abs_curv[f_index+1])+tab_axe_abs_curv[f_index]
                        self.graph.plot([(float(l)+offset) for l in f.attribute('abs_travers').split(',')],tabz,color='blue',label=f.attribute('nom'),zorder = 1)
                        
                        #Affichage des berges
                        i_lit=0
                        berg_gauche_found = False
                        berg_droite_found = False
                        abs_trav = [float(l) for l in f.attribute('abs_travers').split(',')]
                        tablit = [lit for lit in f.attribute('lit').split(',')]  
                        for l in tablit:
                            if(l=="B" and berg_gauche_found == False):
                                self.graph.axvline(abs_trav[i_lit]+offset, color='blue',linestyle='-.')
                                berg_gauche_found = True
                            if(l=="T" and berg_gauche_found ==True and berg_droite_found==False):
                                self.graph.axvline(abs_trav[i_lit-1]+offset, color='blue',linestyle='-.')
                                berg_droite_found = True
                            i_lit=i_lit+1
                        if(berg_droite_found == False and berg_gauche_found == True):
                                self.graph.axvline(abs_trav[i_lit-1]+offset, color='blue',linestyle='-.')
                        
                        
                
                i = i+1
            self.graph.grid(True)
            self.graph.set_ylabel("Z (m)")
            self.graph.set_xlabel("Abscisse en travers (m)")
            lines, labels = self.graph.get_legend_handles_labels()
            self.graph.legend(lines, labels, loc='upper center',  fancybox=True, shadow=True,ncol=4,prop={'size':10})
            self.x_valeur_min = self.graph.get_xlim()[0]
            self.x_valeur_max = self.graph.get_xlim()[1]
                        
            self.y_valeur_min = self.graph.get_ylim()[0]
            self.y_valeur_max = self.graph.get_ylim()[1]
            #print(looseZoom)
            if(not looseZoom):
                self.graph.set_ylim(self.y_valeur_zoom_min,self.y_valeur_zoom_max)
                self.graph.set_xlim(self.x_valeur_zoom_min,self.x_valeur_zoom_max)
                self.canvas.draw()
            else:
                
                self.resetZoom()    
                    
            
            
                #fself.y_valeur_zoom_min = self.y_valeur_min
                #self.y_valeur_zoom_max = self.y_valeur_max
                #self.x_valeur_zoom_min = self.x_valeur_min
                #self.x_valeur_zoom_max = self.x_valeur_max
            
            
                
            
    def export(self):
        """Lance la fonction d'export geo/geoRef"""
        files_types = "fichier Geo (*.geo);;fichier GeoRef (*.georef);;fichier GeoC (*.geoC);;fichier GeoRefC (*.georefC);;fichier ShapeFile(*.shp)"
        filename = QtGui.QFileDialog.getSaveFileName(self, "Export geo", "",files_types)
        if(filename!=""):
            writer = preCourlisGeoRefWriter(self.iface)
            _, ext = os.path.splitext(filename)
            if(ext!=".shp"):
                bief,ok = QInputDialog.getText(None,"Bief","Choisissez un nom pour le bief")
                if(ok):
                    writer.writeGeo(filename,self.couche_choisi,bief)
            else:
                writer.writeShapeFile(filename,self.couche_choisi)
            
            
    def resetZoom(self):
        """
        """
        #print("wtfffffffff?")
        self.graph.set_ylim(self.y_valeur_min,self.y_valeur_max)
        self.graph.set_xlim(self.x_valeur_min,self.x_valeur_max)
        self.y_valeur_zoom_min = self.y_valeur_min
        self.y_valeur_zoom_max = self.y_valeur_max
        self.x_valeur_zoom_min = self.x_valeur_min
        self.x_valeur_zoom_max = self.x_valeur_max
        self.canvas.draw()
        
    def interpolationTickness(self,pt1X,pt1Y,pt2X,pt2Y,x):
        #print(pt1X,pt1Y,pt2X,pt2Y,x)
        pente = (pt2Y-pt1Y)/(pt2X-pt1X)     
        return pente*(x-pt1X)+pt1Y
    
    def get_len_prof(self,p_and_l):
                    
        return self.tab_position[p_and_l[0]]
    
    def deplacementCouche(self,modepoint,abs_monopoint,tick_monopoint):
        
            for f in self.couche_choisi.getFeatures():
                    if(f.id()==self.profil_courant.id()):
                        #On en profite pour mettre à jour la feature
                        self.profil_courant = f
                        break
                
            tab_len =  [float(l) for l in self.profil_courant.attribute('abs_travers').split(',')]
            tab_Z = {}
            tab_newZ = {}
            if(not self.coucheActiveEditable=="Fond"):
                tab_sediname = f.attribute('liste_couche_sediment').split(',')
                index_name = tab_sediname.index(self.coucheActiveEditable)
            #print(self.coucheActiveEditable)
            #if(self.coucheActiveEditable=="Fond"):
            tab_Z['Fond'] =  [float(l) for l in self.profil_courant.attribute('z').split(',')]
            tab_newZ['Fond'] = []
            
            
            self.tab_position = {};
            self.tab_position["Fond"]=0;
            
            fond_dur_stop = {};
            
                      
            j=1
            
            position = 0
                #Et on ajoute toute les couches sedimentaires , pour les decaler
            if(not f.attribute('liste_couche_sediment') is None and not isinstance(f.attribute('liste_couche_sediment'),QPyNullVariant)):
                for couche_sedi in f.attribute('liste_couche_sediment').split(','):
                    tab_Z[couche_sedi] =  [float(l) for l in self.profil_courant.attribute('couche_sedi_'+couche_sedi).split(',')]
                    tab_newZ[couche_sedi] = []    
                    self.tab_position[couche_sedi] = j
                    j=j+1
                
            i=0
            self.couche_choisi.startEditing()
            if(not self.coucheActiveEditable=="Fond"):
                if(index_name==0):
                    tab_Zm1 =  [float(l) for l in self.profil_courant.attribute('z').split(',')]
                else:
                    tab_Zm1 =  [float(l) for l in self.profil_courant.attribute('couche_sedi_'+tab_sediname[index_name-1]).split(',')]
                tab_Zm0 =  [float(l) for l in self.profil_courant.attribute('couche_sedi_'+tab_sediname[index_name]).split(',')]
                       
            for abs in tab_len:
                if(modepoint=="monopoint"):
                    if(abs>=abs_monopoint-0.1 and abs<=abs_monopoint+0.1):
                        tick = tick_monopoint
                        
                    else:
                        #On recopie les epaisseurs deja enregistrées
                        #===========================================================
                        # if(self.coucheActiveEditable=="Fond"):
                        #     tick = 0
                        # else:                                              
                        #     tick = tab_Zm1[i]-tab_Zm0[i]
                        #===========================================================
                        tick = 0
                else:
                    if(abs>=float(self.pt1_len.text())-0.1 and abs<=float(self.pt2_len.text())+0.1):
                        tick = self.interpolationTickness(float(self.pt1_len.text()) ,float(self.pt1_tick.text()) ,float(self.pt2_len.text()) ,float(self.pt2_tick.text()),abs )
                    else:
                        #On recopie les epaisseurs deja enregistrées
                        #===========================================================
                        # if(self.coucheActiveEditable=="Fond"):
                        #     tick = 0
                        # else:                                              
                        #     tick = tab_Zm1[i]-tab_Zm0[i]
                        #===========================================================
                        tick = 0
                
                
                
                tick = -tick #ticket 14
                
                fond_dur_stop["Fond"]=False;            
                if(not f.attribute('liste_couche_sediment') is None and not isinstance(f.attribute('liste_couche_sediment'),QPyNullVariant)):
                    for couche_sedi in f.attribute('liste_couche_sediment').split(','):                    
                        fond_dur_stop[couche_sedi] = False
                
                
                           
                tab_Z_triee = {}        
                tab_Z_triee = sorted(tab_Z.copy().items(), key=self.get_len_prof)        
                
                #print tab_Z
                #print tab_Z_triee
                           
                for name_sedi,t_Z in tab_Z_triee:
                    
                    
                                            
                        
                    if(self.combo_fond_dur.currentText()!="Pas de fond dur" ):
                            #On regarde si on tape un fond dur vers le haut
                            if( tick<0  and self.tab_position[name_sedi]>=self.tab_position[self.combo_fond_dur.currentText()] and self.tab_position[name_sedi]<=self.tab_position[self.coucheActiveEditable] and t_Z[i]-tick>=tab_Z[self.combo_fond_dur.currentText()][i]):
                                fond_dur_stop[name_sedi] = True
                                if(not f.attribute('liste_couche_sediment') is None and not isinstance(f.attribute('liste_couche_sediment'),QPyNullVariant)):
                                    for couche_sedi in f.attribute('liste_couche_sediment').split(','):
                                      if(couche_sedi==self.coucheActiveEditable):
                                          break
                                      else:                    
                                          fond_dur_stop[couche_sedi] = True
                           
                            if( tick>0 and self.tab_position[name_sedi]<=self.tab_position[self.combo_fond_dur.currentText()] and self.tab_position[name_sedi]>=self.tab_position[self.coucheActiveEditable] and t_Z[i]-tick<=tab_Z[self.combo_fond_dur.currentText()][i]):
                                fond_dur_stop[name_sedi] = True
                                fnd = False
                                if(not f.attribute('liste_couche_sediment') is None and not isinstance(f.attribute('liste_couche_sediment'),QPyNullVariant)):
                                  for couche_sedi in f.attribute('liste_couche_sediment').split(','):
                                      
                                      if(couche_sedi==name_sedi):
                                          fnd= True
                                      if(fnd==True):
                                          fond_dur_stop[couche_sedi] = True
                                
                    if(name_sedi!=self.coucheActiveEditable):
                       
                               
                        if(not fond_dur_stop[name_sedi] and name_sedi!=self.combo_fond_dur.currentText() and tick<0 and t_Z[i]>=tab_Z[self.coucheActiveEditable][i] and self.tab_position[self.coucheActiveEditable]>self.tab_position[name_sedi] ):
                            
                            #ok la couche se trouve au dessus de celle en cours d'edition
                            if(tab_Z[self.coucheActiveEditable][i]-tick>t_Z[i]):
                               
                                #print tick
                                
                                #print t_Z[i]
                                #est ce qu'on la pousse en haut ?
                                tab_newZ[name_sedi].append(tab_Z[self.coucheActiveEditable][i]-tick)
                            else:
                                #non ? ok , on y touche pas
                                
                                tab_newZ[name_sedi].append(t_Z[i])
                                
                        elif(not fond_dur_stop[name_sedi] and name_sedi!=self.combo_fond_dur.currentText() and (tick>0 and t_Z[i]<=tab_Z[self.coucheActiveEditable][i]) and self.tab_position[self.coucheActiveEditable]<self.tab_position[name_sedi]):
                            #couche situ� en dessous ?
                            if(tab_Z[self.coucheActiveEditable][i]-tick<t_Z[i]):
                               
                                #print tick
                               
                                #print t_Z[i]
                                #est ce qu'on la pousse en bas ?
                                
                                tab_newZ[name_sedi].append(tab_Z[self.coucheActiveEditable][i]-tick)
                            else:
                                #non ? ok , on y touche pas
                                
                                tab_newZ[name_sedi].append(t_Z[i])
                        else:
                            #on y touche pas
                            if(not fond_dur_stop[name_sedi] ):
                                tab_newZ[name_sedi].append(t_Z[i])
                            else:
                                if((tick>0 and self.tab_position[name_sedi]<=self.tab_position[self.combo_fond_dur.currentText()])or (tick<0 and self.tab_position[name_sedi]>=self.tab_position[self.combo_fond_dur.currentText()])):                            
                                    tab_newZ[name_sedi].append(tab_Z[self.combo_fond_dur.currentText()][i])
                                else:
                                    tab_newZ[name_sedi].append(t_Z[i])
                                    
                                
                    
                    
                        if(name_sedi=="Fond"):
                            fied_index = self.couche_choisi.fieldNameIndex('z')
                        else:
                            fied_index = self.couche_choisi.fieldNameIndex('couche_sedi_'+name_sedi)
                        self.profil_courant[fied_index] = ','.join([str(z) for z in tab_newZ[name_sedi]])
                        self.couche_choisi.updateFeature(self.profil_courant)
                        #self.couche_choisi.commitChanges()
                        #if(not f.attribute('liste_couche_sediment') is None):
                        #    for couche_sedi in f.attribute('liste_couche_sediment').split(','):
                        #        tab_Z[couche_sedi] =  [float(l) for l in self.profil_courant.attribute('couche_sedi_'+couche_sedi).split(',')]
                    
                    #else:
                        #fond_dur_stop = False
                #if(not f.attribute('liste_couche_sediment') is None):
                #  for couche_sedi in f.attribute('liste_couche_sediment').split(','):
                #    tab_Z[couche_sedi] =  [float(l) for l in self.profil_courant.attribute('couche_sedi_'+couche_sedi).split(',')]
                fond_dur_touche = False
                
                for bool in fond_dur_stop.values():
                    if bool:                       
                        fond_dur_touche = True
                
                if(not fond_dur_stop[self.coucheActiveEditable]):
                    tab_newZ[self.coucheActiveEditable].append(tab_Z[self.coucheActiveEditable][i]-tick)
                else:
                    tab_newZ[self.coucheActiveEditable].append(tab_Z[self.combo_fond_dur.currentText()][i])
                    
                if(self.coucheActiveEditable=="Fond"):
                    fied_index = self.couche_choisi.fieldNameIndex('z')
                     
                else:
                    
                    fied_index = self.couche_choisi.fieldNameIndex('couche_sedi_'+self.coucheActiveEditable)
                    
                    
                self.profil_courant[fied_index] = ','.join([str(z) for z in tab_newZ[self.coucheActiveEditable]])
                self.couche_choisi.updateFeature(self.profil_courant) 
                
                i= i+1
            self.couche_choisi.commitChanges()
            
            #self.all_tabs[self.tabs.currentIndex()].model().datac
            self.changeTabEvent(looseZoom=False)
        
    
    def launchInterpol(self):
        if(self.pt1_len.text()!="" and self.pt2_len.text()!="" and self.pt1_tick.text()!="" and self.pt2_tick.text()!=""):
            
            #if(self.coucheActiveEditable=="Fond"):
            if(self.tools.check_if_not_numeric(self.pt1_len.text()) or self.tools.check_if_not_numeric(self.pt2_len.text()) or self.tools.check_if_not_numeric(self.pt1_tick.text()) or self.tools.check_if_not_numeric(self.pt2_tick.text()) ):
                QMessageBox.critical(self, "Erreur", unicode("Veuillez utiliser des réels","utf-8"), QMessageBox.Ok, QMessageBox.NoButton)
                return
            #else:
                #if(self.tools.check_if_not_numeric(self.pt1_len.text()) or self.tools.check_if_not_numeric(self.pt2_len.text()) or self.tools.check_if_not_numeric(self.pt1_tick.text()) or float(self.pt1_tick.text())<0 or self.tools.check_if_not_numeric(self.pt2_tick.text()) or float(self.pt2_tick.text())<0):
                #    QMessageBox.critical(self, "Erreur", unicode("Veuillez utiliser des réels positifs ou nuls","utf-8"), QMessageBox.Ok, QMessageBox.NoButton)
                #    return 
            self.deplacementCouche("multipoint",None,None)
            
        else:
             return   
                           
        
    def line_picker(self,line, mouseevent):
        
        xdata = line.get_xdata()
        ydata = line.get_ydata()
        
        modifiers = QtGui.QApplication.keyboardModifiers()   
        
       
        if(mouseevent.xdata is None or mouseevent.ydata is None): return False, dict()
        d = np.sqrt((xdata-mouseevent.xdata)**2. + (xdata-mouseevent.xdata)**2.)
        
        ind = np.argmin(d)
        
        self._ind = ind
        
        d2 = np.amin(d)
        
        if(self._ind!=None and (modifiers== QtCore.Qt.ControlModifier or self.interp_enable.isChecked())):  #and d2<=(self.graph.get_ylim()[1]-self.graph.get_ylim()[0])/10
            self.active_Zoom = False
            self.rowChange(self.all_tabs[self.tabs.currentIndex()].model().data(self.all_tabs[self.tabs.currentIndex()].model().index(self._ind, 0),Qt.DisplayRole))
            
            if(self.interp_enable.isChecked()):
                if(self.pt1_len.text()==""):
                    self.rowChange(self.all_tabs[self.tabs.currentIndex()].model().data(self.all_tabs[self.tabs.currentIndex()].model().index(self._ind, 0),Qt.DisplayRole))
                    self.pt1_len.setText(self.all_tabs[self.tabs.currentIndex()].model().data(self.all_tabs[self.tabs.currentIndex()].model().index(self._ind, 0),Qt.DisplayRole))                    
                elif(self.pt2_len.text()==""):
                    self.rowChange(self.all_tabs[self.tabs.currentIndex()].model().data(self.all_tabs[self.tabs.currentIndex()].model().index(self._ind, 0),Qt.DisplayRole))
                    self.pt2_len.setText(self.all_tabs[self.tabs.currentIndex()].model().data(self.all_tabs[self.tabs.currentIndex()].model().index(self._ind, 0),Qt.DisplayRole))
                    
            pickx = xdata[ind]
            picky = ydata[ind]
            props = dict(ind=ind, pickx=pickx, picky=picky)
                
            return True, props
            
        else:
            self.active_Zoom = True
            return False, dict()
        
        
        
    def draw_callback(self, event):
        if(self.active_Zoom):
            return
        self.background = self.canvas.copy_from_bbox(self.graph.bbox)
        
        self.graph.draw_artist(self.courbe_principal)
        self.canvas.blit(self.graph.bbox)
        
    def button_press_callback(self, event):
        if(self.active_Zoom):
            return
       
        self.background = self.canvas.copy_from_bbox(self.graph.bbox)
        
        self.graph.draw_artist(self.courbe_principal)
        self.canvas.blit(self.graph.bbox)
        
   
    def button_release_callback(self, event):
        'whenever a mouse button is released'     
        modifiers = QtGui.QApplication.keyboardModifiers()   
        if(not(modifiers== QtCore.Qt.ControlModifier) or self.active_Zoom or self.interp_enable.isChecked()):return       
        if(event.ydata is None):return
        if(event.button != 1):return
        
        xdata = self.courbe_principal.get_xdata()
        
        
        if(not self.coucheActiveEditable=="Fond"):
            tab_Z =  [float(l) for l in self.profil_courant.attribute('couche_sedi_'+self.coucheActiveEditable).split(',')]
        else:
            tab_Z =  [float(l) for l in self.profil_courant.attribute('z').split(',')]
                
        
        #self.all_tabs[self.tabs.currentIndex()].model().setDataWORepaint(self.all_tabs[self.tabs.currentIndex()].model().index(self._ind, self.coucheActiveEditableIndex+1),event.ydata,Qt.EditRole)
        #self.all_tabs[self.tabs.currentIndex()].repaint()
        tick = event.ydata-tab_Z[self._ind] ;
        
        
        self.deplacementCouche("monopoint",xdata[self._ind],tick)
        self._ind = None
        self.changeTabEvent(looseZoom=False)
        #self.canvas.draw()

    

    def motion_notify_callback(self, event):
        
        modifiers = QtGui.QApplication.keyboardModifiers()
        if(event.button != 1):return
        if(not(modifiers== QtCore.Qt.ControlModifier) or self.active_Zoom or self.background is None or self.interp_enable.isChecked()):
            return
        
        if self._ind is None or self.interp_enable.isChecked(): return
        
        x,y = event.xdata, event.ydata

        
        xdata = self.courbe_principal.get_xdata()
        ydata = self.courbe_principal.get_ydata()
        
        #xdata[self._ind] = x
        ydata[self._ind] = y
        
        
        self.courbe_principal.set_data(xdata,ydata)
       
        self.canvas.restore_region(self.background)
        
        self.graph.draw_artist(self.courbe_principal)
        self.canvas.blit(self.graph.bbox)
    
            
    class zoomRectangle(object):
        """ Classe qui permet le zoom rectangle.
            Le constructeur prend en parametre le context graphique (self.graph) et l'objet fenetre.
        """
        def __init__(self, ax, frame):
            self.ax = ax
            self.frame = frame
            self.rect = Rectangle((0, 0), 1, 1, fill=False)
            self.x0 = None
            self.y0 = None
            self.x1 = None
            self.y1 = None
            self.ax.add_patch(self.rect)
            self.ax.figure.canvas.mpl_connect('button_press_event', self.on_press)
            self.ax.figure.canvas.mpl_connect('button_release_event', self.on_release)
            self.ax.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)
            
    
        def on_press(self, event):
             
            if(event.button == 1):
                if(not self.frame.active_Zoom):
                    return
                self.rect = Rectangle((0, 0), 1, 1, fill=False)
                self.x0 = event.xdata
                self.y0 = event.ydata           
                self.x1 = None
                self.y1 = None
                self.ax.add_patch(self.rect)
                self.background = self.ax.figure.canvas.copy_from_bbox(self.ax.bbox)
            if(event.button == 3):
                self.frame.resetZoom()    
    
        def on_release(self, event):
            if(not self.frame.active_Zoom):
                return
            if(event.button == 1):
                self.x1 = event.xdata
                self.y1 = event.ydata
                
                if self.x1 != self.x0 and self.y1 != self.y0:                      
                    
                    if(self.y1 > self.y0):
                        self.frame.y_valeur_zoom_min = self.y0
                        self.frame.y_valeur_zoom_max = self.y1
                        self.ax.set_ylim(self.y0, self.y1)                        
                    else:
                        self.frame.y_valeur_zoom_min = self.y1
                        self.frame.y_valeur_zoom_max = self.y0
                        self.ax.set_ylim(self.y1, self.y0)
                        
                    if(self.x1 > self.x0):
                        self.frame.x_valeur_zoom_min = self.x0
                        self.frame.x_valeur_zoom_max = self.x1
                        self.ax.set_xlim(self.x0, self.x1)
                    else:
                        self.frame.x_valeur_zoom_min = self.x1
                        self.frame.x_valeur_zoom_max = self.x0
                        self.ax.set_xlim(self.x1, self.x0)
                        
                    self.ax.figure.canvas.draw()
                    
                self.rect.remove()  
                self.rect = Rectangle((0, 0), 1, 1, fill=False)             
                self.x0 = None
                self.y0 = None
                self.x1 = None
                self.y1 = None
                
                # self.ax.add_patch(self.rect)   
            
            
        def on_motion(self, event):
            if(not self.frame.active_Zoom):
                return
            self.x1 = event.xdata
            self.y1 = event.ydata
            if self.x1 != self.x0 and self.y1 != self.y0:
                if(self.x0 != None)and (self.x1 != None)and (self.y0 != None)and (self.y1 != None):          
                    self.rect.set_width(abs(float(self.x1) - float(self.x0)))           
                    self.rect.set_height(abs(float(self.y1) - float(self.y0)))
                    if(self.x1 > self.x0):
                        if(self.y1 > self.y0):
                            self.rect.set_xy((self.x0, self.y0))
                        else:
                            self.rect.set_xy((self.x0, self.y1))
                    else:
                        if(self.y1 > self.y0):
                            self.rect.set_xy((self.x1, self.y0))
                        else:
                            self.rect.set_xy((self.x1, self.y1))
                
                
                    self.ax.figure.canvas.restore_region(self.background)
                    self.ax.draw_artist(self.rect)           
                    self.ax.figure.canvas.blit(self.ax.bbox)
      
      
    class TableView(QTableView):
        def keyPressEvent(self, event):
            if (event.key() == Qt.Key_Delete):               
                
                selectedRows = self.selectionModel().selectedRows()
                if selectedRows:
                    selectedIndex = selectedRows[0]
                    index = self.model().index(selectedIndex.row(), 0)
                    #print("suppression du point n°"+str(selectedIndex.row()))
                    self.model().setData(index,'',Qt.EditRole);
            else:
                QTableView.keyPressEvent(self, event)             
                            
    class NumpyModel(QAbstractTableModel):
        
        
        def __init__(self,tab,iface,feature,tl,tz,layer,ui,parent=None):
            QAbstractTableModel.__init__(self,parent)
            self.noms_colonnes = ['Abs travers','Fond(Z)']
            self.tl = tl
            self.zs = tz
            self.feature = feature
            self.iface = iface
            self.tab = tab
            self.couche_choisi = layer
            self.tz_sedi = []
            self.ui = ui
            
        def update(self):
            
            #On met � jour la feature m�moris�
            for f in self.couche_choisi.getFeatures():
                            if(f.id()==self.feature.id()):
                                self.feature = f 
                                break;
                            
            #on met à jour la colonne Z
            self.zs = np.array([float(z) for z in self.feature.attribute('z').split(',')])    
            #on mets a jour les colonnes pour les couches sedimentaires
            if(not self.feature.attribute('liste_couche_sediment') is None and not isinstance(self.feature.attribute('liste_couche_sediment'),QPyNullVariant)):
                    index_c = 0
                    for couche_sedi in self.feature.attribute('liste_couche_sediment').split(','):
                        tabZ = [float(l) for l in self.feature.attribute('couche_sedi_'+couche_sedi).split(',')]
                        if(couche_sedi in self.noms_colonnes):
                            #il faut mettre � jour les colonnes
                            self.tz_sedi[index_c] = tabZ                           
                            self.dataChanged.emit(self.createIndex(0,2),self.createIndex(len(tabZ),len(self.noms_colonnes)))
                        else:
                            #il faut donc rajouter la colonne                            
                            self.addColumn(couche_sedi,tabZ)
                        index_c = index_c +1   
            
            
        def addColumn(self,name,tz):
            
            self.noms_colonnes.append(name)
            self.tz_sedi.append(tz)
            self.insertColumn(len(self.noms_colonnes))      
            
            
        
        def insertColumns(self,col,count,parent=QModelIndex()): 
            self.beginInsertColumns(parent, col, col)
            self.endInsertColumns ()            
            return True
            
        def headerData(self, section, orientation, role=Qt.DisplayRole):
            if role == Qt.DisplayRole and orientation == Qt.Horizontal:                
                return self.noms_colonnes[section]
            return QAbstractTableModel.headerData(self, section, orientation, role)
    
        def rowCount(self, parent=None):
            return self.zs.shape[0]
    
        def columnCount(self, parent=None):
            return len(self.noms_colonnes)
        
        def flags(self, index):
            if index.isValid():
                if(index.column()>=1):
                    return Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable
                else:
                    return Qt.ItemIsEnabled | Qt.ItemIsSelectable
            else:
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
        def data(self, index,role ):
            if index.isValid():
                if role == Qt.DisplayRole or role == Qt.EditRole:
                    row = index.row()
                    col = index.column()
                    
                    if(col==0):                        
                        return str(round(self.tl[row],3))
                    elif(col==1):
                        return str(round(self.zs[row],3))
                    else:
                        return str(round(self.tz_sedi[col-2][row],3)) # -2 , car il y a len et le Z du profil avant les Z des couches sedi
                    
        
                    
        def setData(self,index,value,role):
            for f in self.couche_choisi.getFeatures():
                        if(f.id()==self.feature.id()):
                            self.feature = f 
                            break; 
            if(index.isValid() and role == Qt.EditRole):
                if(value == ''):
                    #suppression
                    ret = QMessageBox.question(None,"Suppression point",unicode("Etes-vous sûr ?","utf-8"),QMessageBox.Ok, QMessageBox.Cancel)
                    if(ret!=QMessageBox.Ok):
                        return
                    taby = np.array([float(y) for y in self.feature.attribute('y').split(',')])
                    tabx = np.array([float(x) for x in self.feature.attribute('x').split(',')])
                    #tab_abs = np.array([float(abs) for abs in self.feature.attribute('abs_travers').split(',')])                    
                    tab_lit = np.array([lit for lit in self.feature.attribute('lit').split(',')])        
                    tabx = np.delete(tabx, index.row())
                    taby = np.delete(taby, index.row())
                    #tab_abs = np.delete(tab_abs, index.row())
                    
                    #On recalcule les abs curv
                    profileLen = 0
                    tab_len = []
                    tab_len.append(.0)
                    for i in range(0, len(tabx)-1):
                        x1 = tabx[i]
                        y1 = taby[i]
                        x2 = tabx[i+1]
                        y2 = taby[i+1]
                        profileLen = math.sqrt (((x2-x1)*(x2-x1)) + ((y2-y1)*(y2-y1))) + profileLen
                        tab_len.append(profileLen)
                    self.tl = np.array(tab_len)
                    tab_lit = np.delete(tab_lit, index.row())
                    self.zs = np.delete(self.zs, index.row())
                    
                    
                    
                    self.couche_choisi.startEditing()
                    fied_index = self.couche_choisi.fieldNameIndex('x')
                    self.feature[fied_index] = ','.join([str(x) for x in tabx])
                    fied_index = self.couche_choisi.fieldNameIndex('y')
                    self.feature[fied_index] = ','.join([str(y) for y in taby])
                    fied_index = self.couche_choisi.fieldNameIndex('z')
                    self.feature[fied_index] = ','.join([str(z) for z in self.zs])
                    fied_index = self.couche_choisi.fieldNameIndex('abs_travers')
                    self.feature[fied_index] = ','.join([str(abs) for abs in tab_len])
                    fied_index = self.couche_choisi.fieldNameIndex('lit')
                    self.feature[fied_index] = ','.join([str(lit) for lit in tab_lit])
                    
                    
                    if(not self.feature.attribute('liste_couche_sediment') is None and not isinstance(self.feature.attribute('liste_couche_sediment'),QPyNullVariant)):
                            i=0
                            for couche_sedi in self.feature.attribute('liste_couche_sediment').split(','):                                
                                field_index_c = self.couche_choisi.fieldNameIndex('couche_sedi_'+couche_sedi)
                                del self.tz_sedi[i][index.row()]
                                self.feature[field_index_c] = ','.join([str(z) for z in self.tz_sedi[i]])
                                i=i+1
                                
                    
                    
                    
                    self.couche_choisi.updateFeature(self.feature)
                    self.couche_choisi.commitChanges()
                    self.dataChanged.emit(index, index)
                    self.update()
                    self.tab.changeTabEvent()
                    
                    return True
                    
                else:
                    if(index.column()==1):                
                        self.zs[index.row()] = value
                        self.couche_choisi.startEditing()
                        fied_index = self.couche_choisi.fieldNameIndex('z')
                        self.feature[fied_index] = ','.join([str(z) for z in self.zs])
                        self.couche_choisi.updateFeature(self.feature)
                        self.couche_choisi.commitChanges()
                        self.dataChanged.emit(index, index)
                        self.tab.changeTabEvent()
                        return True
                    else:
                        
                        self.tz_sedi[index.column()-2][index.row()] = float(value)
                        field_index = -1
                        
                        if(not self.feature.attribute('liste_couche_sediment') is None and not isinstance(self.feature.attribute('liste_couche_sediment'),QPyNullVariant)):
                            found = False
                            i=0
                            for couche_sedi in self.feature.attribute('liste_couche_sediment').split(','):
                                if(i==index.column()-2):                                    
                                    #print('i'+str(i))
                                    field_index_c = self.couche_choisi.fieldNameIndex('couche_sedi_'+couche_sedi)
                                    self.feature[field_index_c] = ','.join([str(z) for z in self.tz_sedi[i]])
                                    self.couche_choisi.startEditing()                    
                                    self.couche_choisi.updateFeature(self.feature)
                                    self.couche_choisi.commitChanges()
                                    break;
                                    
                                
                                i=i+1                           
                        
                        self.dataChanged.emit(index, index)
                        self.tab.changeTabEvent()
                        return True
                        
                
                    
                
                
            return False
                    
                    
