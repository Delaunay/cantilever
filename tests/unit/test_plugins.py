import cantilever.plugins
from cantilever.core import discover_plugins


def test_plugins():
    plugins = discover_plugins(cantilever.plugins)

    assert len(plugins) == 1
