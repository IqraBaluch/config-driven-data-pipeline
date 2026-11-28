# Step 02: The Parquet Writer

## Goal
Save the records returned by a connector to disk as Parquet files in the bronze layer, without ever overwriting earlier data.

## Why

**Inputs and outputs first.**
- **Input:** a list of dictionaries from `extract()`. Each dictionary is one row; its keys are the columns.
- **Output:** a Parquet file in the folder named by the source's `target` in `sources.yaml`.

**Why Parquet?**
It's columnar, compressed and keeps column types. Engines like DuckDB, Spark, Snowflake and Fabric all read it directly.

**Why append-only (a new file every run)?**
Bronze is the permanent receipt of what the source sent. If every run wrote to the same file, each run would overwrite the previous one and the data would be lost. So every run writes a **new** file named with the current time.

**Why a UTC timestamp like `20261128T143441Z`?**
- **Unique:** includes seconds, so even two manual runs in the same hour don't clash.
- **UTC:** the same everywhere. GitHub's servers run in UTC, Pakistan is UTC+5, and some countries change their clocks. `Z` means UTC.
- **Sortable:** biggest unit first (year → second), so alphabetical order = time order.
- **Windows-safe:** no `:` characters, which Windows doesn't allow in file names.

**Why does the writer build the file name, not the caller?**
So the append-only rule lives in **one place** that callers can't bypass. A caller can't accidentally overwrite bronze by forgetting the timestamp, and changing the format later is a one-line change.

## Do it

```python
def write_parquet(records, folder):
    """Write records to a new timestamped Parquet file in folder (append-only)."""
    Path(folder).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    file_path = Path(folder) / f"{timestamp}.parquet"
    table = pa.Table.from_pylist(records)
    pq.write_table(table, file_path)
    return file_path
```

| Line | What it does |
|---|---|
| `mkdir(parents=True, exist_ok=True)` | Creates the folder and any missing parent folders; no error if it already exists |
| `datetime.now(timezone.utc).strftime(...)` | Gets the current **UTC** time, then formats it as text |
| `Path(folder) / f"..."` | Joins the folder and the file name (`/` joins paths in `pathlib`) |
| `pa.Table.from_pylist(records)` | Converts the list of dicts into a pyarrow table |
| `pq.write_table(table, file_path)` | Saves the table as Parquet |
| `return file_path` | Tells the caller which file was created |

## Check it works

```python
import yaml
from ingestion.connectors import get_connector
from ingestion.writer import write_parquet

with open("configs/sources.yaml", encoding="utf-8") as f:
    source = yaml.safe_load(f)["sources"][0]

records = get_connector(source).extract()
saved = write_parquet(records, "data/bronze/crypto/btc_usdt_hourly")
print("Saved to:", saved)
```

Run it twice. You should see **two** timestamped files, nothing overwritten.

Query the files with DuckDB, straight from disk:
```python
import duckdb
duckdb.sql("SELECT COUNT(*) FROM 'data/bronze/crypto/btc_usdt_hourly/*.parquet'").show()
duckdb.sql("DESCRIBE SELECT * FROM 'data/bronze/crypto/btc_usdt_hourly/*.parquet'").show()
```
Prices are `VARCHAR` (text): bronze keeps them exactly as Binance sent them. Typing happens in silver.

## Common errors

**1. `FileNotFoundError: The system cannot find the path specified`**
The folders don't exist yet. `write_table` creates files, not folders. Fix: `mkdir(parents=True, exist_ok=True)` before writing.

**2. `.parent` vs `parents=True` confusion**
- `.parent` walks **up** from a file to its folder. Not needed when you're already given a folder.
- `parents=True` **creates** missing folders above the target. Still needed.

**3. `AttributeError: 'datetime.timezone' object has no attribute 'strftime'`**
Bracket in the wrong place: `datetime.now((timezone.utc).strftime(...))`. Get the time first, then format it: `datetime.now(timezone.utc).strftime(...)`.

**4. `TypeError: unsupported operand type(s) for /: 'NoneType' and 'str'`**
`mkdir()` was used inside a chain. It performs an action and returns `None`, so it must be on its own line.

**5. A timestamp computed outside the function**
Code outside a function runs once, at import. Every file in the same run would get the same name and overwrite each other. Compute it inside the function.

**6. The error shows old code you've already fixed**
The file isn't saved. Python runs what's on disk, not what's on screen. Turn on **File → Auto Save** in VS Code, or check with `Get-Content ingestion\writer.py`.

**7. Escaped quotes (`\"`) break `python -c "..."` in PowerShell**
Use a here-string instead: `@' ... '@ | python -`.

## Known limitations (fixed in later steps)
- Each run fetches the latest 1000 rows, so files overlap heavily: bronze contains duplicates. **Step 04** (watermarks) fetches only new rows; **silver** deduplicates as a safety net.
- Column types are guessed by pyarrow (*type inference*). **Step 06** adds explicit schema control.

## Try it yourself
1. Run the test 3 times and list the folder. Notice how the file names tell you the history of runs.
2. Change the test to use the ETH source (`["sources"][1]`) and its target folder.
3. Query all files at once with DuckDB using `*.parquet`, and count the rows. Why is the count higher than 1000?
