from imap_tools import MailMessage


class MailMessageExt(MailMessage):

    def __init__(self, fetch_data: list):
        super().__init__(fetch_data)

        self.raw_data, _, _ = super()._get_message_data_parts(fetch_data)
