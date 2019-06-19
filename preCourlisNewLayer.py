# -*- coding: utf-8 -*-
'''
Created on 30 mars 2015

@author: quarre
'''
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QComboBox,QPushButton,QGridLayout,QLineEdit,QPushButton,QLabel
from qgis.core import *
from PyQt4.QtCore import QVariant
import qgis

class preCourlisNewLayer(QtGui.QDialog):
    
    def __init__(self,iface):
        QtGui.QDialog.__init__(self,None)
        self.iface = iface
        self.setWindowTitle("Nouvelle couche vectorielle")
        self.resize(270,10)
        
        gridbox = QGridLayout()
        
        self.list_bief = QComboBox()
        self.nom = QLineEdit()
        self.type_layer = QComboBox()
        self.btn_ok = QPushButton("Ok")
        
        root = QgsProject.instance().layerTreeRoot()       
            
        for child in root.children():
            if(isinstance(child, QgsLayerTreeGroup)):
                self.list_bief.addItem(child.name())  
                
        self.type_layer.addItem("Aucun")
        self.type_layer.addItem("Axe hydraulique")
        self.type_layer.addItem("Trace de profil")
        self.type_layer.addItem("Profil")
        self.type_layer.addItem("Rive Gauche")
        self.type_layer.addItem("Rive Droite")           
        
        gridbox.addWidget(QLabel(unicode("Choisissez un bief","utf-8")),0,0)
        gridbox.addWidget(self.list_bief,0,1)    
        gridbox.addWidget(QLabel("Nom de la couche"),1,0)
        gridbox.addWidget(self.nom,1,1)
        gridbox.addWidget(QLabel("Type d'attribut"),2,0)
        gridbox.addWidget(self.type_layer,2,1)
        gridbox.addWidget(self.btn_ok,3,0)
        
        
        QtCore.QObject.connect(self.btn_ok, QtCore.SIGNAL("clicked(bool)"), self.ajout)
        
        self.setLayout(gridbox)
    
        self.show()
      
      
    def ajout(self):
        
        root = QgsProject.instance().layerTreeRoot()
        if(root.findGroup(self.list_bief.currentText())):    
            
            
            self.vl = QgsVectorLayer("LineString",self.nom.text(), "memory")
            
            if(self.type_layer.currentText()=="Axe hydraulique"):
                self.vl.startEditing()
                pr_axe =  self.vl.dataProvider()
                pr_axe.addAttributes( [ QgsField("axe_id",QVariant.Int)] )                
                self.vl.commitChanges()
            if(self.type_layer.currentText()=="Trace de profil"):
                self.vl.startEditing()
                pr_trace =  self.vl.dataProvider()
                pr_trace.addAttributes( [ QgsField("nom_profil",QVariant.String)] )                
                self.vl.commitChanges()
            if(self.type_layer.currentText()=="Profil"):
                self.vl.startEditing()
                pr_profil =  self.vl.dataProvider()
                pr_profil.addAttributes( [ QgsField("nom",QVariant.String),QgsField("x",QVariant.String), QgsField("y",QVariant.String),QgsField("z",QVariant.String),QgsField("lit",QVariant.Int),QgsField("intersection_axe",QVariant.String),QgsField("liste_couche_sediment",QVariant.String),QgsField("liste_couche_sediment_couleur",QVariant.String)] )               
                self.vl.commitChanges()
            if(self.type_layer.currentText()=="Rive Gauche"):
                self.vl.startEditing()
                pr_rg =  self.vl.dataProvider()
                pr_rg.addAttributes( [ QgsField("rg_id",QVariant.Int)] )                
                self.vl.commitChanges()
            if(self.type_layer.currentText()=="Rive Droite"):
                self.vl.startEditing()
                pr_rd =  self.vl.dataProvider()
                pr_rd.addAttributes( [ QgsField("rd_id",QVariant.Int)] )                
                self.vl.commitChanges()
                      
            root.findGroup(self.list_bief.currentText()).addLayer(self.vl)
            QgsMapLayerRegistry.instance().addMapLayer(self.vl,False)   
        
        self.close()
        