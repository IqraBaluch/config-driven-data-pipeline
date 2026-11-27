import pyarrow.parquet as pq #import library to store data as parquet
import pyarrow as pa
from pathlib import Path

def write_parquet(records, path):

    """Write a list of records (dicts) to a Parquet file, creating folders if needed."""

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(records)
    pq.write_table(table, path)