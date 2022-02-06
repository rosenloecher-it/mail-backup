import copy
import datetime
import imaplib
import logging
import os
import signal
import socket
from enum import Enum
from typing import List, Optional

from imap_tools import MailBox, OR

from src.config import Config, ConfigKey
from src.mail_message_ext import MailMessageExt
from src.message_exception import MessageException
from src.naming_utils import NamingUtils

_logger = logging.getLogger(__name__)


class ExistsMethod(Enum):
    COMPARE = "compare"
    OVERWRITE = "overwrite"
    SKIP = "skip"

    def __str__(self):
        return self.__repr__()

    def __repr__(self) -> str:
        return '{}'.format(self.name)


class FolderConfigKey(Enum):
    PATH = "path"
    FILE_PATTERN = "file_pattern"
    LAST_DAYS = "last_days"
    WHEN_EXISTS = "when_exists"

    @classmethod
    def parse(cls, value, default):
        if isinstance(value, cls):
            return value

        comp = str(value).lower().strip() if value is not None else value
        for e in FolderConfigKey:
            if comp == e.value.lower():
                return e

        return default


class FolderConfig:

    def __init__(self, name):
        self.name = name
        self.path = ""
        self.file_pattern = ""
        self.last_days: Optional[int] = None  # "None" means all messages
        self.exists_method = ExistsMethod.COMPARE

    def __str__(self):
        return '{}: {}, {}'.format(self.name, self.path + '|' + self.file_pattern, self.exists_method)

    def __repr__(self) -> str:
        return '{}({})'.format(self.__class__.__name__, str(self))


class Runner:

    DEFAULT_EXIST_METHODE = ExistsMethod.COMPARE
    DEFAULT_FILE_PATTERN = "./downloads/{YEAR}-{MONTH}/{YEAR}{MONTH}{DAY}-{HOUR}{MINUTE}-{UID}-{SUBJECT}.eml"

    def __init__(self, config):
        self._config = config
        self._shutdown = False
        self._count_found = 0
        self._count_saved = 0
        self._count_skipped = 0

        signal.signal(signal.SIGINT, self._shutdown_gracefully)
        signal.signal(signal.SIGTERM, self._shutdown_gracefully)

        if _logger.isEnabledFor(logging.DEBUG):
            cloned_config = copy.deepcopy(self._config)
            cloned_config[ConfigKey.IMAP_PASSWORD.value] = "***"
            _logger.debug("config = %s", cloned_config)

        self._folder_configs = self.parse_folder_configs(self._config)
        _logger.debug("folders = %s", self._folder_configs)

        self._host = Config.get_str(self._config, ConfigKey.IMAP_HOST)
        self._port = Config.get_int(self._config, ConfigKey.IMAP_PORT)
        self._host_info = "{}:{}".format(self._host, self._port) if self._port else self._host

        self._pivot_path = config[ConfigKey.PIVOT_PATH.value]

    def _shutdown_gracefully(self, sig, _frame):
        _logger.info("shutdown signaled (%s)", sig)
        self._shutdown = True

    def run(self):
        try:
            self._connect()
        except socket.gaierror as ex:
            message = "Host ({}) not found! Error: {} ".format(self._host_info, ex.strerror)
            raise MessageException(message)
        except imaplib.IMAP4.error as ex:
            raise MessageException(str(ex))

    def _connect(self):
        username = Config.get_str(self._config, ConfigKey.IMAP_USERNAME)
        password = Config.get_str(self._config, ConfigKey.IMAP_PASSWORD)
        if not self._host or not username or not password:
            raise MessageException("empty IMAP credentials!")

        MailBox.email_message_class = MailMessageExt

        kwargs = {"host": self._host}
        if self._port:
            kwargs["port"] = self._port

        with MailBox(**kwargs).login(username, password) as mailbox:
            _logger.info("logged in (%s@%s)", username, self._host_info)

            folders = mailbox.folder.list()
            folders_names = [f.name for f in folders]
            _logger.info("found mail folders = %s", folders_names)

            for folder_config in self._folder_configs:
                if self._shutdown:
                    break

                if folder_config.name not in folders_names:
                    _logger.warning("folder name (%s) not found, skipping!", folder_config.name)
                    continue

                mailbox.folder.set(folder_config.name)

                query_args = []
                if folder_config.last_days and folder_config.last_days > 0:
                    since = datetime.date.today() - datetime.timedelta(days=folder_config.last_days)
                    query_args = [OR(date_gte=since)]

                try:
                    for mail in mailbox.fetch(*query_args):
                        self.handle_mail(mail, folder_config)
                        if self._shutdown:
                            break
                except Exception as ex:
                    _logger.error("error in folder: %s", folder_config.name)
                    raise ex

        _logger.info("success: %s mails saved (of %s found; %s skipped for legal reasons, e.g. already exists).",
                     self._count_saved, self._count_found, self._count_skipped)

    def handle_mail(self, mail: MailMessageExt, folder_config: FolderConfig):
        attributes = NamingUtils.extract_attributes(mail)
        mail_path = NamingUtils.format_path(folder_config.path, attributes)
        mail_path = os.path.realpath(NamingUtils.join_path(self._pivot_path, mail_path))
        folder_info = "folder '{}' - ".format(folder_config.name)

        self._count_found += 1

        mail_exists = os.path.isfile(mail_path)
        do_write = not mail_exists

        if not do_write:  # == mail file exists
            if folder_config.exists_method == ExistsMethod.OVERWRITE:
                os.remove(mail_path)
                _logger.info("%sremove former mail (%s).", folder_info, mail_path)
                do_write = True
            elif folder_config.exists_method == ExistsMethod.SKIP:
                _logger.debug("%sskip existing file (%s).", folder_info, mail_path)
                self._count_skipped += 1
            else:  # folder_config.exists_method == ExistsMethod.COMPARE:
                new_mail_path = self.find_existing_file_or_new_mail_path(mail, mail_path, folder_config)
                if new_mail_path:
                    mail_path = new_mail_path
                    do_write = True
                else:
                    self._count_skipped += 1

        if do_write:
            _logger.debug("%sbackup mail (%s).", folder_info, mail_path)
            mail_dir = os.path.dirname(mail_path)
            os.makedirs(mail_dir, exist_ok=True)
            with open(mail_path, "wb") as file:
                file.write(mail.raw_data)
            self._count_saved += 1

    @classmethod
    def find_existing_file_or_new_mail_path(cls, mail, orig_mail_path, folder_config: FolderConfig = None) -> Optional[str]:
        """
        :param MailMessageExt mail:
        :param str orig_mail_path:
        :param Optional[FolderConfig] folder_config: only for logging folder info
        :return: new path to write or None when should not be written
        """
        if not os.path.isfile(orig_mail_path):
            return orig_mail_path

        folder_info = ""
        if folder_config:
            folder_info = "folder '{}' - ".format(folder_config.name)

        loop = 0

        while loop < 5:
            if loop == 0:
                new_mail_path = orig_mail_path
            else:
                file_path, file_extension = os.path.splitext(orig_mail_path)
                new_mail_path = file_path + "." + str(loop + 1) + file_extension

            if not os.path.isfile(new_mail_path):
                return new_mail_path

            with open(new_mail_path, "rb") as file:
                compare_data = bytearray(file.read())

            if compare_data == mail.raw_data:
                if orig_mail_path == new_mail_path:
                    _logger.debug("%sskip existing mail (%s).", folder_info, orig_mail_path)
                else:
                    _logger.debug("%sskip existing mail (expected: %s, found as: %s).",
                                  folder_info, orig_mail_path, new_mail_path)
                return None

            loop += 1

        _logger.warning("cannot find other path for existing mail (%s). loop (%s) exceeded!", orig_mail_path, loop)

        return None

    @classmethod
    def parse_folder_configs(cls, config):

        def get_value(source, key, error_message):
            try:
                return source[key]
            except KeyError:
                raise MessageException(error_message)

        key = ConfigKey.IMAP_FOLDERS.value
        configs = get_value(config, key, "no imap folder configuration found ('{}')!".format(key))

        folder_configs = []  # type: List[FolderConfig]

        for config in configs:
            folder_name = config.get("folder_name")
            if not folder_name:
                raise MessageException("invalid folder configuration (no empty folder name)!")

            folder_config = FolderConfig(folder_name)
            key = FolderConfigKey.PATH.value
            error_message = "invalid folder configuration (no '{}' found for '{}')!".format(key, folder_name)
            folder_config.path = get_value(config, key, error_message)
            if not folder_config.path:
                raise MessageException("invalid folder configuration (no empty folder path)!")

            folder_config.file_pattern = config.get(FolderConfigKey.FILE_PATTERN.value, cls.DEFAULT_FILE_PATTERN)
            folder_config.exists_method = FolderConfigKey.parse(
                config.get(FolderConfigKey.WHEN_EXISTS.value),
                cls.DEFAULT_EXIST_METHODE
            )

            last_days = config.get(FolderConfigKey.LAST_DAYS.value)
            if isinstance(last_days, int):
                folder_config.last_days = last_days
            elif last_days:
                folder_config.last_days = int(last_days, 0)

            folder_configs.append(folder_config)

        return folder_configs
