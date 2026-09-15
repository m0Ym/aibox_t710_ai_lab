import os
import importlib
import sys


def test_enable_simulation_monkeypatches_uart_and_cv2(monkeypatch):
    # ensure PANEL_SIM behaviour doesn't depend on real hardware
    os.environ['PANEL_SIM'] = '1'
    # Ensure 'src' is on sys.path so package 'lib' can be imported
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
    mod = importlib.import_module('lib.simulators')
    mod.enable_simulation()
    uart_mod = importlib.import_module('lib.uart')
    assert hasattr(uart_mod, 'Uart')
    # Uart should be our FakeUart class from simulators
    assert uart_mod.Uart.__name__ == 'FakeUart'
