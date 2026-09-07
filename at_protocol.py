import time
import logging
from config import SERIAL_PORT, BAUD_RATE, TIMEOUT, DEBUG, SMS_STORAGE, MAX_RETRIES, RETRY_DELAY

class ATProtocol:
    def __init__(self):
        self.serial_port = SERIAL_PORT
        self.baud_rate = BAUD_RATE
        self.timeout = TIMEOUT
        self.debug = DEBUG
        self.serial_connection = None
        self.logger = logging.getLogger(__name__)

    def open_connection(self):
        try:
            import serial
            self.serial_connection = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                timeout=self.timeout,
            )
            if self.debug:
                self.logger.info(f"Connected to {self.serial_port} at {self.baud_rate} baud")
            return True
        except Exception as e:
            self.logger.error(f"Failed to open serial: {str(e)}")
            return False

    def close_connection(self):
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()

    def send_at_command(self, command, expect_response=True):
        if not self.serial_connection or not self.serial_connection.is_open:
            if not self.open_connection():
                return ""
        if not command.endswith("\r"):
            command += "\r"
        try:
            self.serial_connection.write(command.encode('utf-8'))
            time.sleep(0.1)
            if not expect_response:
                return ""
            response = ""
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                if self.serial_connection.in_waiting:
                    response += self.serial_connection.read(self.serial_connection.in_waiting).decode('utf-8', errors='ignore')
                else:
                    time.sleep(0.05)
            return response
        except Exception as e:
            self.logger.error(f"AT command failed: {str(e)}")
            return ""

    def is_modem_ready(self):
        return "OK" in self.send_at_command("AT")

    def initialize_modem(self):
        if not self.is_modem_ready():
            return False
        if "OK" not in self.send_at_command(f'AT+CPMS="{SMS_STORAGE}"'):
            return False
        if "OK" not in self.send_at_command("AT+CMGF=1"):
            return False
        if "OK" not in self.send_at_command("AT+CNMI=1,2,0,0,0"):
            return False
        return True

    def send_sms(self, phone_number, message):
        for attempt in range(MAX_RETRIES):
            self.send_at_command(f'AT+CMGS="{phone_number}"', expect_response=False)
            time.sleep(0.5)
            response = self.send_at_command(f"{message}\x1A", expect_response=True)
            if "OK" in response or "+CMGS:" in response:
                return True
            time.sleep(RETRY_DELAY)
        return False

    def read_sms(self, index):
        response = self.send_at_command(f"AT+CMGR={index}")
        if "OK" not in response:
            return None
        lines = response.split("\n")
        sender = None
        message = None
        for line in lines:
            line = line.strip()
            if line.startswith("+CMGR:"):
                parts = line.split(",")
                if len(parts) >= 2:
                    sender = parts[1].strip('"')
            elif line and not line.startswith("AT+CMGR") and not line.startswith("OK"):
                message = line
        return {"sender": sender, "message": message} if sender and message else None

    def list_sms(self):
        response = self.send_at_command('AT+CMGL="ALL"')
        if "OK" not in response:
            return []
        sms_list = []
        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("+CMGL:"):
                parts = line.split(",")
                if len(parts) >= 2:
                    index = parts[0].split(":")[1].strip()
                    sender = parts[1].strip('"')
                    sms_list.append({"index": index, "sender": sender})
        return sms_list

    def delete_sms(self, index):
        return "OK" in self.send_at_command(f"AT+CMGD={index}")

    def wait_for_incoming_sms(self, timeout=30):
        start_time = time.time()
        while time.time() - start_time < timeout:
            for sms in self.list_sms():
                sms_data = self.read_sms(sms["index"])
                if sms_data:
                    self.delete_sms(sms["index"])
                    return sms_data
            time.sleep(1)
        return None
