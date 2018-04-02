"""
    propagator_config.py
"""

from datetime import datetime
from tabulate import tabulate

PUBLIC_CONFIG_ALL_PLANETS_AND_MOON = "00000000-0000-0000-0000-000000000001"
PUBLIC_CONFIG_SUN_ONLY = "00000000-0000-0000-0000-000000000002"
PUBLIC_CONFIG_ALL_PLANETS_AND_MOON_AND_ASTEROIDS = "00000000-0000-0000-0000-000000000003"

class PropagatorConfig(object):
    def __init__(self, config_json):
        """Initializes a propagator config from the given JSON, pulling out a few important fields.

           Values for sun, planets, and moon must be "POINT_MASS", "OMIT", or "SPHERICAL_HARMONICS.
           Value for asteroids should be list of asteroid names.
           Value for asteroidsString should be concatenated list of asteroid names.
        """
        supported_params = {'uuid', 'project', 'description', 'sun', 'mercury', 'venus', 'earth', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto', 'moon', 'asteroids', 'asteroidsString'}
        extra_params = config_json.keys() - supported_params
        if len(extra_params) > 0:
            raise KeyError("Unexpected parameters provided: %s" % (extra_params))
        self._uuid = config_json["uuid"]
        self._project = config_json["project"]
        self._description = config_json.get("description")
        self._config_json = config_json


    def __repr__(self):
        return "Config %s" % (self._config_json)
    
    def get_uuid(self):
        return self._uuid
    
    def get_project(self):
        return self._project
        
    def get_description(self):
        return self._description
    
    def get_config_json(self):
        return self._config_json

class PropagatorConfigs(object):
    """Module for managing propagator configurations.

    """
    
    def __init__(self, rest):
        self._rest = rest
        
    def __repr__(self):
        return "PropagatorConfigs module"
    
    def get_configs(self):
        code, response = self._rest.get('/config')
        
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return [PropagatorConfig(c) for c in response['items']]

    # There is no print_configs method. This is much more easily done
    # by viewing the raw json by navigating in a browser to
    # https://adam-dev-193118.appspot.com/_ah/api/adam/v1/config?token=<your token>
    # or http://pro-equinox-162418.appspot.com/_ah/api/adam/v1/config?token=<your token>

    def get_config(self, uuid):
        if uuid is None:
            raise KeyError("UUID is required.")
        
        code, response = self._rest.get('/config/' + uuid)
        
        if code == 404:
            # Project not found.
            return None
        elif code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))
        
        return PropagatorConfig(response)
    
    def new_config(self, config_json):
        """Method to create a config directly from a JSON object rather
           than specifying every parameter. Useful if you'd like to slighly modify
           an existing config (e.g. ignore Jupiter's gravity), or if you are fine
           with default values for most objects ("POINT_MASS" for objects, [] for
           asteroids).
        """
        object_params = {'sun', 'mercury', 'venus', 'earth', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto', 'moon'}
        additional_params = {'project', 'description', 'asteroids'}
        supported_params = object_params | additional_params  # | is set union.
        extra_params = config_json.keys() - supported_params
        if len(extra_params) > 0:
            raise KeyError("Unexpected parameters provided: %s" % (extra_params))
        
        for p in object_params:
            if p in config_json:
                if config_json[p] not in ["POINT_MASS", "OMIT", "SPHERICAL_HARMONICS"]:
                    raise KeyError("Value for " + p + " must be one of " +
                        "POINT_MASS, OMIT, or SPHERICAL_HARMONICS.")
        
        code, response = self._rest.post('/config', config_json)

        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return PropagatorConfig(response)
    
    def delete_config(self, uuid):
        code = self._rest.delete('/config/' + uuid)
        
        if code != 204:
            raise RuntimeError("Server status code: %s" % (code))
