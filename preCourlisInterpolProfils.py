# -*- coding: utf-8 -*-
'''
Created on 30 juil. 2015

@author: quarre
'''
from PyQt4.QtCore import QVariant
from PyQt4.QtGui import QInputDialog,QMessageBox
from qgis.core import *
import qgis
import os
from preCourlisTools import preCourlisTools , Point, Polyligne
from preCourlisLayersChooser import preCourlisLayersChooser 

class preCourlisInterpolProfils():
  def __init__(self,iface): 
      
    self.iface =  iface
    self.tools = preCourlisTools()  
    list_layer = [['Profils maîtres','layer_profils'], ['Lignes de contraintes','multi_layer'],['Pas longitudinal','float'],['Pas transversal','float'],['Conserver profils maîtres','checkbox']]
        
    layChooser = preCourlisLayersChooser(list_layer)
    tab_ret = {}
    self.tab_ret_attr = {}
    if layChooser.exec_():
        tab_ret = layChooser.tab_ret           
        
        self.layer_profils = self.tools.getLayerByName(tab_ret["Profils maîtres"])
        
       
        #self.layer_profils = self.tools.getLayerByName(tab_ret["Profils"])
        #if(tab_ret["Lignes de contraintes"]!='Pas de couche'):
        #    self.ligne_contraintes = self.tools.getLayerByName(tab_ret["Lignes de contraintes"])
        #else:
        #    self.ligne_contraintes = None
        self.pas_longi = float(tab_ret["Pas longitudinal"])
        self.pas_transv = float(tab_ret["Pas transversal"])
        self.conserv_prof_maitre = tab_ret["Conserver profils maîtres"] 
        
        
        
    else:
            return 
    
    root = QgsProject.instance().layerTreeRoot()    
        
    tab_pts_profils = []
    tab_nom_profils = []
    tab_axe_profils = []  
    tab_list_cont = []
    abslongi = []
    
    for f in self.layer_profils.getFeatures():
        
        #Contruction du tableau d'entrée pour les points des profils et des point de passage de l'axe
        tabz = [float(z) for z in f.attribute('z').split(',')]
        taby = [float(y) for y in f.attribute('y').split(',')]
        tabx = [float(x) for x in f.attribute('x').split(',')]
        
        tab_pts_profil = []
        i = 0
        for x in tabx:
            tab_pts_profil.append(Point(x,taby[i],tabz[i]))
            i = i+1
            
        tab_pts_profils.append(tab_pts_profil)        
        tab_nom_profils.append(f.attribute('nom'))
        tab_axe_profils.append(Point(float(f.attribute('intersection_axe').split(' ')[0]),float(f.attribute('intersection_axe').split(' ')[1])))
        abslongi.append(f.attribute('abscisse_axe_hydr'))
    
    geom=None
    #if(self.ligne_contraintes!=None):
    for name_ligne_cont in tab_ret["Lignes de contraintes"]:           
        
        layer_cont = self.tools.getLayerByName(name_ligne_cont)
        for axe in layer_cont.getFeatures():
            geom= axe.geometry()
            pts = geom.asPolyline() 
            
            tab_pts = []
            for pt in pts:                    
               tab_pts.append(Point(pt.x(),pt.y()))
    
            tab_list_cont.append(tab_pts)

    
    #print(tab_list_cont)
    #on genere les nouveau profils
    nom,ok = QInputDialog.getText(None,"Couche de destination","Entrez un nom")
    
    #abs longitudinale du 1er profil de reference
    abs0 = abslongi[0]

    
    
    if(ok):
        
          self.layer_profils_interp = QgsVectorLayer("LineString",nom, "memory")
          
          self.path_log = os.path.dirname(os.path.abspath(self.layer_profils_interp.source()))+"/"+nom+".log"
          self.fichier_log = open(self.path_log, "w")
          
          self.fichier_log.write("-- Interpolation de profils -- \n")
          self.fichier_log.write("\n")
          
          self.fichier_log.write("    Pas longitudinal : "+str(self.pas_longi)+"\n")
          self.fichier_log.write("    Pas transversal : "+str(self.pas_transv)+"\n")
          self.fichier_log.write("    Ligne de contrainte : "+str(tab_ret["Lignes de contraintes"])+"\n")
          self.fichier_log.write("    Profils maitres : "+tab_ret["Profils maîtres"]+"\n")          
          self.fichier_log.write("    Conserver profils maitres : "+("oui" if tab_ret["Conserver profils maîtres"]==True else "non")+"\n\n")
          
          self.layer_profils_interp.startEditing()
          pr_profil =  self.layer_profils_interp.dataProvider()
          pr_profil.addAttributes( [ QgsField("nom",QVariant.String),QgsField("x",QVariant.String), QgsField("y",QVariant.String),QgsField("z",QVariant.String),QgsField("lit",QVariant.Int),QgsField("intersection_axe",QVariant.String),QgsField("abscisse_axe_hydr",QVariant.String),QgsField("liste_couche_sediment",QVariant.String),QgsField("liste_couche_sediment_couleur",QVariant.String),QgsField("abs_travers",QVariant.String)])               
          self.layer_profils_interp.commitChanges()
          QgsMapLayerRegistry.instance().addMapLayer(self.layer_profils_interp,False)
          root.addLayer(self.layer_profils_interp)
          self.fichier_log.write("    Interpolation...\n")
          [profilsInterp, erreur] = self.tools.interpolerProfils(tab_pts_profils, tab_nom_profils, tab_list_cont, tab_axe_profils, abslongi, self.pas_longi, self.pas_transv, self.conserv_prof_maitre)
          
          #print "nbProfils :", len(profilsInterp)
          self.layer_profils_interp.startEditing()
          
          
          if(erreur==0):
              i=0
              for prof_int in profilsInterp:
                  
                  tab_pts = prof_int[0]
                  tab_nom = prof_int[1]
                  tab_axe = prof_int[2]
                  
                  abs = prof_int[3] + abs0
                  
                  #print i, tab_nom
                  
                  tab_x_int = []
                  tab_y_int = []
                  tab_z_int = []
                  tab_lit_int = []
                  list_point =[]
                  
    
                  
                  polyline = []
                  for pt in tab_pts:
                      tab_x_int.append(pt.x)
                      tab_y_int.append(pt.y)
                      tab_z_int.append(pt.z)
                      tab_lit_int.append('B')
                      polyline.append(Point(pt.x,pt.y,pt.z))
                      point = QgsPoint(pt.x,pt.y)
                      list_point.append(point)
                      
    
                  l = Polyligne(polyline)
                  tab_attribute_abstrav = l.calculerAbcisses()
    
                  point_passage_axe =  str(tab_axe.x)+" "+str(tab_axe.y)+" C" 
                      
                  fields = self.layer_profils_interp.pendingFields()
                  
                  fet = QgsFeature()
                  fet.setFields(fields, True)
                  fet.setGeometry(QgsGeometry.fromPolyline(list_point))
                  fet.setAttribute('nom', tab_nom)
                  self.fichier_log.write("        "+tab_nom+"\n")
                  fet.setAttribute('x', ','.join([str(x) for x in tab_x_int]))
                  fet.setAttribute('y', ','.join([str(y) for y in tab_y_int]))
                  fet.setAttribute('z', ','.join([str(z) for z in tab_z_int]))
                  fet.setAttribute('lit', ','.join([lit for lit in tab_lit_int]))
                  fet.setAttribute('intersection_axe', point_passage_axe)
                  fet.setAttribute('abscisse_axe_hydr', abs)
                  fet.setAttribute('abs_travers', ','.join([str(a) for a in tab_attribute_abstrav]))
                  
                  pr_profil.addFeatures([ fet ])
                  
                  i = i+1
                  
              self.layer_profils_interp.commitChanges()     
         
          else:
             print("Erreur dans l'interpolation des profils !")
             self.fichier_log.write("        Erreur dans l'interpolation des profils !\n") 
             
          self.fichier_log.write("    Interpolation terminee\n")
          self.fichier_log.close()
          QMessageBox.information(None, unicode("Interpolation terminée", "utf-8"), unicode("Fichier de log écrit dans ", "utf-8")+self.path_log,QMessageBox.Ok)  
