import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
os.environ['PANEL_SIM']='1'
from lib.simulators import enable_simulation
enable_simulation()
import importlib
mod = importlib.import_module('panel')
print('panel.Uart =', getattr(mod,'Uart',None))
print('panel.Uart.__name__ =', mod.Uart.__name__)
