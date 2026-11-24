from typing import Any

from .api import ApiConnector
from .base import BaseConnector

# Registry: maps `type` in sources.yaml -> connector class
CONNECTORS: dict[str, type[BaseConnector]] = {
    "api": ApiConnector,
}


def get_connector(source_config: dict[str, Any]) -> BaseConnector:
    source_type = source_config["type"]
    if source_type not in CONNECTORS:
        raise ValueError(
            f"Unknown connector type '{source_type}' for source "
            f"'{source_config['name']}'. Available: {list(CONNECTORS)}"
        )
    return CONNECTORS[source_type](source_config)