import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

def compare_success_vs_average(results_file, data_dir, output_dir=None):
    """
    成功ラップ(ラップ5)とアベレージラップの比較分析を行う関数（数値処理のみ）
    
    Parameters:
    -----------
    results_file : str
        分析結果レポートファイルのパス
    data_dir : str
        元データファイルが格納されているディレクトリパス
    output_dir : str, optional
        出力ファイルを保存するディレクトリパス。指定がなければdata_dirと同じ
        
    Returns:
    --------
    dict
        比較分析結果を含む辞書
    """
    if output_dir is None:
        output_dir = data_dir
    
    # 結果ファイルから分類情報を読み込む
    lap_categories = parse_analysis_report(results_file)
    
    # 成功ラップとアベレージラップを特定
    success_laps = [lap for lap, info in lap_categories.items() if info['category'] == 'success']
    average_laps = [lap for lap, info in lap_categories.items() if info['category'] == 'average']
    
    if not success_laps:
        print("成功ラップが見つかりません。")
        return None
    
    if not average_laps:
        print("アベレージラップが見つかりません。")
        return None
    
    # データファイルを特定し読み込む
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    if not csv_files:
        print(f"指定ディレクトリ '{data_dir}' にCSVファイルがありません。")
        return None
    
    # 最初のCSVファイルを使用
    data_file = os.path.join(data_dir, csv_files[0])
    df = load_telemetry_data(data_file)
    df = preprocess_data(df)
    
    # ラップごとのデータをグループ化
    laps = group_laps(df)
    
    # 成功ラップを取得（ラップ5を優先）
    success_lap = 5 if 5 in success_laps else success_laps[0]
    
    # アベレージラップのうち最速のものを選択
    best_average_lap = min(average_laps, key=lambda lap: lap_categories[lap]['time'])
    
    # 比較分析を実行
    comparison_results = process_lap_comparison(
        laps[success_lap], laps[best_average_lap], 
        success_lap, best_average_lap, 
        lap_categories[success_lap]['time'], 
        lap_categories[best_average_lap]['time']
    )
    
    # 有意な差分ポイントの詳細分析
    comparison_results['difference_analysis'] = analyze_difference_points(comparison_results)
    
    # RPM帯域別のパフォーマンス比較
    comparison_results['rpm_band_analysis'] = analyze_rpm_bands(
        laps[success_lap], laps[best_average_lap], success_lap, best_average_lap
    )
    
    # 結果をJSONファイルとして保存
    output_file = os.path.join(output_dir, f"lap_comparison_data_lap{success_lap}_vs_{best_average_lap}.json")
    save_results_to_json(comparison_results, output_file)
    
    print(f"成功ラップ(ラップ{success_lap})とアベレージラップ(ラップ{best_average_lap})の比較分析が完了しました。")
    print(f"結果は '{output_file}' に保存されました。")
    
    return comparison_results


def parse_analysis_report(file_path):
    """分析レポートファイルからラップ分類情報を抽出する関数"""
    lap_categories = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # ラップ詳細セクションを探す
        lap_detail_section = False
        for line in lines:
            if "=== ラップ詳細 ===" in line:
                lap_detail_section = True
                continue
            
            if lap_detail_section and line.strip():
                # ラップ情報を解析: "ラップ 5: 33.510秒 (success), ベストとの差: +0.000秒"
                if line.startswith("ラップ"):
                    parts = line.strip().split(", ")
                    first_part = parts[0].split(": ")
                    lap_num = int(first_part[0].replace("ラップ ", ""))
                    lap_time = float(first_part[1].replace("秒", ""))
                    
                    # カテゴリ抽出 (success, average, miss)
                    category_part = parts[0].split("(")[1].split(")")[0]
                    
                    # ベストラップとの差分
                    diff_part = parts[1].split(": ")[1]
                    diff_time = float(diff_part.replace("+", "").replace("秒", ""))
                    
                    lap_categories[lap_num] = {
                        'time': lap_time,
                        'category': category_part,
                        'diff_from_best': diff_time
                    }
        
        return lap_categories
    
    except Exception as e:
        print(f"分析レポートの解析中にエラーが発生しました: {e}")
        return {}


def load_telemetry_data(file_path):
    """CSVファイルを読み込む関数"""
    try:
        print(f"ファイル '{file_path}' を読み込み中...")
        df = pd.read_csv(file_path, sep=';', encoding='utf-8')
        print(f"データサイズ: {df.shape[0]} 行 x {df.shape[1]} 列")
        df.columns = [col.strip() for col in df.columns]
        return df
    except Exception as e:
        print(f"ファイル読み込み中にエラーが発生しました: {e}")
        raise


def preprocess_data(df):
    """データの前処理を行う関数"""
    # 時間フォーマットの変換（"mm:ss.SSS" → 秒）
    def convert_time_to_seconds(time_str):
        if pd.isna(time_str):
            return np.nan
        if ':' in str(time_str):
            parts = str(time_str).split(':')
            if len(parts) == 2:
                minutes = float(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
        try:
            return float(time_str)
        except:
            return np.nan
    
    # Time Lapカラムを秒単位に変換
    if 'Time Lap' in df.columns:
        df['Time Lap (sec)'] = df['Time Lap'].apply(convert_time_to_seconds)
    
    # 数値データの型変換
    numeric_columns = ['RPM', 'Speed GPS', 'T1', 'T2', 'Gf. X', 'Gf. Y', 'Speed rear']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # ラップ番号を整数に変換
    if 'Lap' in df.columns:
        df['Lap'] = pd.to_numeric(df['Lap'], errors='coerce').fillna(0).astype(int)
    
    return df


def group_laps(df):
    """ラップごとのデータをグループ化する関数"""
    laps = {}
    if 'Lap' in df.columns:
        lap_groups = df.groupby('Lap')
        for lap_num, lap_data in lap_groups:
            if lap_num > 0:  # ラップ0は除外（アウトラップなど）
                laps[lap_num] = lap_data.reset_index(drop=True)
    return laps


def process_lap_comparison(success_data, average_data, success_lap_num, average_lap_num, 
                           success_time, average_time):
    """ラップデータを比較する関数（数値処理のみ）"""
    comparison_results = {
        'success_lap': success_lap_num,
        'average_lap': average_lap_num,
        'success_time': success_time,
        'average_time': average_time,
        'time_difference': average_time - success_time,
        'data_points': min(len(success_data), len(average_data)),
        'speed_diff': [],
        'rpm_diff': [],
        'gforce_x_diff': [],
        'gforce_y_diff': [],
        'significant_points': []
    }
    
    # データ長さの調整（短い方に合わせる）
    min_length = min(len(success_data), len(average_data))
    
    # 各ポイントでの差分を計算
    for i in range(min_length):
        speed_diff = success_data['Speed GPS'].iloc[i] - average_data['Speed GPS'].iloc[i]
        rpm_diff = success_data['RPM'].iloc[i] - average_data['RPM'].iloc[i]
        gfx_diff = success_data['Gf. X'].iloc[i] - average_data['Gf. X'].iloc[i]
        gfy_diff = success_data['Gf. Y'].iloc[i] - average_data['Gf. Y'].iloc[i]
        
        comparison_results['speed_diff'].append(float(speed_diff))
        comparison_results['rpm_diff'].append(float(rpm_diff))
        comparison_results['gforce_x_diff'].append(float(gfx_diff))
        comparison_results['gforce_y_diff'].append(float(gfy_diff))
        
        # 有意な差分ポイントを特定（速度差が3km/h以上、またはG-Force差が0.1G以上）
        if abs(speed_diff) > 3 or abs(gfx_diff) > 0.1 or abs(gfy_diff) > 0.1:
            comparison_results['significant_points'].append({
                'index': i,
                'success_speed': float(success_data['Speed GPS'].iloc[i]),
                'average_speed': float(average_data['Speed GPS'].iloc[i]),
                'speed_diff': float(speed_diff),
                'success_rpm': float(success_data['RPM'].iloc[i]),
                'average_rpm': float(average_data['RPM'].iloc[i]),
                'rpm_diff': float(rpm_diff),
                'success_gfx': float(success_data['Gf. X'].iloc[i]),
                'average_gfx': float(average_data['Gf. X'].iloc[i]),
                'gfx_diff': float(gfx_diff),
                'success_gfy': float(success_data['Gf. Y'].iloc[i]),
                'average_gfy': float(average_data['Gf. Y'].iloc[i]),
                'gfy_diff': float(gfy_diff)
            })
    
    # 基本統計量の追加
    comparison_results['statistics'] = {
        'speed': {
            'mean_diff': float(np.mean(comparison_results['speed_diff'])),
            'std_diff': float(np.std(comparison_results['speed_diff'])),
            'max_diff': float(np.max(comparison_results['speed_diff'])),
            'min_diff': float(np.min(comparison_results['speed_diff'])),
            'success_mean': float(success_data['Speed GPS'].mean()),
            'average_mean': float(average_data['Speed GPS'].mean()),
            'success_max': float(success_data['Speed GPS'].max()),
            'average_max': float(average_data['Speed GPS'].max())
        },
        'rpm': {
            'mean_diff': float(np.mean(comparison_results['rpm_diff'])),
            'std_diff': float(np.std(comparison_results['rpm_diff'])),
            'max_diff': float(np.max(comparison_results['rpm_diff'])),
            'min_diff': float(np.min(comparison_results['rpm_diff'])),
            'success_mean': float(success_data['RPM'].mean()),
            'average_mean': float(average_data['RPM'].mean()),
            'success_max': float(success_data['RPM'].max()),
            'average_max': float(average_data['RPM'].max())
        },
        'gforce_x': {
            'mean_diff': float(np.mean(comparison_results['gforce_x_diff'])),
            'std_diff': float(np.std(comparison_results['gforce_x_diff'])),
            'max_diff': float(np.max(comparison_results['gforce_x_diff'])),
            'min_diff': float(np.min(comparison_results['gforce_x_diff'])),
            'success_mean': float(success_data['Gf. X'].mean()),
            'average_mean': float(average_data['Gf. X'].mean()),
            'success_max': float(success_data['Gf. X'].max()),
            'average_max': float(average_data['Gf. X'].max())
        },
        'gforce_y': {
            'mean_diff': float(np.mean(comparison_results['gforce_y_diff'])),
            'std_diff': float(np.std(comparison_results['gforce_y_diff'])),
            'max_diff': float(np.max(comparison_results['gforce_y_diff'])),
            'min_diff': float(np.min(comparison_results['gforce_y_diff'])),
            'success_mean': float(success_data['Gf. Y'].abs().mean()),
            'average_mean': float(average_data['Gf. Y'].abs().mean()),
            'success_max': float(success_data['Gf. Y'].abs().max()),
            'average_max': float(average_data['Gf. Y'].abs().max())
        }
    }
    
    # 生のデータポイントは含めない（データ量が多すぎるため）
    # 必要な場合は以下のコメントを解除して設定できます
    """
    comparison_results['raw_data'] = {
        'success': {
            'speed': success_data['Speed GPS'].tolist()[:min_length],
            'rpm': success_data['RPM'].tolist()[:min_length],
            'gforce_x': success_data['Gf. X'].tolist()[:min_length],
            'gforce_y': success_data['Gf. Y'].tolist()[:min_length]
        },
        'average': {
            'speed': average_data['Speed GPS'].tolist()[:min_length],
            'rpm': average_data['RPM'].tolist()[:min_length],
            'gforce_x': average_data['Gf. X'].tolist()[:min_length],
            'gforce_y': average_data['Gf. Y'].tolist()[:min_length]
        }
    }
    """
    
    return comparison_results


def analyze_difference_points(comparison_results):
    """有意な差分ポイントを分析する関数（数値処理のみ）"""
    significant_points = comparison_results['significant_points']
    
    if not significant_points:
        print("有意な差分ポイントが見つかりませんでした。")
        return {"significant_points_count": 0}
    
    # 有意な差分ポイントを速度差順にソート
    sorted_points = sorted(significant_points, key=lambda x: abs(x['speed_diff']), reverse=True)
    
    # 上位10ポイントを抽出
    top_points = sorted_points[:min(10, len(sorted_points))]
    
    # 差分分析の結果
    diff_analysis = {
        "significant_points_count": len(significant_points),
        "top_points": top_points,
        "statistics": {
            "avg_speed_diff": float(np.mean([p['speed_diff'] for p in significant_points])),
            "avg_rpm_diff": float(np.mean([p['rpm_diff'] for p in significant_points])),
            "avg_gfx_diff": float(np.mean([p['gfx_diff'] for p in significant_points])),
            "avg_gfy_diff": float(np.mean([p['gfy_diff'] for p in significant_points])),
            "max_speed_diff_point": sorted_points[0] if sorted_points else None,
            "max_gfx_diff_point": sorted(significant_points, key=lambda x: abs(x['gfx_diff']), reverse=True)[0] if significant_points else None,
            "max_gfy_diff_point": sorted(significant_points, key=lambda x: abs(x['gfy_diff']), reverse=True)[0] if significant_points else None
        },
        "sections_with_differences": identify_sections_with_differences(comparison_results)
    }
    
    return diff_analysis


def identify_sections_with_differences(comparison_results):
    """連続した差分ポイントからセクションを特定する関数"""
    significant_points = comparison_results['significant_points']
    
    if not significant_points:
        return []
    
    # 差分ポイントのインデックスをソート
    point_indices = sorted([p['index'] for p in significant_points])
    
    # 連続したポイントをグループ化してセクションを特定
    sections = []
    current_section = {'start': point_indices[0], 'points': [point_indices[0]]}
    
    for i in range(1, len(point_indices)):
        if point_indices[i] - point_indices[i-1] <= 3:  # 3ポイント以内の間隔なら同じセクション
            current_section['points'].append(point_indices[i])
        else:
            # 現在のセクションを終了し、新しいセクションを開始
            current_section['end'] = current_section['points'][-1]
            current_section['count'] = len(current_section['points'])
            
            # セクション内のデータポイントの平均差分を計算
            section_indices = current_section['points']
            current_section['avg_speed_diff'] = float(np.mean([comparison_results['speed_diff'][i] for i in section_indices]))
            current_section['avg_rpm_diff'] = float(np.mean([comparison_results['rpm_diff'][i] for i in section_indices]))
            current_section['avg_gfx_diff'] = float(np.mean([comparison_results['gforce_x_diff'][i] for i in section_indices]))
            current_section['avg_gfy_diff'] = float(np.mean([comparison_results['gforce_y_diff'][i] for i in section_indices]))
            
            sections.append(current_section)
            current_section = {'start': point_indices[i], 'points': [point_indices[i]]}
    
    # 最後のセクションを追加
    if current_section:
        current_section['end'] = current_section['points'][-1]
        current_section['count'] = len(current_section['points'])
        
        section_indices = current_section['points']
        current_section['avg_speed_diff'] = float(np.mean([comparison_results['speed_diff'][i] for i in section_indices]))
        current_section['avg_rpm_diff'] = float(np.mean([comparison_results['rpm_diff'][i] for i in section_indices]))
        current_section['avg_gfx_diff'] = float(np.mean([comparison_results['gforce_x_diff'][i] for i in section_indices]))
        current_section['avg_gfy_diff'] = float(np.mean([comparison_results['gforce_y_diff'][i] for i in section_indices]))
        
        sections.append(current_section)
    
    # セクションの影響度でソート（ポイント数×平均速度差の絶対値）
    for section in sections:
        section['impact_score'] = section['count'] * abs(section['avg_speed_diff'])
    
    sections.sort(key=lambda x: x['impact_score'], reverse=True)
    
    return sections


def analyze_rpm_bands(success_data, average_data, success_lap_num, average_lap_num):
    """RPM帯域別のパフォーマンス比較分析"""
    # RPM帯域の定義
    rpm_bands = [
        (0, 7000, "低速域"),
        (7001, 10000, "中速域"),
        (10001, float('inf'), "高速域")
    ]
    
    rpm_analysis = {}
    
    for min_rpm, max_rpm, band_name in rpm_bands:
        # 成功ラップの該当RPM帯域データ
        success_band_data = success_data[(success_data['RPM'] >= min_rpm) & (success_data['RPM'] <= max_rpm)]
        # アベレージラップの該当RPM帯域データ
        average_band_data = average_data[(average_data['RPM'] >= min_rpm) & (average_data['RPM'] <= max_rpm)]
        
        band_analysis = {
            'rpm_range': [min_rpm, max_rpm],
            'success': {
                'data_points': len(success_band_data),
                'data_points_ratio': len(success_band_data) / len(success_data) if len(success_data) > 0 else 0,
                'avg_speed': float(success_band_data['Speed GPS'].mean()) if len(success_band_data) > 0 else 0,
                'max_speed': float(success_band_data['Speed GPS'].max()) if len(success_band_data) > 0 else 0,
                'avg_rpm': float(success_band_data['RPM'].mean()) if len(success_band_data) > 0 else 0,
                'speed_rpm_ratio': float(success_band_data['Speed GPS'].mean() / success_band_data['RPM'].mean()) 
                               if len(success_band_data) > 0 and success_band_data['RPM'].mean() > 0 else 0
            },
            'average': {
                'data_points': len(average_band_data),
                'data_points_ratio': len(average_band_data) / len(average_data) if len(average_data) > 0 else 0,
                'avg_speed': float(average_band_data['Speed GPS'].mean()) if len(average_band_data) > 0 else 0,
                'max_speed': float(average_band_data['Speed GPS'].max()) if len(average_band_data) > 0 else 0,
                'avg_rpm': float(average_band_data['RPM'].mean()) if len(average_band_data) > 0 else 0,
                'speed_rpm_ratio': float(average_band_data['Speed GPS'].mean() / average_band_data['RPM'].mean())
                               if len(average_band_data) > 0 and average_band_data['RPM'].mean() > 0 else 0
            }
        }
        
        # 差分の計算
        if len(success_band_data) > 0 and len(average_band_data) > 0:
            band_analysis['differences'] = {
                'data_points_ratio_diff': band_analysis['success']['data_points_ratio'] - band_analysis['average']['data_points_ratio'],
                'avg_speed_diff': band_analysis['success']['avg_speed'] - band_analysis['average']['avg_speed'],
                'max_speed_diff': band_analysis['success']['max_speed'] - band_analysis['average']['max_speed'],
                'avg_rpm_diff': band_analysis['success']['avg_rpm'] - band_analysis['average']['avg_rpm'],
                'speed_rpm_ratio_diff': band_analysis['success']['speed_rpm_ratio'] - band_analysis['average']['speed_rpm_ratio']
            }
        else:
            band_analysis['differences'] = {
                'data_points_ratio_diff': 0,
                'avg_speed_diff': 0,
                'max_speed_diff': 0,
                'avg_rpm_diff': 0,
                'speed_rpm_ratio_diff': 0
            }
        
        rpm_analysis[band_name] = band_analysis
    
    return rpm_analysis


def save_results_to_json(results, output_file):
    """結果をJSONファイルとして保存する関数"""
    # NumPy配列などをリストに変換
    def convert_to_serializable(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(i) for i in obj]
        else:
            return obj
    
    # JSON形式で保存
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(convert_to_serializable(results), f, ensure_ascii=False, indent=2)
        print(f"結果を保存しました: {output_file}")
    except Exception as e:
        print(f"結果の保存中にエラーが発生しました: {e}")


# メイン実行部分
if __name__ == "__main__":
    # ディレクトリパスを指定
    data_dir = r"C:\Users\MasatoOkada\Documents\Python Scripts\Alfano Analysis App\data"
    
    # 分析結果レポートファイルパス
    results_file = os.path.join(data_dir, "analysis_report_alfano_data.txt")
    
    # 出力ディレクトリ
    output_dir = os.path.join(data_dir, "lap_comparison_results")
    
    # 出力ディレクトリが存在しない場合は作成
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 成功ラップとアベレージラップの比較分析を実行
    compare_success_vs_average(results_file, data_dir, output_dir)