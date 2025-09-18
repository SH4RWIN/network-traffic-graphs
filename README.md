# Data Visualisation Using Matplotlib (Zeek Logs)

A small, focused toolkit to transform Zeek network logs into tidy CSVs and visualize them with Matplotlib. It includes ready-made charts for: 
- Connections over time (line chart)
- Application protocol share by event count (pie chart)

---

## Why this project exists
- **Operational visibility**: Quickly see traffic volume trends and protocol distribution without spinning up a full SIEM.
- **Reproducible analysis**: A consistent pipeline from raw Zeek logs → CSV → charts.
- **Lightweight & local**: Works on a laptop; no heavy infra required.

---

## What this project does
- Converts Zeek `.log` files into structured `.csv` files.
- Standardizes fields across logs to a common schema: `datetime`, `unified_protocol`, `total_bytes`, `event_count`.
- Generates publication-ready charts saved into `outputs/`.

---

## How it works (High-level)
1. Optional: Use Zeek (local or Docker) to produce `.log` files into `data_processing/logs/`.
2. Run `log2csv.py` to convert `.log` files → `csv/*.csv`.
3. Visualize:
   - `pie_chart.py` loads all CSVs, aggregates by `unified_protocol`, and plots a pie chart (application protocols only).
   - `line_chart.py` loads `csv/conn.log.csv`, resamples events in time bins (e.g., 30 seconds), and plots a line chart.

Data flow:
```
Zeek .log  →  csv/*.csv  →  pandas DataFrame (standardized)  →  Matplotlib charts (outputs/*.png)
```

---

## Repository layout
```
Data_visualisation_using_matplotlib/
  csv/                         # Generated CSVs
  data_processing/             # Zeek integration (logs + docker-compose)
    logs/                      # Raw Zeek logs (.log)
  outputs/                     # Saved charts (.png)
  line_chart.py                # Connections-over-time chart
  pie_chart.py                 # Application-protocol pie chart
  log2csv.py                   # Log → CSV converter
  venv/                        # (Optional) Python virtual environment
```

---

## Standardized data model
- **datetime**: Parsed timestamp as pandas `datetime64[ns]` (from Zeek `ts` if present)
- **unified_protocol**:
  - For `conn.log.csv`: derived from `service` (application protocols), supports comma-separated values (exploded to multiple rows)
  - Else: falls back to `proto` column or filename (e.g., `dns`, `http`)
- **total_bytes**: Sum of `orig_bytes + resp_bytes` when available, otherwise protocol-specific fallbacks, else `0`
- **event_count**: `1` per row, enabling simple counts via groupby/resample

---

## Requirements
- Python 3.12+ (recommended)
- pip
- Packages: `pandas`, `matplotlib`, `seaborn` (optional), `numpy`
- Optional: Docker (to run Zeek via `data_processing/docker-compose.yml`)

This repo already includes a `venv/` with dependencies, but you can recreate your own if preferred.

---

## Setup
```bash
# From the project root
python -m venv .venv
# Windows PowerShell
. .venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

pip install -U pip
pip install pandas matplotlib seaborn numpy
```

If you plan to use Dockerized Zeek:
```bash
# From data_processing/
docker compose up -d
# Zeek logs will appear in data_processing/logs/
```

---

## Generate CSVs from Zeek logs
```bash
# From project root
python log2csv.py
# CSVs will be written into ./csv/
```

Notes:
- Ensure `data_processing/logs/*.log` contains Zeek logs, or adjust paths in `log2csv.py` if needed.

---

## Usage: Visualizations

### Application protocol share (pie chart)
```bash
python pie_chart.py
```
- Loads all CSVs from `./csv/`
- Excludes transport protocols (`tcp`, `udp`, etc.)
- Saves: `outputs/combined_application_protocol_share_by_count_pie.png`

### Connections over time (line chart)
```bash
python line_chart.py
```
- Loads only `csv/conn.log.csv`
- Resamples counts into time bins (default `30S`)
- Saves: `outputs/connections_over_time_from_conn_line.png`

---

## Configuration knobs
- `line_chart.py`
  - `plot_connections_over_time(..., freq="30S")`: adjust resample bin size (examples: `"1S"`, `"1Min"`, `"5Min"`, `"1H"`)
- `pie_chart.py`
  - `transport_protocols_to_exclude`: extend/modify the set to tune what’s considered “application-level”
  - `top_n`: change how many categories are shown before grouping into `other`
- Paths
  - CSV source directory: `csv/`
  - Outputs directory: `outputs/`

---

## Outputs
All generated figures are saved to `outputs/` as `.png` at 150 DPI. You can embed them in reports or dashboards.

---

## Troubleshooting
- Empty charts or “No valid timestamps found”
  - Verify `csv/*.csv` exist and contain a `ts` column (for datetime) or valid `datetime`
  - Ensure timezone consistency (Zeek `ts` is epoch seconds; adjust display as needed)
- “Resample failed” in line chart
  - Check that `datetime` is parsed and set as index; invalid timestamps are dropped
- Pie chart seems dominated by `unknown_*`
  - Confirm `service` (for `conn.log.csv`) or `proto` columns exist; otherwise protocol inference falls back to filename
- Memory/Performance
  - Use `low_memory=False` is already set; for very large logs, consider chunked CSV reads

---

## Extending
- Add new charts by importing `load_all_csvs` / `load_and_standardize_log` from `pie_chart.py`.
- Create additional aggregations (e.g., bytes transferred over time) by grouping on `total_bytes`.
- Consider exporting to Parquet for faster repeated analysis.

---

## Contributing
- Keep code readable and explicit; prefer clear variable names.
- Follow existing formatting; avoid unrelated refactors in edits.
- Add minimal, focused docstrings where behavior is non-obvious.

---

## License
Choose a license for your project (e.g., MIT, Apache-2.0) and add it here.

---

## FAQ
- Can I run only with CSVs and no Zeek? Yes—drop your CSVs into `csv/` with the standardized columns or rely on the loaders to infer columns.
- Do I need the provided `venv/`? No. You can use your own virtual environment or system Python.
- Can I change where outputs are saved? Yes—both scripts accept paths you can modify in-code; you can generalize to CLI flags if desired. 