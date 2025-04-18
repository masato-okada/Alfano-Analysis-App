# ギア比提案スクリプト（セクター単位）
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns


# JSONファイルのパス指定（任意のパスに変更可能）
main_data_path = r"C:\Users\MasatoOkada\Documents\Python Scripts\Alfano Analysis App\nextjs-app\public\all_sessions_combined.json"
sector_time_path = r"C:\Users\MasatoOkada\Documents\Python Scripts\Alfano Analysis App\nextjs-app\public\sector_data.json"

# メインデータ読み込み
with open(main_data_path, "r") as f:
    main_data = json.load(f)

df = pd.DataFrame(main_data)

# セクタータイムデータ読み込み
with open(sector_time_path, "r") as f:
    sector_data = json.load(f)

# 必要なデータのみ抽出・前処理
df_clean = df.dropna(subset=[
    'Session', 'Sector', 'RPM', 'Speed GPS',
    'F_Gear_Ratio', 'R_Gear_Ratio', 'R_Tire_Diameter [mm]', 'Lap'
])

# タイヤ周長を計算
def get_tire_circumference(diameter_mm):
    return np.pi * diameter_mm

# RPMから速度を再計算（km/h）
def rpm_to_speed_kmh(rpm, gear_ratio, tire_circum_mm):
    wheel_rpm = rpm / gear_ratio
    speed_mps = (wheel_rpm * tire_circum_mm) / (60 * 1000)
    return speed_mps * 3.6

# 仮想リアスプロケット候補を生成
def generate_virtual_gear_ratios(current_rear, delta=3):
    return list(range(current_rear - delta, current_rear + delta + 1))

# セクターごとのベストタイムマップを構築（lap情報含む）
def build_best_sector_map(sector_data):
    best_sector_map = {}
    sector_avg_time = {}  # 平均時間を格納
    sector_count = {}
    for lap_entry in sector_data:
        lap = lap_entry.get("lap")
        sector_times = lap_entry.get("sectorTimes", {})
        for sector_name, time in sector_times.items():
            sector_id = int(sector_name.replace("Sector", ""))
            if sector_id not in best_sector_map or time < best_sector_map[sector_id]["time"]:
                best_sector_map[sector_id] = {"time": time, "lap": lap}
            sector_avg_time[sector_id] = sector_avg_time.get(sector_id, 0) + time
            sector_count[sector_id] = sector_count.get(sector_id, 0) + 1
    sector_weight_map = {k: sector_avg_time[k] / sector_count[k] for k in sector_avg_time}
    return best_sector_map, sector_weight_map

# RPMヒストグラムを構築（基準ラップ & セクター）
def get_reference_rpm_hist(df, session_id, sector_id, lap_id, bin_width=250):
    ref_df = df[(df["Session"] == session_id) & (df["Sector"] == sector_id) & (df["Lap"] == lap_id)]
    if len(ref_df) == 0:
        return None
    rpm_bins = np.arange(6000, 13000 + bin_width, bin_width)
    rpm_hist, _ = np.histogram(ref_df["RPM"], bins=rpm_bins)
    total = rpm_hist.sum()
    if total == 0:
        return None
    weights = rpm_hist / total
    return weights, rpm_bins

best_sector_reference, sector_weighted = build_best_sector_map(sector_data)

# セクターごとに処理
sector_results = []
all_scores = []

for (session_id, sector_id), sector_df in df_clean.groupby(["Session", "Sector"]):
    front = sector_df["F_Gear_Ratio"].iloc[0]
    rear = sector_df["R_Gear_Ratio"].iloc[0]
    tire_diameter = sector_df["R_Tire_Diameter [mm]"].iloc[0]
    tire_circum = get_tire_circumference(tire_diameter)
    virtual_teeth_list = generate_virtual_gear_ratios(rear, delta=3)

    best_lap = best_sector_reference.get(sector_id, {}).get("lap")
    ref = get_reference_rpm_hist(df_clean, session_id, sector_id, best_lap)
    if ref is None:
        continue
    ref_weights, rpm_bins = ref

    score_dict = {}
    for virtual_rear in virtual_teeth_list:
        virtual_ratio = virtual_rear / front
        virtual_speeds = rpm_to_speed_kmh(sector_df["RPM"], virtual_ratio, tire_circum)
        actual_speeds = sector_df["Speed GPS"] / 10.0

        rpm_indices = np.digitize(sector_df["RPM"], rpm_bins) - 1
        valid = (rpm_indices >= 0) & (rpm_indices < len(ref_weights))
        weights = np.array([ref_weights[i] if v else 0 for i, v in zip(rpm_indices, valid)])

        weighted_error = ((virtual_speeds - actual_speeds) ** 2) * weights
        weighted_rmse = np.sqrt(np.sum(weighted_error) / np.sum(weights))
        score_dict[virtual_rear] = weighted_rmse

        all_scores.append({
            "Session": session_id,
            "Sector": sector_id,
            "Virtual Rear Teeth": virtual_rear,
            "Score (Weighted RMSE)": weighted_rmse
        })

    best_rear = min(score_dict, key=score_dict.get)
    sector_results.append({
        "Session": session_id,
        "Sector": sector_id,
        "Current Rear Teeth": rear,
        "Suggested Rear Teeth": best_rear,
        "Score": score_dict[best_rear],
        "Data Points": len(sector_df)
    })

# 結果データフレーム化
result_sector_df = pd.DataFrame(sector_results)
print("--- 推奨ギア比（セクター単位） ---")
print(result_sector_df)

# セクターごとの最適ギア比を個別に出力
print("\n--- セクター別 最適ギア比一覧 ---")
for _, row in result_sector_df.iterrows():
    print(f"セクター{row['Sector']}: {row['Suggested Rear Teeth']}T")

# 全仮想ギア比ごとのスコア出力
all_scores_df = pd.DataFrame(all_scores)
print("\n--- 全ギア比候補と加重スコア（Weighted RMSE） ---")
print(all_scores_df)

# ✅ 可視化（セクターごとのギア比スコア）
plt.figure(figsize=(12, 6))
sns.lineplot(data=all_scores_df, x="Virtual Rear Teeth", y="Score (Weighted RMSE)", hue="Sector", marker="o")
plt.title("仮想ギア比ごとの加重スコア（セクター別）")
plt.xlabel("リアスプロケット歯数")
plt.ylabel("加重RMSE")
plt.grid(True)
plt.legend(title="Sector")
plt.tight_layout()
plt.show()

# ✅ 全体最適ギア比を計算（セクター加重平均）
def compute_weighted_optimal_gear(result_df, weight_map):
    total_weight = 0
    weighted_sum = 0
    for _, row in result_df.iterrows():
        sector = row["Sector"]
        gear = row["Suggested Rear Teeth"]
        weight = weight_map.get(sector, 1.0)
        weighted_sum += gear * weight
        total_weight += weight
    return round(weighted_sum / total_weight, 1) if total_weight > 0 else None

optimal_gear = compute_weighted_optimal_gear(result_sector_df, sector_weighted)
print(f"\n✅ 全体最適リアスプロケット歯数（セクター平均時間加重）: {optimal_gear}T")

"""
このバージョンでは:
1. 各セクターの最速ラップに基づくRPM分布を参照し、仮想ギア比ごとの加重RMSEを算出
2. 全セクターの結果を可視化（セクター別スコアラインプロット）
3. 各セクターの平均タイムを重みとして、全体最適ギア比を加重平均で導出
4. セクター別の最適ギア比一覧を個別出力
"""
