import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# CSVファイルパス（Windows環境用パス）
csv_path = r"C:\Users\MasatoOkada\Documents\Python Scripts\Alfano Analysis App\data\test-lap2.csv"

# CSV読み込み
df = pd.read_csv(csv_path, sep=',', encoding='utf-8')
df.columns = [col.strip() for col in df.columns]

manual_corners_geo = [
    {
        "name": "Corner 1",
        "lat_min": 35.3815536, "lat_max": 35.3819542,
        "lon_min": 140.281662, "lon_max": 140.2819214
    },
    {
        "name": "Corner 2",
        "lat_min": 35.3814621, "lat_max": 35.3817215,
        "lon_min": 140.2812653, "lon_max": 140.281662
    },
    {
        "name": "Corner 3",
        "lat_min": 35.3817215, "lat_max": 35.3819427,
        "lon_min": 140.2810516, "lon_max": 140.2817535
    },
    {
        "name": "Corner 4",
        "lat_min": 35.3815727, "lat_max": 35.3818512,
        "lon_min": 140.2806091, "lon_max": 140.2810516
    },
    {
        "name": "Corner 5",
        "lat_min": 35.3813477, "lat_max": 35.3816147,
        "lon_min": 140.2804413, "lon_max": 140.2810974
    },
    {
        "name": "Corner 6",
        "lat_min": 35.381546, "lat_max": 35.3820724,
        "lon_min": 140.280426, "lon_max": 140.2818756
    },
]


# 緯度・経度データを抽出
latitudes = df['Lat.'].dropna().tolist()
longitudes = df['Lon.'].dropna().tolist()

# 基準点（スタート位置）を決定
lat0 = latitudes[0]
lon0 = longitudes[0]

# 1度あたりの距離[m]を計算
lat_meter = 111000  # 緯度方向
lon_meter = 111320 * np.cos(np.radians(lat0))  # 経度方向

# ローカル座標に変換（相対距離[m]）
x = [(lon - lon0) * lon_meter for lon in longitudes]
y = [(lat - lat0) * lat_meter for lat in latitudes]

# 最大値取得
x_max = max(abs(min(x)), abs(max(x)))
y_max = max(abs(min(y)), abs(max(y)))

# プロット
plt.figure(figsize=(8, 8))
plt.plot(x, y, '-o', markersize=2, color='blue', label='Lap 2 Trace')
plt.title("Mobara Twin Circuit West Course - Local Coordinates (Centered Axis)")
plt.xlabel("X [m]")
plt.ylabel("Y [m]")
plt.axis('equal')
plt.xlim(-x_max, x_max)
plt.ylim(-y_max, y_max)
plt.grid(True)
plt.legend()
plt.show()

# 任意に区間を指定（start_idx, end_idx）
manual_corners = [
    (50, 80),   # コーナー1
    (120, 150), # コーナー2
    (200, 230), # コーナー3
]

# プロットで確認
plt.figure(figsize=(8, 8))
plt.plot(x, y, '-o', markersize=1, label='Lap Trace')

for idx, (start, end) in enumerate(manual_corners):
    plt.plot(x[start:end], y[start:end], linewidth=4, label=f'Corner {idx+1}')

plt.title("Manual Corner Sections - Mobara Twin Circuit West")
plt.xlabel("X [m]")
plt.ylabel("Y [m]")
plt.axis('equal')
plt.grid(True)
plt.legend()
plt.show()
