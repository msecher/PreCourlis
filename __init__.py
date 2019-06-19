def name(): 
  return "precourlis" 
def description():
  return "test import georef"
def version(): 
  return "Version 0.1" 
def qgisMinimumVersion():
  return "2.0"
def classFactory(iface): 
  # load precourlis class from file precourlis
  from precourlis import precourlis 
  return precourlis(iface)
