import pyarrow.parquet as pq  # write Parquet files
import pyarrow as pa          # build tables
from pathlib import Path      # work with folders and paths
from datetime import datetime, timezone  # get the current time


def write_parquet(records, folder):
    """Write records to a new timestamped Parquet file in folder (append-only)."""
    Path(folder).mkdir(parents=True, exist_ok=True)                    # 1. build the folder (and any missing parents)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")  # 2. current UTC time → 20261128T133256Z
    file_path = Path(folder) / f"{timestamp}.parquet"                  # 3. folder + file name
    table = pa.Table.from_pylist(records)                              # 4. list of dicts → table
    pq.write_table(table, file_path)                                   # 5. save it
    return file_path                                                   # 6. tell the caller where it went