import os
import unittest
from datetime import datetime

from src.runner import Runner


class TestRunner(unittest.TestCase):

    def test_find_existing_file_or_new_mail_path_1(self):
        # test that file already exists!
        class DummyMail:
            def __init__(self):
                self.uid = 123
                self.date = datetime(2020, 9, 10, 18, 7, 6)
                self.subject = " Fwd: Re: Fwd: fwD:    re:  123 "
                self.to = ("to@dummy.de", "to2@dummy.de", )
                self.from_ = "from@dummy.de"
                self.raw_data = bytearray(b"\x00\x11\x0F")  # no mail data

        mail = DummyMail()

        test_path = os.path.join(os.path.dirname(__file__), "../__test__/find")
        os.makedirs(test_path, exist_ok=True)

        mail_path = os.path.join(test_path, "orig.no-eml")
        with open(mail_path, "wb") as file:
            file.write(mail.raw_data)

        result = Runner.find_existing_file_or_new_mail_path(mail, mail_path)
        self.assertEqual(result, None)  # file exits already

    def test_find_existing_file_or_new_mail_path_2(self):
        # test that file already exists!
        class DummyMail:
            def __init__(self):
                self.uid = 123
                self.date = datetime(2020, 9, 10, 18, 7, 6)
                self.subject = " Fwd: Re: Fwd: fwD:    re:  123 "
                self.to = ("to@dummy.de", "to2@dummy.de", )
                self.from_ = "from@dummy.de"
                self.raw_data = bytearray(b"\x00\x11\x0F")  # no mail data

        mail = DummyMail()

        test_path = os.path.join(os.path.dirname(__file__), "../__test__/find")
        test_path = os.path.realpath(test_path)
        os.makedirs(test_path, exist_ok=True)

        orig_mail_path = os.path.join(test_path, "orig.no-eml")
        with open(orig_mail_path, "wb") as file:
            file.write(bytearray(b"\x00\x11\x11\x11\x0F"))

        result = Runner.find_existing_file_or_new_mail_path(mail, orig_mail_path)
        expected_result = os.path.join(test_path, "orig.2.no-eml")
        self.assertEqual(result, expected_result)
        self.assertFalse(os.path.isfile(expected_result))
