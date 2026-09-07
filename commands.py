"""
Command definitions and handlers for the SMS Gateway.
Add or modify commands in this file to customize the gateway's behavior.
"""

from datetime import datetime
import platform
import psutil
import socket
import struct
from config import MODBUS_TCP_IP, MODBUS_TCP_PORT

def help_handler(args):
    """Return a list of all available commands."""
    commands_list = [
        "HELP - List all available commands",
        "STATUS - Return system status",
        "TIME - Return current time",
        "ECHO <text> - Echo back the provided text",
        "CPU - Return CPU usage",
        "MEM - Return memory usage",
        "HOSTNAME - Return the hostname",
        "RSTM - Send Modbus TCP command to set coil 0 ON (192.168.4.253)",
    ]
    return "Available commands:\n" + "\n".join(commands_list)

def status_handler(args):
    """Return the current system status."""
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent
        return (
            f"System Status:\n"
            f"CPU: {cpu_usage}%\n"
            f"Memory: {memory_usage}%\n"
            f"Disk: {disk_usage}%\n"
            f"Hostname: {platform.node()}"
        )
    except Exception as e:
        return f"Error getting status: {str(e)}"

def time_handler(args):
    """Return the current time."""
    now = datetime.now()
    return f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}"

def echo_handler(args):
    """Echo back the provided text."""
    if args:
        return f"Echo: {args}"
    else:
        return "Echo: (no text provided)"

def cpu_handler(args):
    """Return CPU usage."""
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        return f"CPU Usage: {cpu_usage}%"
    except Exception as e:
        return f"Error getting CPU usage: {str(e)}"

def mem_handler(args):
    """Return memory usage."""
    try:
        memory = psutil.virtual_memory()
        return (
            f"Memory Usage:\n"
            f"Total: {memory.total / (1024 ** 3):.2f} GB\n"
            f"Used: {memory.used / (1024 ** 3):.2f} GB\n"
            f"Free: {memory.free / (1024 ** 3):.2f} GB\n"
            f"Usage: {memory.percent}%"
        )
    except Exception as e:
        return f"Error getting memory usage: {str(e)}"

def hostname_handler(args):
    """Return the hostname."""
    return f"Hostname: {platform.node()}"

def rstm_handler(args):
    """
    Send a Modbus TCP command to write to coil 0 of the PLC at 192.168.4.253.
    Args: None (command is fixed: write to coil 0, value=True)
    Returns: Success or error message.
    """
    try:
        # Modbus TCP default port is 502
        plc_ip = MODBUS_TCP_IP
        plc_port = MODBUS_TCP_PORT

        # Create a TCP socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)  # 5 seconds timeout
            s.connect((plc_ip, plc_port))

            # Modbus TCP request to write to coil 0 (Function Code 0x05)
            # Transaction ID (2 bytes), Protocol ID (2 bytes), Length (2 bytes), Unit ID (1 byte)
            transaction_id = 0x0001
            protocol_id = 0x0000
            length = 0x0006  # Remaining bytes
            unit_id = 0x01   # Modbus unit ID

            # Function Code 0x05 (Write Single Coil)
            function_code = 0x05
            # Coil address (0 for coil 0)
            coil_address = 0x0000
            # Value to write (0xFF00 = True, 0x0000 = False)
            value = 0xFF00

            # Build the Modbus TCP frame
            request = (
                struct.pack('>HHH', transaction_id, protocol_id, length) +
                struct.pack('>B', unit_id) +
                struct.pack('>H', function_code) +
                struct.pack('>H', coil_address) +
                struct.pack('>H', value)
            )

            if DEBUG:
                print(f"Sending Modbus TCP request to {plc_ip}:{plc_port}")
                print(f"Request bytes: {request.hex()}")

            s.sendall(request)

            # Receive response
            response = s.recv(1024)

            if DEBUG:
                print(f"Response bytes: {response.hex()}")

            # Parse response (first 6 bytes: MBAP header, then Modbus response)
            if len(response) >= 8:
                # Check function code in response (should echo 0x05)
                modbus_response = response[6:]
                if len(modbus_response) >= 2:
                    response_function_code = modbus_response[0]
                    if response_function_code == function_code:
                        # Check if the write was successful (next 2 bytes should be coil address and value)
                        return f"Modbus TCP: Coil 0 set to ON (192.168.4.253)"
                    else:
                        return f"Modbus TCP: Error - Function code mismatch"

            return f"Modbus TCP: Success (192.168.4.253)"

    except socket.timeout:
        return f"Modbus TCP: Timeout - No response from 192.168.4.253"
    except ConnectionRefusedError:
        return f"Modbus TCP: Connection refused - Check if PLC is running at 192.168.4.253"
    except Exception as e:
        return f"Modbus TCP: Error - {str(e)}"

# Command registry
# Format: {
#   "command_name": {
#       "description": "Description of the command",
#       "handler": function_to_call,
#   },
# }
COMMANDS = {
    "HELP": {
        "description": "List all available commands",
        "handler": help_handler,
    },
    "STATUS": {
        "description": "Return system status",
        "handler": status_handler,
    },
    "TIME": {
        "description": "Return current time",
        "handler": time_handler,
    },
    "ECHO": {
        "description": "Echo back the provided text",
        "handler": echo_handler,
    },
    "CPU": {
        "description": "Return CPU usage",
        "handler": cpu_handler,
    },
    "MEM": {
        "description": "Return memory usage",
        "handler": mem_handler,
    },
    "HOSTNAME": {
        "description": "Return the hostname",
        "handler": hostname_handler,
    },
    "RSTM": {
        "description": "Send Modbus TCP command to set coil 0 ON (192.168.4.253)",
        "handler": rstm_handler,
    },
}

def get_command(command_name):
    """
    Retrieve a command by name.

    Args:
        command_name (str): The name of the command (case-insensitive).

    Returns:
        dict: The command definition, or None if not found.
    """
    return COMMANDS.get(command_name.upper())

def process_command(command_name, args):
    """
    Process a command and return the response.

    Args:
        command_name (str): The name of the command.
        args (str): The arguments for the command.

    Returns:
        str: The response from the command handler.
    """
    command = get_command(command_name)
    if command:
        try:
            return command["handler"](args)
        except Exception as e:
            return f"Error executing command: {str(e)}"
    else:
        return f"Unknown command: {command_name}. Type HELP for available commands."
