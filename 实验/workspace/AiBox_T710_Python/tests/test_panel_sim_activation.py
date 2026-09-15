import os
import importlib
import sys


def test_panel_uses_fake_uart_when_panel_sim_set():
    # Prepare env and path
    os.environ['PANEL_SIM'] = '1'
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    # Ensure a fresh import of panel (remove if previously loaded)
    if 'panel' in sys.modules:
        del sys.modules['panel']

    mod = importlib.import_module('panel')

    # panel should have imported Uart from lib.uart, and simulation should have been enabled
    assert hasattr(mod, 'Uart')
    assert mod.Uart.__name__ == 'FakeUart'

    # cleanup
    del os.environ['PANEL_SIM']
