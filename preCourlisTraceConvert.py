# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui 
import numpy as np
from PyQt4.QtGui import QComboBox,QPushButton,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QLineEdit,QInputDialog,QMessageBox
from PyQt4.QtCore import QVariant
from qgis.core import *
import qgis
import processing
import os.path
import math
import copy
from qgis.analysis import QgsGeometryAnalyzer
from shapely.geometry import LineString
from preCourlisTools import preCourlisTools , Point, Polyligne
from preCourlisLayersChooser import preCourlisLayersChooser 


# create the dialog for precourlis
class preCourlisTraceConvert():
  def __init__(self,iface): 
      
    self.iface =  iface
    self.tools = preCourlisTools()  
    list_layer = [['Traces','layer_vector','Nom'], ['MNT','layer_raster'],['Axe','layer_vector_1'],['Nom = abcisse profil sur axe','checkbox']]
        
    layChooser = preCourlisLayersChooser(list_layer)
    tab_ret = {}
    self.tab_ret_attr = {}
    if layChooser.exec_():
        tab_ret = layChooser.tab_ret           
        self.tab_ret_attr = layChooser.tab_ret_attr  
        #print(self.tab_ret_attr)  
        self.layer_traces = self.tools.getLayerByName(tab_ret["Traces"])
        #self.layer_profils = self.tools.getLayerByName(tab_ret["Profils"])
        self.mnt = self.tools.getLayerByName(tab_ret["MNT"])
        self.axe = self.tools.getLayerByName(tab_ret["Axe"])
        self.nomAbcisseProfilSurAxe = tab_ret["Nom = abcisse profil sur axe"]
        #print self.nomAbcisseProfilSurAxe 
    else:
            return  
      
    
    
    
    self.layer_a_completer = None
    
    
    root = QgsProject.instance().layerTreeRoot()
    
    while True:
        num_pts,ok = QInputDialog.getText(None,"Distance","Distance maxi entre les points d'un profil")
    
        if(self.tools.check_if_not_numeric(num_pts)):
            QMessageBox.critical(None, unicode("Erreur", "utf-8"), unicode("La distance doit être un nombre", "utf-8"),QMessageBox.Ok)
        else:
            break
    
    if(ok):
          self.distance=num_pts
 
    while True:
        val,ok = QInputDialog.getText(None,"Distance","Abcisse du 1er profil")
    
        if(self.tools.check_if_not_numeric(num_pts)):
            QMessageBox.critical(None, unicode("Erreur", "utf-8"), unicode("L'abcisse du 1er profil doit être un nombre", "utf-8"),QMessageBox.Ok)
        else:
            break
    
    self.absc0=0
    if(ok):
        self.absc0=val
        
                   
    nom,ok = QInputDialog.getText(None,"Couche de destination","Entrez un nom")
    if(ok):
          
          self.layer_profils = QgsVectorLayer("LineString",nom, "memory")
          self.layer_profils.startEditing()
          pr_profil =  self.layer_profils.dataProvider()
          pr_profil.addAttributes( [ QgsField("nom",QVariant.String),QgsField("x",QVariant.String), QgsField("y",QVariant.String),QgsField("z",QVariant.String),QgsField("lit",QVariant.Int),QgsField("intersection_axe",QVariant.String),QgsField("abscisse_axe_hydr",QVariant.String),QgsField("liste_couche_sediment",QVariant.String),QgsField("liste_couche_sediment_couleur",QVariant.String),QgsField("abs_travers",QVariant.String)] )               
          self.layer_profils.commitChanges()
          QgsMapLayerRegistry.instance().addMapLayer(self.layer_profils,False)
          root.addLayer(self.layer_profils)
    
    
    
    # Creation d'un fichier de log
    self.path_log = os.path.dirname(os.path.abspath(self.layer_profils.source()))+"/"+nom+".log"
    self.fichier_log = open(self.path_log, "w")

    self.fichier_log.write("-- Conversion des traces de profils en profils-- \n")
    self.fichier_log.write("\n")
    self.fichier_log.write("    Traces utilisees : "+tab_ret["Traces"]+"\n")
    self.fichier_log.write("    MNT : "+tab_ret["MNT"]+"\n")
    self.fichier_log.write("    Axe hydraulique : "+tab_ret["Axe"]+"\n")
    self.fichier_log.write("    Distance maxi entre les points d'un profil: "+num_pts+"\n")
    self.fichier_log.write("    Couche profils de destination : "+nom+"\n")
    
    
    ########        
    self.conversion()
    
    
    
  def ajoutBief(self):
      nomBief,ok = QInputDialog.getText(self,"Nouveau bief","Entrez un nom")
      if(ok):
          #Nouveau bief , on lui crée une couche profils
          numg = self.iface.legendInterface().addGroup(nomBief,True,2)
          layer=QgsVectorLayer("LineString", "Profils", "memory")
          QgsMapLayerRegistry.instance().addMapLayer(layer)
          self.iface.legendInterface().moveLayer(layer,numg)
          
          #couche temporaire pour l'axe d'ecoulement , pour faire fonctionner l'editeur de profil.. Dans le futur on le choisira dans le calque 1D
          axe =QgsVectorLayer("LineString", "Axe hydraulique", "memory")
          QgsMapLayerRegistry.instance().addMapLayer(axe)
          self.iface.legendInterface().moveLayer(axe,numg)

  def getLayerByName(self, layerName ,type=0):
      layerMap = QgsMapLayerRegistry.instance().mapLayers()
      for name, layer in layerMap.iteritems():
        #print(layer.name(),layer.type())
        if layer.type() == type  and layer.name() == layerName:
          if layer.isValid():            
            return layer
          else:
           
            return None

          
  def conversion(self):
      
      self.fichier_log.write("\n")
      self.fichier_log.write("    Début de conversion ...\n")
      
      root = QgsProject.instance().layerTreeRoot()
      
      #layer_trace = self.getLayerByName(self.trace1D.currentText(),QgsMapLayer.VectorLayer)
      layer_trace = self.layer_traces
                  

      layer_axe = self.axe
            
      geom=None
      for axe in layer_axe.getFeatures():
        geom= axe.geometry()
        pts = geom.asPolyline()

      polyline1 = []                
      points1 = []
      for pt in pts:                    
          polyline1.append([pt.x(),pt.y()])
          points1.append(Point(pt.x(),pt.y()))                  
      
      lsAxe = LineString(polyline1)
      #print lsAxe
      plAxe = Polyligne(points1)
      plAxe.pprint()

      working_dir = os.path.dirname(os.path.abspath(layer_trace.source()))
      self.fichier_log.write("        Repertoire de travail : "+working_dir+"\n")
      
      #On supprime les fichiers MesPoints si il existe.
      if(os.path.isfile(working_dir+"\\MesPoints.shp")):
          os.remove(working_dir+"\\MesPoints.shp")
      if(os.path.isfile(working_dir+"\\MesPoints.shx")):
          os.remove(working_dir+"\\MesPoints.shx")
      if(os.path.isfile(working_dir+"\\MesPoints.prj")):
          os.remove(working_dir+"\\MesPoints.prj")
      if(os.path.isfile(working_dir+"\\MesPoints.qpj")):
          os.remove(working_dir+"\\MesPoints.qpj")
      if(os.path.isfile(working_dir+"\\MesPoints.dbf")):
          os.remove(working_dir+"\\MesPoints.dbf")
      if(os.path.isfile(working_dir+"\\layer_trace_tmp.shp")):
          os.remove(working_dir+"\\layer_trace_tmp.shp")
    
      #layer_trace_copy = QgsVectorLayer(layer_trace.source(), layer_trace.name(), layer_trace.providerType())
      #QgsMapLayerRegistry.instance().addMapLayer(layer_trace_copy)
      #self.iface.legendInterface().moveLayer(layer_trace_copy,1)
      
      
      #writer = QgsVectorFileWriter()
      error = QgsVectorFileWriter.writeAsVectorFormat(layer_trace, working_dir+"\\layer_trace_tmp.shp","System",None,"ESRI Shapefile")
      if error == QgsVectorFileWriter.NoError:
            #print "layer_trace_tmp.shp ecrit"
            self.fichier_log.write("        layer_trace_tmp.shp ecrit\n")
      
      #del writer
      #QgsGeometryAnalyzer().buffer(layer_trace, working_dir+"\\layer_trace_tmp.shp", -1, False, False, -1)
      layer_trace_to_delete=QgsVectorLayer(working_dir+"\\layer_trace_tmp.shp", "Trace_temp", "ogr")
      QgsMapLayerRegistry.instance().addMapLayer(layer_trace_to_delete)
      extent=layer_trace_to_delete.extent()
      xmax=extent.xMaximum()
      xmin=extent.xMinimum()
      ymax=extent.yMaximum()
      ymin=extent.yMinimum()
      coords = "%f,%f,%f,%f" %(xmin, xmax, ymin, ymax)

      
      self.fichier_log.write("        execution de v.to.points\n")
      processing.runalg("grass7:v.to.points", layer_trace_to_delete,self.distance,0,True,coords,False,False,0,working_dir+"\\MesPoints.shp")
      layer_tmp=QgsVectorLayer(working_dir+"\\MesPoints.shp", "point_temporaire", "ogr")
      if not layer_tmp.isValid():
          print "Impossible de charger la couche de point."
          self.fichier_log.write("       Impossible de charger la couche de point.\n")
          self.fichier_log.close()
          return
      
      
      
      QgsMapLayerRegistry.instance().addMapLayer(layer_tmp)
      self.iface.legendInterface().moveLayer(layer_tmp,1)      
      
      
      #=========================================================================
      # noerror = QgsVectorFileWriter.deleteShapeFile(working_dir+"\\layer_trace_tmp.shp")
      # if not noerror:
      #      print "Erreur a la suppresion de layer_trace_tmp.shp "
      #      self.fichier_log.write("       Erreur a la suppresion de layer_trace_tmp.shp\n ")
      #=========================================================================
      
      
       #On supprime les fichiers MesPointsZ si il existe.
      if(os.path.isfile(working_dir+"\\MesPointsZ.shp")):
          os.remove(working_dir+"\\MesPointsZ.shp")
      if(os.path.isfile(working_dir+"\\MesPointsZ.shx")):
          os.remove(working_dir+"\\MesPointsZ.shx")
      if(os.path.isfile(working_dir+"\\MesPointsZ.prj")):
          os.remove(working_dir+"\\MesPointsZ.prj")
      if(os.path.isfile(working_dir+"\\MesPointsZ.qpj")):
          os.remove(working_dir+"\\MesPointsZ.qpj")
      if(os.path.isfile(working_dir+"\\MesPointsZ.dbf")):
          os.remove(working_dir+"\\MesPointsZ.dbf")
          
      if(self.mnt!=None): 
          self.fichier_log.write("        execution de addgridvaluestopoints\n")   
#MS2018 prototypage de la fonction saga via runalg a changé entre 2.18.3 et 2.18.16 ==> 5eme parametre en plus dont l'utilite n'est pas claire (redondant avec le 4eme?)
#gestion d'erreur à intégrer : processing.runalg('saga:addgridvaluestopoints') renvoie un dictionnaire lorsqu'il fonctionne (et None sinon)
          processing.runalg('saga:addgridvaluestopoints', layer_tmp, self.mnt.source(), 0, 0,working_dir+"\\MesPointsZ.shp")
          layer_tmp2=QgsVectorLayer(working_dir+"\\MesPointsZ.shp", "point_temporaire_Z", "ogr")
          if not layer_tmp.isValid():
              print "Impossible de charger la couche de point avec valeur."
              self.fichier_log.write("       Impossible de charger la couche de point avec valeur\n ")
              return
          QgsMapLayerRegistry.instance().addMapLayer(layer_tmp2)
          self.iface.legendInterface().moveLayer(layer_tmp2,1)  
      
      # *** Copie des profils dans le bief selectionné ***
      
      # il faut d'abord retrouvé la couche profil du bief choisi (ou nouvellement crée..)
      
      #=========================================================================
      # if(self.layer_a_completer is None):
      #     
      #   for layer in root.findGroup(self.comboBief.currentText()).children():
      #         
      #             if(layer.layerName()=='Profils'):
      #                 self.layer_a_completer = layer.layer()
      #                 #on supprime toute les features pour vide la couche
      #                 self.layer_a_completer.startEditing()
      #                 for p in self.layer_a_completer.getFeatures():
      #                     self.layer_a_completer.deleteFeature(p.id())
      #                 self.layer_a_completer.commitChanges()
      #             
      # 
      # if(self.layer_a_completer is None):
      #     #Il n'y a pas de couche profils dans ce biefs , on la fait.
      #     self.layer_a_completer = QgsVectorLayer("LineString", "Profils", "memory")
      #     QgsMapLayerRegistry.instance().addMapLayer(self.layer_a_completer,False)
      #     root.findGroup(self.comboBief.currentText()).addLayer(self.layer_a_completer)
      #=========================================================================
          
      
      pr = self.layer_profils.dataProvider()
      #pr.addAttributes( [ QgsField("nom",QVariant.String),QgsField("x",QVariant.String), QgsField("y",QVariant.String),QgsField("z",QVariant.String),QgsField("lit",QVariant.Int),QgsField("intersection_axe",QVariant.String),QgsField("liste_couche_sediment",QVariant.String),QgsField("liste_couche_sediment_couleur",QVariant.String)] )
    
      #pr_axe = self.layerAxe_a_completer.dataProvider()
                    
      self.layer_profils.startEditing()
      #self.layerAxe_a_completer.startEditing()
      
      #Parcours de la couche des point de la couche generé (point Z). Chaque id different genere un nouveau profil
      if(self.mnt!=None):
          points_generes = layer_tmp2.getFeatures()
      else:
          points_generes = layer_tmp.getFeatures()
          
      id_prec = "-1"
      tab_attribute_X = []
      tab_attribute_Y = []
      tab_attribute_Z = []
      tab_attribute_abstrav = []

      list_point = []
      list_point_axe = []
      tab_lit = []
      polylineProfil = []
      polylineProfil2 = []
      
      fet = None
      
      tab_fet = []
      nom_temp = 0
      for point in points_generes:
          
          id = str(point[0])
          #id = point.attribute(self.tab_ret_attr["Traces"]) #on recupere l'attribut de l'identifiant des traces
          
          
          
          if(id_prec == "-1"):
              id_prec = id
          
          Z = -9999.
          
          if(self.mnt!=None):
              if(isinstance(point.attribute(self.mnt.name()),float)):   # !='PyQt4.QtCore.QPyNullVariant'
                  Z = float(point.attribute(self.mnt.name()))
          point_geom = point.geometry().asPoint()
          X = point_geom.x()
          Y = point_geom.y()
          
          
          if(id_prec != id):
              #on commence un nouveau profil
              self.fichier_log.write("       ... profil "+id_prec+"\n")
              
              #on enregistre le profil precedent
              #Analyse du sens de definition du profil par rapport a l'axe hydraulique 
              lsProfil = LineString(polylineProfil)
              p = lsProfil.intersection(lsAxe)
              pInter = Point(p.x,p.y)
              pInter.pprint("pInter Axe hydro profil "+str(id_prec))
              
              plProfil = Polyligne(polylineProfil2)              
              sens = plProfil.orienterPolyline(plAxe, pInter)
              #print "Sens profil ",id_prec," :",sens
              
              if(sens == False):
                tab_attribute_X.reverse()    
                tab_attribute_Y.reverse()
                tab_attribute_Z.reverse()
                tab_lit.reverse()
                list_point.reverse()
               
              polyline = []
              i = 0
              for x in tab_attribute_X:
                polyline.append(Point(x,tab_attribute_Y[i],tab_attribute_Z[i]))
                i = i + 1

              l = Polyligne(polyline)
              tab_attribute_abstrav = l.calculerAbcisses()

              ind = np.argmin(tab_attribute_Z)
              fields = self.layer_profils.pendingFields()
              
              fet = QgsFeature()
              fet.setFields( fields, True )
              
              fet.setGeometry( QgsGeometry.fromPolyline(list_point))
              fet.setAttribute('nom',id_prec)                       
              fet.setAttribute('x',','.join([str(x) for x in tab_attribute_X]))
              fet.setAttribute('y',','.join([str(y) for y in tab_attribute_Y]))
              fet.setAttribute('z',','.join([str(z) for z in tab_attribute_Z]))
              fet.setAttribute('lit',','.join([lit for lit in tab_lit]))                        
              fet.setAttribute('intersection_axe',str(pInter.x)+" "+str(pInter.y)+" C")
              fet.setAttribute('abs_travers', ','.join([str(a) for a in tab_attribute_abstrav]))
              
              tab_fet.append(fet)
              #pr.addFeatures( [ fet ] )
              
              
              #En attendant les devs , on prend le plus petit Z pour le passage de l'axe d'ecoulement (plus tard on calculera l'intersection)
              
              #list_point_axe.append(QgsPoint(tab_attribute_X[ind],tab_attribute_Y[ind]))
              
              tab_attribute_X = []
              tab_attribute_Y = []
              tab_attribute_Z = []
              list_point = []
              polylineProfil = []
              polylineProfil2 = []
              tab_lit = []
              
                              
              polylineProfil.append((X,Y))
              polylineProfil2.append(Point(X,Y))
              tab_attribute_X.append(X)
              tab_attribute_Y.append(Y)
              tab_attribute_Z.append(Z)
              tab_lit.append('B')
              pts = QgsPoint(X,Y)
              list_point.append(pts)
              
              id_prec = id
              
              
               
          else:
              #ajout des points au profil courant..
              polylineProfil.append((X,Y))
              polylineProfil2.append(Point(X,Y))
              tab_attribute_X.append(X)
              tab_attribute_Y.append(Y)
              tab_attribute_Z.append(Z)
              tab_lit.append('B')
              pts = QgsPoint(X,Y)
              list_point.append(pts)
          
      #Analyse du sens par rapport au profil hydraulique
          
      
      #dernier point
      self.fichier_log.write("       ... profil "+id+"\n")
      #Analyse du sens de definition du profil par rapport a l'axe hydraulique 
      lsProfil = LineString(polylineProfil)
      plProfil = Polyligne(polylineProfil2);
      
      p = lsProfil.intersection(lsAxe)
      pInter = Point(p.x,p.y)
      #pInter.pprint("pInter Axe hydro profil "+str(id))
      sens = plProfil.orienterPolyline(plAxe, pInter)
      #print "Sens profil ",id," :",sens
      
      if(sens == False):
         tab_attribute_X.reverse()    
         tab_attribute_Y.reverse()
         tab_attribute_Z.reverse()
         tab_lit.reverse()
         list_point.reverse()
               
      polyline = []
      i = 0
      for x in tab_attribute_X:
        polyline.append(Point(x,tab_attribute_Y[i],tab_attribute_Z[i]))
        i = i + 1

      l = Polyligne(polyline)
      tab_attribute_abstrav = l.calculerAbcisses()

      fields = self.layer_profils.pendingFields()
              
      fet = QgsFeature()
      fet.setFields( fields, True )
      ind = np.argmin(tab_attribute_Z)       
      fet.setGeometry( QgsGeometry.fromPolyline(list_point))
      fet.setAttribute('nom',id)
      #print "id profil", id                     
      fet.setAttribute('x',','.join([str(x) for x in tab_attribute_X]))
      fet.setAttribute('y',','.join([str(y) for y in tab_attribute_Y]))
      fet.setAttribute('z',','.join([str(z) for z in tab_attribute_Z]))
      fet.setAttribute('lit',','.join([lit for lit in tab_lit]))                        
      fet.setAttribute('intersection_axe',str(pInter.x)+" "+str(pInter.y)+" C")       
      fet.setAttribute('abs_travers', ','.join([str(a) for a in tab_attribute_abstrav]))
      
      tab_fet.append(fet)
      
      #tab_fet_ordonnee = []
      #for key, value in self.tools.getProfilsOrdonnesFeaturesv07(layer_axe,tab_fet,self.absc0,self.nomAbcisseProfilSurAxe):
          #tab_fet_ordonnee.append(key)
                      
              
      list_abs_long = []
      for feat in tab_fet:
        intersection_axe = feat.attribute('intersection_axe').split(' ')
        list_abs_long.append(self.tools.abcissePointSurPolyline(Point(intersection_axe[0],intersection_axe[1]),points1))

      index = [i for i in range(0,len(tab_fet))]
      conv = lambda i: list_abs_long[i]
      index.sort(key=conv)

      offset = float(self.absc0) - list_abs_long[index[0]]
      tab_fet_ordonnee = []
      for i in range(0,len(index)):
        d = list_abs_long[index[i]] + offset 
        tab_fet[index[i]].setAttribute("abscisse_axe_hydr",d)
        if(self.nomAbcisseProfilSurAxe==True):
            tab_fet[index[i]].setAttribute("nom","P_"+"{:0.3f}".format(d))
          
        tab_fet_ordonnee.append(tab_fet[index[i]])
      
      
      pr.addFeatures(tab_fet_ordonnee)         
          
      self.layer_profils.commitChanges()

      
      
      if(self.mnt!=None):
          QgsMapLayerRegistry.instance().removeMapLayers([layer_tmp.id(),layer_tmp2.id(),layer_trace_to_delete.id()])
      else:
          QgsMapLayerRegistry.instance().removeMapLayers([layer_tmp.id(),layer_tmp.id(),layer_trace_to_delete.id()])
      del layer_trace
      if(os.path.isfile(working_dir+"\\MesPoints.shp")):
          os.remove(working_dir+"\\MesPoints.shp")
      if(os.path.isfile(working_dir+"\\MesPoints.shx")):
          os.remove(working_dir+"\\MesPoints.shx")
      if(os.path.isfile(working_dir+"\\MesPoints.prj")):
          os.remove(working_dir+"\\MesPoints.prj")
      if(os.path.isfile(working_dir+"\\MesPoints.qpj")):
          os.remove(working_dir+"\\MesPoints.qpj")
      if(os.path.isfile(working_dir+"\\MesPoints.dbf")):
          os.remove(working_dir+"\\MesPoints.dbf")
      
      if(os.path.isfile(working_dir+"\\MesPointsZ.mshp")):
          os.remove(working_dir+"\\MesPointsZ.mshp")
      if(os.path.isfile(working_dir+"\\MesPointsZ.shp")):
          os.remove(working_dir+"\\MesPointsZ.shp")
      if(os.path.isfile(working_dir+"\\MesPointsZ.shx")):
          os.remove(working_dir+"\\MesPointsZ.shx")
      if(os.path.isfile(working_dir+"\\MesPointsZ.prj")):
          os.remove(working_dir+"\\MesPointsZ.prj")
      if(os.path.isfile(working_dir+"\\MesPointsZ.qpj")):
          os.remove(working_dir+"\\MesPointsZ.qpj")
      if(os.path.isfile(working_dir+"\\MesPointsZ.dbf")):
          os.remove(working_dir+"\\MesPointsZ.dbf")
      if(os.path.isfile(working_dir+"\\layer_trace_tmp.shp")):
          os.remove(working_dir+"\\layer_trace_tmp.shp")
          os.remove(working_dir+"\\layer_trace_tmp.shx")
          os.remove(working_dir+"\\layer_trace_tmp.prj")
          os.remove(working_dir+"\\layer_trace_tmp.dbf")
          os.remove(working_dir+"\\layer_trace_tmp.qpj")
          
      
      
          
      #self.close()
      self.fichier_log.write("    Fin de conversion \n")
      self.fichier_log.close()
      
      QMessageBox.information(None, unicode("Conversion terminée", "utf-8"), unicode("Fichier de log écrit dans ", "utf-8")+self.path_log,QMessageBox.Ok)
      self.layer_profils = None
      #self.layerAxe_a_completer.commitChanges()
        
          
      
      
          
      
      
      