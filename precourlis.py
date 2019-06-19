# Import the PyQt and QGIS libraries
from PyQt4.QtCore import * 
from PyQt4.QtGui import *
from qgis.core import *
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from precourlisDialog import precourlisDialog
from preCourlisNewLayer import preCourlisNewLayer
from preCourlisGeoRefParser import preCourlisGeoRefParser
from preCourlisTraceConvert import preCourlisTraceConvert
from preCourlisProfilEditor import preCourlisProfilEditor
from preCourlisProjZProfils import preCourlisProjZProfils
from preCourlisProjAxeBerge import preCourlisProjAxeBerge
from preCourlisInterpolProfils import preCourlisInterpolProfils

class precourlis: 

  def __init__(self, iface):
    # Save reference to the QGIS interface
    self.iface = iface

  def initGui(self):  
    # Create action that will start plugin configuration
    self.action = QAction(QIcon(":/plugins/precourlis/icon.png"), "PreCourlis", self.iface.mainWindow())
    
    
    #self.actionBief = QAction("&Bief", self.iface.mainWindow())
    self.actionGeoRef = QAction("Importer un fichier .georef", self.iface.mainWindow())
    self.actionVisuProfils = QAction("Visualiser les profils", self.iface.mainWindow())
    self.actionInterpProfils = QAction("Interpoler des profils", self.iface.mainWindow())
    self.actionConverTrace = QAction("Convertir les traces en profils", self.iface.mainWindow())
    self.actionProjZ = QAction("Projeter un semis de point sur les profils", self.iface.mainWindow())
    self.actionProjRive = QAction("Projeter les berges", self.iface.mainWindow())
    self.actionAbout = QAction(QIcon(":/plugins/precourlis/icon.png"), "A propos", self.iface.mainWindow())
    
    self.actionAddBief = QAction("Ajouter un bief", self.iface.mainWindow())
    self.actionRenaBief = QAction("Renommer un bief", self.iface.mainWindow())
    self.actionDelBief = QAction("Supprimmer un bief", self.iface.mainWindow())
    self.actionAddLayer = QAction("Ajouter une couche vectorielle", self.iface.mainWindow())
    
       
    self.menuBief = QMenu(self.iface.mainWindow())
    self.menuBief.setTitle("&Biefs") 
    
     
    self.menuBief.addAction(self.actionAddBief)
    self.menuBief.addAction(self.actionRenaBief)
    self.menuBief.addAction(self.actionDelBief)
    self.menuBief.addAction(self.actionAddLayer) 
    
    
    self.menuToolBar =  QMenu(self.iface.mainWindow())
    self.menuToolBar.addAction(self.actionGeoRef)
    self.menuToolBar.addAction(self.actionVisuProfils)
    self.menuToolBar.addAction(self.actionConverTrace)
    self.menuToolBar.addAction(self.actionProjZ)
    self.menuToolBar.addAction(self.actionProjRive)
    self.menuToolBar.addAction(self.actionInterpProfils)
    self.menuToolBar.addAction(self.actionAbout)        
    
    
    self.action.setMenu(self.menuToolBar)
    
    
    self.iface.addToolBarIcon(self.action)
    
    
    
    #self.iface.addPluginToMenu("&PreCourlis", self.actionBief)
    self.iface.addPluginToMenu("&PreCourlis", self.actionGeoRef)
    self.iface.addPluginToMenu("&PreCourlis", self.actionVisuProfils)
    self.iface.addPluginToMenu("&PreCourlis", self.actionConverTrace)
    self.iface.addPluginToMenu("&PreCourlis", self.actionProjZ)
    self.iface.addPluginToMenu("&PreCourlis", self.actionProjRive)
    self.iface.addPluginToMenu("&PreCourlis", self.actionInterpProfils)
    self.iface.addPluginToMenu("&PreCourlis", self.actionAbout)
   
    # connect the action to the run method
    #QObject.connect(self.action, SIGNAL("activated()"), self.run) 
    QObject.connect(self.actionAddBief, SIGNAL("activated()"), self.ajoutBief) 
    QObject.connect(self.actionAddLayer, SIGNAL("activated()"), self.ajoutLayer)
    QObject.connect(self.actionGeoRef, SIGNAL("activated()"), self.importGeoRef)
    QObject.connect(self.actionConverTrace, SIGNAL("activated()"), self.convertirTrace)
    QObject.connect(self.actionVisuProfils, SIGNAL("activated()"), self.openEditor) 
    QObject.connect(self.actionProjZ, SIGNAL("activated()"), self.projZProfil)
    QObject.connect(self.actionProjRive, SIGNAL("activated()"), self.projAxeBerge)
    QObject.connect(self.actionInterpProfils, SIGNAL("activated()"), self.interpProfils)  

    # Add toolbar button and menu item
    
    
    
    

  def unload(self):
    # Remove the plugin menu item and icon
    self.iface.removePluginMenu("&PreCourlis", self.action)
    self.iface.removePluginMenu("&PreCourlis", self.actionGeoRef)
    self.iface.removePluginMenu("&PreCourlis", self.actionVisuProfils)
    self.iface.removePluginMenu("&PreCourlis", self.actionInterpProfils)
    self.iface.removePluginMenu("&PreCourlis", self.actionConverTrace)
    self.iface.removePluginMenu("&PreCourlis", self.actionProjZ)
    self.iface.removePluginMenu("&PreCourlis", self.actionProjRive)
    self.iface.removePluginMenu("&PreCourlis", self.actionAbout)
    
    self.iface.removeToolBarIcon(self.action)

  # run method that performs all the real work
  def run(self): 
    # create and show the dialog 
    dlg = precourlisDialog(self.iface) 
    # show the dialog
    dlg.show()
    result = dlg.exec_() 
    # See if OK was pressed
    if result == 1: 
      # do something useful (delete the line containing pass and
      # substitute with your code
      pass 


  def ajoutBief(self):
      
      # ajouter un groupe au treeLayer
    nom_bief, ok = QInputDialog.getText(self.iface.mainWindow(), "Nouveau bief", "Entrez un nom")
    if(nom_bief == "" or not ok):
        return    
        
    root = QgsProject.instance().layerTreeRoot()
    current_bief_group = root.addGroup(nom_bief)
    
  def ajoutLayer(self):
      
      #Ajouter une nouvelle couche vectorielle de type "memory"
      self.dlg = preCourlisNewLayer(self.iface)
      #dlg.show()
    
  def importGeoRef(self):
      
      self.geoRefParser = preCourlisGeoRefParser()
      self.geoRefParser.selectFile()
      
  def convertirTrace(self):
      self.traceConverter = preCourlisTraceConvert(self.iface)
      
  def openEditor(self):
      self.editor = preCourlisProfilEditor(self.iface)
      
  def projZProfil(self):
      self.proj = preCourlisProjZProfils(self.iface)
      
  def projAxeBerge(self):
      self.proj = preCourlisProjAxeBerge(self.iface)
      
  def interpProfils(self):
      self.interp = preCourlisInterpolProfils(self.iface)
