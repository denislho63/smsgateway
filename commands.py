from datetime import datetime
import platform
import psutil

def help_handler(args):
    commands_list = [
        "HELP - List all available commands",
        "STATUS - Return system status",
        "TIME - Return current time",
        "ECHO <text> - Echo back the provided text",
        "CPU - Return CPU usage",
        "MEM - Return memory usage",
        "HOSTNAME - Return the hostname",
    ]
    return "Available commands:\n" + "\n".join(commands_list)

def status_handler(args):
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
    now = datetime.now()
    return f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}"

def echo_handler(args):
    return f"Echo: {args}" if args else "Echo: (no text provided)"

def cpu_handler(args):
    try:
        return f"CPU Usage: {psutil.cpu_percent(interval=1)}%"
    except Exception as e:
        return f"Error: {str(e)}"

def mem_handler(args):
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
        return f"Error: {str(e)}"

def hostname_handler(args):
    return f"Hostname: {platform.node()}"

COMMANDS = {
    "HELP": {"description": "List all commands", "handler": help_handler},
    "STATUS": {"description": "System status", "handler": status_handler},
    "TIME": {"description": "Current time", "handler": time_handler},
    "ECHO": {"description": "Echo text", "handler": echo_handler},
    "CPU": {"description": "CPU usage", "handler": cpu_handler},
    "MEM": {"description": "Memory usage", "handler": mem_handler},
    "HOSTNAME": {"description": "Hostname", "handler": hostname_handler},
}

def process_command(command_name, args):
    command = COMMANDS.get(command_name.upper())
    if command:
        try:
            return command["handler"](args)
        except Exception as e:
            return f"Error: {str(e)}"
    return f"Unknown command: {command_name}. Type HELP for available commands."
