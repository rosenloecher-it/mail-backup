import logging


class Constant:
    APP_NAME = "Mail Backup"
    APP_DESC = "Download emails via IMAP"

    DEFAULT_CONFFILE = "/etc/mail-backup.yaml"

    DEFAULT_LOGLEVEL = logging.INFO
    DEFAULT_LOG_MAX_BYTES = 1048576
    DEFAULT_LOG_MAX_COUNT = 5
