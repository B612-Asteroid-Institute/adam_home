import json

class Config(object):
    def __init__(self, config):
        self.config = config
    
    def get_url(self):
        return self.config['url']
    
    def get_token(self):
        return self.config['token']
    
    def set_token(self, token):
        self.config['token'] = token
    
    def get_workspace(self):
        return self.config['workspace']
    
    def set_workspace(self, workspace):
        self.config['workspace'] = workspace

class ConfigManager(object):
    def __init__(self, file_name):
        with open(file_name, 'r') as f:
            self.raw_config = json.load(f)
    
    def get_config(self, environment=None):
        if environment is None:
            environment = self.raw_config['default_env']
        
        for config in self.raw_config['env_configs']:
            if config['env'] == environment:
                return Config(config)
                
        print("Could not find config for environment %s" % (environment))
        return None

    def to_file(self, file_name):
        with open(file_name, 'w') as f:
            json.dump(self.raw_config, f, indent=4)