# Step 01: The API Connector

## Goal
Build a generic connector that fetches data from a REST API and turns the raw response into named records, driven entirely by `sources.yaml`.

## Why

**The problem:** Binance returns rows as bare arrays with no column names:
```
[1791943200000, "83328.00", "83700.00", ...]
```
Raw API data is rarely analysis-ready. Something has to map positions to meaningful names.

**Why put the column mapping in the config?**
Because the schema is *metadata*. Keeping it in YAML means a new API source with a different shape needs a config change, not a code change.

**Why a base class + registry?**
| File | Role |
|---|---|
| `connectors/base.py` | The **contract**: every connector must implement `extract()` |
| `connectors/api.py` | One implementation for REST APIs |
| `connectors/__init__.py` | The **registry**: maps `type: api` in YAML to `ApiConnector` |

Adding a CSV or database connector later = write one class + add one line to the registry. Nothing else changes. This is the *open/closed principle*: open for extension, closed for modification.

**Why keep prices as strings?**
The bronze layer stores data **exactly as received**. If we cast types here and something goes wrong, the original data is lost. Type casting happens later, in silver.

**Why the schema-mismatch check?**
If the API adds or removes a field, the pipeline **fails loudly** instead of silently putting values under the wrong column names. This is the first defence against *schema drift*.

## Do it

1. Add `page_size`, `incremental_param` and `columns` to each source in `configs/sources.yaml`. A YAML anchor (`&kline_columns`) defines the column list once, and `*kline_columns` reuses it.
2. Create `ingestion/connectors/base.py` (abstract `BaseConnector`).
3. Create `ingestion/connectors/api.py` (`ApiConnector`).
4. Add the registry and `get_connector()` to `ingestion/connectors/__init__.py`.

## Check it works

```python
import yaml
from ingestion.connectors import get_connector

with open("configs/sources.yaml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

for source in config["sources"]:
    records = get_connector(source).extract()
    print(f"{source['name']}: {len(records)} records")
    print(records[0], "\n")
```

Expected: about 1000 records per source, with named columns:
```
btc_usdt_hourly: 1000 records
{'open_time': 1791943200000, 'open': '83328.00000000', 'high': '83700.00000000', ...}
```

## Common errors

**1. `ImportError: cannot import name 'get_connector'`**
The registry code isn't in `ingestion/connectors/__init__.py` (or the file isn't saved).

**2. `ModuleNotFoundError: No module named 'ingestion.api'`**
The registry code was pasted into the wrong `__init__.py`. There are two:
- `ingestion/__init__.py` must stay **empty**
- `ingestion/connectors/__init__.py` holds the registry

Check the breadcrumb path above the code in VS Code.

**3. Changes made from the terminal get undone**
VS Code tabs keep their own copy of a file. If a tab is open with unsaved changes, "Save All" overwrites what the terminal wrote. Close the tab before editing a file from the terminal.

**4. `KeyError: 'sources'` even though the file looks right**
On Windows, Python's default file encoding isn't UTF-8, and PowerShell's `Set-Content -Encoding utf8` adds a hidden BOM character at the start of the file. The first key is read as `ï»¿sources`. Fix: always open files with `encoding="utf-8"`.

**5. `KeyError: 'columns'`**
`sources.yaml` is still the Step 00 version. Add the `columns` list.

## Known limitations (fixed in later steps)
- Only the latest 1000 rows are fetched, with no pagination yet. Step 04 adds watermarks for incremental loads.
- No retries if the API is temporarily down. Step 06 adds them.

## Try it yourself
1. Add `SOLUSDT` as a third source. You only need to copy a block and change `name`, `symbol` and `target`; the columns are reused via `*kline_columns`.
2. Change `interval` to `1d` for one source and see what you get.
3. Change `type: api` to `type: csv` and read the error message. The registry tells you exactly what's available.
