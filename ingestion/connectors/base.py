from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    """Contract every connector (api, csv, database) must follow."""

    def __init__(self, source_config: dict[str, Any]):
        self.config = source_config
        self.name = source_config["name"]

    @abstractmethod
    def extract(self, since: int | None = None) -> list[dict[str, Any]]:
        """Return records as a list of dicts.

        since: the last watermark value already loaded (None = first load).
        """