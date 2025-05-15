# examples/caching_with_decorators/console_utils.py

class Colors:
    """ANSI escape codes for colored terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'  # Reset to default
    BOLD = '\033[1m'

    @staticmethod
    def format(message: str, color: str = "", bold: bool = False) -> str:
        """Formats a message with optional color and bold style."""
        prefix = ""
        if bold:
            prefix += Colors.BOLD
        if color:
            prefix += color
        
        if prefix:
            return f"{prefix}{message}{Colors.ENDC}"
        return message 