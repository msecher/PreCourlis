# -*- coding: utf-8 -*-
'''
Created on 30 mars 2015

@author: quarre
'''
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QComboBox,QPushButton,QGridLayout,QLineEdit,QPushButton,QLabel
from qgis.core import *
import qgis

class preCourlisRenameBief(QtGui.QDialog):
    
    def __init__(self,iface,l_bief):
        QtGui.QDialog.__init__(self,None)
        self.iface = iface
        self.setWindowTitle("Renommer un bief")
        
        self.list_b = l_bief
        gridbox = QGridLayout()
        
        self.list_bief = QComboBox()
        self.nouveau_nom = QLineEdit()
        self.btn_ok = QPushButton("Ok")
        
        root = QgsProject.instance().layerTreeRoot()
        if(root.findGroup("Biefs")):    
            
            for child in root.findGroup("Biefs").children():
                self.list_bief.addItem(child.name())              
        
        gridbox.addWidget(QLabel(unicode("Choisissez un bief","utf-8")),0,0)
        gridbox.addWidget(self.list_bief,0,1)    
        gridbox.addWidget(QLabel("Nouveau nom"),1,0)
        gridbox.addWidget(self.nouveau_nom,1,1)
        gridbox.addWidget(self.btn_ok,2,0)
        
        
        QtCore.QObject.connect(self.btn_ok, QtCore.SIGNAL("clicked(bool)"), self.rename)
        
        self.setLayout(gridbox)
    
        self.show()
      
      
    def rename(self):
        
        root = QgsProject.instance().layerTreeRoot()
        if(root.findGroup("Biefs")):    
            
            root.findGroup(self.list_bief.currentText()).setName(self.nouveau_nom.text())
            root.findGroup("Traces_"+self.list_bief.currentText()).setName("Traces_"+self.nouveau_nom.text()) 
            self.list_b[self.nouveau_nom.text()] = self.list_b.pop(self.list_bief.currentText())    
                
        
        self.close()
        