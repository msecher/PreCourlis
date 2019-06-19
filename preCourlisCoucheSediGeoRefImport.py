# -*- coding: utf-8 -*-
'''
Created on 25 ao�t 2015

@author: quarre
'''
from qgis.core import *
from PyQt4.QtCore import QVariant,QPyNullVariant
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QComboBox, QPushButton, QGridLayout, QLineEdit, QPushButton, QLabel, QCheckBox, QFileDialog, QInputDialog, QMessageBox, QColorDialog
from preCourlisTools import preCourlisTools , Point, Polyligne

class preCourlisCoucheSediGeoRefImport(QtGui.QDialog):
    
    def __init__(self, profil_editor):
        
        QtGui.QFrame.__init__(self)
        
        self.editor = profil_editor
        self.profil_courant = None
        
        self.ecart_abcisse_max = 1.
        
        
        self.setWindowTitle(unicode("Importer une couche sédimentaire", "utf-8"))
        self.resize(270, 10)
        gridbox = QGridLayout()
        
        gridbox.addWidget(QLabel(unicode("Nom de la nouvelle couche sédimentaire: ", "utf-8")), 0, 0)
        self.nom_couche = QLineEdit()
        gridbox.addWidget(self.nom_couche, 0, 1)
        
        gridbox.addWidget(QLabel(unicode("A placer en dessous de : ", "utf-8")), 1, 0)
        self.liste_couche = QComboBox()
        
        # recuperation des couches sedi déjà en place
        for f in self.editor.couche_choisi.getFeatures():
            self.lst_couche_sedi = []
            if(not f.attribute('liste_couche_sediment') is None and not isinstance(f.attribute('liste_couche_sediment'),QPyNullVariant)):
                self.lst_couche_sedi = [str(c) for c in f.attribute('liste_couche_sediment').split(',')]
            self.liste_couche.addItem("Fond")
            self.liste_couche.addItems(self.lst_couche_sedi)
            break  # Une seul iteration suffit
        
        
        gridbox.addWidget(self.liste_couche, 1, 1)        
        
        btn_imp = QPushButton("Choisir le fichier")
        gridbox.addWidget(btn_imp, 2, 1)
        
        self.setLayout(gridbox)   
        
        QtCore.QObject.connect(btn_imp, QtCore.SIGNAL("clicked(bool)"), self.import_geoRef)
        self.show()
        
        
    def import_geoRef(self):
        """
        """
        self.name_couche_sedi = self.nom_couche.text()
        
        filename = QFileDialog.getOpenFileName()
        if(filename == ""):
            return 
        
        for f in self.editor.couche_choisi.getFeatures():
            if(f.id() == self.editor.profil_courant.id()):
                self.profil_courant = f 
                break;
        
        if(not self.profil_courant.attribute('liste_couche_sediment') is None and not isinstance(self.profil_courant.attribute('liste_couche_sediment'),QPyNullVariant)):
            if(self.name_couche_sedi in self.profil_courant.attribute('liste_couche_sediment').split(',')):
                QMessageBox.critical(self, "Erreur", unicode("Ce nom est déjà utilisé", "utf-8"), QMessageBox.Ok, QMessageBox.NoButton)                
                return
        
        color = QColorDialog.getColor()
        if not color.isValid():
            return
        
        
        
        self.editor.couche_choisi.startEditing()
        self.editor.couche_choisi.dataProvider().addAttributes([QgsField('couche_sedi_' + self.name_couche_sedi, QVariant.String)])
        self.editor.couche_choisi.updateFields()
        field = self.editor.couche_choisi.pendingFields()
        absLongi = []
        
         # on recopie tout point Z des profils pour initialisé cette nouvelle couche
        for f in self.editor.couche_choisi.getFeatures():
            #print(f.attribute('liste_couche_sediment'))
            absLongi.append(f.attribute('abscisse_axe_hydr'))
            fied_index_Z = -1 
            if(not f.attribute('liste_couche_sediment') is None and not isinstance(f.attribute('liste_couche_sediment'),QPyNullVariant)):
                self.lst_couche_sedi = [str(c) for c in f.attribute('liste_couche_sediment').split(',')]
                lst_couche_sedi_couleur = [str(c) for c in f.attribute('liste_couche_sediment_couleur').split(',')]
                
                if(self.liste_couche.currentText()!="Fond"):
                    fied_index_Z = self.editor.couche_choisi.fieldNameIndex('couche_sedi_' + self.liste_couche.currentText())
                else:
                    fied_index_Z = self.editor.couche_choisi.fieldNameIndex("z")
            else:
                fied_index_Z = self.editor.couche_choisi.fieldNameIndex("z")
                self.lst_couche_sedi = []
                lst_couche_sedi_couleur = []
                
                
            #self.lst_couche_sedi.append(self.name_couche_sedi)
            #lst_couche_sedi_couleur.append(color.rgb())
            #Il faut inserer la couche :
            
            new_list_couch = []
            new_list_couch_color = []
            
            
            if(self.liste_couche.currentText()=="Fond"):
                new_list_couch.append(self.name_couche_sedi)
                new_list_couch_color.append(color.rgb())
                i=0
                for c in self.lst_couche_sedi:
                    new_list_couch.append(c)
                    new_list_couch_color.append(lst_couche_sedi_couleur[i])
                i=i+1
            else:
                i=0
                for c in self.lst_couche_sedi:
                    new_list_couch.append(c)
                    new_list_couch_color.append(lst_couche_sedi_couleur[i])
                    if(c==self.liste_couche.currentText()):
                        new_list_couch.append(self.name_couche_sedi)
                        new_list_couch_color.append(color.rgb())
                    i=i+1
            
            self.lst_couche_sedi = new_list_couch
            lst_couche_sedi_couleur = new_list_couch_color
            
           
            fied_index_lst = self.editor.couche_choisi.fieldNameIndex("liste_couche_sediment") 
            fied_index_lst_couleur = self.editor.couche_choisi.fieldNameIndex("liste_couche_sediment_couleur")       
            self.fied_index_new_sedi = self.editor.couche_choisi.fieldNameIndex('couche_sedi_' + self.name_couche_sedi)
            f[self.fied_index_new_sedi] = f[fied_index_Z]
            f[fied_index_lst] = ','.join([str(l) for l in self.lst_couche_sedi])
            f[fied_index_lst_couleur] = ','.join([str(l) for l in lst_couche_sedi_couleur])
            self.editor.couche_choisi.updateFeature(f)
        
        self.editor.couche_choisi.commitChanges()
        
        tolerance = absLongi[-1]/10000
        
        file = open(filename, 'r')
        lignes = file.readlines()
        
        profil_to_update = None
        tab_point_lus = []  # ya que des Z 
                
        couche_inf = None
        n = False
        for c in self.lst_couche_sedi:
            if(n==True):
                couche_inf=c
            if(c==self.name_couche_sedi):
                n=True
            
            abscisse_profs=[]
            nom_profs=[]
            tab_point_profs = []
            tab_point_lus = []
            for ligne in lignes:
                ligne = ligne.upper()
                if(ligne.split(' ')[0] == 'PROFIL'):
                    # On ligne une entete 
                    abscisse_profs.append(float(ligne.split(' ')[3]))
                    nom_profs.append(ligne.split(' ')[2])
                    # pour le premier profil, rien n'est encore lu
                    if(len(tab_point_lus) != 0):
                        tab_point_profs.append(tab_point_lus)
                        tab_point_lus = []                       
                else:
                    tab_point_lus.append(Point(float(ligne.split(' ')[0]), 0., float(ligne.split(' ')[1]))) 
            
            tab_point_profs.append(tab_point_lus)
                
            for i in range(0,len(abscisse_profs)): 
                trouve = False
                distMin = 10e+20 
                for f in self.editor.couche_choisi.getFeatures():
                    dist = abs(f.attribute("abscisse_axe_hydr") - abscisse_profs[i])
                    #print f.attribute("nom"), dist,f.attribute("abscisse_axe_hydr")
                    if(dist < distMin):
                        distMin = dist            
                    if(dist <=  tolerance):
                        profil_to_update = f
                        tab_point_lus = []
                        trouve = True
                        break
                if(not trouve):
                    QMessageBox.critical(None, unicode("ERREUR", "utf-8"), unicode(nom_profs[i]+" : trop eloigne d'un profil maitre, distance = ","utf-8") +str(distMin)+" tolerance = "+str(tolerance),QMessageBox.Ok)
                else:   
                    tablen = [float(y) for y in profil_to_update.attribute('abs_travers').split(',')]
                    longueur = tablen[-1]
                    # Controle de verticalite
                    vert = False
                    for j in range(1,len(tab_point_profs[i])):
                        p_i = tab_point_profs[i][j].x
                        p_im1 = tab_point_profs[i][j-1].x
                        #print(p_i.distance(p_im1))

#MS2018 glut : raison de la présence de ce test non-analysée (?) ==> commenté
#                        if(abs(p_i-p_im1)<longueur/10000):
#                            vert = True
#                            QMessageBox.critical(None, unicode("ERREUR", "utf-8"), unicode(nom+" : points trop proches àl'abcisse ","utf-8") +str(p_i),QMessageBox.Ok)

                    if(not vert):
                        poly = []                        
                        for l in tablen:
                            poly.append(Point(l, 0, -9999))
                            
                        polyline = Polyligne(poly)
                        # Tolerance de distance entre points lus et poly de 10 pas utile car on travaille en coord transversale donc point toujours sur poly
                        polyline.definirZparPointsProches3(tab_point_profs[i], 10, True)
                        j= 0
                                                
                        new_pts = polyline.getPts()
                        self.editor.couche_choisi.startEditing()
                        
                        if(self.liste_couche.currentText() == "Fond"):
                            tabz_supp = [float(z) for z in profil_to_update.attribute('z').split(',')]
                        else:
                            tabz_supp = [float(z) for z in profil_to_update.attribute('couche_sedi_' + self.liste_couche.currentText()).split(',')]
                            
                        if(couche_inf!=None):
                            tabz_inf = [float(z) for z in profil_to_update.attribute('couche_sedi_'+couche_inf).split(',')]   
                        
                        pts_to_write = []
                        for i in range(len(new_pts)):
                            zc = new_pts[i][2]
                            if(zc >= tabz_supp[i] or zc == -9999):
                                pts_to_write.append(tabz_supp[i])
                            elif(couche_inf!=None and zc<=tabz_inf[i]):
                                pts_to_write.append(tabz_inf[i])
                            else:
                                pts_to_write.append(zc)
                        
                        profil_to_update[self.fied_index_new_sedi] = ','.join([str(pts) for pts in pts_to_write])
                        
                        self.editor.couche_choisi.updateFeature(profil_to_update) 
                        self.editor.couche_choisi.commitChanges()
                            
        self.editor.updateComboSedi()  
        self.editor.comboSediChangeEvent()
        self.close()
        
        
