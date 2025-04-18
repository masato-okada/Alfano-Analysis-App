# ギア比提案スクリプト（セクター単位 + RPM分布可視化）
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns

# JSONファイルのパス指定
main_data_path = r"C:\Users\MasatoOkada\Documents\Python Scripts\Alfano Analysis App\nextjs-app\public\all_sessions_combined.json"
sector_time_path = r"C:\Users\MasatoOkada\Documents\Python Scripts\Alfano Analysis App\nextjs-app\public\sector_data.json"

# メインデータ読み込み
with open(main_data_path, "r") as f:
    main_data = json.load(f)

df = pd.DataFrame(main_data)

# セクタータイムデータ読み込み
with open(sector_time_path, "r") as f:
    sector_data = json.load(f)

# 前処理
df_clean = df.dropna(subset=[
    'Session', 'Sector', 'RPM', 'Speed GPS',
    'F_Gear_Ratio', 'R_Gear_Ratio', 'R_Tire_Diameter [mm]', 'Lap'
])

# ベストセクターラップと全体のRPM分布を比較可視化
def plot_rpm_distribution_by_sector(df, sector_data, bin_width=250):
    best_lap_map = {}
    for entry in sector_data:
        lap = entry.get("lap")
        for sector_name, time in entry.get("sectorTimes", {}).items():
            sector_id = int(sector_name.replace("Sector", ""))
            if sector_id not in best_lap_map or time < best_lap_map[sector_id]["time"]:
                best_lap_map[sector_id] = {"lap": lap, "time": time}

    rpm_bins = np.arange(6000, 13000 + bin_width, bin_width)
    sectors = sorted(df["Sector"].unique())
    num_sectors = len(sectors)

    fig, axes = plt.subplots(nrows=(num_sectors + 1) // 2, ncols=2, figsize=(14, 3 * ((num_sectors + 1) // 2)))
    axes = axes.flatten()

    for i, sector_id in enumerate(sectors):
        ax = axes[i]
        sector_df = df[df["Sector"] == sector_id]
        best_lap = best_lap_map.get(sector_id, {}).get("lap")

        if best_lap is not None:
            best_rpms = sector_df[sector_df["Lap"] == best_lap]["RPM"]
            all_rpms = sector_df["RPM"]

            sns.histplot(all_rpms, bins=rpm_bins, kde=False, stat="density", label="全体平均", ax=ax, color="gray", alpha=0.5)
            sns.histplot(best_rpms, bins=rpm_bins, kde=False, stat="density", label="最速ラップ", ax=ax, color="red", alpha=0.7)
            ax.set_title(f"セクター{sector_id} RPM分布")
            ax.set_xlabel("RPM")
            ax.set_ylabel("頻度（密度）")
            ax.legend()

    plt.tight_layout()
    plt.show()

# RPM分布をプロット
plot_rpm_distribution_by_sector(df_clean, sector_data)

"""
このスクリプトは各セクターにおいて、
1. 全体のRPM使用傾向
2. 最速ラップ時のRPM使用傾向
をそれぞれヒストグラムで比較表示します。
"""