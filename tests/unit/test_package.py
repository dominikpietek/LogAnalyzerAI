from importlib.metadata import version
import stackscout

def test_version():
    assert version("stackscout") == stackscout.__version__