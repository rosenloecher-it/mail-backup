from enum import Enum


class NamingKey(Enum):
    YEAR = "YEAR"
    MONTH = "MONTH"
    DAY = "DAY"
    HOUR = "HOUR"
    MINUTE = "MINUTE"
    UID = "UID"
    SUBJECT = "SUBJECT"
    TO1 = "TO1"
    FROM = "FROM"

    DATETIME_OBJ = "DATETIME_OBJ"

    def __str__(self):
        return self.__repr__()

    def __repr__(self) -> str:
        return '{}'.format(self.name)
