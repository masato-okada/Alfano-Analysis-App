import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from scipy.spatial.distance import cdist
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Tuple

class RefinedCornerClassifier:
    def __init__(self, reference_lap_path: str):
        """
        リファレンスラップからコーナー特性を学習
        
        Args:
            reference_lap_path (str): 基準となるラップのCSVファイルパス
        """
        # CSVファイルの読み込み
        self.reference_df = pd.read_csv(reference_lap_path, sep=',', encoding='utf-8')
        self.reference_df.columns = [col.strip() for col in self.reference_df.columns]
        
        # コーナー検出と特徴量計算
        self.reference_corners = self._detect_corners_with_features()
    
    def _calculate_corner_features(self, df: pd.DataFrame, indices: np.ndarray) -> np.ndarray:
        """
        コーナーの特徴量を計算
        
        Args:
            df (pd.DataFrame): データフレーム
            indices (np.ndarray): コーナーインデックス
        
        Returns:
            np.ndarray: コーナーの特徴量
        """
        features = []
        for idx in indices:
            # 周辺データポイントの範囲（前後50ポイント）
            start = max(0, idx - 50)
            end = min(len(df), idx + 50)
            
            # 特徴量計算
            section = df.iloc[start:end]
            feature = [
                df['Gf. Y'].iloc[idx] / 9.8,  # 横G
                np.mean(section['Speed GPS']),  # 平均速度
                np.std(section['Speed GPS']),  # 速度の標準偏差
                np.mean(section['RPM']),  # 平均RPM
                np.std(section['RPM']),  # RPMの標準偏差
            ]
            features.append(feature)
        
        return np.array(features)
    
    def _detect_corners_with_features(self, 
                                      g_force_threshold: float = 0.2, 
                                      min_distance: int = 10,
                                      max_corners: int = None) -> List[int]:
        """
        特徴量を考慮したコーナー検出
        
        Args:
            g_force_threshold (float): G-Forceの閾値
            min_distance (int): コーナー間の最小距離
            max_corners (int, optional): 検出するコーナーの最大数
        
        Returns:
            List[int]: 検出されたコーナーのインデックス
        """
        # G-Forceに基づくコーナー検出
        g_force_lateral = np.abs(self.reference_df['Gf. Y'] / 9.8)
        
        # ピーク検出
        peaks, _ = find_peaks(
            g_force_lateral, 
            height=g_force_threshold, 
            distance=min_distance
        )
        
        # コーナーの最大数を制限
        if max_corners is not None and len(peaks) > max_corners:
            # G-Forceの大きさでソートし、上位のコーナーを選択
            sorted_indices = np.argsort(g_force_lateral[peaks])[::-1]
            peaks = peaks[sorted_indices[:max_corners]]
        
        return peaks
    
    def classify_lap(self, lap_path: str, 
                     max_corners: int = None) -> Dict[str, Any]:
        """
        新しいラップデータのコーナー分類
        
        Args:
            lap_path (str): 分類するラップのCSVファイルパス
            max_corners (int, optional): 検出するコーナーの最大数
        
        Returns:
            Dict[str, Any]: コーナー分類結果
        """
        # 新しいラップデータの読み込み
        lap_df = pd.read_csv(lap_path, sep=',', encoding='utf-8')
        lap_df.columns = [col.strip() for col in lap_df.columns]
        
        # 新しいラップのコーナー検出
        g_force_lateral = np.abs(lap_df['Gf. Y'] / 9.8)
        peaks, _ = find_peaks(
            g_force_lateral, 
            height=0.2, 
            distance=10
        )
        
        # コーナーの最大数を制限
        if max_corners is not None and len(peaks) > max_corners:
            sorted_indices = np.argsort(g_force_lateral[peaks])[::-1]
            peaks = peaks[sorted_indices[:max_corners]]
        
        # 参照と新しいラップのコーナー特徴量計算
        ref_corner_features = self._calculate_corner_features(self.reference_df, self.reference_corners)
        new_corner_features = self._calculate_corner_features(lap_df, peaks)
        
        # 特徴量に基づくマッチング
        feature_distances = cdist(ref_corner_features, new_corner_features)
        
        # コーナーマッピング
        corner_mapping = []
        used_new_corners = set()
        
        for i, ref_corner_idx in enumerate(self.reference_corners):
            # 最も近い特徴量を持つコーナーを見つける
            best_match = np.argmin(feature_distances[i, :])
            
            if best_match not in used_new_corners:
                corner_mapping.append({
                    'reference_corner_index': ref_corner_idx,
                    'new_lap_corner_index': peaks[best_match],
                    'feature_distance': feature_distances[i, best_match]
                })
                used_new_corners.add(best_match)
        
        return {
            'corner_mapping': corner_mapping,
            'total_corners_ref': len(self.reference_corners),
            'total_corners_new': len(peaks)
        }
    
    def visualize_corner_mapping(self, classification_result: Dict[str, Any], 
                                 reference_lap_path: str, 
                                 other_lap_path: str):
        """
        コーナーマッピングの可視化
        
        Args:
            classification_result (Dict[str, Any]): コーナー分類結果
            reference_lap_path (str): 基準ラップのCSVパス
            other_lap_path (str): 比較するラップのCSVパス
        """
        # データ読み込み
        ref_df = pd.read_csv(reference_lap_path, sep=',', encoding='utf-8')
        other_df = pd.read_csv(other_lap_path, sep=',', encoding='utf-8')
        
        plt.figure(figsize=(12, 8))
        
        # 基準ラップの軌跡
        plt.plot(ref_df['Lon.'], ref_df['Lat.'], '-', color='blue', label='基準ラップ', alpha=0.5)
        
        # 比較ラップの軌跡
        plt.plot(other_df['Lon.'], other_df['Lat.'], '-', color='green', label='比較ラップ', alpha=0.5)
        
        # マッピングの可視化
        for mapping in classification_result['corner_mapping']:
            ref_idx = mapping['reference_corner_index']
            new_corner_idx = mapping['new_lap_corner_index']
            
            plt.plot(
                [ref_df['Lon.'].iloc[ref_idx], other_df['Lon.'].iloc[new_corner_idx]],
                [ref_df['Lat.'].iloc[ref_idx], other_df['Lat.'].iloc[new_corner_idx]],
                'r-', alpha=0.7
            )
            plt.scatter(
                [ref_df['Lon.'].iloc[ref_idx], other_df['Lon.'].iloc[new_corner_idx]],
                [ref_df['Lat.'].iloc[ref_idx], other_df['Lat.'].iloc[new_corner_idx]],
                color=['blue', 'green'], 
                s=100, 
                alpha=0.7
            )
        
        plt.title("コーナーマッピング")
        plt.xlabel("経度")
        plt.ylabel("緯度")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

# 使用例
def main():
    # CSVファイルのパス
    reference_lap_path = r"C:\Users\MasatoOkada\Documents\Python Scripts\Alfano Analysis App\data\test-lap2.csv"
    other_lap_path = r"C:\Users\MasatoOkada\Documents\Python Scripts\Alfano Analysis App\data\test-lap3.csv"
    
    # インスタンス作成
    classifier = RefinedCornerClassifier(reference_lap_path)
    
    # コーナー分類（最大6つのコーナーに制限）
    classification_result = classifier.classify_lap(
        other_lap_path, 
        max_corners=30
    )
    
    # 結果出力
    print("コーナー分類結果:")
    for mapping in classification_result['corner_mapping']:
        print(f"リファレンスコーナー: {mapping['reference_corner_index']}, "
              f"新しいラップコーナー: {mapping['new_lap_corner_index']}, "
              f"特徴量距離: {mapping['feature_distance']:.6f}")
    
    # 可視化
    classifier.visualize_corner_mapping(
        classification_result, 
        reference_lap_path, 
        other_lap_path
    )

if __name__ == '__main__':
    main()