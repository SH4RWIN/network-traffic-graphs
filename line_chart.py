import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from pie_chart import load_and_standardize_log


def plot_connections_over_time(df: pd.DataFrame, freq: str = "30S", out_path: Path | None = None) -> None:
	"""Plot count of connections (events) over time at the given interval."""
	# Ensure datetime is valid and present
	df = df.copy()
	df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
	df = df[df["datetime"].notna()]
	if df.empty:
		print("No valid timestamps found for line chart.")
		return

	series_df = df.set_index("datetime").sort_index()

	# Resample by interval and count events
	try:
		connections = series_df["event_count"].resample(freq).sum()
	except Exception as e:
		print(f"Resample failed: {e}")
		return

	if connections.empty:
		print("No data after resampling for the selected frequency.")
		return

	plt.figure(figsize=(12, 5))
	plt.plot(connections.index, connections.values, color="tab:blue", label="Connections")
	plt.xlabel("Time")
	plt.ylabel("Connections (count)")
	plt.title(f"Connections over time (bin={freq})")
	plt.legend(loc="upper left")
	plt.tight_layout()
	if out_path is not None:
		plt.savefig(out_path, dpi=150)
	plt.show()


def main():
	csv_dir = Path(__file__).parent / "csv"
	conn_csv = csv_dir / "conn.log.csv"
	if not conn_csv.exists():
		print(f"File not found: {conn_csv}")
		return

	conn_df = load_and_standardize_log(conn_csv)
	if conn_df is None or conn_df.empty:
		print("No data loaded from conn.log.csv")
		return

	# Outputs
	out_dir = Path("outputs")
	out_dir.mkdir(exist_ok=True)

	# Line chart: Connections over time (from conn.log.csv only)
	plot_connections_over_time(
		conn_df,
		freq="30S",
		out_path=out_dir / "connections_over_time_from_conn_line.png",
	)


if __name__ == "__main__":
	main()
