import yaml
import os
import os.path
import xdg.BaseDirectory as xdgb

# filename of the config file (w/o the full path)
ADAM_CONFIG_FN = "config"


def _load_raw_config(config_file=None):
    """Load ADAM config from default locations or ``config_file``

    Locates and loads the configuration information for ADAM. If
    ``config_file`` is not None, loads it and returns the de-serialized
    YAML. If ``config_file`` is None, follows the XDG Base Directory
    specification to locate a file named ``$.../adam/config``, usually
    ``~/.config/adam/config``.

    Parameters
    ----------
    config_file : str
        Path to config file to load, or None to search default locations.

    Returns
    -------
    dict
        De-serialized configuration in the form of nested dictionaries.

    """

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
    """Save ADAM config to default location or ``config_file``

    Saves the configuration in ``data`` (nested dicts) to ``config_file``
    (if given) or to the default user-writable location given by the
    XDG Base Directory specification (typically ``~/.config/adam/config``).
    If the file already exists, atomically replaces it with the new data.
    Permissions on the saved file are set to 0o0600.

    Parameters
    ----------
    data : dict
        Configuration data to save
    config_file : str
        Path to config file to save, or None to save to default location.
    """

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
    """Configuration object for ADAM client

    A dict-like object holding the loaded ADAM configuration file.
    Individual items can be get/set/deleted via the ``[]`` notation.
    The keys must be fully-qualified dot-separated names, such as::

        conf["envs.dev.workspace"] = " .... "

    When a key does not refer to a leaf node, returns a nested dict
    of the key's children, i.e.::

        conf["envs.dev"] = " .... "

    returns ``dict(url=..., workspace=..., token=....)``.
    """

    def __init__(self, file_name=None, raw_config=None):
        """Load the ADAM configuration

        Loads ADAM configuration from ``file_name``, or default config file
        if ``file_name==None``.  If ``raw_config`` is given, uses its
        contents to load the configuration (``file_name`` is ignored in that
        case).  The typical use is to instantiate this class w.
        ``file_name`` and ``raw_config`` set to None (i.e., read from the
        default config file).

        Parameters
        ----------
        file_name : str
            Path to config file to load, or None to search default locations.
        raw_config : dict
            dict() of values to interpret as configuration data.
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
        """Get configuration of an ADAM environment

        If ``environment`` is given, equivalent to calling::

            self[f"envs.{environment}"]

        If ``environment`` is None, and ``self["default_env"]`` is set,
        equivalent to calling:

            self[f"envs.{self['default_env']}"]

        If ``environment`` is None, and ``self["default_env"]`` is not set,
        returns the first key in the ``self[envs]`` dict.

        Parameters
        ----------
        environment : str
            environment name (e.g., ``prod`` or ``dev``)

        Raises
        ------
        KeyError
            If the requested environment isn't found.

        """
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
        """Set configuration of an ADAM environment

        Equivalent to calling::

            self[f"envs.{name}"] = cfg

        Parameters
        ----------
        environment : str
            environment name (e.g., ``prod`` or ``dev``)
        cfg : dict
            environment data
        """
        if 'envs' not in self._config:
            self._config['envs'] = {}
        self._config['envs'][name] = cfg

    def to_file(self, file_name=None):
        """Save configuration to ``file_name`` or the default location

        Saves to location proscribed by XDG spec (typically ``~/.config/adam/config``)
        or to ``file_name``, if it's not set to ``None``.

        Parameters
        ----------
        file_name : str
            Path to config file to save, or None to save to default location.
        """
        if file_name is None:
            file_name = self._dest_filename
        _store_raw_config(self._config, file_name)

    def __str__(self):
        ret = "# original config source: {}\n".format(self._source_filename)
        ret += yaml.dump(self._config, indent=2)
        return ret
