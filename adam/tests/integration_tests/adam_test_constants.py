import os

# This is a bit janky. When run automatically through Travis, this file will
# be auto-generated. When run locally, you should put a config file with
# test tokens in your repo at integration_tests/config.json. Contact Laura
# to get the test config file.
TEST_CONFIG_FILE = os.path.dirname(__file__)+ '/config.json'