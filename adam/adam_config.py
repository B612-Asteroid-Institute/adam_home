"""
    PASSED FLAKE8 8/28/18
    Set up adam configuration paths
    REVISED: August 22, 2018
"""
import json
from os.path import expanduser
import os


class setPaths(object):
    def initPaths(home=None):

        # Initialize ADAM_home directory path
        pathExists = os.path.exists(home)
        if not pathExists:
            print("Directory: ", home, " does not exist")
            return
        elif pathExists:
            print("Changing adam home path to = ", home)
        else:
            home = expanduser("~") + "/adam_home"
            print("Setting home to default path: ", home)

        OS = "/"
        config_file = home + OS + 'config' + OS + 'adam_config.json'
        config_template_file = home + OS + 'config' + OS +\
            'adam_config_template.json'

        try:
            f = open(config_file)
            f.close()
            file_to_open = config_file
        except FileNotFoundError:
            print("adam_config.json NOT FOUND -\
                 loading adam_config_template.json")
            file_to_open = config_template_file

        # Load ADAM_config.json file to set standard paths wrt ADAM_home
        with open(file_to_open, 'r') as f:
            raw_config = json.load(f)
            adam_path = home + OS +\
                raw_config['adam_config']['adam_package_path']
            data_path = home + OS +\
                raw_config['adam_config']['data_path']
            env_template_path = home + OS +\
                raw_config['adam_config']['environment_template_file']
            env_config_path = home + OS +\
                raw_config['adam_config']['environment_config_file']
            ephem_path = home + OS +\
                raw_config['adam_config']['ephem_path']
            MY_functions_path = home + OS +\
                raw_config['MY_config']['MY_functions_path']

        return (adam_path, data_path, env_template_path,
                env_config_path, ephem_path, MY_functions_path)
