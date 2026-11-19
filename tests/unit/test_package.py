from importlib.metadata import version

import stackscout


def test_version() -> None:
    assert version("stackscout") == stackscout.__version__
