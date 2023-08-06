import os
import json
from functools import partial

from appdirs import user_config_dir



def option(namespace, name, default=None):
    env_key = f"{namespace.upper()}_{name.upper().replace('.', '_')}"
    return os.getenv(env_key, default=default)


def load_app_configuration(name, author, file):
    filename = os.path.join(user_config_dir(name, author), file)

    with open(filename, 'r') as f:
        configuration = json.load(f)

    return configuration


def save_app_configuration(name, author, file, configuration):
    filename = os.path.join(user_config_dir(name, author), file)

    with open(filename, 'w') as f:
        json.dump(configuration, file)


def namespaced_option(namespace):
    return partial(option, namespace)



