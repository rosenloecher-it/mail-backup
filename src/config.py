import logging
import os
from argparse import ArgumentParser
from enum import Enum

import yaml

from src.constant import Constant


class ConfigKey(Enum):
    CONF_FILE = "conf_file"

    PIVOT_PATH = "pivot_path"  # path off configuration file => pivot for configuration

    LOG_FILE = "log_file"
    LOG_LEVEL = "log_level"
    LOG_MAX_BYTES = "log_max_bytes"
    LOG_MAX_COUNT = "log_max_count"
    LOG_PRINT = "log_print"

    IMAP_HOST = "imap_host"
    IMAP_PORT = "imap_port"
    IMAP_USERNAME = "imap_username"
    IMAP_PASSWORD = "imap_password"
    IMAP_FOLDERS = "imap_folders"


class Config:

    def __init__(self):
        self._config_cli = {}

    @classmethod
    def load(cls):
        instance = Config()
        instance._parse_cli()
        return instance._load_conf_file()

    def _load_conf_file(self):
        conf_file = self._config_cli[ConfigKey.CONF_FILE.value]
        if not os.path.isfile(conf_file):
            raise FileNotFoundError('config file ({}) does not exist!'.format(conf_file))
        with open(conf_file, 'r') as stream:
            data = yaml.unsafe_load(stream)

        config = {**data, **self._config_cli}

        config[ConfigKey.PIVOT_PATH.value] = os.path.dirname(os.path.abspath(conf_file))

        return config

    def _parse_cli(self):
        parser = self.create_cli_parser()
        args = parser.parse_args()

        def handle_cli(key_enum, default_value=None):
            key = key_enum.value
            value = getattr(args, key, default_value)
            if value is not None:
                self._config_cli[key] = value

        handle_cli(ConfigKey.CONF_FILE, Constant.DEFAULT_CONFFILE)

        handle_cli(ConfigKey.LOG_LEVEL)
        handle_cli(ConfigKey.LOG_FILE)
        handle_cli(ConfigKey.LOG_MAX_BYTES)
        handle_cli(ConfigKey.LOG_MAX_COUNT)
        handle_cli(ConfigKey.LOG_PRINT)
        handle_cli(ConfigKey.IMAP_PASSWORD)

    @classmethod
    def create_cli_parser(cls):
        parser = ArgumentParser(
            description=Constant.APP_DESC,
            add_help=True
        )

        parser.add_argument(
            "-c", "--" + ConfigKey.CONF_FILE.value,
            help="config file path",
            default=Constant.DEFAULT_CONFFILE
        )
        parser.add_argument(
            "-f", "--" + ConfigKey.LOG_FILE.value,
            help="log file (if stated journal logging is disabled)"
        )
        parser.add_argument(
            "-l", "--" + ConfigKey.LOG_LEVEL.value,
            choices=["debug", "info", "warning", "error"],
            help="set log level"
        )
        parser.add_argument(
            "-p", "--" + ConfigKey.LOG_PRINT.value,
            action="store_true",
            default=None,
            help="print log output to console too (standard if no log file was specified)"
        )
        parser.add_argument(
            "-s", "--" + ConfigKey.IMAP_PASSWORD.value,
            help="secret IMAP password"
        )

        return parser

    @classmethod
    def get_str(cls, config, key_enum, default=None):
        key = key_enum.value
        value = config.get(key)

        if value is None:
            return default
        else:
            return str(value)

    @classmethod
    def get_bool(cls, config, key_enum, default=None):
        key = key_enum.value
        value = config.get(key)

        if value is None:
            return default
        elif isinstance(value, bool):
            return value
        else:
            temp = str(value).lower().strip()
            if temp in ["true", "1", "on", "active"]:
                return True
            elif temp in ["false", "0", "off", "inactive"]:
                return False
            else:
                raise ValueError("cannot parse '{}' ({}) as bool!".format(key, value))

    @classmethod
    def get_int(cls, config, key_enum, default=None):
        key = key_enum.value
        value = config.get(key)

        if value is None:
            return default
        elif isinstance(value, int):
            return value
        else:
            try:
                return int(value, 0)  # auto convert hex
            except ValueError:
                raise ValueError("cannot parse '{}' ({}) as int!".format(key, value))

    @classmethod
    def get_loglevel(cls, config, key_enum, default=logging.INFO):
        key = key_enum.value
        value = config.get(key)

        if not isinstance(value, type(logging.INFO)):
            loglevel = str(value).lower().strip() if value is not None else value
            if loglevel == "debug":
                value = logging.DEBUG
            elif loglevel == "info":
                value = logging.INFO
            elif loglevel == "warning":
                value = logging.WARNING
            elif loglevel == "error":
                value = logging.ERROR
            else:
                if loglevel is not None:
                    print("cannot parse '{}' ({})!".format(key, loglevel))
                value = default

        return value
