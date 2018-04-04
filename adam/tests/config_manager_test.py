from adam import ConfigManager
import json
import unittest
import tempfile


class ConfigManagerTest(unittest.TestCase):
    """Unit tests for config manager

    """

    def test_empty_config(self):
        config = {}
        config_manager = ConfigManager(file_name=None, raw_config=config)

        self.assertIsNone(config_manager.get_config())

    def test_no_default(self):
        config = {
            'env_configs': [
                {
                    'env': 'a',
                    'url': 'https://a',
                    'workspace': 'a-a-a',
                    'token': 'aaa'
                },
            ]
        }
        config_manager = ConfigManager(file_name=None, raw_config=config)
        self.assertIsNone(config_manager.get_config())

        config['default_env'] = 'a'
        config_manager = ConfigManager(file_name=None, raw_config=config)
        self.assertIsNotNone(config_manager.get_config())

    def test_no_config_for_environment(self):
        config = {
            'default_env': 'a',
            'env_configs': [
                {
                    'env': 'a',
                    'url': 'https://a',
                    'workspace': 'a-a-a',
                    'token': 'aaa'
                },
            ]
        }
        config_manager = ConfigManager(file_name=None, raw_config=config)
        self.assertIsNotNone(config_manager.get_config(environment='a'))
        self.assertIsNone(config_manager.get_config(environment='b'))

    def test_read_config(self):
        config = {
            'default_env': 'a',
            'env_configs': [
                {
                    'env': 'b',
                    'url': 'https://b',
                    'workspace': 'b-b-b',
                    'token': 'bbb'
                },
                {
                    'env': 'a',
                    'url': 'https://a',
                    'workspace': 'a-a-a',
                    'token': 'aaa'
                },
            ]
        }
        config_manager = ConfigManager(file_name=None, raw_config=config)

        a_config = config_manager.get_config(environment='a')
        self.assertIsNotNone(a_config)
        self.assertEqual('a', a_config.get_environment())
        self.assertEqual('https://a', a_config.get_url())
        self.assertEqual('a-a-a', a_config.get_workspace())
        self.assertEqual('aaa', a_config.get_token())

        b_config = config_manager.get_config(environment='b')
        self.assertIsNotNone(b_config)
        self.assertEqual('b', b_config.get_environment())
        self.assertEqual('https://b', b_config.get_url())
        self.assertEqual('b-b-b', b_config.get_workspace())
        self.assertEqual('bbb', b_config.get_token())

        default_config = config_manager.get_config()
        self.assertEqual('a', default_config.get_environment())

    def test_io(self):
        config = {
            'default_env': 'a',
            'env_configs': [
                {
                    'env': 'b',
                    'url': 'https://b',
                    'workspace': 'b-b-b',
                    'token': 'bbb'
                },
                {
                    'env': 'a',
                    'url': 'https://a',
                    'workspace': 'a-a-a',
                    'token': 'aaa'
                },
            ]
        }
        with tempfile.NamedTemporaryFile('w+') as f:
            json.dump(config, f, indent=4)
            f.seek(0)

            config_manager = ConfigManager(f.name)
            a_config = config_manager.get_config()
            a_config.set_token('ccc')

            config_manager.to_file(f.name)
            written_config = json.load(f)
            self.assertDictEqual(config_manager.raw_config, written_config)
