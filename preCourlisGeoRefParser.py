# -*- coding: utf-8 -*-
from qgis.core import *
from PyQt4.QtCore import QVariant
from PyQt4.QtGui import QFileDialog,QInputDialog,QMessageBox
from PyQt4.QtCore import QVariant

import os, math
from preCourlisLayersChooser import preCourlisLayersChooser
from preCourlisTools import preCourlisTools,Point,Polyligne
from fileinput import filename


class preCourlisGeoRefParser():
    
    def __init__(self):
        
        self.layer_traces = None
        self.layer_axe = None
        self.layer_profils = None
        self.layer_rg = None
        self.layer_rd = None
        self.tools = preCourlisTools()
        
        # self.list_bief = biefs
        # self.layer_trace_profil = ltp
        # self.layer_trace_berge = ltb
        # self.layer_trace_axe_hydro = ltah
        
        
    def getListBiefs(self):
        """Retourne la liste des biefs lus et leur contenu"""
        return self.list_bief
    
    
    def selectFile(self):  
        
        filename = QFileDialog.getOpenFileName()
        if(filename == ""):
            return 
        
        root = QgsProject.instance().layerTreeRoot()    
        nom,ok = QInputDialog.getText(None,"Bief","Entrez un nom de bief")
        if(ok):
              
              biefgroup= root.insertGroup(0,nom)  
          
              self.layer_profils = QgsVectorLayer("LineString","Profils", "memory")
              
              self.path_log = os.path.dirname(os.path.abspath(self.layer_profils.source()))+"\\"+nom+".log"
              self.fichier_log = open(self.path_log, "w")
              
              self.fichier_log.write("-- Import d'un fichier geoRef -- \n")
              self.fichier_log.write("\n")
              self.fichier_log.write("    Fichier d'import : "+filename+"\n")
              self.fichier_log.write(("    Bief cree : "+nom+"\n").encode('utf-8'))
              
              self.layer_profils.startEditing()
              pr_profil =  self.layer_profils.dataProvider()
              pr_profil.addAttributes( [ QgsField("nom",QVariant.String),QgsField("x",QVariant.String), QgsField("y",QVariant.String),QgsField("z",QVariant.String),QgsField("lit",QVariant.Int),QgsField("intersection_axe",QVariant.String),QgsField("abscisse_axe_hydr",QVariant.String),QgsField("liste_couche_sediment",QVariant.String),QgsField("liste_couche_sediment_couleur",QVariant.String),QgsField("abs_travers",QVariant.String)])               
              self.layer_profils.commitChanges()
              QgsMapLayerRegistry.instance().addMapLayer(self.layer_profils,False)              
              biefgroup.addLayer(self.layer_profils)
        
              self.layer_traces = QgsVectorLayer("LineString","Traces", "memory")
              self.layer_traces.startEditing()
              pr_trace =  self.layer_traces.dataProvider()
              pr_trace.addAttributes( [ QgsField("nom_profil",QVariant.String)] )
              self.layer_traces.commitChanges()
              QgsMapLayerRegistry.instance().addMapLayer(self.layer_traces,False)
              biefgroup.addLayer(self.layer_traces)
        
          
              self.layer_axe = QgsVectorLayer("LineString","Axe hydraulique", "memory")
              self.layer_axe.startEditing()
              pr_axe =  self.layer_axe.dataProvider()
              #pr_axe.addAttributes( [ QgsField("axe_id",QVariant.Int)] )
              self.layer_axe.commitChanges()
              QgsMapLayerRegistry.instance().addMapLayer(self.layer_axe,False)
              biefgroup.addLayer(self.layer_axe)		  
              
              self.layer_rg = QgsVectorLayer("LineString","Rive gauche", "memory")
              self.layer_rg.startEditing()
              pr_rg =  self.layer_rg.dataProvider()
              #pr_rg.addAttributes( [ QgsField("rg_id",QVariant.Int)] )
              self.layer_rg.commitChanges()
              QgsMapLayerRegistry.instance().addMapLayer(self.layer_rg,False)       
              biefgroup.addLayer(self.layer_rg)
              
              self.layer_rd = QgsVectorLayer("LineString","Rive droite", "memory")
              self.layer_rd.startEditing()
              pr_rd =  self.layer_rd.dataProvider()
              #pr_rd.addAttributes( [ QgsField("rd_id",QVariant.Int)] )
              self.layer_rd.commitChanges()
              QgsMapLayerRegistry.instance().addMapLayer(self.layer_rd,False)
              biefgroup.addLayer(self.layer_rd)
              self.fichier_log.write("    Couche Traces, Axe hydraulique, Rive gauche, Rive droite crees.\n\n")
        else:
            return  
        
        
        self.loadGeoRef(filename)
    
    def loadGeoRef(self, filename):
        
        rive_gauche_found = False
        rive_droite_found = False
        point_passage_axe = ""
        pr = None
        pr_trace = None
        
        file = open(filename, 'r')
        
        self.fichier_log.write("    Lecture du fichier...\n")
        
        list_point = []
        list_point_axe = []
        list_point_riveG = []
        list_point_riveD = []
        list_abs_long = []
        tab_fet = [] 
        tab_fet_trace = []
                
        # Affectation des providers
        pr = self.layer_profils.dataProvider()
        pr_trace = self.layer_traces.dataProvider()
        pr_rg = self.layer_rg.dataProvider()
        pr_rd = self.layer_rd.dataProvider()
        pr_axe = self.layer_axe.dataProvider()
        
        self.layer_profils.startEditing()
        self.layer_traces.startEditing()
        self.layer_axe.startEditing()
        self.layer_rg.startEditing()
        self.layer_rd.startEditing()
        
        
        fet = None
        fet_trace = None
        fet_point = None
        profil_nom = None
        lignes = file.readlines()
        longueur = None
    
        for ligne in lignes:
                ligne = ligne.upper()
                if(ligne.split(' ')[0] == 'PROFIL'):
                    # on creer un nouveau profil
                    
                    # Un profil vient d'etre fini et on a pas detecter de rive droit , on prend donc le dernier point connu
                    if(not rive_droite_found and fet != None):
                        list_point_riveD.append(list_point[len(list_point) - 1])
                    
                    rive_gauche_found = False
                    rive_droite_found = False  
                    
                        
                    
                    
                    
                    
                    if(fet != None):
                        # profil deja entamé on l'ajoute au layer
                        fet.setGeometry(QgsGeometry.fromPolyline(list_point))
                        fet.setAttribute('nom', profil_nom) 
                        
                        self.fichier_log.write("        "+profil_nom+"\n");
                        fet.setAttribute('x', ','.join([str(x) for x in tab_attribute_X]))
                        fet.setAttribute('y', ','.join([str(y) for y in tab_attribute_Y]))
                        fet.setAttribute('z', ','.join([str(z) for z in tab_attribute_Z]))
                        fet.setAttribute('lit', ','.join([lit for lit in tab_lit]))
                        fet.setAttribute('intersection_axe', point_passage_axe)
                        fet.setAttribute('abscisse_axe_hydr',abs_long)
                        fet.setAttribute('abs_travers', ','.join([str(a) for a in tab_attribute_abstrav]))
                        list_abs_long.append(abs_long) 
                        
                        tab_fet.append(fet)
                        #pr.addFeatures([ fet ])
                        
                        fet_trace.setGeometry(QgsGeometry.fromPolyline(list_point))
                        fet_trace.setAttribute('nom_profil', profil_nom) 
                        #pr_trace.addFeatures([ fet_trace ])
                        tab_fet_trace.append(fet_trace)
                 
                    abs_long =  float(ligne.split(' ')[3])
                    fields = self.layer_profils.pendingFields()
                    fields_trace = self.layer_traces.pendingFields()
                    fet = QgsFeature()
                    fet.setFields(fields, True)
                        
                    fet_trace = QgsFeature()
                    fet_trace.setFields(fields_trace, True)
                        
                    profil_nom = ligne.split(' ')[2]
                    list_point = []
                    tab_attribute_X = []
                    tab_attribute_Y = []
                    tab_attribute_Z = []
                    tab_attribute_abstrav = []
                    tab_lit = []
                    xyAxe = ligne.split("AXE")[1]
                    xAxe = float(xyAxe.split(' ')[1])
                    yAxe = float(xyAxe.split(' ')[2])
                    list_point_axe.append(QgsPoint(xAxe, yAxe))
                    point_passage_axe = str(xAxe) + " " + str(yAxe) + " I"  # le string enleve le \n qui pose probleme... 
                    
                    p_debut = Point(float(ligne.split(' ')[4]),float(ligne.split(' ')[5]))
                    finProfil = ligne.split("AXE")[0]
                    print finProfil.split(' ')[-3],finProfil.split(' ')[-2]
                    p_fin = Point(float(finProfil.split(' ')[-3]),float(finProfil.split(' ')[-2]))
                    longueur = p_debut.distance(p_fin)
                    
                    
                else:
                    
                    
                    
                    if(len(list_point)>1 and longueur != None):
                        p_i =  Point(float(ligne.split(' ')[3]), float(ligne.split(' ')[4]))
                        p_im1 =  Point(list_point[len(list_point)-1].x(), list_point[len(list_point)-1].y())
                        
                        if(p_i.distance(p_im1)<(longueur/10000)):
                             self.fichier_log.write(profil_nom+" : ERREUR : points trop proches à l'abcisse "+ligne.split(' ')[0]+".\n")
                             self.fichier_log.close()
                             self.layer_profils.commitChanges()
                             self.layer_traces.commitChanges()
                             self.layer_axe.commitChanges()
                             self.layer_rg.commitChanges()
                             self.layer_rd.commitChanges()
                             QMessageBox.critical(None, unicode("ERREUR", "utf-8"), unicode(profil_nom+" : Points trops proches à l'abcisse ", "utf-8")+ligne.split(' ')[0],QMessageBox.Ok)
                             return
                         
                    point = QgsPoint(float(ligne.split(' ')[3]), float(ligne.split(' ')[4]))
                    list_point.append(point)        
                                        
                    tab_attribute_X.append(float(ligne.split(' ')[3]))
                    tab_attribute_Y.append(float(ligne.split(' ')[4]))
                    tab_attribute_Z.append(float(ligne.split(' ')[1]))
                    tab_attribute_abstrav.append(float(ligne.split(' ')[0]))
                    tab_lit.append(ligne.split(' ')[2])
                    
                    # on part (pour l'instant) du principe que la rive gauche est celle la plus proche du 0 de l'abs curv
                    
                    if(ligne.split(' ')[2] == 'B'  and rive_gauche_found == False):
                        # donc ce point est la rive gauche
                        list_point_riveG.append(point)
                        rive_gauche_found = True
                    
                    if(ligne.split(' ')[2] == 'T'  and rive_gauche_found == True and rive_droite_found == False):
                        # donc le point precedent est la rive droite
                        list_point_riveD.append(list_point[len(list_point) - 1])
                        rive_droite_found = True
                    
                    
                    
                    self.layer_traces.commitChanges()
                    self.layer_profils.commitChanges()
                    
                    
               # Fin de lecture du fichier , on enregistre le profil en cours , l'axe et les rive            
                
        fet.setGeometry(QgsGeometry.fromPolyline(list_point))
        fet.setAttribute('nom', profil_nom)
        self.fichier_log.write("        "+profil_nom+"\n");
        fet.setAttribute('x', ','.join([str(x) for x in tab_attribute_X]))
        fet.setAttribute('y', ','.join([str(y) for y in tab_attribute_Y]))
        fet.setAttribute('z', ','.join([str(z) for z in tab_attribute_Z]))
        fet.setAttribute('lit', ','.join([lit for lit in tab_lit]))
        fet.setAttribute('intersection_axe', point_passage_axe)
        fet.setAttribute('abscisse_axe_hydr',abs_long)
        fet.setAttribute('abs_travers', ','.join([str(a) for a in tab_attribute_abstrav]))
        list_abs_long.append(abs_long)
                 # fet.setAttribute('abs_travers',"")
        tab_fet.append(fet)            
        #pr.addFeatures([ fet ])
                                        
        fet_trace.setGeometry(QgsGeometry.fromPolyline(list_point))
        fet_trace.setAttribute("nom_profil", profil_nom) 
        #pr_trace.addFeatures([ fet_trace ])
        tab_fet_trace.append(fet_trace)
                    # self.layer_trace_axe_hydro.startEditing()
                    # pr_axe = self.layer_trace_axe_hydro.dataProvider()
        if(not rive_droite_found):
            list_point_riveD.append(list_point[len(list_point) - 1])

        tab_fet_ordonnee = []
        list_point_axe_ord = []
        list_point_riveG_ord = []
        list_point_riveD_ord = []
        tab_fet_trace_ord = []          
        #for key, value in self.tools.getProfilsOrdonnesFeatures(tab_fet):
          #tab_fet_ordonnee.append(key)
          #self.fichier_log.write("        "+key.attribute('nom')+"\n");

        #tri selon les abcisses longi
        index = [i for i in range(0,len(list_abs_long))]
        conv = lambda i: list_abs_long[i]
        index.sort(key=conv)
        for i in range(0,len(index)):
            tab_fet_ordonnee.append(tab_fet[index[i]])
            tab_fet_trace_ord.append(tab_fet_trace[index[i]])
            list_point_axe_ord.append(list_point_axe[index[i]])
            list_point_riveG_ord.append(list_point_riveG[index[i]])
            list_point_riveD_ord.append(list_point_riveD[index[i]])            
            self.fichier_log.write("        "+tab_fet[index[i]].attribute('nom')+"\n");

        fields_axe = self.layer_axe.pendingFields()
        axe = QgsFeature()
        axe.setFields(fields_axe, True)
        axe.setGeometry(QgsGeometry.fromPolyline(list_point_axe_ord))
        #axe.setAttribute('axe_id', 1)
        pr_axe.addFeatures([ axe ])
                    
                    # rive droite ?
        fields_rg = self.layer_rg.pendingFields()
        riveG = QgsFeature()
        riveG.setFields(fields_rg, True)
        riveG.setGeometry(QgsGeometry.fromPolyline(list_point_riveG_ord))
        #riveG.setAttribute('rg_id', 1)
        pr_rg.addFeatures([ riveG ])
                                        
        fields_rd = self.layer_rd.pendingFields()
        riveD = QgsFeature()
        riveD.setFields(fields_rd, True)
        riveD.setGeometry(QgsGeometry.fromPolyline(list_point_riveD_ord))
        #riveD.setAttribute('rd_id', 1)
        pr_rd.addFeatures([ riveD ])
                    
        
        self.layer_traces.commitChanges()
                # self.layer_trace_axe_hydro.commitChanges()
        self.layer_axe.commitChanges()
        self.layer_rg.commitChanges()
        self.layer_rd.commitChanges()
                # et on genere l'axe d'ecoulement
        self.fichier_log.write("        --Tri sur l'axe hydraulique\n");

        
        #profils_ordonne = {}        
        #for feat in features:
            #profils_ordonne[feat] = feat.attribute('abscisse_axe_hydr') 
        """
        if(len(tab_fet_ordonnee)>=2):
            #Il y a plus de deux profil , on peut essayer de tracer le debut de l'axe hydraulique
            p1 = tab_fet_ordonnee[0].attribute('intersection_axe').split(' ')
            p2 = tab_fet_ordonnee[1].attribute('intersection_axe').split(' ')
            
            distance = tab_fet_ordonnee[0].attribute('abscisse_axe_hydr')
            
            point_p1 = Point(float(p1[0]),float(p1[1]))
            point_p2 = Point(float(p2[0]),float(p2[1]))
            
            geom=None
            for axe in self.layer_axe.getFeatures():
                geom= axe.geometry()
            pts = geom.asPolyline()
            
            polyline = []            
            #polyligne correspondant a l'axe d'origine    
            for pt in pts:                    
                polyline.append(Point(pt.x(),pt.y()))
            
            #on lui rajoute un bout..
            poly = Polyligne(polyline)
            deb = poly.newSegment(point_p1,point_p2,distance,-1)
            
            #maintenant on regenere le nouvelle axe 
            new_pts = poly.getPts()
            list_point_axe = []
            
            list_point_axe.append(QgsPoint(deb.x, deb.y))
            for pts in new_pts:
                list_point_axe.append(QgsPoint(pts[0], pts[1]))
            
            self.layer_axe.startEditing()
            #on efface la feature existante
            for axe in self.layer_axe.getFeatures():
                pr_axe.deleteFeatures([axe])
            fields_axe = self.layer_axe.pendingFields()
            axe = QgsFeature()
            axe.setFields(fields_axe, True)
            axe.setGeometry(QgsGeometry.fromPolyline(list_point_axe))
            #axe.setAttribute('axe_id', 1)
            pr_axe.addFeatures([ axe ])
            self.layer_axe.commitChanges()   
        """            
            
          
        pr.addFeatures(tab_fet_ordonnee)
        pr_trace.addFeatures(tab_fet_trace_ord)
        self.layer_profils.commitChanges()            
        self.layer_profils.updateExtents()                                 
        self.fichier_log.write("    Import termine\n")
        self.fichier_log.close()
        QMessageBox.information(None, unicode("Import terminé", "utf-8"), unicode("Fichier de log écrit dans ", "utf-8")+self.path_log,QMessageBox.Ok)
    

         
