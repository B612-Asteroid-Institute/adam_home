"""The ADAM configuration profile being used by ADAM clients.

Usually, users would not have to use this class because the default configuration just uses prod.
However, in the case of using a sandbox/experimental/demo/etc. environment, the user might define
additional configuration profiles (i.e. using `adamctl login <profile_name> <url>` or
`adamctl config envs.<profile_name>.workspace <workspace_id>`). To set their Python SDK to talk to
that other ADAM environment, the user will include an extra line of code before using the ADAM SDK,
e.g.:

set_config_profile('dev')
"""


class AdamConfigProfile(object):
    """The ADAM config profile being used by ADAM client."""

    def __init__(self, profile_name=None):
        self._profile_name = profile_name

    def __repr__(self):
        return f'AdamConfigProfile(server_env={self._profile_name})'

    @property
    def profile_name(self):
        return self._profile_name

    @profile_name.setter
    def profile_name(self, profile_name):
        self._profile_name = profile_name


def set_config_profile(profile_name=None):
    ADAM_CONFIG_PROFILE.profile_name = profile_name


ADAM_CONFIG_PROFILE = AdamConfigProfile()
