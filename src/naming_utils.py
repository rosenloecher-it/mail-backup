import os
import re
from datetime import datetime

from unidecode import unidecode

from src.mail_message_ext import MailMessageExt
from src.naming_key import NamingKey
from typing import Dict


class NamingUtils:

    MAX_ATTRIBUTE_LENGTH = 32

    @classmethod
    def format_path(cls, pattern, attributes) -> str:
        return pattern.format(**attributes)

    @classmethod
    def join_path(cls, pivot, mail_path) -> str:
        if mail_path.startswith("/"):
            return mail_path
        return os.path.join(pivot, mail_path)

    @classmethod
    def prepare_text(cls, value, max_length=MAX_ATTRIBUTE_LENGTH) -> str:
        if value is None:
            return ""

        value = unidecode(str(value).strip())

        def replace_all(text, old, new):
            while True:
                orig_text = text
                text = text.replace(old, new)
                if orig_text == text:
                    break
            return text

        value = replace_all(value, "_", ".")
        value = replace_all(value, " ", ".")
        value = replace_all(value, ".-", "-")
        value = replace_all(value, "-.", "-")

        regex = re.compile("[^a-zA-Z0-9-.]")
        value = regex.sub('.', value)  # First parameter is the replacement, second parameter is your input string

        value = replace_all(value, "..", ".")

        value = value[:max_length]
        value = value.strip(".")

        return value

    @classmethod
    def prepare_email(cls, value) -> str:
        if value is None:
            return ""

        if type(value) == tuple:
            value = value[0] if len(value) > 0 else ""

        value = str(value).strip()
        value = value.replace("@", ".")
        return value

    @classmethod
    def prepare_subject(cls, value):
        if value is None:
            return ""

        while True:
            value = str(value).strip()
            lower = value.lower()

            found = False
            prefixes = ["fw:", "fwd:", "re:", "aw:"]
            for prefix in prefixes:
                if lower.startswith(prefix):
                    value = value[len(prefix):]
                    found = True
                    break
            if not found:
                break

        return value

    @classmethod
    def prepare_int(cls, value: int, digits: int) -> str:
        if value is None:
            return ""

        output = str(value)
        while len(output) < digits:
            output = "0" + output

        return output

    @classmethod
    def extract_attributes(cls, mail: MailMessageExt) -> Dict[str, any]:
        attributes = {}

        def add_to_attributes(key, value, max_length=cls.MAX_ATTRIBUTE_LENGTH):
            value = cls.prepare_text(value, max_length)
            attributes[key.name] = value

        add_to_attributes(NamingKey.UID, mail.uid)
        add_to_attributes(NamingKey.FROM, cls.prepare_email(mail.from_))
        add_to_attributes(NamingKey.TO1, cls.prepare_email(mail.to))
        add_to_attributes(NamingKey.SUBJECT, cls.prepare_subject(mail.subject), 50)

        date = mail.date
        if date.year < 1971:
            date = datetime(0, 1, 1, 0, 0, 0)

        add_to_attributes(NamingKey.YEAR, cls.prepare_int(date.year, 4))
        add_to_attributes(NamingKey.MONTH, cls.prepare_int(date.month, 2))
        add_to_attributes(NamingKey.DAY, cls.prepare_int(date.day, 2))
        add_to_attributes(NamingKey.HOUR, cls.prepare_int(date.hour, 2))
        add_to_attributes(NamingKey.MINUTE, cls.prepare_int(date.minute, 2))

        return attributes
