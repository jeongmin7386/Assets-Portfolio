import logging
import re

from pythonjsonlogger.json import JsonFormatter

from app.core.config import settings


SECRET_PATTERN = re.compile(
    r"(?i)(client_secret|access_token|authorization|notion_api_key|database_url|password)"
)


class SecretRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        if SECRET_PATTERN.search(message):
            record.msg = "Sensitive value redacted"
            record.args = ()
        return True


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    handler.addFilter(SecretRedactionFilter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level.upper())
