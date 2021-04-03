import unittest
from datetime import datetime

from src.naming_utils import NamingUtils


class TestNamingUtils(unittest.TestCase):

    def test_prepare_text(self):
        result = NamingUtils.prepare_text(" a##b:c;d\\e..  ")
        self.assertEqual(result, "a.b.c.d.e")

        result = NamingUtils.prepare_text("123456789", 3)
        self.assertEqual(result, "123")

        result = NamingUtils.prepare_text(" äÜß    gghJ    lk  ")
        self.assertEqual(result, "aUss.gghJ.lk")

    def test_prepare_email(self):
        result = NamingUtils.prepare_email(" reply_to@mail.de ")
        self.assertEqual(result, "reply_to.mail.de")

        result = NamingUtils.prepare_email(("reply_to@mail.de", ))
        self.assertEqual(result, "reply_to.mail.de")

        result = NamingUtils.prepare_email(("reply_to@mail.de", "reply_to2@mail.de", ))
        self.assertEqual(result, "reply_to.mail.de")

        result = NamingUtils.prepare_email(())
        self.assertEqual(result, "")

    def test_prepare_subject(self):
        result = NamingUtils.prepare_subject("  fw:  Fwd: Re: Fwd: fwD:    re:  123 ")
        self.assertEqual(result, "123")

    def test_extract_attributes(self):
        class DummyMail:
            def __init__(self):
                self.uid = 123
                self.date = datetime(2020, 9, 10, 18, 7, 6)
                self.subject = " Fwd: Re: Fwd: fwD:    re:  123 "
                self.to = ("to@dummy.de", "to2@dummy.de", )
                self.from_ = "from@dummy.de"

        mail = DummyMail()

        result = NamingUtils.extract_attributes(mail)
        self.assertEqual(result, {
            "DAY": "10",
            "FROM": "from.dummy.de",
            "HOUR": "18",
            "MINUTE": "07",
            "MONTH": "09",
            "SUBJECT": "123",
            "TO1": "to.dummy.de",
            "UID": "123",
            "YEAR": "2020"
        })

    def test_format_path(self):
        attributes = {
            "DAY": "10",
            "FROM": "from.dummy.de",
            "HOUR": "18",
            "MINUTE": "07",
            "MONTH": "09",
            "SUBJECT": "subject",
            "TO1": "to.dummy.de",
            "UID": "123",
            "YEAR": "2020"
        }

        result = NamingUtils.format_path(
            "./__work__/{YEAR}-{MONTH}/{YEAR}{MONTH}{DAY}-OUT-{FROM}-{TO1}-{SUBJECT}.eml",
            attributes
        )
        self.assertEqual(result, "./__work__/2020-09/20200910-OUT-from.dummy.de-to.dummy.de-subject.eml")

        result = NamingUtils.format_path("./__work__/{YEAR}-{MONTH}/{YEAR}{MONTH}{DAY}-OUT-{SUBJECT}.eml", attributes)
        self.assertEqual(result, "./__work__/2020-09/20200910-OUT-subject.eml")

    def test_join_path(self):
        result = NamingUtils.join_path("/home/x/mb", "./2020/11/x.eml")
        self.assertEqual(result, "/home/x/mb/./2020/11/x.eml")

        result = NamingUtils.join_path("/home/x/mb", "2020/11/x.eml")
        self.assertEqual(result, "/home/x/mb/2020/11/x.eml")

        result = NamingUtils.join_path("/home/x/mb/", "2020/11/x.eml")
        self.assertEqual(result, "/home/x/mb/2020/11/x.eml")

        result = NamingUtils.join_path("/home/x/mb/", "/2020/11/x.eml")
        self.assertEqual(result, "/2020/11/x.eml")  # absolute path!
