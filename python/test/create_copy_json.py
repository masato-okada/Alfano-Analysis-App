import pandas as pd
import json

# --- ファイルパスの定義 ---
csv_data_path = r"C:\Users\MasatoOkada\Documents\Python Scripts\Alfano Analysis App\python\test\dashware_data_with_sector_column.csv"
csv_summary_path = r"C:\Users\MasatoOkada\Documents\Python Scripts\Alfano Analysis App\python\test\sector_times_per_lap.csv"
json_output_path = r"C:\Users\MasatoOkada\Documents\Python Scripts\Alfano Analysis App\nextjs-app\public\sector_data.json"

# --- CSVの読み込み ---
df_data = pd.read_csv(csv_data_path)
df_summary = pd.read_csv(csv_summary_path)

# --- Time_sec を補完（もし未定義なら） ---
if "Time_sec" not in df_data.columns and "Time [1/10 s]" in df_data.columns:
    df_data["Time_sec"] = df_data["Time [1/10 s]"] * 0.1

# --- Lapごとにデータを統合して JSON 化 ---
combined = []

for lap in sorted(df_data["Lap"].dropna().unique()):
    lap_points = df_data[df_data["Lap"] == lap][["x", "y", "Time_sec", "Sector"]].to_dict(orient="records")

    sector_times_row = df_summary[df_summary["Lap"] == lap]
    if not sector_times_row.empty:
        sector_times = sector_times_row.drop(columns=["Lap"]).iloc[0].to_dict()
    else:
        sector_times = {}

    combined.append({
        "lap": int(lap),
        "sectorTimes": sector_times,
        "points": lap_points
    })

# --- JSONとして保存 ---
with open(json_output_path, "w", encoding="utf-8") as f:
    json.dump(combined, f, ensure_ascii=False, indent=2)

print(f"✅ JSONファイルを保存しました → {json_output_path}")
