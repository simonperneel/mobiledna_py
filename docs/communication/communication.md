## 1. elastic.py
These are some of the functions in `elastic.py`:

```python

connect(server=cfg.server, port=cfg.port) -> Elasticsearch
```

Connects to the ES server and returns an ES object. Make sure you have the correct version of the `elasticsearch` package installed. This functionality breaks with updates beyond the recommended version. Requires a **config file** to work. Returns an Elasticsearch object.


```python
ids_from_file(dir: str, file_name='ids', file_type='csv')
```

Reads a list of mobileDNA IDs from a CSV file, containing a single column. Returns them as a list.

```python

ids_from_server(index="appevents",
                    time_range=('2018-01-01T00:00:00.000', '2030-01-01T00:00:00.000'),
                    study=None) -> dict:
```

Extracts IDs from the server that have logged _something_ in the given time range, in the given index, in the given study. Returns them as a dictionary (keys: IDs, values: doc_counts).

## 2. snapshot_restore.py

Script that automates the process of creating a snapshot creation, and recovering and restoring it to the dbcopy server.

Requires a **config file** with server credentials, and the geckodriver (https://github.com/mozilla/geckodriver/releases) to work.
