import os
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Any


def load_and_standardize_log(csv_path: Path) -> pd.DataFrame | None:
	"""Loads a single CSV, standardizes columns, and infers protocol if needed."""
	file_name = csv_path.name
	log_type = file_name.replace(".log.csv", "")

	try:
		df = pd.read_csv(
			csv_path,
			header=0,
			na_values=["-", "(empty)", ""],
			low_memory=False,
		)
		df["event_count"] = 1  # Add a generic event counter
		
		# Convert ts (epoch seconds) to datetime
		if "ts" in df.columns:
			df["ts"] = pd.to_numeric(df["ts"], errors="coerce")
			df["datetime"] = pd.to_datetime(df["ts"], unit="s", errors="coerce")
		else:
			df["datetime"] = pd.NaT

		# --- Protocol Standardization ---
		if file_name == "conn.log.csv" and "service" in df.columns:
			# For conn.log.csv, prioritize 'service' which lists application protocols
			df["unified_protocol"] = df["service"].fillna("unknown_service")
			# Handle comma-separated services (e.g., "gssapi,dce_rpc")
			df["unified_protocol"] = df["unified_protocol"].apply(
				lambda x: [s.strip().lower() for s in str(x).split(',')] # Lowercase here
			)
			df = df.explode("unified_protocol")
		elif "proto" in df.columns:
			# Fallback to 'proto' if not conn.log or no 'service'
			df["unified_protocol"] = df["proto"].fillna("unknown_protocol").str.lower()
		elif log_type:
			# Infer from filename for other log types
			df["unified_protocol"] = log_type.lower()
		else:
			df["unified_protocol"] = "unknown_log_type"

		# --- total_bytes Standardization ---
		df["total_bytes"] = 0 # Default to 0 if no specific byte column is found

		if {"orig_bytes", "resp_bytes"}.issubset(df.columns):
			for col in ["orig_bytes", "resp_bytes"]:
				df[col] = pd.to_numeric(df[col], errors="coerce")
			df["total_bytes"] = df["orig_bytes"].fillna(0) + df["resp_bytes"].fillna(0)
		elif "response_body_len" in df.columns:
			df["total_bytes"] = pd.to_numeric(df["response_body_len"], errors="coerce").fillna(0)
		elif file_name == "files.log.csv" and "total_bytes" in df.columns:
			# For files.log, 'total_bytes' directly represents the file size
			df["total_bytes"] = pd.to_numeric(df["total_bytes"], errors="coerce").fillna(0)
			
		# Select and return only the standardized columns
		return df[["datetime", "unified_protocol", "total_bytes", "event_count"]]

	except Exception as e:
		print(f"Error processing {csv_path}: {e}")
		return None


def load_all_csvs(csv_dir: str | os.PathLike) -> pd.DataFrame:
	"""Loads and combines all CSV files from a directory."""
	csv_dir_path = Path(csv_dir)
	all_dfs = []

	for csv_file in csv_dir_path.glob("*.csv"):
		df = load_and_standardize_log(csv_file)
		if df is not None:
			all_dfs.append(df)

	if not all_dfs:
		return pd.DataFrame(columns=["datetime", "unified_protocol", "total_bytes", "event_count"])

	combined_df = pd.concat(all_dfs, ignore_index=True)
	# Enforce datetime dtype after concat (important for resampling)
	combined_df["datetime"] = pd.to_datetime(combined_df["datetime"], errors="coerce")
	# Ensure numeric bytes
	combined_df["total_bytes"] = pd.to_numeric(combined_df["total_bytes"], errors="coerce").fillna(0)
	return combined_df


def plot_protocol_pie(df: pd.DataFrame, out_path: Path | None = None) -> None:
	"""Plot protocol share pie by event count, excluding transport protocols."""
	# Define transport protocols to exclude (all lowercase)
	transport_protocols_to_exclude = {'tcp', 'udp', 'unknown_transport', 'icmp', 'arp', 'unknown_protocol', 'unknown_service', 'unknown_log_type'}

	# Filter out transport-layer protocols
	filtered_df = df[~df["unified_protocol"].isin(transport_protocols_to_exclude)]

	# Group by unified_protocol and count events
	agg = filtered_df.groupby("unified_protocol", dropna=False)["event_count"].sum().sort_values(ascending=False)
	label = "Application Protocol share by event count"

	# Keep top categories and group rest into 'other' if there are many
	top_n = 8
	if len(agg) > top_n:
		top = agg.iloc[:top_n]
		other = pd.Series({"other": agg.iloc[top_n:].sum()})
		agg = pd.concat([top, other])

	plt.figure(figsize=(8, 8))
	colors = plt.cm.tab20.colors
	plt.pie(agg.values, labels=agg.index, autopct="%1.1f%%", startangle=90, colors=colors)
	plt.title(label)
	plt.tight_layout()
	if out_path is not None:
		plt.savefig(out_path, dpi=150)
	plt.show()


def main():
	csv_dir = Path(__file__).parent / "csv"
	combined_df = load_all_csvs(csv_dir)

	# Outputs
	out_dir = Path("outputs")
	out_dir.mkdir(exist_ok=True)

	# Pie chart by event count
	plot_protocol_pie(combined_df, out_path=out_dir / "combined_application_protocol_share_by_count_pie.png")


if __name__ == "__main__":
	main()
