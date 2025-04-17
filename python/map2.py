import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

class MobaraTrackAlignment:
    def __init__(self, csv_path):
        """
        トラックの座標変換と整列
        
        Args:
            csv_path (str): CSVファイルのパス
        """
        # CSVファイルの読み込み
        self.df = pd.read_csv(csv_path, sep=',', encoding='utf-8')
        self.df.columns = [col.strip() for col in self.df.columns]
        
        # 座標データの抽出
        self.latitudes = self.df['Lat.'].dropna().values
        self.longitudes = self.df['Lon.'].dropna().values
    
    def _align_coordinates(self):
        """
        座標を正確に整列し、トラックの向きを揃える
        
        Returns:
            tuple: 変換後のx, y座標
        """
        # 基準点（最初の点）
        lat0 = self.latitudes[0]
        lon0 = self.longitudes[0]
        
        # 緯度・経度から距離への変換係数
        lat_meter = 111000  # 緯度1度あたりの距離（メートル）
        lon_meter = 111320 * np.cos(np.radians(lat0))  # 経度1度あたりの距離（メートル）
        
        # 相対座標への変換
        x_raw = (self.longitudes - lon0) * lon_meter
        y_raw = (self.latitudes - lat0) * lat_meter
        
        # 主成分分析による座標回転の微調整
        coords = np.column_stack([x_raw, y_raw])
        cov_matrix = np.cov(coords.T)
        eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)
        
        # 主軸を基準に回転角を計算
        main_axis = eigenvectors[:, np.argmax(eigenvalues)]
        rotation_angle = np.arctan2(main_axis[1], main_axis[0])
        
        # 座標を回転
        rotation_matrix = np.array([
            [np.cos(-rotation_angle), -np.sin(-rotation_angle)],
            [np.sin(-rotation_angle), np.cos(-rotation_angle)]
        ])
        
        rotated_coords = coords @ rotation_matrix.T
        
        return rotated_coords[:, 0], rotated_coords[:, 1]
    
    def detect_corners(self, max_corners=None, g_force_threshold=0.2):
        """
        G-Forceに基づいてコーナーを検出
        
        Args:
            max_corners (int, optional): 検出するコーナーの最大数
            g_force_threshold (float): G-Forceの閾値
        
        Returns:
            tuple: コーナーのインデックス、x座標、y座標
        """
        # G-Forceに基づくコーナー検出
        g_force_lateral = np.abs(self.df['Gf. Y'] / 9.8)
        
        # コーナー検出
        peaks, _ = find_peaks(g_force_lateral, height=g_force_threshold, distance=10)
        
        # 最大数の制限
        if max_corners is not None and len(peaks) > max_corners:
            # G-Forceの大きさでソートし、上位のコーナーを選択
            sorted_peak_indices = np.argsort(g_force_lateral[peaks])[::-1]
            peaks = peaks[sorted_peak_indices[:max_corners]]
        
        # 座標の整列
        x, y = self._align_coordinates()
        
        return peaks, x[peaks], y[peaks]
    
    def visualize_track(self, max_corners=None, g_force_threshold=0.2):
        """
        トラックの上面図を可視化
        
        Args:
            max_corners (int, optional): 表示するコーナーの最大数
            g_force_threshold (float): G-Forceの閾値
        """
        # 座標の整列
        x, y = self._align_coordinates()
        
        plt.figure(figsize=(10, 10))
        
        # トラックのトレース
        plt.plot(x, y, '-o', markersize=2, color='blue', label='トラックトレース')
        
        # コーナー検出と表示
        corner_indices, corner_x, corner_y = self.detect_corners(
            max_corners=max_corners, 
            g_force_threshold=g_force_threshold
        )
        
        plt.scatter(corner_x, corner_y, color='red', s=100, label='コーナー')
        
        plt.title('モバラツインサーキット 上面図')
        plt.xlabel('X [m]')
        plt.ylabel('Y [m]')
        
        # アスペクト比を1:1に設定
        plt.gca().set_aspect('equal')
        
        plt.grid(True)
        plt.legend()
        
        # トラック形状の特徴量計算
        track_length = np.sum(np.sqrt(np.diff(x)**2 + np.diff(y)**2))
        width_x = np.ptp(x)
        width_y = np.ptp(y)
        
        # トラック情報の表示
        plt.annotate(
            f'トラック長: {track_length:.2f} m\n'
            f'X幅: {width_x:.2f} m\n'
            f'Y幅: {width_y:.2f} m\n'
            f'検出コーナー数: {len(corner_indices)}',
            xy=(0.05, 0.95), 
            xycoords='axes fraction',
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.7)
        )
        
        plt.tight_layout()
        plt.show()
    
    def get_track_characteristics(self, max_corners=None, g_force_threshold=0.2):
        """
        トラックの特徴量を取得
        
        Args:
            max_corners (int, optional): 検出するコーナーの最大数
            g_force_threshold (float): G-Forceの閾値
        
        Returns:
            dict: トラックの特徴量
        """
        x, y = self._align_coordinates()
        
        # コーナー検出
        corner_indices, corner_x, corner_y = self.detect_corners(
            max_corners=max_corners, 
            g_force_threshold=g_force_threshold
        )
        
        return {
            'track_length': np.sum(np.sqrt(np.diff(x)**2 + np.diff(y)**2)),
            'width_x': np.ptp(x),
            'width_y': np.ptp(y),
            'num_corners': len(corner_indices),
            'corner_coordinates': list(zip(corner_x, corner_y))
        }

# 使用例
def main():
    # CSVファイルのパス
    csv_path = r"C:\Users\MasatoOkada\Documents\Python Scripts\Alfano Analysis App\data\test-lap2.csv"
    
    # インスタンス作成
    track_aligner = MobaraTrackAlignment(csv_path)
    
    # トラックの上面図を表示（コーナーを最大6つに制限）
    track_aligner.visualize_track(max_corners=6)
    
    # トラックの特徴量を表示
    track_characteristics = track_aligner.get_track_characteristics(max_corners=6)
    print("トラックの特徴:")
    for key, value in track_characteristics.items():
        print(f"{key}: {value}")

if __name__ == '__main__':
    main()