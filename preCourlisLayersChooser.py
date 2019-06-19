# -*- coding: utf-8 -*-
'''
Created on 8 juil. 2015

@author: quarre
'''

from qgis.core import *
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QComboBox,QPushButton,QGridLayout,QLineEdit,QPushButton,QLabel,QCheckBox
from functools import partial
from preCourlisTools import preCourlisTools




#Permet de demander la selection de 1 ou N couches


class preCourlisLayersChooser(QtGui.QDialog):
    
    def __init__(self,layers_needed):
        
        QtGui.QFrame.__init__(self)
        
        self.setWindowTitle("Selectionnez la ou les couches")
        self.resize(270,10)
        gridbox = QGridLayout()
        
        self.btn_ok = QPushButton("OK")
        self.tools = preCourlisTools()
         
        self.list_layer_dispo = ['Pas de couche']
        self.list_layer_raster = ['Pas de couche']
        self.list_layer_vector_1 = ['Pas de couche']
        self.list_layer_vector = ['Pas de couche']
        self.list_layer_profil = ['Pas de couche']
        self.list_layer_point = ['Pas de couche']
        self.parseTree(QgsProject.instance().layerTreeRoot())        
       
        
        i =0
        self.tab_ret ={}
        self.tab_ret_attr ={}
        self.tab_combo ={}
        self.tab_comboAttr ={}
        for tab in layers_needed:
            name=tab[0]
            type=tab[1] # 'all_layer','layer_raster' , 'layer_vector' , 'layer_point','layer_profils','float','checkbox'
            gridbox.addWidget(QLabel(unicode(name,"utf-8")),i,0)
            
            if(type=="all_layer" or type=="layer_raster" or type=="layer_vector" or type=="layer_vector_1" or type=="layer_profils" or type=="layer_point"):
                combo = QComboBox()
                if(type=="layer_raster"):
                    combo.addItems(self.list_layer_raster)
                elif(type=="layer_profils"):
                    combo.addItems(self.list_layer_profil)
                elif(type=="layer_vector"):
                    combo.addItems(self.list_layer_vector)
                elif(type=="layer_vector_1"):
                    combo.addItems(self.list_layer_vector_1)
                elif(type=="layer_point"):
                    combo.addItems(self.list_layer_point)
                else:
                    combo.addItems(self.list_layer_dispo)
                self.tab_combo[name]=combo;
                
                gridbox.addWidget(combo,i,1)
                
                if(len(tab)==3):
                    #un attribut est a choisir
                    gridbox.addWidget(QLabel(unicode(tab[2],"utf-8")),i,2)
                    comboAttr = QComboBox()
                    self.tab_comboAttr[name]=comboAttr;
                    gridbox.addWidget(comboAttr,i,3)
                    combo.currentIndexChanged.connect(partial(self.comboChange , combo=combo, comboAttr=comboAttr))
                    self.comboChange(combo,comboAttr)
                    
            if(type=="float"):
                tf = QLineEdit()
                self.tab_combo[name]=tf;
                gridbox.addWidget(tf,i,1)
                
            if(type=="checkbox"):
                ck = QCheckBox()                
                self.tab_combo[name]=ck;
                gridbox.addWidget(ck,i,1)
                
            if(type=="multi_layer"):
                gridbox_multi = QGridLayout()
                pos=0
                self.tab_combo[name]={}   
                for lay in self.list_layer_vector: 
                    if(lay=='Pas de couche'):
                        continue
                    ck = QCheckBox()                                
                    self.tab_combo[name][lay]=ck;
                    gridbox_multi.addWidget(QLabel(lay),pos,0)
                    gridbox_multi.addWidget(ck,pos,1)
                    pos = pos +1
                    
                gridbox.addItem(gridbox_multi,i,1)
                
            
            i=i+1
        
        gridbox.addWidget( self.btn_ok,i,1)    
        self.btn_ok.clicked.connect(self.submitclose)  
        
        self.setLayout(gridbox)   
        self.show()
        
    def comboChange(self,combo,comboAttr):
        
        comboAttr.clear()
        comboAttr.addItems(self.updateAttribut(self.tools.getLayerByName(combo.currentText())))
        
        
    def updateAttribut(self,layer):
        
        ret = []
        try:
            for attr in layer.pendingFields():
                ret.append(attr.name())
        except:
            ret = []
        return ret
    
    def isProfilLayer(self,layer):
        try:
            for attr in layer.pendingFields():
                if(attr.name()=="intersection_axe"):
                     return True
        except:
            return False
        return False
    
    def hasOnlyOneFeature(self,layer):
            if(layer.pendingFeatureCount()<=1):
                return True
            else:      
                return False
                
    def parseTree(self,root):        
        
        for child in root.children():
            if(isinstance(child, QgsLayerTreeLayer)):
                if(child.layer().type()!=1):
                    print(child.layer().dataProvider().geometryType())
                    print(child.layerName()) 
                if(child.layer().type()==1):
                    self.list_layer_raster.append(child.layerName())
                elif(child.layer().type()==0 and self.isProfilLayer(child.layer())):            
                    self.list_layer_profil.append(child.layerName())
                elif(child.layer().type()==0 and child.layer().dataProvider().geometryType()!=1):            
                    self.list_layer_vector.append(child.layerName())
                    if(child.layer().type()==0 and self.hasOnlyOneFeature(child.layer()) and  child.layer().dataProvider().geometryType()!=1 and child.layer().dataProvider().geometryType()!=1 ):            
                        self.list_layer_vector_1.append(child.layerName())
                elif(child.layer().type()==0 and  (child.layer().dataProvider().geometryType() ==1 or child.layer().dataProvider().geometryType()==1 )):            
                    self.list_layer_point.append(child.layerName())
                      
                
                self.list_layer_dispo.append(child.layerName())
            if(isinstance(child, QgsLayerTreeGroup)):
                self.parseTree(child)
            
    def submitclose(self):
        
        
        
        for lay,com in self.tab_combo.items():
            if(isinstance(com,QComboBox)):
                self.tab_ret[lay]=com.currentText()
            if(isinstance(com,QCheckBox)):
                self.tab_ret[lay]=com.isChecked()
            if(isinstance(com,QLineEdit)):
                self.tab_ret[lay]=com.text()
            if(isinstance(com,dict)):                
                self.tab_ret[lay]=[]                
                for l,c in com.items():
                    if (c.isChecked()):
                        self.tab_ret[lay].append(l)
                
        for lay,com in self.tab_comboAttr.items():
            self.tab_ret_attr[lay]=com.currentText()
        
        self.accept()
             