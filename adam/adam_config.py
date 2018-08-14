"""
    set up adam configuration paths
"""
import json
from os.path import expanduser


class setPaths(object):

    home = expanduser("~") + "/adam_home"
    OS = "/"
    config_file = home + OS + 'config' + OS + 'adam_config.json'

    with open(config_file, 'r') as f:
        raw_config = json.load(f)
        adam_path = home + OS + raw_config['adam_config']['adam_package_path']
        data_path = home + OS + raw_config['adam_config']['data_path']
        env_config_path = home + OS + raw_config['adam_config']['environment_config_file']
