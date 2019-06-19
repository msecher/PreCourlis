# -*- coding: utf-8 -*-
'''
Created on 9 juil. 2015

@author: quarre
'''
import os.path
from qgis.core import *
from PyQt4.QtCore import QVariant
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QPushButton,QTableView,QTabWidget,QMessageBox,QComboBox,QGroupBox,QInputDialog,QCheckBox,QLineEdit,QLabel,QColorDialog,QColor,QButtonGroup,QRadioButton
from qgis.analysis import QgsGeometryAnalyzer
from shapely.geometry import LineString
from preCourlisTools import preCourlisTools , Point, Polyligne
from preCourlisLayersChooser import preCourlisLayersChooser 

class preCourlisProjZProfils:
    
    
    def __init__(self, iface):
        
        self.iface = iface
        self.tools = preCourlisTools()  
        list_layer = [["Profils",'layer_profils'], ['Semis','layer_point','Choix attribut Z']]
            
        layChooser = preCourlisLayersChooser(list_layer)
        tab_ret = {}
        self.tab_ret_attr = {}
        if layChooser.exec_():
            tab_ret = layChooser.tab_ret           
            self.tab_ret_attr = layChooser.tab_ret_attr  
            
            
            self.layer_profils = self.tools.getLayerByName(tab_ret["Profils"])
            self.layer_semis = self.tools.getLayerByName(tab_ret["Semis"])
        else:
            return    
        
        self.path_log = os.path.dirname(os.path.abspath(self.layer_profils.source()))+"\\"+tab_ret["Profils"]+".log"
        self.fichier_log = open(self.path_log, "a")
        self.fichier_log.write("-- Projection d'un semis de point sur les profils \n")
        self.fichier_log.write("\n")
        self.fichier_log.write("    Semis utilisees : "+tab_ret["Semis"]+"\n")
        self.fichier_log.write("    Profils de destination : "+tab_ret["Profils"]+"\n")
        self.fichier_log.write("\n")
        
        self.projectionZpointsProche()
    
    
    
    def projectionZpointsProche(self):
            """
            """
        
            
            self.fichier_log.write("    Debut de projection...\n")
            
            layer_choisi = self.layer_profils
            
            distance = 10.
            # distance a rentrer en boite de dialogue
            dist, ok = QInputDialog.getText(None, "Distance", "Distance de selection des points du semis")
            if(ok):
                distance = float(dist)
             
            self.fichier_log.write("        distance de selection des points du semis : "+dist+"\n") 
                                        
            layer_semis = self.layer_semis
            
            

            layer_choisi.startEditing()
            
            # Recuperation des points de la couche semis
            geom = None
            pointSemis = []
            for semis in layer_semis.getFeatures():
                geom = semis.geometry()
                
                pts = geom.asPoint()         
                
                pointSemis.append(Point(pts.x(), pts.y(), semis.attribute(self.tab_ret_attr['Semis'])))          
            
            nProfil = 0
            for profil in layer_choisi.getFeatures():
                nom_profil = profil.attribute('nom')
                self.fichier_log.write("            "+nom_profil+"...\n")
                
                tabx = [float(x) for x in profil.attribute('x').split(',')]
                taby = [float(y) for y in profil.attribute('y').split(',')]
                tabz = [float(z) for z in profil.attribute('z').split(',')]
                
                pointsProfil = []
                for i in range(0, len(tabx)):
                    pointsProfil.append(Point(tabx[i], taby[i], tabz[i]))
                
                plProfil = Polyligne(pointsProfil)
                nModif = plProfil.definirZparPointsProches4(pointSemis, distance, False)
                
                if(nModif != 0):                    
                    tab_attribute_Z = []
                    for i in range(0, len(tabx)):
                        tab_attribute_Z.append(plProfil.pts[i].z)
                        
                    profil.setAttribute('z', ','.join([str(z) for z in tab_attribute_Z]))
                    
                    nProfil = nProfil + 1
                    layer_choisi.updateFeature(profil)
   

            layer_choisi.commitChanges()
            self.fichier_log.write("    Projection terminee")
            self.fichier_log.close()
            QMessageBox.information(None, "Projection points proches", str(nProfil) + unicode(" profil(s) mis à jour. \n Log écrit dans ", "utf-8")+self.path_log, QMessageBox.Ok)                      
                                      
              
