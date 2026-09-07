import logging
from at_protocol import ATProtocol
from commands import process_command
from config import DEBUG, TARGET_PHONE_NUMBER

class SMSGateway:
    def __init__(self):
        self.at_protocol = ATProtocol()
        self.logger = logging.getLogger(__name__)
        self.running = False

    def start(self):
        if not self.at_protocol.open_connection():
            return False
        if not self.at_protocol.initialize_modem():
            self.at_protocol.close_connection()
            return False
        self.running = True
        return True

    def stop(self):
        self.running = False
        self.at_protocol.close_connection()

    def process_incoming_sms(self, sms_data):
        if not sms_data or "sender" not in sms_data or "message" not in sms_data:
            return False
        sender = sms_data["sender"]
        message = sms_data["message"].strip()
        if TARGET_PHONE_NUMBER and sender != TARGET_PHONE_NUMBER:
            return True
        if not message:
            return True
        parts = message.split(maxsplit=1)
        command = parts[0].upper()
        args = parts[1] if len(parts) > 1 else ""
        response = process_command(command, args)
        if response and not self.at_protocol.send_sms(sender, response):
            return False
        return True

    def run(self):
        if not self.start():
            return
        try:
            while self.running:
                sms_data = self.at_protocol.wait_for_incoming_sms(timeout=5)
                if sms_data:
                    self.process_incoming_sms(sms_data)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
