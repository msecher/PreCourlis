# -*- coding: utf-8 -*-
'''
Created on 9 juil. 2015

@author: quarre
'''
import processing
import os.path
import math
from qgis.core import *
from PyQt4.QtCore import QVariant
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QPushButton,QTableView,QTabWidget,QMessageBox,QComboBox,QGroupBox,QInputDialog,QCheckBox,QLineEdit,QLabel,QColorDialog,QColor,QButtonGroup,QRadioButton
from qgis.analysis import QgsGeometryAnalyzer
from shapely.geometry import LineString
from preCourlisTools import preCourlisTools , Point, Polyligne
from preCourlisLayersChooser import preCourlisLayersChooser 

class preCourlisProjAxeBerge:
    
    
    def __init__(self, iface):
        
        self.iface = iface
        self.tools = preCourlisTools()  
        list_layer = [['Profils','layer_profils','Nom'], ['Rive Gauche','layer_vector_1'],['Rive Droite','layer_vector_1']]
            
        layChooser = preCourlisLayersChooser(list_layer)
        tab_ret = {}
        self.tab_ret_attr = {}
        if layChooser.exec_():
            tab_ret = layChooser.tab_ret           
            self.tab_ret_attr = layChooser.tab_ret_attr  
            
            #self.layer_trace_profils = self.tools.getLayerByName(tab_ret["Traces"])
            self.layer_profils = self.tools.getLayerByName(tab_ret["Profils"])  
                      
            self.layer_rg = self.tools.getLayerByName(tab_ret["Rive Gauche"])
            #self.axe = self.tools.getLayerByName(tab_ret["Axe"])
            self.layer_rd = self.tools.getLayerByName(tab_ret["Rive Droite"])
        else:
            return    
        
        
        self.path_log = os.path.dirname(os.path.abspath(self.layer_profils.source()))+"\\"+tab_ret["Profils"]+".log"
        self.fichier_log = open(self.path_log, "w")
        
        self.fichier_log.write("-- Projection des berges sur les profils \n")
        self.fichier_log.write("\n")
        self.fichier_log.write("    Couche rive gauche : "+tab_ret["Rive Gauche"]+"\n")
        self.fichier_log.write("    Couche rive droite : "+tab_ret["Rive Droite"]+"\n")
        self.fichier_log.write("\n")
        
        self.generePointPassageAxeHydro()
        
        
    def generePointPassageAxeHydro(self):
            """
            """
        
            
            root = QgsProject.instance().layerTreeRoot()
            
            layer_choisi = self.layer_profils
            
            tools = preCourlisTools()
            
            
                    
            
            #recherche des trace de  l'axe hydro et des profils
            #trace_profils = self.layer_trace_profils
           
            trace_riveG = self.layer_rg
            trace_riveD = self.layer_rd            
            
            
            
            if(os.path.isfile("profil.shp")):
                os.remove("profil.shp")
            if(os.path.isfile("trace_riveG.shp")):
                os.remove("trace_riveG.shp")
            if(os.path.isfile("trace_riveD.shp")):
                os.remove("trace_riveD.shp")
                   
           
            self.fichier_log.write("    Projection..\n")
           
            
            error = QgsVectorFileWriter.writeAsVectorFormat(trace_riveG, "trace_riveG.shp","System",None,"ESRI Shapefile")
            if error == QgsVectorFileWriter.NoError:
               #print "fichier riveG ecrit"
               self.fichier_log.write("    fichier riveG ecrit\n")
            else:
               print "Erreur lors de l'ecriture du fichier trace_riveG.shp"
               self.fichier_log.write("    Erreur lors de l'ecriture du fichier trace_riveG.shp\n")
               return
           
            layer_riveG_to_delete = QgsVectorLayer("trace_riveG.shp", "Trace_temp", "ogr")
            QgsMapLayerRegistry.instance().addMapLayer(layer_riveG_to_delete)
            self.iface.legendInterface().moveLayer(layer_riveG_to_delete,1)
           
            error = QgsVectorFileWriter.writeAsVectorFormat(trace_riveD, "trace_riveD.shp","System",None,"ESRI Shapefile")
            if error == QgsVectorFileWriter.NoError:
               #print "fichier riveD ecrit"
               self.fichier_log.write("    fichier riveD ecrit\n")
            else:
               print "Erreur lors de l'ecriture du fichier trace_riveD.shp"
               self.fichier_log.write("    Erreur lors de l'ecriture du fichier trace_riveD.shp\n")
               return
           
            layer_riveD_to_delete = QgsVectorLayer("trace_riveD.shp", "Trace_temp", "ogr")
            QgsMapLayerRegistry.instance().addMapLayer(layer_riveD_to_delete)
            self.iface.legendInterface().moveLayer(layer_riveD_to_delete,1)
            
            error = QgsVectorFileWriter.writeAsVectorFormat(self.layer_profils, "profil.shp","System",None,"ESRI Shapefile")
            if error == QgsVectorFileWriter.NoError:
               #print "fichier profil ecrit"
               self.fichier_log.write("    fichier profil ecrit\n")
            else:
               print "Erreur lors de l'ecriture du fichier trace_profil.shp"
               self.fichier_log.write("    Erreur lors de l'ecriture du fichier trace_profil.shp\n")
               return
           
            layer_profil_to_delete = QgsVectorLayer("profil.shp", "Trace_temp2", "ogr")
            QgsMapLayerRegistry.instance().addMapLayer(layer_profil_to_delete)
            self.iface.legendInterface().moveLayer(layer_profil_to_delete,1) #On le deplace dans un coin , sinon il prend il se retrouve en current_layer .. 
           
           
           
            
            #**************************************************************
            
             #*************intersection de la rive Gauche***********
            if(os.path.isfile("intersectionRG.shp")):
                os.remove("intersectionRG.shp")
            self.fichier_log.write("    Lancement de qgis:lineintersections.. (rive gauche)\n")    
            processing.runalg("qgis:lineintersections", layer_profil_to_delete,layer_riveG_to_delete,self.tab_ret_attr['Profils'],"id","intersectionRG.shp")  
            layer_tmp_rg=QgsVectorLayer("intersectionRG.shp", "point_temporaire", "ogr")
            if not layer_tmp_rg.isValid():
               print "Impossible de charger la couche de point (RG)."
               self.fichier_log.write("    Impossible de charger la couche de point (RG).")
               return
            QgsMapLayerRegistry.instance().addMapLayer(layer_tmp_rg)
            self.iface.legendInterface().moveLayer(layer_tmp_rg,1)
            
           
            
            
            #**************************************************************
            
            #*************intersection de la rive Droite***********
            if(os.path.isfile("intersectionRD.shp")):
                os.remove("intersectionRD.shp")
            self.fichier_log.write("    Lancement de qgis:lineintersections.. (rive droite)\n")    
            processing.runalg("qgis:lineintersections", layer_profil_to_delete,layer_riveD_to_delete,self.tab_ret_attr['Profils'],"id","intersectionRD.shp")  
            layer_tmp_rd=QgsVectorLayer("intersectionRD.shp", "point_temporaire", "ogr")
            if not layer_tmp_rg.isValid():
               print "Impossible de charger la couche de point (RG)."
               self.fichier_log.write("    Impossible de charger la couche de point (RD).")
               return
            QgsMapLayerRegistry.instance().addMapLayer(layer_tmp_rd)
            self.iface.legendInterface().moveLayer(layer_tmp_rd,1)
            
            
            #**************************************************************
            layer_choisi.startEditing()        
            
            nb_maj_bergeG = 0
            nb_maj_bergeD = 0

            len_pts_berg_rg = 0
            
            tolerance = 1/1000.          
                        
            for f in layer_tmp_rg.getFeatures():
                
                nom_profil = f.attribute(self.tab_ret_attr['Profils'])
                pts = f.geometry().asPoint()
                #on recherche dans la couche profils , les profils à updater
                for fp in layer_choisi.getFeatures():
                     if(fp.attribute('nom')==nom_profil):
                         
                        self.fichier_log.write("        intersection entre la rive gauche et "+fp.attribute('nom')+"\n")
                        # Ok , on croise un profil :
                        
                        # On va contruire une table de Point pour le calcul de la distance entre le passage de la berge et le point 0 du profil
                        tabx = [float(x) for x in fp.attribute('x').split(',')]
                        taby = [float(y) for y in fp.attribute('y').split(',')]
                        tabz = [float(z) for z in fp.attribute('z').split(',')]
                        tabAbs = [float(a) for a in fp.attribute('abs_travers').split(',')]
                        
                        i =0
                        polyline = []
                        for x in tabx:
                            polyline.append(Point(x,taby[i],tabz[i]))
                            i = i+1
                            
                            
                        len_pts_berg_rg = tools.abcissePointSurPolyline(Point(pts.x(),pts.y()),polyline)
                        
                        tab_lit=[]                       
                        for i in range(0, len(tabx)):
                            tab_lit.append('B')
                        
                        len_pts = 0
                        bergeG = 0
                        insertion = False 
                        #if(len_pts_berg_rg>0):
                            #tab_lit.append('T')
                        #else:
                        #    tab_lit.append('B')
                        l = Polyligne(polyline)
                        absTrans = l.calculerAbcisses()
                        #print len_pts_berg_rg, absTrans[0], absTrans[-1]                                
                        for i in range(0, len(tabx)):
                        
                            if(len_pts_berg_rg!=-1 and absTrans[i]<len_pts_berg_rg):
                                #on compare la distance entre chaque point du profil et le premier , et la distance entre la berge et le premier point du profil
                                #len_pts_berg<len_pts = rive 
                                tab_lit[i]='T'                                
                            else:
                                if(bergeG == 0):
                                    bergeG = i
                                    erreur = l.longueur()*tolerance
                                    if(abs(absTrans[i]-len_pts_berg_rg)>erreur):
                                        insertion = True                                        
                                tab_lit[i]='B'                       

                        if(insertion):
                            pg = l.pointAbcissseSurPolyline(len_pts_berg_rg)
                            #pg.pprint("insertion :"+str(len_pts_berg_rg)+" "+str(bergeG))
                            #print "insertion :",len_pts_berg_rg,bergeG
                            tabx.insert(bergeG,pg.x)
                            taby.insert(bergeG,pg.y)
                            tabz.insert(bergeG,pg.z)
                            tabAbs.insert(bergeG, len_pts_berg_rg)
                            tab_lit.insert(bergeG,'B')
                               
                        #print "G",len(tabAbs),len(tab_lit),len(tabx),tab_lit[bergeG],tabAbs[bergeG]
                        #print tab_lit                        
                        fp.setAttribute('lit',','.join([lit for lit in tab_lit]))                                               
                        fp.setAttribute('x',','.join([str(x) for x in tabx]))
                        fp.setAttribute('y',','.join([str(y) for y in taby]))
                        fp.setAttribute('z',','.join([str(z) for z in tabz]))
                        fp.setAttribute('abs_travers',','.join([str(a) for a in tabAbs]))
                         
                        layer_choisi.updateFeature(fp)
                        nb_maj_bergeG =nb_maj_bergeG+1
                        break;
            layer_choisi.commitChanges()
            
            layer_choisi.startEditing()
                        
            for f in layer_tmp_rd.getFeatures():
                nom_profil = f.attribute(self.tab_ret_attr['Profils'])
                pts = f.geometry().asPoint()
                
                #on recherche dans la couche profils , les profils à updater
                for fp in layer_choisi.getFeatures():
                    
                    if(fp.attribute('nom')==nom_profil):
                        # Ok , on croise un profil :
                        self.fichier_log.write("        intersection entre la rive droite et "+fp.attribute('nom')+"\n")
                        # On va contruire une table de Point pour le calcul de la distance entre le passage de la berge et le point 0 du profil
                        tabx = [float(x) for x in fp.attribute('x').split(',')]
                        taby = [float(y) for y in fp.attribute('y').split(',')]
                        tabz = [float(z) for z in fp.attribute('z').split(',')]
                        tabAbs = [float(a) for a in fp.attribute('abs_travers').split(',')]
                        
                        #self.fichier_log.write("        => x:"+str(fp.attribute('x'))+" y:"+str(fp.attribute('y'))+"\n")
                        
                        #tablit_now = [str(l) for l in fp.attribute('lit').split(',')]
                        tab_lit = [str(l) for l in fp.attribute('lit').split(',')]
                                       
                        i =0
                        polyline = []
                        for x in tabx:
                            polyline.append(Point(x,taby[i],tabz[i]))
                            i = i+1
                            
                            
                        len_pts_berg = tools.abcissePointSurPolyline(Point(pts.x(),pts.y()),polyline)
                        
                        bergeD = 0
                        insertion = False                        
                        l = Polyligne(polyline)
                        p = l.pointAbcissseSurPolyline(len_pts_berg)
                        absTrans = l.calculerAbcisses()
 
                        for i in range(0, len(tabx)):
                            if(len_pts_berg!=-1 and absTrans[i]>=len_pts_berg):                                
                                #on compare la distance entre chaque point du profil et le premier , et la distance entre la berge et le premier point du profil
                                #len_pts_berg<len_pts = rive                                 
                                if(bergeD == 0):
                                    bergeD = i
                                    erreur = l.longueur()*tolerance
                                    if(abs(absTrans[i]-len_pts_berg)>erreur):
                                        insertion = True                                        
                                tab_lit[i]='T'                               
                        
                        if(insertion):
                            tabx.insert(bergeD,p.x)
                            taby.insert(bergeD,p.y)
                            tabz.insert(bergeD,p.z)
                            tab_lit.insert(bergeD,'B')
                            tabAbs.insert(bergeD,len_pts_berg)
                           
                        #print "D",len(tabAbs),len(tab_lit),len(tabx),tab_lit[bergeD],tabAbs[bergeD]
                        #print tab_lit
                        fp.setAttribute('lit',','.join([lit for lit in tab_lit]))                                               
                        fp.setAttribute('x',','.join([str(x) for x in tabx]))
                        fp.setAttribute('y',','.join([str(y) for y in taby]))
                        fp.setAttribute('z',','.join([str(z) for z in tabz]))
                        fp.setAttribute('abs_travers',','.join([str(a) for a in tabAbs]))
                         
                        layer_choisi.updateFeature(fp)
                        nb_maj_bergeD =nb_maj_bergeD+1
                        break;
            
            QgsMapLayerRegistry.instance().removeMapLayers([layer_profil_to_delete.id(),layer_riveD_to_delete.id(),layer_tmp_rd.id(),layer_riveG_to_delete.id(),layer_tmp_rg.id()])
            if(os.path.isfile("intersectionRG.shp")):
                os.remove("intersectionRG.shp")
                os.remove("intersectionRG.shx")
                os.remove("intersectionRG.dbf")
                os.remove("intersectionRG.prj")
                os.remove("intersectionRG.qpj")                
            if(os.path.isfile("intersectionRD.shp")):
                os.remove("intersectionRD.shp")            
                os.remove("intersectionRD.shx")            
                os.remove("intersectionRD.dbf")            
                os.remove("intersectionRD.prj")            
                os.remove("intersectionRD.qpj")            
            if(os.path.isfile("profil.shp")):
                os.remove("profil.shp")
                os.remove("profil.shx")
                os.remove("profil.dbf")
                os.remove("profil.prj")
                os.remove("profil.qpj")
            if(os.path.isfile("trace_riveG.shp")):
                os.remove("trace_riveG.shp")
                os.remove("trace_riveG.shx")
                os.remove("trace_riveG.dbf")
                os.remove("trace_riveG.prj")
                os.remove("trace_riveG.qpj")
            if(os.path.isfile("trace_riveD.shp")):
                os.remove("trace_riveD.shp")
                os.remove("trace_riveD.shx")
                os.remove("trace_riveD.dbf")
                os.remove("trace_riveD.prj")
                os.remove("trace_riveD.qpj")
            
            layer_choisi.commitChanges()
            self.fichier_log.write("   Projection terminee\n")
            self.fichier_log.close() 
            
            QMessageBox.information(None, "Intersection", str(nb_maj_bergeG)+unicode(" profil(s) mis à jour (berge gauche) \n","utf-8")+str(nb_maj_bergeD)+unicode(" profil(s) mis à jour (berge droite)\nFichier de log écrit dans ","utf-8")+self.path_log, QMessageBox.Ok)                      
                                      
       