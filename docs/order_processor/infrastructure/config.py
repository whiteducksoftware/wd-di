from dataclasses import dataclass

@dataclass
class AppConfig:
    debug: bool = False
    email_server: str = ""