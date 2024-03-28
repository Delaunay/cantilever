import importlib
import pkgutil

from cantilever.core.parallel import submit, as_completed


def discover_plugins_simple(module):
    """Discover plugins"""
    path = module.__path__
    name = module.__name__

    plugins = {}

    for _, name, _ in pkgutil.iter_modules(path, name + "."):
        plugins[name] = importlib.import_module(name)

    return plugins


def discover_plugins_parallel(module):
    """Discover plugins"""
    path = module.__path__
    name = module.__name__

    plugins = {}

    futures = dict()
    for _, name, _ in pkgutil.iter_modules(path, name + "."):
        f = submit(importlib.import_module, name)
        futures[f] = name
    
    for future in as_completed(futures):
        name = futures[future]
        module = future.result()
        plugins[name] = module

    return plugins


def discover_plugins(module):
    """Discover plugins"""
    return discover_plugins_parallel(module)
