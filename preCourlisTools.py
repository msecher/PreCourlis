# -*- coding: utf-8 -*-
'''
Created on 2 avr. 2015

@author: quarre
'''

import math
from qgis.core import *
from shapely.geometry import LineString
from getopt import do_longs
from PyQt4.Qt import QPyNullVariant

DEBUG = False

def logPrint(s):
    if DEBUG:
        print(s)

class Point(object):
    "Point 3D"
    def __init__(self, x, y, z=-9999):
      self.x = float(x)
      self.y = float(y)
      self.z = float(z)
      return
    
    def pprint(self, com=""):
        "Impression"
        if(self.z == -9999):
          logPrint(com+" "+str(self.x)+" "+str(self.y))
        else:
          logPrint(com+" "+str(self.x)+" "+str(self.y)+" "+str(self.z))

    
    def distance_squared(self, p):
        "distance au carre entre le point et un point p"
        dx = self.x - p.x
        dy = self.y - p.y
        return dx * dx + dy * dy
    
    def distance(self, p):
        "distance entre le point et un point p"
        return math.sqrt(self.distance_squared(p))
    
    def distance_point_segment_squared(self, v, w):
        "distance normale du point a un segment defini par 2 point v et w"
        "retourne le carre de la distance normale au segement, et l'abcisse curviligne du point projete sur le segment (-1 si hors segment)"
        # Segment length squared, |w-v|^2
        # v.pprint()
        # w.pprint()
        d2 = v.distance_squared(w)
        if d2 == 0: 
          # v == w, return distance to v
          return self.distance_squared(v), 0.
        # Consider the line extending the segment, parameterized as v + t (w - v).
        # We find projection of point p onto the line. 
        t = ((self.x - v.x) * (w.x - v.x) + (self.y - v.y) * (w.y - v.y)) / d2;
        if t < 0:
          # Beyond v end of the segment
          return self.distance_squared(v), -1
        elif t > 1.0:
          # Beyond w end of the segment
          return self.distance_squared(w), -1
        else:
          # Projection falls on the segment. (GH : hors segment ça marche aussi, mais faut mettre un indicateur)
          proj = Point(v.x + t * (w.x - v.x), v.y + t * (w.y - v.y))
          # Calcul de la distance du debut du segment au point projete
          l = math.sqrt(v.distance_squared(proj))
          # logPrint "projection:",d2, t, proj.x, proj.y,"l=",l
          return self.distance_squared(proj), l

    def distance_point_segment2(self, v, w):
      "distance normale du point a un segment defini par 2 point v et w"
      "retourne le carre de la distance normale au segement, et l'abcisse curviligne du point projete sur le segment"
      "une valeur de l negative si proj avant deut segment et une valeur superieure à longueur segment si proj apres fin"
      # Segment length squared, |w-v|^2
      # v.pprint()
      # w.pprint()
      d2 = v.distance_squared(w)
      if d2 == 0: 
        # v == w, return distance to v
        return self.distance_squared(v), 0.
      # Consider the line extending the segment, parameterized as v + t (w - v).
      # We find projection of point p onto the line. 
      t = ((self.x - v.x) * (w.x - v.x) + (self.y - v.y) * (w.y - v.y)) / d2;
      # Projection falls on the segment. (GH : hors segment ça marche aussi, mais faut mettre un indicateur)
      proj = Point(v.x + t * (w.x - v.x), v.y + t * (w.y - v.y))
      # Calcul de la distance du debut du segment au point projete
      l = math.sqrt(v.distance_squared(proj))
      # logPrint "projection:",d2, t, proj.x, proj.y,"l=",l
      return self.distance(proj), l
    
    def distance_point_segment(self, v, w):
      "distance normale d'un point p a un segment defini par 2 point v et w"
      "retourne le carre de la distance normale au segemnt, et l'abcisse curviligne du point projete sur le segment (-1 si hors segment)"
      d = self.distance_point_segment_squared(v, w)
      return math.sqrt(d[0]), d[1]
  
class Polyligne(object):
    "Point 2D"
    def __init__(self, points):
      self.pts = points

    def pprint(self, com=""):
      "Impression"
      if (com != ""):
        logPrint(com)
      for s in range(0, len(self.pts)):
         self.pts[s].pprint()

    def getNpts(self):
      return len(self.pts)
  
    def getPts(self):
      tabPts = []
      for s in range(0, len(self.pts)):
         x = self.pts[s].x
         y = self.pts[s].y
         z = self.pts[s].z
         tabPts.append((x,y,z)); 
      return tabPts
         
    def abcissePointSurPolyline(self, p):
      debut = self.pts[0]
      # self.pprint("")
      # logPrint "nbr pts :", len(self.pts)
      dmin = 10.e+20
      # initialisation : pas de segment trouve, et pas de distance de projection valide
      strouve = -1
      lstrouve = -1
      for s in range(1, len(self.pts)):
        fin = self.pts[s]
        d = p.distance_point_segment(debut, fin)
        # logPrint s, d
        # la distance au debut du segment d[1] doit etre >0, projection valide
        if ((d[0] < dmin) and (d[1] >= 0)):
          dmin = d[0]
          strouve = s
          lstrouve = d[1]
          # logPrint s, dmin, lstrouve
        debut = fin
        # logPrint strouve, lstrouve
    
      if (strouve == -1):
          return -1
      abcisse = 0.
      debut = self.pts[0]
      for s in range(1, strouve):
        # logPrint s
        fin = self.pts[s]
        d = debut.distance(fin)
        abcisse = abcisse + d
        debut = fin
      if (lstrouve > 0):
        abcisse = abcisse + lstrouve
        # logPrint abcisse
      return abcisse

  
    def projeterPointSurPolyline2(self, p):
      #pour la projection de Z  avec prise en compte de points projetes en dehors de la poliligne ...
      debut = self.pts[0]
      # self.pprint("")
      # logPrint "nbr pts :", len(self.pts)
      dmin = 10.e+20
      # initialisation : pas de segment trouve, et pas de distance de projection valide
      strouve = -1
      lstrouve = -1
 
      for s in range(1, len(self.pts)):
        fin = self.pts[s]
        d = p.distance_point_segment2(debut, fin)
        longueur = debut.distance(fin)      
        #logPrint s, d
        # la distance au debut du segment d[1] doit etre >0, projection valide
        if (d[0] < dmin and s==1 and  d[1] < 0):
          dmin = d[0]
          strouve = s
          lstrouve = d[1]
          break
        elif (d[0] < dmin and s==len(self.pts)-1 and  d[1] > longueur):
          dmin = d[0]
          strouve = s
          lstrouve = d[1]
          break
        elif (d[0] < dmin):
          dmin = d[0]
          strouve = s
          lstrouve = d[1]
          # logPrint s, dmin, lstrouve
        debut = fin
        # logPrint strouve, lstrouve
    
      if (strouve == -1):
          return -1, -1
      abcisse = 0.
      debut = self.pts[0]
      for s in range(1, strouve):
        # logPrint s
        fin = self.pts[s]
        d = debut.distance(fin)
        abcisse = abcisse + d
        debut = fin
      if (lstrouve > 0):
        abcisse = abcisse + lstrouve
        # logPrint abcisse
      return abcisse, dmin

    def projeterPointSurPolyline(self, p):
      #pour la projection de Z ...
      debut = self.pts[0]
      # self.pprint("")
      # logPrint "nbr pts :", len(self.pts)
      dmin = 10.e+20
      # initialisation : pas de segment trouve, et pas de distance de projection valide
      strouve = -1
      lstrouve = -1
      for s in range(1, len(self.pts)):
        fin = self.pts[s]
        d = p.distance_point_segment(debut, fin)
        #logPrint s, d
        # la distance au debut du segment d[1] doit etre >0, projection valide
        if ((d[0] < dmin) and (d[1] >= 0)):
          dmin = d[0]
          strouve = s
          lstrouve = d[1]
          # logPrint s, dmin, lstrouve
        debut = fin
        # logPrint strouve, lstrouve
    
      if (strouve == -1):
          return -1, -1
      abcisse = 0.
      debut = self.pts[0]
      for s in range(1, strouve):
        # logPrint s
        fin = self.pts[s]
        d = debut.distance(fin)
        abcisse = abcisse + d
        debut = fin
      if (lstrouve > 0):
        abcisse = abcisse + lstrouve
        # logPrint abcisse
      return abcisse, dmin
  
    def calculerAbcisses(self):
      debut = self.pts[0]
      abcisse = []
      abcisse.append(0.)
      for s in range(1, self.getNpts()):
        fin = self.pts[s]
        d = debut.distance(fin)
        abcisse.append(abcisse[s - 1] + d)
        debut = fin
      return abcisse
  
    def longueur(self):
      abcisses = self.calculerAbcisses()
      return abcisses[-1]
   
    def pointsAvantApresAbcissse(self, abcissePoint):
      abcisse = self.calculerAbcisses()
      for s in range(1, self.getNpts()):
        if (abcisse[s] > abcissePoint):
          l = s - 1
          break
      return self.pts[l], self.pts[l + 1]
  
    def pointAbcissseSurPolyline(self, abcissePoint):
      abcisse = self.calculerAbcisses()
      #logPrint("pointAbcissseSurPolyline")
      #self.pprint()
      for s in range(1, self.getNpts()):
         if (abcisse[s] > abcissePoint):
          s = s - 1
          break
      logPrint(abcisse)
      logPrint(str(abcissePoint) + str(s))
      if (s != self.getNpts()-1):
          # si avant le dernier point
          d = abcissePoint - abcisse[s]
          dt = abcisse[s + 1] - abcisse[s]
          x = self.pts[s].x + d * (self.pts[s + 1].x - self.pts[s].x) / dt
          y = self.pts[s].y + d * (self.pts[s + 1].y - self.pts[s].y) / dt
          zs = self.pts[s].z
          zs1 = self.pts[s + 1].z
          if(zs == -9999 or zs1 == -9999):
            z = -9999
          else:
            z = zs + d * (zs1 - zs) / dt
      else:
          x = self.pts[s].x
          y = self.pts[s].y
          z = self.pts[s].z
          
      p = Point(x, y, z)
      #p.pprint()
      # logPrint "pointAbcissseSurPolyline",abcissePoint,s, p.x, p.y, z
      return p

    def discretiserPolylineDl(self, dl):
      # discretisation suivant longueur prescrite  
      abci = self.calculerAbcisses()
      l = abci[len(self.pts) - 1]
      nseg = 1 + int(l / dl)
      logPrint("discretisation a dl fixe" + str(dl) + " nbr seg :" + str(nseg))
      pd = self.discretiserPolyline(nseg)
      return pd  
  
    def discretiserPolyline(self, nseg):
      abci = self.calculerAbcisses()
      dl = abci[self.getNpts() - 1] / nseg
      pd = []
      abcissePt = 0.
      pd.append(self.pts[0]);
      for s in range(0, nseg - 1):
        abcissePt = abcissePt + dl
        p = self.pointAbcissseSurPolyline(abcissePt)
        # logPrint abcissePt, p.x, p.y
        pd.append(p)
      pd.append(self.pts[len(self.pts) - 1]);
  
      # for s in range(0, nseg + 1):
      #  pd[s].pprint("Pts " + str(s) + ":")
 
      return pd

    def definirZparPointsProches(self, points, dist, all):
      #Methode par distance autour du point traite et moyene ponderee
      all = True
      d2 = dist * dist
      nModif = 0
      for i in range(0, self.getNpts()):
        pt = self.pts[i]
        # le point n'est traite que s'il n'a pas de z ou que l'on veut modifier tous les z des points du profil
        if (pt.z == -9999 or all == True):
          # recherche des points du nuage proches
          sd = 0.
          sz = 0.
          for j in range(0, len(points)):
            d = pt.distance_squared(points[j])
            # logPrint d
            if(d < d2):
              if(d == 0):
                sz = points[j].z
                sd = 1.
                break
              else:
                dp = 1 / d
                sz = sz + dp * points[j].z
                sd = sd + dp
          # calcul de la valeur ponderee en fonction de la
          if(sd != 0.):
            pt.z = sz / sd
            nModif = nModif + 1
          # pt.plogPrint()
      return nModif
  
    def definirZparPointsProches2(self, points, dist, all):
      #Methode par projection de points sur le profil (les points projetes hors profils ne sont pas gérés)
      all = True
      d2 = dist * dist
      nModif = 0
      ptCandidat = []
      for j in range(0, len(points)):
        d = self.projeterPointSurPolyline(points[j])
        #logPrint d[1]
        if(d[1] <= dist and d[0] > 0):
            ptCandidat.append([d[0], points[j].z, j])

      #logPrint "ptCandidat", ptCandidat

      for i in range(0, self.getNpts()):
        pt = self.pts[i]
        # le point n'est traite que s'il n'a pas de z ou que l'on veut modifier tous les z des points du profil
        if (pt.z == -9999 or all == True):
          # recherche des points du nuage proches
          # calcul des distances des points a la polyligne et stocker les abcisses curvilignes
          [absPt, d0] = self.projeterPointSurPolyline(pt)
          #pt.pprint("pt traité")
          #logPrint "absPt ", absPt, "d0 ", d0
          
          # recherche du point precedent et du point suivant les plus proches du point à déterminer
          dprec = 10.e+20
          dsuiv = 10.e+10
          zprec = -9999
          zsuiv = -9999
          for j in range(0, len(ptCandidat)):
             if(ptCandidat[j][0] <= absPt):
               d = absPt - ptCandidat[j][0]
               if (d < dprec):
                 dprec = d
                 zprec = ptCandidat[j][1]
             if(ptCandidat[j][0] >= absPt):
               d = ptCandidat[j][0] - absPt 
               if (d < dsuiv):
                 dsuiv = d
                 zsuiv = ptCandidat[j][1]

          # faire l'interpolation
          #logPrint dprec, zprec, dsuiv, zsuiv
          if(zprec != -9999 and zsuiv != -9999):
            if(dprec == 0):
               pt.z = zprec
            if(dsuiv == 0):
               pt.z = zsuiv
            if(dprec != 0 and dsuiv != 0):               
                dl = dprec + dsuiv
                pt.z = zprec + dprec * (zsuiv - zprec) / dl
            nModif = nModif + 1
            #pt.pprint("new z")
      return nModif

    def newSegment(self, v, w, dl, sens):
        # Donne le point extremite d'un sgment solineaire au segment v,w situé avant ou apres et de longueur dl
        pt = Point(0,0)
        d = v.distance_squared(w)
        if d == 0:
          #logPrint "Segment de longueur nulle"
          #v.pprint()
          #w.pprint()
          return None
        if(w.x != v.x):
          pente = (w.y - v.y)/(w.x - v.x)
          #v.pprint("v")
          #w.pprint("w")
          #logPrint pente
          if(w.x > v.x):
            dx = dl/math.sqrt(1+(pente*pente))
          else:
            dx = -dl/math.sqrt(1+(pente*pente))
          dy = dx * pente            
        else:
          dx = 0
          if(w.y > v.y):
            dy = dl
          else:
            dy = -dl
                        
        #logPrint dx, dy
        if(sens > 0):
          pt.x = w.x + dx
          pt.y = w.y + dy
        else:
          pt.x = v.x - dx
          pt.y = v.y - dy
                   
        return pt

           
    
    def definirZparPointsProches3(self, points, dist, all):
      #Methode par projection de points sur le profil (les points projetes hors profils ne sont pas gérés)
      d2 = dist * dist
      nModif = 0
      # On prolonge le profil au debut et a la fin d'un segment egal à 2 fois la distance par 
      # creation d'un point en debut et d'un autre en fin d eprofil
      dl = 2 * dist
      #segment de debut
      newDebut = self.newSegment(self.pts[0], self.pts[1], dl, -1)
      ldebut = newDebut.distance(self.pts[0])
      #newDebut.pprint("newDebut")
      nb = self.getNpts()
      newFin = self.newSegment(self.pts[nb-2], self.pts[nb-1], dl, +1)
      #newFin.pprint("newFin")
      newPts = []
      newPts.append(newDebut)
      for i in range(0, self.getNpts()):
          newPts.append(self.pts[i])
      newPts.append(newFin)
      newPoly = Polyligne(newPts)
      #newPoly.pprint("newPoly")
      
      ptCandidat = []
      for j in range(0, len(points)):
        d = newPoly.projeterPointSurPolyline(points[j])
        #logPrint d[1]
        if(d[1] <= dist and d[0] > 0):
            ptCandidat.append([d[0]-ldebut, points[j].z, j])

      #for j in range(0, len(ptCandidat)):
        #logPrint("ptCandidat " + str(ptCandidat[j][0]) + " " + str(ptCandidat[j][1]) + " " + str(ptCandidat[j][2]))
        #logPrint("ptCandidat ",ptCandidat[j][0],ptCandidat[j][1],ptCandidat[j][2])

      for i in range(0, self.getNpts()):
        pt = self.pts[i]
        # le point n'est traite que s'il n'a pas de z ou que l'on veut modifier tous les z des points du profil
        if (pt.z == -9999 or all == True):
          # recherche des points du nuage proches
          # calcul des distances des points a la polyligne et stocker les abcisses curvilignes
          [absPt, d0] = self.projeterPointSurPolyline(pt)
          #pt.pprint("pt traité :"+str(i))
          #print  "deb1",absPt, d0
          #logPrint("absPt "+str(absPt)+"d0 "+str(d0))
          
          # recherche du point precedent et du point suivant les plus proches du point à déterminer
          dprec = 10.e+20
          dsuiv = 10.e+10
          zprec = -9999
          zsuiv = -9999
          for j in range(0, len(ptCandidat)):
             if(ptCandidat[j][0] <= absPt):
               d = absPt - ptCandidat[j][0]
               if (d < dprec):
                 dprec = d
                 zprec = ptCandidat[j][1]
             if(ptCandidat[j][0] >= absPt):
               d = ptCandidat[j][0] - absPt 
               if (d < dsuiv):
                 dsuiv = d
                 zsuiv = ptCandidat[j][1]

          # faire l'interpolation
          #print "deb1" ,dprec, zprec, dsuiv, zsuiv
          if(zprec != -9999 and zsuiv != -9999):
            if(dprec == 0):
               pt.z = zprec
            if(dsuiv == 0):
               pt.z = zsuiv
            if(dprec != 0 and dsuiv != 0):               
                dl = dprec + dsuiv
                pt.z = zprec + dprec * (zsuiv - zprec) / dl
            nModif = nModif + 1
        #print "z ", pt.z
      return nModif
    
  
    def definirZparPointsProches4(self, points, dist, all):
      #Methode par projection de points sur le profil (les points projetes hors profils ne sont pas gérés)
      d2 = dist * dist
      nModif = 0
      # On prolonge le profil au debut et a la fin d'un segment egal à 2 fois la distance par 
      # creation d'un point en debut et d'un autre en fin d eprofil
      dl = 2 * dist
      #segment de debut
      newDebut = self.newSegment(self.pts[0], self.pts[1], dl, -1)
      ldebut = newDebut.distance(self.pts[0])
      #newDebut.pprint("newDebut")
      nb = self.getNpts()
      newFin = self.newSegment(self.pts[nb-2], self.pts[nb-1], dl, +1)
      #newFin.pprint("newFin")
      newPts = []
      newPts.append(newDebut)
      for i in range(0, self.getNpts()):
          newPts.append(self.pts[i])
      newPts.append(newFin)
      newPoly = Polyligne(newPts)
      #newPoly.pprint("newPoly")
      
      ptCandidat = []
      for j in range(0, len(points)):
        d = newPoly.projeterPointSurPolyline(points[j])
        #logPrint d[1]
        if(d[1] <= dist and d[0] > 0):
            ptCandidat.append([d[0]-ldebut, points[j].z, j])

      #print "ptCandidat", ptCandidat

      for i in range(0, self.getNpts()):
                
        pt = self.pts[i]
        # le point n'est traite que s'il n'a pas de z ou que l'on veut modifier tous les z des points du profil
        if (pt.z == -9999 or all == True):
          # recherche des points du nuage proches
          # calcul des distances des points a la polyligne et stocker les abcisses curvilignes
          [absPt, d0] = self.projeterPointSurPolyline(pt)
          #pt.pprint("pt traité :"+str(i))
          #logPrint "absPt ", absPt, "d0 ", d0
          
          # recherche du point precedent et du point suivant les plus proches du point à déterminer
          dprec = 10.e+20
          dsuiv = 10.e+10
          zprec = -9999
          zsuiv = -9999
          # On regarde si dans l'ancienne polyligne (newPoly), quel est le premier point avant et apres qui a son altitude definie
          # indice augmente de 1, car on a rajoute un point au debut et  a la fin de Newpoly, 
          # donc le 1er et le dernier point ont toujours z indefini

          if (all != True):
              iprec = i-1+1
              isuiv = i+1+1
              #logPrint "toto", iprec, isuiv
              for j in range(iprec, 0, -1): 
                  if(newPoly.pts[j].z != -9999):
                      zprec = newPoly.pts[j].z
                      [absPrec, d0] = newPoly.projeterPointSurPolyline(newPoly.pts[j])
                      dprec = absPt - (absPrec - ldebut)
                      break
                  
              for j in range(isuiv, newPoly.getNpts()): 
                  if(newPoly.pts[j].z != -9999):
                      zsuiv = newPoly.pts[j].z
                      [absSuiv, d0] = newPoly.projeterPointSurPolyline(newPoly.pts[j])
                      dsuiv = (absSuiv - ldebut) - absPt
                      break
          #logPrint "toto",i, dprec, zprec, dsuiv, zsuiv
          
          for j in range(0, len(ptCandidat)):
             if(ptCandidat[j][0] <= absPt):
               d = absPt - ptCandidat[j][0]
               if (d < dprec):
                 dprec = d
                 zprec = ptCandidat[j][1]
             if(ptCandidat[j][0] >= absPt):
               d = ptCandidat[j][0] - absPt 
               if (d < dsuiv):
                 dsuiv = d
                 zsuiv = ptCandidat[j][1]

          # faire l'interpolation
          #logPrint dprec, zprec, dsuiv, zsuiv
          if(zprec != -9999 and zsuiv != -9999):
            if(dprec == 0):
               pt.z = zprec
            if(dsuiv == 0):
               pt.z = zsuiv
            if(dprec != 0 and dsuiv != 0):               
                dl = dprec + dsuiv
                pt.z = zprec + dprec * (zsuiv - zprec) / dl
            nModif = nModif + 1
            pt.pprint("new z")
      return nModif
  
    def orienterPolyline(self, axeHydro, ptInters):
        abscisAxe = axeHydro.abcissePointSurPolyline(ptInters)
        abscisProfil = self.abcissePointSurPolyline(ptInters)
        ptsAxe = axeHydro.pointsAvantApresAbcissse(abscisAxe)
        ptsProfil = self.pointsAvantApresAbcissse(abscisProfil)
        # Vecteur Axe
        vAxe = Vecteur2d()
        vAxe.par2points(ptsAxe[0], ptsAxe[1])
         # Vecteur normal au profil
        vProfil = Vecteur2d()
        vProfil.par2points(ptsProfil[0], ptsProfil[1])
        vNormalProfil = Vecteur2d()
        vNormalProfil.parNormal(vProfil)      
        # Cosinus(vAxe,vNormalProfil)
        cos = vAxe.cosinus(vNormalProfil)
        okSens = True
        if (cos < 0.):
          okSens = False
        return okSens

class Vecteur2d():
    def __init__(self):
      self.u = 0.
      self.v = 0.
      return   

    def pprint(self, com=""):
      "Impression"
      logPrint(com + str(self.u) + str(self.v))
            
    def par2points(self, pt1, pt2):
      self.u = pt2.x - pt1.x
      self.v = pt2.y - pt1.y
      return

    def parNormal(self, v1):
      self.u = -v1.v
      self.v = v1.u
      return

    def norme(self):
      return math.sqrt(self.u * self.u + self.v * self.v)
    
    def cosinus(self, v1):
      scal = self.u * v1.u + self.v * v1.v
      return scal / (self.norme() * v1.norme())
                         



class preCourlisTools():
    
    def __init__(self):
        self.layer = None
        
    def getLayerByName(self,name):    
        
        if(name!='Pas de couche'):
            self.parseTree(QgsProject.instance().layerTreeRoot(),name)
            
        else:
            self.layer = None
        
        return self.layer
        
    def parseTree(self,root,name):        
        
        #parcour recursif
        
        for child in root.children():
            
            if(isinstance(child, QgsLayerTreeGroup)):
                self.parseTree(child,name)
            if(isinstance(child, QgsLayerTreeLayer)):                                     
                if(child.layerName()==name):                                 
                   self.layer = child.layer()
            
    def getProfilsOrdonnesFeatures(self,features):
        profils_ordonne = {}        
        for feat in features:
            profils_ordonne[feat] = feat.attribute('abscisse_axe_hydr') 

        tab_prof_ordonnee =  sorted(profils_ordonne.copy().items(), key=self.get_len_prof)
        return tab_prof_ordonnee  
    
    def getProfilsOrdonnesFeaturesv07(self,lay_axe,features,rename):
        
        
        layer_axe = lay_axe   
        geom=None
        for axe in layer_axe.getFeatures():
            geom= axe.geometry()
        pts = geom.asPolyline()
        
        if(not len(pts)>0):
            QMessageBox.error(None, "Erreur", unicode("Pas d'axe d'écoulement tracé, impossible d'ordonner les profils.","utf-8"), QMessageBox.Ok)   
            return                   
          
            
        polyline = []
        profils_ordonne = {}
        
        first_point = None

                
        for pt in pts:                    
            polyline.append(Point(pt.x(),pt.y()))
            if(first_point==None):
                first_point = Point(pt.x(),pt.y())
                    
        Len = self.abcissePointSurPolyline(Point(pts[-1].x(),pts[-1].y()),polyline)
        #print "Longueur axe = ",Len
              
        for feat in features:
            intersection_axe = feat.attribute('intersection_axe').split(' ')
            Len = self.abcissePointSurPolyline(Point(intersection_axe[0],intersection_axe[1]),polyline)
            #-feat.setAttribute("abscisse_axe_hydr",Len)
            profils_ordonne[feat] = Len 
            feat.setAttribute("abscisse_axe_hydr",Len)
            if(rename==True):
                feat.setAttribute("nom","P_"+"{:0.3f}".format(Len))
            
        tab_prof_ordonnee =  sorted(profils_ordonne.copy().items(), key=self.get_len_prof)
        
        #Petite modif... on n'enregiste plus l'abcisse reel du point de passage de l'axe hydro , mais la distance avant le point precedent
        """
        polyline = []
        polyline.append(first_point)
        for key, value in tab_prof_ordonnee:
            intersection_axe = key.attribute('intersection_axe').split(' ')
            polyline.append(Point(intersection_axe[0],intersection_axe[1]))
        
        #print(polyline)
        offset = 0 
        for key, value in tab_prof_ordonnee:
            intersection_axe = key.attribute('intersection_axe').split(' ')
            Len = self.abcissePointSurPolyline(Point(intersection_axe[0],intersection_axe[1]),polyline)
            print Len
            
            if(Len==0.):
                #Grosse bidouille pour ne pas faire demarrer l'abcisse a zero..
                if(not key.attribute("abscisse_axe_hydr") is None and not isinstance(key.attribute("abscisse_axe_hydr"),QPyNullVariant)):
                    offset=key.attribute("abscisse_axe_hydr")
            if(rename==True):
                key.setAttribute("nom","P_"+"{:0.3f}".format(Len+offset))
            
            key.setAttribute("abscisse_axe_hydr",Len+offset)
                   
            
        #on ordonne les profils selon la distance avec le premier point de l'axe hydro
        """
        return tab_prof_ordonnee  

    def get_len_prof(self,p_and_l):
                    
        return p_and_l[1]
    
    def getProfilsOrdonnes(self,lay_axe,lay_prof):
        
        
        layer_axe = lay_axe   
        geom=None
        for axe in layer_axe.getFeatures():
            geom= axe.geometry()
        pts = geom.asPolyline()
        
        if(not len(pts)>0):
            QMessageBox.error(None, "Erreur", unicode("Pas d'axe d'écoulement tracé, impossible d'ordonner les profils.","utf-8"), QMessageBox.Ok)   
            return                   
          
            
        polyline = []
        profils_ordonne = {}
                
        for pt in pts:                    
            polyline.append(Point(pt.x(),pt.y()))
                    
              
        for profil in lay_prof():
            intersection_axe = profil.attribute('intersection_axe').split(' ')
            Len = self.abcissePointSurPolyline(Point(intersection_axe[0],intersection_axe[1]),polyline)
            profils_ordonne[profil] = Len   
            
        #on ordonne les profils selon la distance avec le premier point de l'axe hydro
        return sorted(profils_ordonne.copy().items(), key=self.get_len_prof)     
        
                
    def check_if_not_numeric(self, a):
       try:
           float(a)
       except ValueError:
           return True
       return False
    
    def square(self, x):
      return x * x
      
    def distance_squared(self, v, w):
      "distance au carre en 2 points v et w"
      return v.distance_squared(w)
    
    def distance_point_segment_squared(self, p, v, w):
      "distance normale d'un point p a un segment defini par 2 point v et w"
      "retourne le carre de la distance normale au segement, et l'abcisse curviligne du point projete sur le segment (-1 si hors segment)"
      # Segment length squared, |w-v|^2
      return p.distance_point_segment_squared(v, w)
      
    def distance_point_segment(self, p, v, w):
      "distance normale d'un point p a un segment defini par 2 point v et w"
      "retourne le carre de la distance normale au segemnt, et l'abcisse curviligne du point projete sur le segment (-1 si hors segment)"
      d = p.distance_point_segment_squared(v, w)
      return math.sqrt(d[0]), d[1]
    
    def abcissePointSurPolyline(self, p, poly):
      pl = Polyligne(poly)
      return pl.abcissePointSurPolyline(p)

    def creerListePoints(self, tabx, taby, tabz):
      listePoints = []
      for l in range(0, len(tabx)):
        listePoints.append(Point(tabx[l], taby[l], tabz[l]))
      return listePoints                             
        
    def creerPolylineIntermediaire(self, l1, l2, pt1Axe, pt2Axe, ptsAxe, profilExtrem=True):
      nt = len(l1.pts)
      # logPrint nt
      li = []
      if (profilExtrem == True):
        li.append(l1)
      nl = len(ptsAxe)
      # logPrint nl
      for l in range(0, nl):
        Pti = []
        dl0 = pt1Axe.distance(ptsAxe[l]) / pt1Axe.distance(pt2Axe)
        # logPrint dl0
        for t in range(0, nt):
          poly = [l1.pts[t], l2.pts[t]]
          seg = Polyligne(poly)
          lseg = l1.pts[t].distance(l2.pts[t])          
          dl = dl0 * lseg
          # logPrint l,t,lseg, dl
          Pti.append(seg.pointAbcissseSurPolyline(dl))
        lnew = Polyligne(Pti)
        li.append(lnew) 
      if (profilExtrem == True):
        li.append(l2)
    
      return li

    def creerPolylineIntermediairePctr(self, poly1, poly2, pctr1, pctr2, pt1Axe, pt2Axe, ptsAxe, profilExtrem, dltrans):
      
      nbDiscret = 500
      abci1 = poly1.calculerAbcisses()
      abci2 = poly2.calculerAbcisses()
      s1ori = 0.
      s2ori = 0.
      ptsPoly1 = []
      ptsPoly2 = []
      ptsPoly1.append(poly1.pts[0])
      ptsPoly2.append(poly2.pts[0])
      nctr = len(pctr1)
      #print "Nctr",nctr
      polyFinal = []
    
      for t in range(0, nctr):
        # Projeter les points de contraintes
        pctr1[t].pprint("Ligne de contrainte : " + str(t) + "\npctr1")
        s1ext = poly1.abcissePointSurPolyline(pctr1[t])
        # logPrint s1ext
        poly1.pprint("poly1")
        p1 = poly1.pointAbcissseSurPolyline(s1ext)
        p1.pprint("p1")

        pctr2[t].pprint("pctr2")
        s2ext = poly2.abcissePointSurPolyline(pctr2[t])
        # logPrint s2ext
        poly2.pprint("poly2")
        p2 = poly2.pointAbcissseSurPolyline(s2ext)
        p2.pprint("p2")
        for s in range(1, len(poly1.pts)):
          if (abci1[s] > s1ori and abci1[s] < s1ext):
            ptsPoly1.append(poly1.pts[s])
        ptsPoly1.append(p1)
        
        segPoly1 = Polyligne(ptsPoly1)
        segPoly1.pprint("segment poly1 :")
    
        for s in range(1, len(poly2.pts)):
          if (abci2[s] > s2ori and abci2[s] < s2ext):
            ptsPoly2.append(poly2.pts[s])
        ptsPoly2.append(p2)
        
        segPoly2 = Polyligne(ptsPoly2)
        segPoly2.pprint("segment poly2 :")
        
        # discretisation du segment pour avoir un nombre d'intervalle egal amont et aval
        Pt1 = segPoly1.discretiserPolyline(nbDiscret)
        polyPt1 = Polyligne(Pt1)
        polyPt1.pprint("Pt1:")
        #print "nbr points Pt1",t,len(Pt1)
        Pt2 = segPoly2.discretiserPolyline(nbDiscret)
        polyPt2 = Polyligne(Pt2)
        #polyPt2.pprint("Pt2:")
    
        # logPrint "\n polylines interpolees"
        plsint = self.creerPolylineIntermediaire(polyPt1, polyPt2, pt1Axe, pt2Axe, ptsAxe, profilExtrem)
        
        # rediscretiser les segments amont, intermediaire(s) et aval
        polySeg = []
        for l in range(0, len(plsint)):
          polySeg.append(plsint[l].discretiserPolylineDl(dltrans))
    
        polyFinal.append(polySeg)
        s1ori = s1ext
        s2ori = s2ext
        ptsPoly1 = []
        ptsPoly2 = []
        ptsPoly1.append(p1)
        ptsPoly2.append(p2)
      
      # dernier segment
      s1ext = abci1[len(abci1) - 1]
      for s in range(1, len(poly1.pts)):
        if (abci1[s] > s1ori and abci1[s] < s1ext):
          ptsPoly1.append(poly1.pts[s])
      ptsPoly1.append(poly1.pts[len(abci1) - 1])
      # logPrint "segment poly1 :",nctr+1
      # for s in range(0, len(ptsPoly1)):
      #  logPrint s,ptsPoly1[s].x,ptsPoly1[s].y
    
      s2ext = abci2[len(abci2) - 1]
      for s in range(1, len(poly2.pts)):
        if (abci2[s] > s2ori and abci2[s] < s2ext):
          ptsPoly2.append(poly2.pts[s])
      ptsPoly2.append(poly2.pts[len(abci2) - 1])
      # logPrint "segment poly2 :",nctr+1
      # for s in range(0, len(ptsPoly2)):
      #  logPrint s,ptsPoly2[s].x,ptsPoly2[s].y
    
      # discretisation du dernier segment
      newPoly1 = Polyligne(ptsPoly1)
      Pt1 = newPoly1.discretiserPolyline(nbDiscret)
      # for s in range(0, 4):
      #  logPrint "Pt1:",Pt1[s].x,Pt1[s].y
      newPoly2 = Polyligne(ptsPoly2)
      Pt2 = newPoly2.discretiserPolyline(nbDiscret)
      # for s in range(0, 4):
      #  logPrint "Pt2:",Pt2[s].x,Pt2[s].y
    
      logPrint("\n polylines interpolees")
      
      plsint = self.creerPolylineIntermediaire(Polyligne(Pt1), Polyligne(Pt2), pt1Axe, pt2Axe, ptsAxe, profilExtrem)
      polySeg = []
      for s in range(0, len(plsint)):
        polySeg.append(plsint[s].discretiserPolylineDl(dltrans))
      polyFinal.append(polySeg)
      for l in range(0, len(plsint)):
        logPrint("profil : " + str(l))
        #for t in range(0, nctr + 1):
          #for s in range(0, len(polyFinal[t][l])):
            #logPrint(str(t) + str(polyFinal[t][l][s].x) + str(polyFinal[t][l][s].y) + str(polyFinal[t][l][s].z))
          
      polyComp = []
      for l in range(0, len(plsint)):
        polySeg = []
        for t in range(0, nctr + 1):
          nbp = len(polyFinal[t][l]) - 1
          if (t == nctr) : nbp = nbp + 1
          #logPrint("nbp, l, t :" + str(nbp) + str(l) + str(t))
          for n in range(0, nbp):
            polySeg.append(polyFinal[t][l][n])
        #for n in range(0, len(polySeg)):
          #logPrint("Profil :" + str(l) + "points :" + str(n) + str(polySeg[n].x) + str(polySeg[n].y) + str(polySeg[n].z))
          
        polyComp.append(polySeg)
    
      #for l in range(0, len(plsint)):
        #logPrint("profil : " + str(l))
        #for t in range(0, len(polyComp[l])):
          #logPrint(str(t) + str(polyComp[l][t].x) + str(polyComp[l][t].y) + str(polyComp[l][t].z))
      return polyComp

    def interpolerProfils(self, ptProfilsMaitres, nomProfils, ptPolyCtrts, ptInterProfilsAxe, absLongiPm, dlLong, dlTrans, MaitreEtInterp):
        #les Profils sont supposés etre dans l'ordre Amont->Aval de l'axe hydraulique
        #Intersection de l'axe hydraulique avec chaque profil (un point ou null)
        #Intersection des lignes de contraintes avec les profils (un tableau contenant un point ou null pour chaque ligne de contrainte) 
         
        ProfInterp = []
        erreur = 0
        
        nbProfMaitre = len(ptProfilsMaitres)
        nbCtrt = len(ptPolyCtrts)
        # verifier si autant ptInterProfilsAxe que de ptProfilsMaitres
        if(len(ptInterProfilsAxe) != nbProfMaitre):
            print "Erreur tools.interpolerProfils : nbr intersections Axe profils different du nbr de profils maitres ",nbProfMaitre, len(ptInterProfilsAxe)
            erreur = -1
            return ProfInterp, erreur
        
        ptInterProfilsCtrts = []
        profilsMaitres = []
        absAxePm = []
        polyAxe = Polyligne(ptInterProfilsAxe)
        # Sauvegarde de l'abcisse longi à l'origine
        absLongiPm0 = absLongiPm[0]
        for i in range(0, nbProfMaitre):
            profilsMaitres.append(Polyligne(ptProfilsMaitres[i]))
            profilsMaitres[i].pprint(nomProfils[i])
            lsProfil = LineString(profilsMaitres[i].getPts())
            absc = polyAxe.abcissePointSurPolyline(ptInterProfilsAxe[i])
            absAxePm.append(absc)
            # on enleve l'abciise longi a l'origine pour que ce soit comparable à absAxePm
            absLongiPm[i] = absLongiPm[i] - absLongiPm0
            ptInterProfilsCtrt = []
            for j in range(0, len(ptPolyCtrts)):
                polyCtrt = Polyligne(ptPolyCtrts[j])
                #polyCtrt.pprint("ctr " + str(j))
                lsCtrt = LineString(polyCtrt.getPts())
                #polyCtrts[j].pprint()ProfilsMaitres
                p = lsProfil.intersection(lsCtrt)
                #print "INtersection crt", i, j, p
                pt = None
                if(p.is_empty != True):
                    pt = Point(p.x,p.y)
                    pt.pprint("Inter profil - ctr :")
                ptInterProfilsCtrt.insert(j,pt)
                             
            #print ptInterProfilsCtrt
            ptInterProfilsCtrts.append(ptInterProfilsCtrt)
        
        logPrint("absAxePm :" + str(absAxePm))
        #print "absAxePm :" , absAxePm
        
        #determination de l'abcisse sur l'axe hydro des profils interpolles
        #abcisse curviligne du 1er profil sur l'axe hydro
        #verification que l'axe hydro coupe tous les profils
        
        absAxeProfInterpol = []
        absLongiProfInterpol = []
        
        longAxePm = absAxePm[-1]
        longLongiPm = absLongiPm[-1]
        #print "longAxePm",longAxePm,"longLongiPm",longLongiPm
        absAxe = absAxePm[0]
        absLongi = absLongiPm[0]
        
        for i in range(0, nbProfMaitre-1):            
            rapport = (absAxePm[i+1]-absAxePm[i])/(absLongiPm[i+1]-absLongiPm[i])
            while absLongi < absLongiPm[i+1] :
               absAxeProfInterpol.append(absAxe)
               absLongiProfInterpol.append(absLongi)
               absAxe = absAxe + dlLong*rapport
               absLongi = absLongi + dlLong

        # Ajout du dernier profil
        absAxeProfInterpol.append(longAxePm)
        absLongiProfInterpol.append(longLongiPm)
        logPrint("absAxeProfInterpol :" + str(absAxeProfInterpol))
        #print "absAxeProfInterpol :" , absAxeProfInterpol
        

        # creation des profils
        nbProfilInterpol = len(absAxeProfInterpol)
        tmpProfInterp = []
        for i in range(0, nbProfilInterpol):
            logPrint("\n profil interpolé : \n" + str(i))
            #recherche de l'intervalle dans lequel se trouve le profil a interpoler
            ptAxeProfInterpol = polyAxe.pointAbcissseSurPolyline(absAxeProfInterpol[i])
            
            amont = 0
            aval = 0
            for j in range(1, nbProfMaitre-1):
                #print absAxeProfInterpol[i], absAxePms[j] 
                if(absAxePm[j] < absAxeProfInterpol[i]):
                    amont = amont + 1               

            aval = amont + 1
            logPrint("profil amont =" + str(amont))
            #print absAxeProfInterpol[i], absAxeProfMaitre[amont]
         
            pctrAval = []
            pctrAmont = []
            absctPctrAmont = []
            pctrAmont_for_trie = []
            pctrAval_for_trie = []
            # recherche des lignes de contraintes a utiliser sur ce profil
            for k in range(0, nbCtrt):
                if(ptInterProfilsCtrts[amont][k] != None and  ptInterProfilsCtrts[aval][k] != None):
                    pt = ptInterProfilsCtrts[amont][k]
                    pctrAmont.append(pt)
                    pctrAval.append(ptInterProfilsCtrts[aval][k])
                    absctPctrAmont.append(Polyligne(ptProfilsMaitres[amont]).abcissePointSurPolyline(pt))
                    #self.absctPctrAmont_cop = absctPctrAmont
                    i_pctr=0
                    for pts in  pctrAmont:
                        pctrAmont_for_trie.append([pts,absctPctrAmont[i_pctr]])
                        pctrAval_for_trie.append([pctrAval[i_pctr],absctPctrAmont[i_pctr]])
                        i_pctr = i_pctr+1
                    
            
            #tri pour ordonner les points de contraintes sur le profil dans l'ordre de l'abcisse curviligne
            if(len(pctrAmont) != 0):
                pctrAmont_for_trie.sort(key=lambda colonnes: colonnes[1], reverse=False)
                pctrAval_for_trie.sort(key=lambda colonnes: colonnes[1], reverse=False)
                 
                pctrAmont = [pt_t[0] for pt_t in pctrAmont_for_trie]
                pctrAval = [pt_t[0] for pt_t in pctrAval_for_trie]
            
            l1 = profilsMaitres[amont]
            l2 = profilsMaitres[aval]
            pt1Axe = ptInterProfilsAxe[amont]
            pt2Axe = ptInterProfilsAxe[aval]
            ptAxe = [ptAxeProfInterpol]
            ptProfil = self.creerPolylineIntermediairePctr(l1, l2, pctrAmont, pctrAval, pt1Axe, pt2Axe, ptAxe, False, dlTrans)
            absLongi = absLongiProfInterpol[i] + absLongiPm0
            nomProfilInterpol = "P_" + "{:0.3f}".format(absLongi)
            tmpProfInterp.append((ptProfil[0], nomProfilInterpol, ptAxeProfInterpol,absLongiProfInterpol[i]))
                
        if(MaitreEtInterp == False):
            ProfInterp = tmpProfInterp
        else:
            #on ajoute les profils maitres (on garde profil maitre si trop proche de profil interpole)
            inter = 0.001 * dlLong
            #on commence par le premier profil
            for i in range(0, nbProfMaitre - 1):
                absc = absLongiPm[i]
                ProfInterp.append((ptProfilsMaitres[i], nomProfils[i],ptInterProfilsAxe[i],absc))
                abscNext = absLongiPm[i+1]
                # insertion des profils interpoles
                for j in range(0, nbProfilInterpol):
                    absInter = absLongiProfInterpol[j]
                    # on garde un profilinterpole s'il est distant de plus de "inter" des profils maitres
                    if(absInter > (absc + inter) and absInter < (abscNext - inter)):
                       ProfInterp.append((tmpProfInterp[j][0], tmpProfInterp[j][1],tmpProfInterp[j][2],absInter))

            ProfInterp.append((ptProfilsMaitres[-1], nomProfils[-1],ptInterProfilsAxe[-1],abscNext))
             
        return ProfInterp, erreur

    def interpolerProfilsv07(self, ptProfilsMaitres, nomProfils, ptPolyCtrts, ptInterProfilsAxe, dlLong, dlTrans, MaitreEtInterp, abs0):
        #les Profils sont supposés etre dans l'ordre Amont->Aval de l'axe hydraulique
        #Intersection de l'axe hydraulique avec chaque profil (un point ou null)
        #Intersection des lignes de contraintes avec les profils (un tableau contenant un point ou null pour chaque ligne de contrainte) 
         
        ProfInterp = []
        erreur = 0
        
        nbProfMaitre = len(ptProfilsMaitres)
        nbCtrt = len(ptPolyCtrts)
        # verifier si autant ptInterProfilsAxe que de ptProfilsMaitres
        if(len(ptInterProfilsAxe) != nbProfMaitre):
            print "Erreur tools.interpolerProfils : nbr intersections Axe profils different du nbr de profils maitres ",nbProfMaitre, len(ptInterProfilsAxe)
            erreur = -1
            return ProfInterp, erreur
        
        ptInterProfilsCtrts = []
        profilsMaitres = []
        polyAxe = Polyligne(ptInterProfilsAxe)
        absAxeProfMaitre = []       
        for i in range(0, nbProfMaitre):
            profilsMaitres.append(Polyligne(ptProfilsMaitres[i]))
            profilsMaitres[i].pprint(nomProfils[i])
            lsProfil = LineString(profilsMaitres[i].getPts())
            absc = polyAxe.abcissePointSurPolyline(ptInterProfilsAxe[i])
            absAxeProfMaitre.append(absc)
            ptInterProfilsCtrt = []
            for j in range(0, len(ptPolyCtrts)):
                polyCtrt = Polyligne(ptPolyCtrts[j])
                #polyCtrt.pprint("ctr " + str(j))
                lsCtrt = LineString(polyCtrt.getPts())
                #polyCtrts[j].pprint()
                p = lsProfil.intersection(lsCtrt)
                #print "INtersection crt", i, j, p
                pt = None
                if(p.is_empty != True):
                    pt = Point(p.x,p.y)
                    pt.pprint("Inter profil - ctr :")
                ptInterProfilsCtrt.insert(j,pt)
                             
            #print ptInterProfilsCtrt
            ptInterProfilsCtrts.append(ptInterProfilsCtrt)
        
        logPrint("absAxeProfMaitre :" + str(absAxeProfMaitre))
        #print "absAxeProfMaitre :" , absAxeProfMaitre
        
        #determination de l'abcisse sur l'axe hydro des profils interpolles
        #abcisse curviligne du 1er profil sur l'axe hydro
        #verification que l'axe hydro coupe tous les profils
        
        absAxeProfInterpol = []
        
        longAxe = polyAxe.abcissePointSurPolyline(ptInterProfilsAxe[len(ptInterProfilsAxe)-1])
        absc = polyAxe.abcissePointSurPolyline(ptInterProfilsAxe[0])
        absAxeProfInterpol.append(absc)
        absc = absc + dlLong
        while absc < longAxe :
           absAxeProfInterpol.append(absc)
           absc = absc + dlLong
        # Ajout du dernier profil
        absAxeProfInterpol.append(longAxe)
        logPrint("absAxeProfInterpol :" + str(absAxeProfInterpol))
        #print "absAxeProfInterpol :" , absAxeProfInterpol
        
        # creation des profils
        nbProfilInterpol = len(absAxeProfInterpol)
        tmpProfInterp = []
        for i in range(0, nbProfilInterpol):
            logPrint("\n profil interpolé : \n" + str(i))
            #recherche de l'intervalle dans lequel se trouve le profil a interpoler
            ptAxeProfInterpol = polyAxe.pointAbcissseSurPolyline(absAxeProfInterpol[i])
            
            amont = 0
            aval = 0
            for j in range(1, nbProfMaitre-1):
                #print absAxeProfInterpol[i], absAxeProfMaitre[j] 
                if(absAxeProfMaitre[j] < absAxeProfInterpol[i]):
                    amont = amont + 1               

            aval = amont + 1
            logPrint("profil amont =" + str(amont))
            #print absAxeProfInterpol[i], absAxeProfMaitre[amont]
         
            pctrAval = []
            pctrAmont = []
            absctPctrAmont = []
            pctrAmont_for_trie = []
            pctrAval_for_trie = []
            # recherche des lignes de contraintes a utiliser sur ce profil
            for k in range(0, nbCtrt):
                if(ptInterProfilsCtrts[amont][k] != None and  ptInterProfilsCtrts[aval][k] != None):
                    pt = ptInterProfilsCtrts[amont][k]
                    pctrAmont.append(pt)
                    pctrAval.append(ptInterProfilsCtrts[aval][k])
                    absctPctrAmont.append(Polyligne(ptProfilsMaitres[amont]).abcissePointSurPolyline(pt))
                    #self.absctPctrAmont_cop = absctPctrAmont
                    i_pctr=0
                    for pts in  pctrAmont:
                        pctrAmont_for_trie.append([pts,absctPctrAmont[i_pctr]])
                        pctrAval_for_trie.append([pctrAval[i_pctr],absctPctrAmont[i_pctr]])
                        i_pctr = i_pctr+1
                    
            
            #tri pour ordonner les points de contraintes sur le profil dans l'ordre de l'abcisse curviligne
            if(len(pctrAmont) != 0):
                pctrAmont_for_trie.sort(key=lambda colonnes: colonnes[1], reverse=False)
                pctrAval_for_trie.sort(key=lambda colonnes: colonnes[1], reverse=False)
                 
                pctrAmont = [pt_t[0] for pt_t in pctrAmont_for_trie]
                pctrAval = [pt_t[0] for pt_t in pctrAval_for_trie]
            
            l1 = profilsMaitres[amont]
            l2 = profilsMaitres[aval]
            pt1Axe = ptInterProfilsAxe[amont]
            pt2Axe = ptInterProfilsAxe[aval]
            ptsAxe = [ptAxeProfInterpol]
            ptProfil = self.creerPolylineIntermediairePctr(l1, l2, pctrAmont, pctrAval, pt1Axe, pt2Axe, ptsAxe, False, dlTrans)
            absLongi = absAxeProfInterpol[i] + abs0 
            nomProfilInterpol = "P_" + "{:0.3f}".format(absLongi)
            tmpProfInterp.append((ptProfil[0], nomProfilInterpol, ptAxeProfInterpol,absAxeProfInterpol[i]))
                
        Test = False
        if(Test == True):
            for i in range(0, nbProfMaitre):
                ProfInterp.append((ptProfilsMaitres[i], nomProfils[i],ptInterProfilsAxe[i]))
        else:            
            if(MaitreEtInterp == False):
                ProfInterp = tmpProfInterp
            else:
                #on ajoute les profils maitres (on garde profil maitre si trop proche de profil interpole)
                inter = 0.001 * dlLong
                #on commence par le premier profil
                for i in range(0, nbProfMaitre - 1):
                    absc = absAxeProfMaitre[i]
                    ProfInterp.append((ptProfilsMaitres[i], nomProfils[i],ptInterProfilsAxe[i],absc))
                    abscNext = absAxeProfMaitre[i+1]
                    # insertion des profils interpoles
                    for j in range(0, nbProfilInterpol):
                        absInter = absAxeProfInterpol[j]
                        # on garde un profilinterpole s'il est distant de plus de "inter" des profils maitres
                        if(absInter > (absc + inter) and absInter < (abscNext - inter)):
                           ProfInterp.append((tmpProfInterp[j][0], tmpProfInterp[j][1],tmpProfInterp[j][2],absInter)) 
                ProfInterp.append((ptProfilsMaitres[nbProfMaitre - 1], nomProfils[nbProfMaitre - 1],ptInterProfilsAxe[nbProfMaitre - 1],abscNext))
             
        return ProfInterp, erreur
       
if __name__ == "__main__":
  p = Point(0, 0)
  p.pprint()
  v = Point(-1, 1)
  w = Point(1, 1)
  
  print p.distance_squared(v)
  print p.distance(v)
  assert p.distance_point_segment(v, w) == (1.0, 1.0)
  
  tools = preCourlisTools()
  assert tools.distance_point_segment(p, v, w) == (1.0, 1.0)
  
  v = Point(-1, -1)
  w = Point(1, 1)
  assert tools.distance_point_segment(p, v, w) == (0.0, math.sqrt(1 + 1))

  v = Point(0, 5)  
  w = Point(10, -5)
  assert tools.distance_point_segment(p, v, w) == (math.sqrt(6.25 + 6.25), math.sqrt(2.5 * 2.5 + 2.5 * 2.5))
  
  v = Point(10, 10)
  w = Point(20, 20)
  assert tools.distance_point_segment(p, v, w) == (math.sqrt(100 + 100), -1)

  p = Point(9, 3)
  v = Point(7, 2)
  w = Point(11, 4)
  assert tools.distance_point_segment(p, v, w) == (0., math.sqrt(2 * 2 + 1 * 1))
  
  points1 = [Point(0, 0), Point(2, 2), Point(7, 2, -20), Point(11, 4, -20)]
  polyz1 = [1, 2, 3, 4]
  
  l1 = Polyligne(points1)
  print "l1"
  l1.pprint()  
  l = l1.calculerAbcisses()
  print l[len(points1) - 1]
  l1.pointAbcissseSurPolyline(1.414213562373095).pprint("abscisse : 1.414213562373095 : Point")
  l1.pointAbcissseSurPolyline(12.3005630797).pprint("abscisse : 12.3005630797 : Point")

  p = Point(1, -2)
  p.pprint()
  print "abcisse sur l1 =", l1.abcissePointSurPolyline(p)
    
  p = Point(1, 1)
  p.pprint()
  print "abcisse sur l1 =", l1.abcissePointSurPolyline(p)

  p = Point(0, 2)
  p.pprint()
  print "abcisse sur l1 =", l1.abcissePointSurPolyline(p)

  p = Point(3, 2)
  p.pprint()
  print "abcisse sur l1 =", l1.abcissePointSurPolyline(p)

  p = Point(4.5, 2)
  p.pprint()
  print "abcisse sur l1 =", l1.abcissePointSurPolyline(p)
  
  p = Point(6, 2)
  p.pprint()
  print "abcisse sur l1 =", l1.abcissePointSurPolyline(p)

  p = Point(7, 2)
  p.pprint()
  print "abcisse sur l1 =", l1.abcissePointSurPolyline(p)

  p = Point(9, 3)
  p.pprint()
  print "abcisse sur l1 =", l1.abcissePointSurPolyline(p)

  p = Point(11, 4)
  p.pprint()
  print "abcisse sur l1 =", l1.abcissePointSurPolyline(p)

  p = Point(0, 0)
  p.pprint()
  print "abcisse sur l1 =", l1.abcissePointSurPolyline(p)

  p = Point(11.1, 4)
  p.pprint()
  print "abcisse sur l1 =", l1.abcissePointSurPolyline(p)

  points2 = [Point(1, 1), Point(3, 3), Point(8, 3), Point(12, 5)]
  polyz2 = [2, 3, 4, 5]
  l2 = Polyligne(points2)
  print "l2"
  l2.pprint()
  
  l = l2.calculerAbcisses()
  print l[len(points2) - 1]

  print "abscisse : 1.414213562373095 : Point "
  l2.pointAbcissseSurPolyline(1.414213562373095).pprint()
  print "abscisse : 12.3005630797 : Point "
  l2.pointAbcissseSurPolyline(12.3005630797).pprint()
   
  print "\npoly1"
  Pt1 = l1.discretiserPolyline(3)
  for s in range(0, 4):
    Pt1[s].pprint("Pts " + str(s) + ":")

  print "\npoly2"
  Pt2 = l2.discretiserPolyline(3)
  for s in range(0, 4):
    Pt2[s].pprint("Pts " + str(s) + ":")

  print "\n test Vecteur2d"
  v1 = Vecteur2d()
  pt1 = Point(1, 1)
  pt2 = Point(4, 3)  
  v1.par2points(pt1, pt2)
  v1.pprint("v1")
  v2 = Vecteur2d()
  v2.parNormal(v1)
  v2.pprint("v2 normal à v1")
  print "cos v1 v1 :", v1.cosinus(v1)
  print "cos v1 v2 :", v1.cosinus(v2)
  
  pAxe1 = [Point(7, -3), Point(7, 2), Point(3, 6), Point(3, 11)]
  laxe1 = Polyligne(pAxe1)
  print "laxe1"
  p = Point(6, 3)
  p.pprint("pInters :")  
  print "Orientation profil l2 par rapport axe1 :", l2.orienterPolyline(laxe1, p)
  
  pAxe2 = [Point(1, 3), Point(3, 1)]
  laxe2 = Polyligne(pAxe2)
  print "laxe2"
  p = Point(2, 2) 
  p.pprint("pInters :")
  print "Orientation profil l2 par rapport axe2 :", l2.orienterPolyline(laxe2, p)
  
  pt = l2.pointAbcissseSurPolyline(11.)
  pt.pprint("\npoint interpollé à 11.sur l2")
  
  pt = l2.pointAbcissseSurPolyline(1.)
  pt.pprint("point interpollé à 1. sur l2")
  
  pt1Axe = Point(7, 2)
  pt2Axe = Point(8, 3)
  #ptsAxe = [Point(7.01, 2.01), Point(7.5, 2.5), Point(7.99, 2.99)]
  ptsAxe = [Point(7.0, 2.0), Point(7.5, 2.5), Point(8., 3.)]
  
  print "\nCreation de polylignes entre 2 profils passant par des points de l'axe hydroulique"
  l1.pprint("profil 1 (Amont)")
  pt1Axe.pprint("point de passage de l'axe hydralique sur profil 1 :")
  l2.pprint("profil 2 (Aval)")
  pt2Axe.pprint("point de passage de l'axe hydralique sur profil 2 :")
  for l in range(0, len(ptsAxe)):
    ptsAxe[l].pprint("points de passage des profils a creer sur l'axe hydraulique" + str(l) + ": ")
  
  profils = tools.creerPolylineIntermediaire(l1, l2, pt1Axe, pt2Axe, ptsAxe, True)
  for l in range(0, len(profils)):
    profils[l].pprint("profil : " + str(l))

  
  pCtr1 = [Point(4.5, 2)]
  pCtr2 = [Point(5.5, 3)]
  print("\nProjection point de contraites sur l1")
  l1.abcissePointSurPolyline(pCtr1[0])
  print("\nInterpolation avec lignes de contraites")
  tools.creerPolylineIntermediairePctr(l1, l2, pCtr1, pCtr2, pt1Axe, pt2Axe, ptsAxe, True, 1.5)
  
  tabx = [1., 2., 3.]
  taby = [10., 20., 30.]
  tabz = [100., 200., 300.]
  
  listeP = tools.creerListePoints(tabx, taby, tabz)
  lp = Polyligne(listeP)
  lp.pprint("poly lp")
  
  pt = l1.newSegment(Point(1,1),Point(3,2),1.,-1)
  pt.pprint("newSegment(Point(1,1),Point(3,2),1.,-1)")
  
  pt = l1.newSegment(Point(1,1),Point(3,2),1.,1)
  pt.pprint("newSegment(Point(1,1),Point(3,2),1.,1)")
  
  pt = l1.newSegment(Point(3,2),Point(1,1),1.,-1)
  pt.pprint("newSegment(Point(3,2),Point(1,1),1.,-1)")

  pt = l1.newSegment(Point(3,2),Point(1,1),1.,1)
  pt.pprint("newSegment(Point(3,2),Point(1,1),1.,1)")
  
  pt = l1.newSegment(Point(1,1),Point(3,0),1.,-1)
  pt.pprint("newSegment(Point(1,1),Point(3,0),1.,-1)")
  
  pt = l1.newSegment(Point(1,1),Point(3,0),1.,1)
  pt.pprint("newSegment(Point(1,1),Point(3,0),1.,)")
  
  pt = l1.newSegment(Point(1,1),Point(-1,2),1.,-1)
  pt.pprint("newSegment(Point(1,1),Point(3,0),1.,-1)")
  
  pt = l1.newSegment(Point(1,1),Point(-1,2),1.,1)
  pt.pprint("newSegment(Point(1,1),Point(3,0),1.,1)")
  
  
  pt = l1.newSegment(Point(1,1),Point(1,2),1.,1)
  pt.pprint("newSegment(Point(1,1),Point(1,2),1.,1)")
  
  pt = l1.newSegment(Point(1,2),Point(1,1),1.,1)
  pt.pprint("newSegment(Point(1,2),Point(1,1),1.,1)")
  
  pt = l1.newSegment(Point(1,1),Point(1,2),1.,-1)
  pt.pprint("newSegment(Point(1,1),Point(1,2),1.,-1)")
  
  pt = l1.newSegment(Point(1,2),Point(1,1),1.,-1)
  pt.pprint("newSegment(Point(1,2),Point(1,1),1.,-1)")
  
  pProches = [Point(8, 4, -10), Point(8, 1, -20), Point(10, 2, -20), Point(2.9, 3, 20), Point(7, 2, 20), Point(13, 5, 20), Point(1,0,10)]
  
  points2 = [Point(1, 1), Point(3, 3,-20), Point(8, 3), Point(10, 4, -10), Point(12, 5)]
  l2 = Polyligne(points2)
  l2.definirZparPointsProches3(pProches, 1.5, False)
  l2.pprint("\nl2 apres projections points proches 3 :")
  points2 = [Point(1, 1), Point(3, 3,-20), Point(8, 3), Point(10, 4, -10), Point(12, 5)]
  l2 = Polyligne(points2)
  l2.definirZparPointsProches4(pProches, 1.5, False)
  l2.pprint("\nl2 apres projections points proches 4 :")
  
  ptsPolyProfils = []
  points1 = [Point(0, 0), Point(2, 2), Point(7, 2, -20), Point(11, 4, -20)]
  points2 = [Point(0, 10), Point(2, 12), Point(7, 12, -20), Point(11, 14, -20)]
  points3 = [Point(0, 20), Point(2, 22), Point(7, 22, -20), Point(11, 24, -20)]
  ptsPolyProfils.append(points1)
  ptsPolyProfils.append(points2)
  ptsPolyProfils.append(points3)
  
  nomProfils = ["Profil1","Profil2","Profil3"]
  
  ptsPolyCtrts = []
  plc1 = [Point(1, 0),Point(1, 11)]
  plc2 = [Point(5, 0),Point(5, 22)]
  plc3 = [Point(9, 9),Point(9, 24)]
  ptsPolyCtrts.append(plc1)
  ptsPolyCtrts.append(plc2)
  ptsPolyCtrts.append(plc3)
  
  ptsAxe = [Point(4, 2), Point(4, 12), Point(4, 22)]
  DEBUG = True
  
  [profilsInterp, erreur] = tools.interpolerProfils(ptsPolyProfils, nomProfils, ptsPolyCtrts, ptsAxe, 6., 1., False)
  
  logPrint("\nProfils interpoles")
  DEBUG = True
  if(erreur == 0):
      nbProfilsInterp = len(profilsInterp)
      for i in range(0, nbProfilsInterp):
         print "-",profilsInterp[i][1]
         profilsInterp[i][2].pprint("ptInterAxe")
         for j in range(0, len(profilsInterp[i][0])):
             profilsInterp[i][0][j].pprint("Pt " + str(j) + ":")
      