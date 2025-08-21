import importlib

def test_import():
    mod = importlib.import_module("deepgem")
    assert hasattr(mod, "__version__")
