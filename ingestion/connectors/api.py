from typing import Any

import requests

from .base import BaseConnector


class ApiConnector(BaseConnector):
    """Reads JSON array responses from a REST API and names the columns from config."""

    def extract(self, since: int | None = None) -> list[dict[str, Any]]:
        params = dict(self.config.get("params", {}))
        params["limit"] = self.config.get("page_size", 1000)

        # Incremental load: only ask for data after the last watermark
        if since is not None and self.config.get("incremental_param"):
            params[self.config["incremental_param"]] = since + 1

        response = requests.get(self.config["url"], params=params, timeout=30)
        response.raise_for_status()  # fail loudly on 4xx / 5xx errors
        rows = response.json()

        columns = self.config["columns"]
        records = []
        for row in rows:
            if len(row) != len(columns):
                raise ValueError(
                    f"[{self.name}] Schema mismatch: API returned {len(row)} fields, "
                    f"config defines {len(columns)} columns."
                )
            records.append(dict(zip(columns, row)))

        return records