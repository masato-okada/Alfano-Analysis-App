
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# CSVファイルの読み込み（パスを変更してください）
df_lap2 = pd.read_csv("test-lap2.csv")
df_lap3 = pd.read_csv("test-lap3.csv")

# 列名の整形
df_lap2.rename(columns={'Lat.': 'Lat', 'Lon.': 'Lon'}, inplace=True)
df_lap3.rename(columns={'Lat.': 'Lat', 'Lon.': 'Lon'}, inplace=True)

# 中心点を共通化
lat0 = df_lap2['Lat'].mean()
lon0 = df_lap2['Lon'].mean()
R = 6378137  # 地球半径

# 緯度経度→相対XY座標に変換
for df in [df_lap2, df_lap3]:
    df['x'] = (df['Lon'] - lon0) * (np.pi / 180) * R * np.cos(np.deg2rad(lat0 / 1e6))
    df['y'] = (df['Lat'] - lat0) * (np.pi / 180) * R

# クリック処理
clicked_points = []

def onclick(event):
    if event.xdata and event.ydata:
        clicked_points.append((event.xdata, event.ydata))
        plt.plot(event.xdata, event.ydata, 'ro')
        if len(clicked_points) % 2 == 0:
            x_vals = [clicked_points[-2][0], clicked_points[-1][0]]
            y_vals = [clicked_points[-2][1], clicked_points[-1][1]]
            plt.plot(x_vals, y_vals, 'r--', label=f'Gate {len(clicked_points)//2}')
            plt.legend()
            plt.draw()
        if len(clicked_points) == 12:
            print("すべての仮想ラインを選択しました。座標：")
            for i in range(0, 12, 2):
                print(f"Gate {i//2 + 1}: Start={clicked_points[i]}, End={clicked_points[i+1]}")
            fig.canvas.mpl_disconnect(cid)

fig, ax = plt.subplots(figsize=(10, 8))
ax.plot(df_lap2['x'], df_lap2['y'], label='Lap2', linewidth=2)
ax.plot(df_lap3['x'], df_lap3['y'], label='Lap3', linewidth=2, linestyle='--')
ax.set_title("Click 12 Points (6 Gates) to Define Sector Gates")
ax.set_xlabel("X [m]")
ax.set_ylabel("Y [m]")
ax.axis('equal')
ax.grid(True)
ax.legend()

cid = fig.canvas.mpl_connect('button_press_event', onclick)
plt.show()
