from adam import ConfigManager
import unittest
import tempfile
import pytest
import os.path
import yaml


class ConfigManagerTest(unittest.TestCase):
    """Unit tests for config manager

    """

    def test_empty_config(self):
        config = {}
        config_manager = ConfigManager(file_name=None, raw_config=config)

        with pytest.raises(KeyError):
            config_manager.get_config()

    def test_no_default(self):
        config = {
            'envs': {
                'a': {
                    'url': 'https://a',
                    'workspace': 'a-a-a',
                    'token': 'aaa'
                },
            }
        }
        config_manager = ConfigManager(file_name=None, raw_config=config)
        self.assertIsNotNone(config_manager.get_config())

        config['default_env'] = 'a'
        config_manager = ConfigManager(file_name=None, raw_config=config)
        self.assertIsNotNone(config_manager.get_config())

    def test_no_config_for_environment(self):
        config = {
            'default_env': 'a',
            'envs': {
                'a': {
                    'url': 'https://a',
                    'workspace': 'a-a-a',
                    'token': 'aaa'
                },
            }
        }
        config_manager = ConfigManager(file_name=None, raw_config=config)
        self.assertIsNotNone(config_manager.get_config(environment='a'))

        with pytest.raises(KeyError):
            config_manager.get_config(environment='b')

    def test_read_config(self):
        config = {
            'default_env': 'a',
            'envs': {
                'b': {
                    'url': 'https://b',
                    'workspace': 'b-b-b',
                    'token': 'bbb'
                },
                'a': {
                    'url': 'https://a',
                    'workspace': 'a-a-a',
                    'token': 'aaa'
                },
            }
        }
        config_manager = ConfigManager(file_name=None, raw_config=config)

        a_config = config_manager.get_config(environment='a')
        self.assertIsNotNone(a_config)
        self.assertEqual('https://a', a_config['url'])
        self.assertEqual('a-a-a', a_config['workspace'])
        self.assertEqual('aaa', a_config['token'])

        b_config = config_manager.get_config(environment='b')
        self.assertIsNotNone(b_config)
        self.assertEqual('https://b', b_config['url'])
        self.assertEqual('b-b-b', b_config['workspace'])
        self.assertEqual('bbb', b_config['token'])

        default_config = config_manager.get_config()
        self.assertEqual('aaa', default_config['token'])

    def test_io(self):
        config = {
            'default_env': 'a',
            'envs': {
                'b': {
                    'url': 'https://b',
                    'workspace': 'b-b-b',
                    'token': 'bbb'
                },
                'a': {
                    'url': 'https://a',
                    'workspace': 'a-a-a',
                    'token': 'aaa'
                },
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            fn = os.path.join(tmp, "config1")
            with open(fn, 'w') as fp:
                yaml.dump(config, fp)

            # load, make a change, and write back
            config_manager = ConfigManager(fn)
            a_config = config_manager.get_config()
            a_config['token'] = 'ccc'
            config_manager.to_file()
            print(config_manager)

            # re-read and verify the change has been recorded
            written_config = yaml.safe_load(open(fn))
            print(type(written_config))
            import pprint
            pp = pprint.PrettyPrinter(indent=2)
            pp.pprint(config_manager._config)
            pp.pprint(written_config)
            self.assertDictEqual(config_manager._config, written_config)
