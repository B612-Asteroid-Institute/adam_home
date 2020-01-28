import yaml
import os, os.path
import xdg.BaseDirectory as xdgb

# filename of the config file (w/o the full path)
ADAM_CONFIG_FN = "config"

def _load_raw_config(config_file=None):
    if config_file is None:
        # get the default location (if exists)
        config_dir = next(xdgb.load_config_paths("adam"), None)
        if config_dir is not None:
            def_config_file = os.path.join(config_dir, ADAM_CONFIG_FN)
            if os.path.exists(def_config_file):
                config_file = def_config_file

        if config_file is None:
            return "", {}

    # Load the config file (if we have it)
    with open(config_file) as fp:
        return config_file, yaml.safe_load(fp)

def _store_raw_config(data, config_file=None):
    # get place to write
    if config_file is None:
        config_dir = xdgb.save_config_path("adam")
        config_file = os.path.join(config_dir, ADAM_CONFIG_FN)

    # atomically replace the old file (if any) with the new one
    # also ensure permissions are restrictive (since this file holds secrets)
    config_file_tmp = config_file + "." + str(os.getpid())
    fd = os.open(config_file_tmp, os.O_CREAT | os.O_WRONLY, mode=0o600)
    with open(fd, "w") as fp:
        yaml.dump(data, fp, indent=2)
    os.rename(config_file_tmp, config_file)

    return config_file

class ConfigManager(object):

    def __init__(self, file_name=None, raw_config=None):
        """ Initializes from the given file. If a file name is not given,
            checks raw_config, where it would expect a python dictionary
            as would be parsed using json from the config file.
        """
        if raw_config is not None:
            self._source_filename, self._dest_filename, self._config = "", "", raw_config
        else:
            self._source_filename, self._config = _load_raw_config(file_name)
            self._dest_filename = file_name

    def __delitem__(self, key):
        *parents, key = key.split('.')

        c = self._config
        for k in parents:
            c = c[k]

        del c[key]

    def __getitem__(self, key):
        c = self._config
        for k in key.split('.'):
            c = c[k]
        return c

    def __setitem__(self, key, value):
        *parents, key = key.split('.')

        cfg = self._config
        for k in parents:
            try:
                cfg = cfg[k]
            except KeyError:
                cfg = cfg[k] = {}

        cfg[key] = value

    def get_config(self, environment=None):
        # raises KeyError if environment not present, or
        # a default environment is requested but not set
        if environment is None:
            # explicit default environment
            environment = self._config.get('default_env', None)
            if environment is None:
                # first environment listed in the file
                environment = next(iter(self._config['envs'].keys()))

        return self._config['envs'][environment]

    def set_config(self, name, cfg):
        if 'envs' not in self._config:
            self._config['envs'] = {}
        self._config['envs'][name] = cfg

    def to_file(self, file_name=None):
        if file_name is None:
            file_name = self._dest_filename
        _store_raw_config(self._config, file_name)

    def __str__(self):
        ret = "# original config source: {}\n".format(self._source_filename)
        ret += yaml.dump(self._config, indent=2)
        return ret
