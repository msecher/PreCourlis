# -*- coding: utf-8 -*-
'''
Created on 31 mars 2015

@author: quarre
'''
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QComboBox,QPushButton,QGridLayout,QPushButton,QLabel,QMessageBox
from qgis.core import *
import qgis

class preCourlisDeleteBief(QtGui.QDialog):
    
    def __init__(self,iface,l_bief):
        QtGui.QDialog.__init__(self,None)
        self.iface = iface
        self.setWindowTitle("Supprimer un bief")
        
        self.list_b = l_bief
        
        gridbox = QGridLayout()
        
        self.list_bief = QComboBox()
        
        self.btn_ok = QPushButton("Ok")
        
        root = QgsProject.instance().layerTreeRoot()
        if(root.findGroup("Biefs")):    
            
            for child in root.findGroup("Biefs").children():
                self.list_bief.addItem(child.name())  
        
        gridbox.addWidget(QLabel(unicode("Choisissez un bief","utf-8")),0,0)
        gridbox.addWidget(self.list_bief,0,1)        
        gridbox.addWidget(self.btn_ok,1,0)
        
        QtCore.QObject.connect(self.btn_ok, QtCore.SIGNAL("clicked(bool)"), self.delete)
        
        self.setLayout(gridbox)
    
        self.show()
        
    def delete(self):
        
        root = QgsProject.instance().layerTreeRoot()
        if(root.findGroup("Biefs")):    
            ret = QMessageBox.question(self,"Suppression",unicode("Etes-vous sûr ?","utf-8"),QMessageBox.Ok, QMessageBox.Cancel)
            if(ret==QMessageBox.Ok):
                root.findGroup("Biefs").removeChildNode(root.findGroup(self.list_bief.currentText()))
                root.findGroup(unicode("Entité 1D","utf-8")).removeChildNode(root.findGroup("Traces_"+self.list_bief.currentText()))
                del self.list_b[self.list_bief.currentText()]
                self.close()
            else:
                return
        