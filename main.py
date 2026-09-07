#!/usr/bin/env python3
import logging
import sys
from sms_gateway import SMSGateway
from config import DEBUG

def configure_logging():
    log_level = logging.DEBUG if DEBUG else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)],
    )

def main():
    configure_logging()
    logging.getLogger(__name__).info("Starting SMS Gateway...")
    gateway = SMSGateway()
    gateway.run()

if __name__ == "__main__":
    main()
