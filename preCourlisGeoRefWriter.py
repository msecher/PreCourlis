# -*- coding: utf-8 -*-
from qgis.core import *
from PyQt4.QtCore import QVariant
import os, math

from preCourlisTools import preCourlisTools , Point
from preCourlisLayersChooser import preCourlisLayersChooser
from PyQt4.QtCore import QVariant,QPyNullVariant 
'''
Created on 26 janv. 2015

@author: quarre
'''

class preCourlisGeoRefWriter():
    
    
    def __init__(self, iface):
        """
        
        """
        self.iface = iface
        self.tools = preCourlisTools()
        

    def writeGeo(self, filename, layer_profil,bief):
        """
        """
        fileExtension = os.path.splitext(filename)[1]
        
        
        root = QgsProject.instance().layerTreeRoot()
        
        if(fileExtension == '.geo' or fileExtension == '.georef' or fileExtension == '.geoC' or fileExtension == '.georefC'):
                fichier = open(filename, "w")
            # for bief in self.list_bief:
                

                
                for profil in layer_profil.getFeatures():
                    
                    
                    
                    
                    tabx = [float(x) for x in profil.attribute('x').split(',')]
                    taby = [float(y) for y in profil.attribute('y').split(',')]
                    tabz = [float(z) for z in profil.attribute('z').split(',')]
                    
                    tabz_sedi = []
                    if(not profil.attribute('liste_couche_sediment') is None and not isinstance(profil.attribute('liste_couche_sediment'),QPyNullVariant)):
                        for couche_sedi in profil.attribute('liste_couche_sediment').split(','):
                            tabz_sedi.append([str(l) for l in profil.attribute('couche_sedi_' + couche_sedi).split(',')]) 
                    
                    # abs curv du point de l'axe d'ecoulement
                    
                    intersection_axe = profil.attribute('intersection_axe').split(' ')
                   
                    if(fileExtension == '.geo' or fileExtension == '.geoC'):
                        fichier.write("Profil " + bief + " " + profil.attribute('nom') + " " + str(profil.attribute('abscisse_axe_hydr')) + '\n')
                    if(fileExtension == '.georef' or fileExtension == '.georefC'):
                        fichier.write("Profil " + bief + " " + profil.attribute('nom') + " " + str(profil.attribute('abscisse_axe_hydr')) + " " + str(tabx[0]) + " " + str(taby[0]) + " " + str(tabx[len(tabx) - 1]) + " " + str(taby[len(taby) - 1]) + " AXE " + str(intersection_axe[0]) + " " + str(intersection_axe[1]) + "\n")
                   
                    i = 0 
                    
                    tablit = [lit for lit in profil.attribute('lit').split(',')]
                    for abs in [float(l) for l in profil.attribute('abs_travers').split(',')]:
                        if(fileExtension == '.geo'):
                            fichier.write(str(abs) + " " + str(tabz[i]) + " " + tablit[i] + "\n")
                        if(fileExtension == '.georef'):
                            fichier.write(str(abs) + " " + str(tabz[i]) + " " + tablit[i] + " " + str(tabx[i]) + " " + str(taby[i]) + "\n")
                        if(fileExtension == '.geoC'):
                            fichier.write(str(abs) + " " + str(tabz[i]))
                            for c in tabz_sedi:
                                fichier.write(" " + c[i])
                            fichier.write(" " + tablit[i] + "\n") 
                        if(fileExtension == '.georefC'):
                            fichier.write(str(abs) + " " + str(tabz[i]))
                            for c in tabz_sedi:                                                             
                                fichier.write(" " + c[i])
                            fichier.write(" " + tablit[i] + " " + str(tabx[i]) + " " + str(taby[i]) + "\n")   
                        i = i + 1
                        
                fichier.close()
                
    def  writeShapeFile(self, fileName, layer_profil):
        
        		  
        
                  # creation d'une couche temporaire
                  
                  layer_tmp = QgsVectorLayer("multipoint", "export shape", "memory")
                  if not layer_tmp.isValid():
                      print "Impossible de charger la couche de point avec valeur."
                      return
                  QgsMapLayerRegistry.instance().addMapLayer(layer_tmp)
                  
                  
                  pr = layer_tmp.dataProvider()
                  pr.addAttributes([ QgsField("nom", QVariant.String), QgsField("absAxeHydr", QVariant.Double), QgsField("x", QVariant.Double), QgsField("y", QVariant.Double), QgsField("z", QVariant.Double), QgsField("lit", QVariant.String), QgsField("absTravers", QVariant.Double)])
    
                  
        
                  
                  
                 
                  
                  profils = layer_profil.getFeatures()
                  
                  for profil in profils:
                      
                      nom = profil.attribute("nom")
                      tab_x = [float(x) for x in profil.attribute('x').split(',')]
                      tab_y = [float(y) for y in profil.attribute('y').split(',')]
                      tab_z = [float(z) for z in profil.attribute('z').split(',')]
                      tab_lit = [str(z) for z in profil.attribute('lit').split(',')]
                      tab_abs = [float(z) for z in profil.attribute('abs_travers').split(',')]
                      abs_axe = float(profil.attribute('abscisse_axe_hydr'))

                      i = 0
                      tab_Z = {}
                      if(i==0):
                          j=0
                          if(not profil.attribute('liste_couche_sediment') is None and not isinstance(profil.attribute('liste_couche_sediment'),QPyNullVariant)):
                              for couche_sedi in profil.attribute('liste_couche_sediment').split(','):
                                  #pr.addAttributes([ QgsField("z"+str(j+1), QVariant.Double)])
                                  #tab_Z["z"+str(j+1)] =  [float(l) for l in profil.attribute('couche_sedi_'+couche_sedi).split(',')]
                                  pr.addAttributes([ QgsField(couche_sedi, QVariant.Double)])
                                  tab_Z[couche_sedi] =  [float(l) for l in profil.attribute('couche_sedi_'+couche_sedi).split(',')]
                                  j=j+1
                          layer_tmp.startEditing()
                      
                      for pt_x in tab_x:
                          fields = layer_tmp.pendingFields()
              
                          fet = QgsFeature()
                          fet.setFields(fields, True)
                          
                          fet.setGeometry(QgsGeometry.fromPoint(QgsPoint(float(tab_x[i]), float(tab_y[i]))))
                          fet.setAttribute('nom', nom.strip(" "))    
                          fet.setAttribute('absAxeHydr', abs_axe)                                             
                          fet.setAttribute('x', tab_x[i])
                          fet.setAttribute('y', tab_y[i])
                          fet.setAttribute('z', tab_z[i])
                          fet.setAttribute('lit', tab_lit[i].strip(" "))
                          fet.setAttribute('absTravers', tab_abs[i])
                          j=0  
                          if(not profil.attribute('liste_couche_sediment') is None and not isinstance(profil.attribute('liste_couche_sediment'),QPyNullVariant)):
                              for couche_sedi in profil.attribute('liste_couche_sediment').split(','):
                                  #fet.setAttribute("z"+str(j+1), tab_Z["z"+str(j+1)][i]) 
                                  fet.setAttribute(couche_sedi, tab_Z[couche_sedi][i]) 
                                  j=j+1                 
                         # fet.setAttribute('intersection_axe',str(tab_attribute_X[ind])+" "+str(tab_attribute_Y[ind])+" M") 
                          
                          pr.addFeatures([ fet ])
                          i= i+1
                          
                          
                  layer_tmp.commitChanges()
                  #error = QgsVectorFileWriter( fileName,"CP1250", pr.fields(),pr.geometryType(),pr.crs() , "ESRI Shapefile")
                  error = QgsVectorFileWriter.writeAsVectorFormat(layer_tmp, fileName,"System",None,"ESRI Shapefile")
                  if error == QgsVectorFileWriter.NoError:
                      print "layer_trace_tmp.shp ecrit"       
                  else:
                      print "Erreur a l'ecriture du fichier"
                  QgsMapLayerRegistry.instance().removeMapLayer(layer_tmp.id())
                  
                  
                          
                          
                          
                          
                  
                  
               
          
