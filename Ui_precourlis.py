# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file Ui_precourlis.ui
# Created with: PyQt4 UI code generator 4.4.4
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QVariant
from PyQt4.QtGui import QPushButton,QFileDialog,QGridLayout,QMessageBox,QInputDialog

from preCourlisGeoRefParser import preCourlisGeoRefParser
from preCourlisProfilEditor import preCourlisProfilEditor
from preCourlisTraceConvert import preCourlisTraceConvert
from preCourlisRenameBief import preCourlisRenameBief
from preCourlisDeleteBief import preCourlisDeleteBief
from preCourlisTools import preCourlisTools, Point, Polyligne

import math

from qgis.core import *
import processing
import os.path
#from serial.tools.list_ports_windows import PTSTR

class Ui_precourlis(object):
    def setupUi(self, precourlis,iface):
        self.iface = iface
        self.precourlis = precourlis
        precourlis.setObjectName("PreCourlis")
        precourlis.resize(200, 100)
        precourlis.move(100,100)
        
        self.buttonBox = QtGui.QDialogButtonBox(precourlis)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        #self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        #self.buttonBox.setObjectName("buttonBox")
        self.btn_new_project = QPushButton("Nouveau projet")
        
        self.btn_new_bief = QPushButton("Ajout Bief")
        self.btn_modif_bief = QPushButton("Renom. Bief")
        self.btn_suppr_bief = QPushButton("Supp. Bief")
        
        self.btn_load_file = QPushButton("Importer un fichier .georef")
        self.btn_open_editor = QPushButton("Visualiser les profils")
        self.btn_genere_pt_pass_axe = QPushButton(unicode("Projeter l'axe hydraulique et les berges","utf-8"))
        self.btn_convertion_trace = QPushButton("Convertir les traces de profil en profils")
        self.btn_projette_pt_proche = QPushButton(unicode("Projeter des points proches sur les profils","utf-8"))

        self.retranslateUi(precourlis)
        QtCore.QObject.connect(self.btn_new_project, QtCore.SIGNAL("clicked(bool)"), self.newProjectEvent)
        QtCore.QObject.connect(self.btn_new_bief, QtCore.SIGNAL("clicked(bool)"), self.newBief)
        QtCore.QObject.connect(self.btn_modif_bief, QtCore.SIGNAL("clicked(bool)"), self.renameBief)
        QtCore.QObject.connect(self.btn_suppr_bief, QtCore.SIGNAL("clicked(bool)"), self.deleteBief)
        QtCore.QObject.connect(self.btn_load_file, QtCore.SIGNAL("clicked(bool)"), self.selectFile)
        QtCore.QObject.connect(self.btn_open_editor, QtCore.SIGNAL("clicked(bool)"), self.openEditor)
        QtCore.QObject.connect(self.btn_genere_pt_pass_axe, QtCore.SIGNAL("clicked(bool)"), self.generePointPassageAxeHydro)
        QtCore.QObject.connect(self.btn_convertion_trace, QtCore.SIGNAL("clicked(bool)"), self.launchConvertTraceToProfil)
        QtCore.QObject.connect(self.btn_projette_pt_proche, QtCore.SIGNAL("clicked(bool)"), self.projectionZpointsProche)
        
        grid = QGridLayout()
        precourlis.setLayout(grid)
        
        grid.addWidget(self.btn_new_project,0,0,1,3)
        
        grid.addWidget(self.btn_new_bief,1,0,1,1)
        grid.addWidget(self.btn_modif_bief,1,1,1,1)
        grid.addWidget(self.btn_suppr_bief,1,2,1,1)
        
        grid.addWidget(self.btn_load_file,2,0,1,3)
        grid.addWidget(self.btn_open_editor,3,0,1,3)        
        grid.addWidget(self.btn_convertion_trace,4,0,1,3)
        grid.addWidget(self.btn_genere_pt_pass_axe,5,0,1,3)
        grid.addWidget(self.btn_projette_pt_proche,6,0,1,3)
        
        #On efface tout les groupes et couches.         
        root = QgsProject.instance().layerTreeRoot()
       
        if(len(root.children())>0):
                            
                #L'enjeu ici est d'essayer de reconstituer 'self.list_bief' sans avoir lu de fichier 
               
                if(root.findGroup("Biefs")):
                    """
                    Ici , on par de l'hypothese que c'est un projet PreCourlis qui est ouvert
                    """
                    self.list_bief = {}
                    for child in root.findGroup("Biefs").children():
                        
                        self.list_bief[child.name()]={}
                        
                        for layer in child.findLayers():                           
                        
                            if(layer.layerName()=='Profils'):
                                self.list_bief[child.name()]['profil'] = layer.layer()                            
                            
                    
                    self.group_layer_entity = 0 
                    self.group_layer_alti = 1                       
                    self.group_layer_biefs =  2
              
                            
                
                return
        
        self.list_bief = {}
        self.group_layer_entity = self.iface.legendInterface().addGroup(unicode('Entité 1D',"utf-8"))
        self.group_layer_alti = self.iface.legendInterface().addGroup(unicode('Données altimétriques',"utf-8"))        
        #self.default_bief_group_entity = self.iface.legendInterface().addGroup(unicode("Traces_Bief_default","utf-8"),True,self.group_layer_entity)
        
        self.group_layer_biefs = self.iface.legendInterface().addGroup(unicode('Biefs',"utf-8"))
        
        
        
    
    def newBief(self):
        #Ajoute un nouveau bief au projet
        nom_bief, ok = QInputDialog.getText(self.precourlis, "Nouveau bief", "Entrez un nom")
        if(nom_bief=="" or not ok):
            return    
        
        root = QgsProject.instance().layerTreeRoot()
        current_bief_group = root.findGroup(unicode("Biefs","utf-8")).addGroup(nom_bief)
        trace_current_bief_group = root.findGroup(unicode("Entité 1D","utf-8")).addGroup("Traces_"+nom_bief)
        
        
        layer_traces = QgsVectorLayer("LineString", "Traces profils", "memory")
        layer_rive_droite = QgsVectorLayer("LineString", "Rive droite", "memory")
        layer_rive_gauche = QgsVectorLayer("LineString", "Rive gauche", "memory")
        layer_axe_hydro = QgsVectorLayer("LineString", "Axe hydraulique", "memory")
        
        layer_rive_droite.startEditing()
        pr_rd = layer_rive_droite.dataProvider()
        pr_rd.addAttributes( [ QgsField("rd_id",QVariant.Int)])      
        layer_rive_droite.commitChanges()
        
        layer_rive_gauche.startEditing()
        pr_rg = layer_rive_gauche.dataProvider()
        pr_rg.addAttributes( [ QgsField("rg_id",QVariant.Int)])      
        layer_rive_gauche.commitChanges()
        
        layer_axe_hydro.startEditing()
        pr_axe = layer_axe_hydro.dataProvider()
        pr_axe.addAttributes( [ QgsField("axe_id",QVariant.Int)])      
        layer_axe_hydro.commitChanges()
        
        layer_traces.startEditing()
        pr = layer_traces.dataProvider()
        pr.addAttributes( [ QgsField("nom_profil",QVariant.String)])      
        layer_traces.commitChanges()
        
        QgsMapLayerRegistry.instance().addMapLayer(layer_axe_hydro,False)
        QgsMapLayerRegistry.instance().addMapLayer(layer_traces,False)
        QgsMapLayerRegistry.instance().addMapLayer(layer_rive_droite,False)
        QgsMapLayerRegistry.instance().addMapLayer(layer_rive_gauche,False)
        
        
        trace_current_bief_group.addLayer(layer_axe_hydro)
        trace_current_bief_group.addLayer(layer_traces)
        trace_current_bief_group.addLayer(layer_rive_droite)
        trace_current_bief_group.addLayer(layer_rive_gauche)
        self.list_bief[nom_bief]={}
        
        
    def renameBief(self):
        #Renomme un bief
        self.renameFrame = preCourlisRenameBief(self.iface,self.list_bief)
        
    def deleteBief(self):
        #Renomme un bief
        self.deleteFrame = preCourlisDeleteBief(self.iface,self.list_bief)
        
     
    def newProjectEvent(self):
        ret = QMessageBox.question(self.precourlis,"Nouveau projet",unicode("Etes-vous sûr ?","utf-8"),QMessageBox.Ok, QMessageBox.Cancel)
        if(ret==QMessageBox.Ok):
            root = QgsProject.instance().layerTreeRoot()
            for child in root.children():
                root.removeChildNode(child)
        
            layers = self.iface.legendInterface().layers()
            for layer in layers:
                QgsMapLayerRegistry.instance().removeMapLayers( layer.id() )
        
        else:
            return
        
        self.list_bief = {}
        self.group_layer_entity = self.iface.legendInterface().addGroup(unicode('Entité 1D',"utf-8"))
        self.group_layer_alti = self.iface.legendInterface().addGroup(unicode('Données altimétriques',"utf-8"))
        
           
        self.group_layer_biefs = self.iface.legendInterface().addGroup(unicode('Biefs',"utf-8"))
        
        
     
        
    def selectFile_old(self):
        filename = QFileDialog.getOpenFileName()
        if(filename==""):
            return
        list_bief_tmp = self.list_bief.copy()
        self.georefParser = preCourlisGeoRefParser(self.list_bief)
        self.georefParser.loadGeoRef(filename)
        
        #on ajoute les couches
        #QgsMapLayerRegistry.instance().addMapLayer(georefParser.get_couche_profils())
        #QgsMapLayerRegistry.instance().addMapLayer(georefParser.get_couche_axe_ecoulement())
        root = QgsProject.instance().layerTreeRoot()
        #on les deplaces dans les groupes approprié
        for bief in self.georefParser.getListBiefs():
            if(not bief in list_bief_tmp):
                #si c'est un bief que l'on n'a pas déjà importé
                #current_bief_group = self.iface.legendInterface().addGroup(unicode(bief,"utf-8"),True,self.group_layer_biefs)
                trace_current_bief_group = root.findGroup(unicode("Entité 1D","utf-8")).addGroup(unicode("Traces_"+bief,"utf-8"))
                current_bief_group = root.findGroup(unicode("Biefs","utf-8")).addGroup(unicode(bief,"utf-8"))
                
                
                layer_p = self.georefParser.list_bief[bief]['profil']
                layer_pt = self.georefParser.list_bief[bief]['trace_profil']
                layer_a = self.georefParser.list_bief[bief]['axe']
                layer_rg = self.georefParser.list_bief[bief]['rive_G']
                layer_rd = self.georefParser.list_bief[bief]['rive_D']
                QgsMapLayerRegistry.instance().addMapLayer(layer_p,False)
                QgsMapLayerRegistry.instance().addMapLayer(layer_pt,False)
                QgsMapLayerRegistry.instance().addMapLayer(layer_a,False)
                QgsMapLayerRegistry.instance().addMapLayer(layer_rg,False)
                QgsMapLayerRegistry.instance().addMapLayer(layer_rd,False)
                #self.iface.legendInterface().moveLayer(layer_p,current_bief_group)
                current_bief_group.addLayer(layer_p)
                trace_current_bief_group.addLayer(layer_a)
                trace_current_bief_group.addLayer(layer_rg)
                trace_current_bief_group.addLayer(layer_rd)
                trace_current_bief_group.addLayer(layer_pt)
                
        
    
    def openEditor(self):
        
        if(self.iface.mapCanvas().currentLayer()!=None) and (self.iface.mapCanvas().currentLayer().name()=='Profils'):
            
            #recherche du bief...
            b = ""
            
            root = QgsProject.instance().layerTreeRoot()
            if(root.findGroup("Biefs")):                    
                    for child in root.findGroup("Biefs").children():
                        for layer in child.findLayers():
                            if(layer.layer() == self.iface.mapCanvas().currentLayer()):
                                b = child.name()
                                break
            
            self.editor = preCourlisProfilEditor(self.iface,b)        
            self.editor.show()
        else:
            QMessageBox.critical(self.precourlis,"Erreur","Selectionnez une couche 'Profils' ! ",QMessageBox.Ok)
        
    def launchConvertTraceToProfil(self):
        
        self.l = preCourlisTraceConvert(self.iface)
        
    def retranslateUi(self, precourlis):
        precourlis.setWindowTitle(QtGui.QApplication.translate("PreCourlis", "PreCourlis", None, QtGui.QApplication.UnicodeUTF8))
        
    def generePointPassageAxeHydro(self):
        """
        """
        if(self.iface.mapCanvas().currentLayer()!=None) and (self.iface.mapCanvas().currentLayer().name()=='Profils'):
            
            root = QgsProject.instance().layerTreeRoot()
            
            layer_choisi = self.iface.mapCanvas().currentLayer()
            
            tools = preCourlisTools()
            
            #recherche du bief parent de la couche profil selectionné
            bief_choisi = ""
            list_biefs = root.findGroup(unicode("Biefs","utf-8"))
            
            for bief in list_biefs.children():
                for layer in bief.children():
                    if layer.layer() == layer_choisi:
                        bief_choisi = bief.name()
                        break
                    
            
            #recherche des trace de  l'axe hydro et des profils
            trace_profils = None
            trace_axe_hydro = None
            trace_riveG = None
            trace_riveD = None
            
            trace_biefs = root.findGroup("Traces_"+bief_choisi)
            
            for trace in trace_biefs.children():
                if(trace.layerName()=="Traces profils"):
                    trace_profils = trace.layer()
                if(trace.layerName()=="Axe hydraulique"):    
                    trace_axe_hydro = trace.layer()
                if(trace.layerName()=="Rive gauche"):    
                    trace_riveG = trace.layer()
                if(trace.layerName()=="Rive droite"):    
                    trace_riveD = trace.layer()
            
            
            if(os.path.isfile("trace_axe.shp")):
                os.remove("trace_axe.shp")
            if(os.path.isfile("trace_profil.shp")):
                os.remove("trace_profil.shp")
            if(os.path.isfile("trace_riveG.shp")):
                os.remove("trace_riveG.shp")
            if(os.path.isfile("trace_riveD.shp")):
                os.remove("trace_riveD.shp")
            if(os.path.isfile("intersection.shp")):
                os.remove("intersection.shp")
            
            error = QgsVectorFileWriter.writeAsVectorFormat(trace_axe_hydro, "trace_axe.shp","System",None,"ESRI Shapefile")
            if error == QgsVectorFileWriter.NoError:
               print "fichier axe ecrit"
            else:
               print "Erreur lors de l'ecriture du fichier trace_axe.shp"
               return
           
            #Hack pour arriver à supprimer les fichier shp , qui ont tendance à rester lockés apres un runalg
            layer_axe_to_delete = QgsVectorLayer("trace_axe.shp", "Trace_temp", "ogr")
            QgsMapLayerRegistry.instance().addMapLayer(layer_axe_to_delete)
            self.iface.legendInterface().moveLayer(layer_axe_to_delete,1) #On le deplace dans un coin , sinon il prend il se retrouve en current_layer .. 
           
            
            error = QgsVectorFileWriter.writeAsVectorFormat(trace_riveG, "trace_riveG.shp","System",None,"ESRI Shapefile")
            if error == QgsVectorFileWriter.NoError:
               print "fichier riveG ecrit"
            else:
               print "Erreur lors de l'ecriture du fichier trace_riveG.shp"
               return
           
            layer_riveG_to_delete = QgsVectorLayer("trace_riveG.shp", "Trace_temp", "ogr")
            QgsMapLayerRegistry.instance().addMapLayer(layer_riveG_to_delete)
            self.iface.legendInterface().moveLayer(layer_riveG_to_delete,1)
           
            error = QgsVectorFileWriter.writeAsVectorFormat(trace_riveD, "trace_riveD.shp","System",None,"ESRI Shapefile")
            if error == QgsVectorFileWriter.NoError:
               print "fichier riveD ecrit"
            else:
               print "Erreur lors de l'ecriture du fichier trace_riveD.shp"
               return
           
            layer_riveD_to_delete = QgsVectorLayer("trace_riveD.shp", "Trace_temp", "ogr")
            QgsMapLayerRegistry.instance().addMapLayer(layer_riveD_to_delete)
            self.iface.legendInterface().moveLayer(layer_riveD_to_delete,1)
            
            error = QgsVectorFileWriter.writeAsVectorFormat(trace_profils, "trace_profil.shp","System",None,"ESRI Shapefile")
            if error == QgsVectorFileWriter.NoError:
               print "fichier profil ecrit"
            else:
               print "Erreur lors de l'ecriture du fichier trace_profil.shp"
               return
           
            layer_profil_to_delete = QgsVectorLayer("trace_profil.shp", "Trace_temp2", "ogr")
            QgsMapLayerRegistry.instance().addMapLayer(layer_profil_to_delete)
            self.iface.legendInterface().moveLayer(layer_profil_to_delete,1) #On le deplace dans un coin , sinon il prend il se retrouve en current_layer .. 
           
            #*************intersection de l'axe d'ecoulelement******
            if(os.path.isfile("intersection.shp")):
                os.remove("intersection.shp")
                
            processing.runalg("qgis:lineintersections", layer_profil_to_delete,layer_axe_to_delete,"id","axe_id","intersection.shp")  
            layer_tmp=QgsVectorLayer("intersection.shp", "point_temporaire", "ogr")
            if not layer_tmp.isValid():
               print "Impossible de charger la couche de point."
               return
            QgsMapLayerRegistry.instance().addMapLayer(layer_tmp)
            self.iface.legendInterface().moveLayer(layer_tmp,1)
            
            
            #**************************************************************
            
             #*************intersection de la rive Gauche***********
            if(os.path.isfile("intersectionRG.shp")):
                os.remove("intersectionRG.shp")
                
            processing.runalg("qgis:lineintersections", layer_profil_to_delete,layer_riveG_to_delete,"id","rg_id","intersectionRG.shp")  
            layer_tmp_rg=QgsVectorLayer("intersectionRG.shp", "point_temporaire", "ogr")
            if not layer_tmp_rg.isValid():
               print "Impossible de charger la couche de point (RG)."
               return
            QgsMapLayerRegistry.instance().addMapLayer(layer_tmp_rg)
            self.iface.legendInterface().moveLayer(layer_tmp_rg,1)
            
           
            
            
            #**************************************************************
            
            #*************intersection de la rive Droite***********
            if(os.path.isfile("intersectionRD.shp")):
                os.remove("intersectionRD.shp")
                
            processing.runalg("qgis:lineintersections", layer_profil_to_delete,layer_riveD_to_delete,"id","rd_id","intersectionRD.shp")  
            layer_tmp_rd=QgsVectorLayer("intersectionRD.shp", "point_temporaire", "ogr")
            if not layer_tmp_rg.isValid():
               print "Impossible de charger la couche de point (RG)."
               return
            QgsMapLayerRegistry.instance().addMapLayer(layer_tmp_rd)
            self.iface.legendInterface().moveLayer(layer_tmp_rd,1)
            
            
            #**************************************************************
            layer_choisi.startEditing()
            
            
            
            nb_maj_axe = 0
            nb_maj_berge = 0
            for f in layer_tmp.getFeatures():
                nom_profil = f.attribute('nom_profil')
                pts = f.geometry().asPoint()
                print(nom_profil+" -> Axe")
                
                #on recherche dans la couche profils , les profils à updater
                for fp in layer_choisi.getFeatures():
                    if(fp.attribute('nom')==nom_profil):                                                
                        fp.setAttribute('intersection_axe',str(pts.x())+" "+str(pts.y())+" C")             
                        self.iface.mapCanvas().currentLayer().updateFeature(fp)
                        nb_maj_axe = nb_maj_axe+1
                        break;
            
            print(nb_maj_axe)            
            len_pts_berg_rg = 0           
                        
            for f in layer_tmp_rg.getFeatures():
                
                nom_profil = f.attribute('nom_profil')
                pts = f.geometry().asPoint()
                print(nom_profil+" -> rive gauche")
                #on recherche dans la couche profils , les profils à updater
                for fp in layer_choisi.getFeatures():
                     if(fp.attribute('nom')==nom_profil):
                        # Ok , on croise un profil :
                        
                        # On va contruire une table de Point pour le calcul de la distance entre le passage de la berge et le point 0 du profil
                        tabx = [float(x) for x in fp.attribute('x').split(',')]
                        taby = [float(y) for y in fp.attribute('y').split(',')]
                        
                        i =0
                        polyline = []
                        for x in tabx:
                            polyline.append(Point(x,taby[i]))
                            i = i+1
                            
                            
                        len_pts_berg_rg = tools.abcissePointSurPolyline(Point(pts.x(),pts.y()),polyline)
                        
                        tab_lit=[]
                        
                        len_pts = 0 
                        if(len_pts_berg_rg>0):
                            tab_lit.append('T')
                        else:
                            tab_lit.append('B')
                        for i in range(0, len(tabx)-1):
                            x1 = tabx[i]
                            y1 = taby[i]
                            x2 = tabx[i+1]
                            y2 = taby[i+1]
                            len_pts = math.sqrt (((x2-x1)*(x2-x1)) + ((y2-y1)*(y2-y1))) + len_pts                  
                        
                            if(len_pts_berg_rg!=-1 and len_pts<len_pts_berg_rg):
                                #on compare la distance entre chaque point du profil et le premier , et la distance entre la berge et le premier point du profil
                                #len_pts_berg<len_pts = rive 
                                tab_lit.append('T')
                                
                            else:
                                tab_lit.append('B')                       
                            
                        
                        fp.setAttribute('lit',','.join([lit for lit in tab_lit]))                                               
                         
                        layer_choisi.updateFeature(fp)
                        nb_maj_berge =nb_maj_berge+1
                        break;
            layer_choisi.commitChanges()
            
            layer_choisi.startEditing()
                        
            for f in layer_tmp_rd.getFeatures():
                nom_profil = f.attribute('nom_profil')
                pts = f.geometry().asPoint()
                
                print(nom_profil+" -> rive droite")
                #on recherche dans la couche profils , les profils à updater
                for fp in layer_choisi.getFeatures():
                    
                    if(fp.attribute('nom')==nom_profil):
                        # Ok , on croise un profil :
                        
                        # On va contruire une table de Point pour le calcul de la distance entre le passage de la berge et le point 0 du profil
                        tabx = [float(x) for x in fp.attribute('x').split(',')]
                        taby = [float(y) for y in fp.attribute('y').split(',')]
                        tablit_now = [str(l) for l in fp.attribute('lit').split(',')]
                                        
                        i =0
                        polyline = []
                        for x in tabx:
                            polyline.append(Point(x,taby[i]))
                            i = i+1
                            
                            
                        len_pts_berg = tools.abcissePointSurPolyline(Point(pts.x(),pts.y()),polyline)
                        
                        tab_lit=[]
                        len_pts = 0
                        
                        tab_lit.append(tablit_now[0]) 
                        for i in range(0, len(tabx)-1):
                            x1 = tabx[i]
                            y1 = taby[i]
                            x2 = tabx[i+1]
                            y2 = taby[i+1]
                            len_pts = math.sqrt (((x2-x1)*(x2-x1)) + ((y2-y1)*(y2-y1))) + len_pts  
                            if(len_pts_berg!=-1 and len_pts>=len_pts_berg):                                
                                #on compare la distance entre chaque point du profil et le premier , et la distance entre la berge et le premier point du profil
                                #len_pts_berg<len_pts = rive                                 
                                tab_lit.append('T')                                
                            else:                                
                                tab_lit.append(tablit_now[i])                       
                        
                           
                        
                        fp.setAttribute('lit',','.join([lit for lit in tab_lit]))                                               
                         
                        layer_choisi.updateFeature(fp)
                        nb_maj_berge =nb_maj_berge+1
                        break;
            
            QgsMapLayerRegistry.instance().removeMapLayers([layer_tmp.id(),layer_axe_to_delete.id(),layer_profil_to_delete.id(),layer_riveD_to_delete.id(),layer_tmp_rd.id(),layer_riveG_to_delete.id(),layer_tmp_rg.id()])
            if(os.path.isfile("intersection.shp")):
                os.remove("intersection.shp")
            if(os.path.isfile("intersectionRG.shp")):
                os.remove("intersectionRG.shp")
            if(os.path.isfile("intersectionRD.shp")):
                os.remove("intersectionRD.shp")
            if(os.path.isfile("trace_axe.shp")):
                os.remove("trace_axe.shp")
            if(os.path.isfile("trace_profil.shp")):
                os.remove("trace_profil.shp")
            if(os.path.isfile("trace_riveG.shp")):
                os.remove("trace_riveG.shp")
            if(os.path.isfile("trace_riveD.shp")):
                os.remove("trace_riveD.shp")
            
            layer_choisi.commitChanges()
            
            
            QMessageBox.information(None, "Intersection", str(nb_maj_axe)+unicode(" profil(s) mis à jour (passage de l'axe d'écoulement) \n","utf-8")+str(nb_maj_berge)+unicode(" profil(s) mis à jour (berges)","utf-8"), QMessageBox.Ok)                      
                                      
        else:
            QMessageBox.critical(self.precourlis,"Erreur","Selectionnez une couche 'Profils' ! ",QMessageBox.Ok)
            

       