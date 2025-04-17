import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import LineString, Point
import os

# --- 設定 ---
TIME_COL = 'Time [1/10 s]'
LAP_COL = 'Lap'
LAT_COL = 'Lat.'
LON_COL = 'Lon.'

# --- ゲート定義（5セクターに対応する5ゲート） ---
sector_gates = [
    ((49778708.997923136, -20106684.331129372), (43431703.8760539, -12294985.719597995)),
    ((37768222.38269365, -3018593.6184044927), (32983556.98313068, 4402520.062550306)),
    ((272069.0473430604, 12800096.069946542), (-2071440.5361163616, 19732978.587680638)),
    ((-32048833.957867995, -8779721.344408885), (-28533569.58267887, -17860820.9803141)),
    ((-30584140.468205854, -32312463.41164714), (-35759390.798345394, -41002978.11697579))
]

# --- XY変換関数 ---
def convert_to_xy(df, lat0, lon0, R=6378137):
    df['x'] = (df[LON_COL] - lon0) * (np.pi / 180) * R * np.cos(np.deg2rad(lat0 / 1e6))
    df['y'] = (df[LAT_COL] - lat0) * (np.pi / 180) * R
    return df

# --- セクター識別 ---
def assign_sector(df, gate_times):
    df['Sector'] = None

    if any(g is None for g in gate_times):
        return df

    sector_bounds = [gt[2] for gt in gate_times]

    for i in range(len(sector_bounds) - 1):
        t_start = sector_bounds[i]
        t_end = sector_bounds[i + 1]
        mask = (df[TIME_COL] >= t_start) & (df[TIME_COL] < t_end)
        df.loc[mask, 'Sector'] = i + 1

    # セクター5: gate5 → gate1（ラップ内）
    t_start = sector_bounds[-1]
    t_end = sector_bounds[0]
    mask = (df[TIME_COL] >= t_start) | (df[TIME_COL] < t_end)
    df.loc[mask, 'Sector'] = 5

    return df

# --- ゲート通過時刻補間 ---
def compute_crossing_time(df, gate_start, gate_end):
    gate_line = LineString([gate_start, gate_end])
    for i in range(len(df) - 1):
        p1 = (df.iloc[i]['x'], df.iloc[i]['y'])
        p2 = (df.iloc[i + 1]['x'], df.iloc[i + 1]['y'])
        segment = LineString([p1, p2])
        if segment.crosses(gate_line):
            intersection = segment.intersection(gate_line)
            if intersection.geom_type == 'Point':
                time1 = df.iloc[i][TIME_COL]
                time2 = df.iloc[i + 1][TIME_COL]
                dist1 = Point(p1).distance(intersection)
                dist2 = Point(p2).distance(intersection)
                ratio = dist1 / (dist1 + dist2)
                time_cross = time1 + ratio * (time2 - time1)
                return (intersection.x, intersection.y, time_cross)
    return None

# --- データ読み込み ---
df_all = pd.read_csv("dashware_data.csv")

# --- 基準緯度経度取得（Lap1基準） ---
lat0 = df_all[df_all[LAP_COL] == 1][LAT_COL].mean()
lon0 = df_all[df_all[LAP_COL] == 1][LON_COL].mean()

# --- セクター割り当て用の新しいDataFrame構築 ---
df_all['Sector'] = None

# --- 各Lapごとの処理 ---
lap_ids = sorted(df_all[LAP_COL].dropna().unique())

for lap in lap_ids:
    df_lap = df_all[df_all['Lap'] == lap].copy()
    df_lap = convert_to_xy(df_lap, lat0, lon0)
    gate_times = [compute_crossing_time(df_lap, start, end) for start, end in sector_gates]
    df_lap = assign_sector(df_lap, gate_times)
    df_all.loc[df_lap.index, 'Sector'] = df_lap['Sector']

# --- 全体にも x, y を追加 ---
df_all = convert_to_xy(df_all, lat0, lon0)
df_all.to_csv("dashware_data_with_sector_column.csv", index=False)

# --- セクタータイム計算（diff積算方式） ---
df_all['Time_sec'] = df_all['Time [1/10 s]'] * 0.1
sector_times = []

for lap in lap_ids:
    df_lap = df_all[df_all['Lap'] == lap].copy()
    df_lap = df_lap.sort_values('Time_sec').reset_index(drop=True)
    df_lap['Time_diff'] = df_lap['Time_sec'].diff().fillna(0)

    for sector in range(1, 6):
        df_sector = df_lap[df_lap['Sector'] == sector]
        if df_sector.empty:
            continue
        time_sum = df_sector['Time_diff'].sum()
        sector_times.append({
            'Lap': lap,
            'Sector': sector,
            'SectorTime_sec': time_sum
        })

# --- 集計と保存 ---
df_sector_times = pd.DataFrame(sector_times)
pivot_df = df_sector_times.pivot(index="Lap", columns="Sector", values="SectorTime_sec")
pivot_df.columns = [f"Sector{i}" for i in pivot_df.columns]
pivot_df.to_csv("sector_times_per_lap.csv")
print("セクタータイムを保存しました → sector_times_per_lap.csv")

# --- 可視化 ---
plt.figure(figsize=(10, 8))
for sector_id in sorted(df_all['Sector'].dropna().unique()):
    df_sector = df_all[df_all['Sector'] == sector_id]
    plt.plot(df_sector['x'], df_sector['y'], label=f"Sector {int(sector_id)}")

# ゲートの描画
for i, (start, end) in enumerate(sector_gates):
    plt.plot([start[0], end[0]], [start[1], end[1]], 'k--', linewidth=1)
    mid_x = (start[0] + end[0]) / 2
    mid_y = (start[1] + end[1]) / 2
    plt.text(mid_x, mid_y, f"Gate {i+1}", fontsize=9, color='black')

plt.title("Lap Trajectory with Sector Coloring")
plt.xlabel("X")
plt.ylabel("Y")
plt.axis('equal')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()