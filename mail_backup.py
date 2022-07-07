#!/usr/bin/env python3

import logging
import sys
import logging.handlers

from src.config import ConfigKey, Config
from src.constant import Constant
from src.message_exception import MessageException
from src.runner import Runner


_logger = logging.getLogger("main")


def init_logging(config):
    handlers = []

    format_simple = '[%(levelname)8s]: %(message)s'
    format_with_ts = '%(asctime)s [%(levelname)8s]: %(message)s'

    log_file = Config.get_str(config, ConfigKey.LOG_FILE)
    log_level = Config.get_loglevel(config, ConfigKey.LOG_LEVEL, Constant.DEFAULT_LOGLEVEL)
    print_console = Config.get_bool(config, ConfigKey.LOG_PRINT, False)

    if log_file:
        max_bytes = Config.get_int(config, ConfigKey.LOG_MAX_BYTES, Constant.DEFAULT_LOG_MAX_BYTES)
        max_count = Config.get_int(config, ConfigKey.LOG_MAX_COUNT, Constant.DEFAULT_LOG_MAX_COUNT)
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=int(max_bytes),
            backupCount=int(max_count)
        )
        formatter = logging.Formatter(format_with_ts)
        handler.setFormatter(formatter)
        handlers.append(handler)

    format_ = format_with_ts if log_file else format_simple

    if print_console or not log_file:
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        format=format_,
        level=log_level,
        handlers=handlers
    )


def main():

    try:
        config = Config.load()

        init_logging(config)

        runner = Runner(config)
        runner.run()

        return 0

    except KeyboardInterrupt:
        _logger.info("aborted.")
        return 0

    except MessageException as ex:
        _logger.error(ex)
        _logger.error("aborted!")
        return 1

    except Exception as ex:
        _logger.exception(ex)
        _logger.error("aborted!")
        # no runner.close() to signal abnormal termination!
        return 1


if __name__ == '__main__':
    sys.exit(main())
