import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import seaborn as sns
from datetime import datetime
import os
import json

# ディレクトリ内のCSVファイルを一覧表示する関数
def list_csv_files(directory):
    csv_files = []
    try:
        for file in os.listdir(directory):
            if file.endswith('.csv'):
                csv_files.append(file)
        return csv_files
    except Exception as e:
        print(f"ディレクトリ読み込みエラー: {e}")
        return []

# CSVファイルの読み込み
def load_telemetry_data(file_path):
    try:
        # セミコロン区切りCSVを読み込む
        print(f"ファイル '{file_path}' を読み込み中...")
        df = pd.read_csv(file_path, sep=';', encoding='utf-8')
        
        # カラム名を確認
        print(f"読み込まれたカラム: {df.columns.tolist()}")
        
        # データサイズを確認
        print(f"データサイズ: {df.shape[0]} 行 x {df.shape[1]} 列")
        
        # カラム名を整理（スペースを削除）
        df.columns = [col.strip() for col in df.columns]
        
        return df
    except Exception as e:
        print(f"ファイル読み込み中にエラーが発生しました: {e}")
        # ファイルのヘッダー部分だけでも読み込んでみる
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                header = f.readline()
                print(f"ファイルヘッダー: {header}")
        except:
            pass
        raise

# データの前処理
def preprocess_data(df):
    # 時間フォーマットの変換（"mm:ss.SSS" → 秒）
    def convert_time_to_seconds(time_str):
        if pd.isna(time_str):
            return np.nan
        # 時間が ":" を含むかチェック
        if ':' in str(time_str):
            parts = str(time_str).split(':')
            # "mm:ss.SSS" 形式の場合
            if len(parts) == 2:
                minutes = float(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
        # 既に数値の場合はそのまま返す
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

# ラップごとのデータをグループ化
def group_laps(df):
    laps = {}
    if 'Lap' in df.columns:
        lap_groups = df.groupby('Lap')
        for lap_num, lap_data in lap_groups:
            if lap_num > 0:  # ラップ0は除外（アウトラップなど）
                laps[lap_num] = lap_data.reset_index(drop=True)
    return laps

# ラップタイムを取得して分類
def classify_laps(laps_dict):
    lap_times = {}
    for lap_num, lap_data in laps_dict.items():
        # ラップタイムを取得（各ラップの最後のTime Lap値）
        if 'Time Lap (sec)' in lap_data.columns and not lap_data['Time Lap (sec)'].empty:
            last_valid_time = lap_data['Time Lap (sec)'].dropna().iloc[-1] if not lap_data['Time Lap (sec)'].dropna().empty else np.nan
            if not np.isnan(last_valid_time):
                lap_times[lap_num] = last_valid_time
    
    if not lap_times:
        return {}, np.nan, {}
    
    # ベストラップタイム
    best_lap_time = min(lap_times.values())
    best_lap = [lap for lap, time in lap_times.items() if time == best_lap_time][0]
    
    # ラップ分類（条件に基づいて）
    lap_categories = {}
    for lap, time in lap_times.items():
        time_diff = time - best_lap_time
        if 0 <= time_diff < 0.1:
            category = 'success'  # 成功ラップ: ベスト+0.0〜0.1秒
        elif 0.1 <= time_diff < 0.3:
            category = 'average'  # アベレージラップ: ベスト+0.1〜0.3秒
        else:
            category = 'miss'     # ミスラップ: ベスト+0.3秒以上
        lap_categories[lap] = {
            'time': time,
            'diff_from_best': time_diff,
            'category': category
        }
    
    return lap_times, best_lap_time, lap_categories

# コーナー検出（G-Force Yに基づく）
def detect_corners(lap_data):
    corners = []
    in_corner = False
    corner_start_idx = None
    threshold = 0.1  # コーナー検出の閾値
    consecutive_points = 2  # 連続するポイント数の閾値
    
    if 'Gf. Y' not in lap_data.columns:
        return []
    
    # 連続したポイントでG-Force Yの閾値を確認
    for i in range(len(lap_data) - consecutive_points + 1):
        g_forces = lap_data['Gf. Y'].iloc[i:i+consecutive_points].abs()
        
        if not in_corner and all(g_forces > threshold):
            # コーナー開始を検出
            in_corner = True
            corner_start_idx = i
        elif in_corner and all(g_forces <= threshold):
            # コーナー終了を検出
            in_corner = False
            if corner_start_idx is not None:
                corner_type = 'right' if lap_data['Gf. Y'].iloc[corner_start_idx:i].mean() > 0 else 'left'
                corners.append({
                    'start_idx': corner_start_idx,
                    'end_idx': i - 1,
                    'type': corner_type,
                    'data': lap_data.iloc[corner_start_idx:i]
                })
    
    # 最後のコーナーが検出中だった場合
    if in_corner and corner_start_idx is not None:
        corner_type = 'right' if lap_data['Gf. Y'].iloc[corner_start_idx:].mean() > 0 else 'left'
        corners.append({
            'start_idx': corner_start_idx,
            'end_idx': len(lap_data) - 1,
            'type': corner_type,
            'data': lap_data.iloc[corner_start_idx:]
        })
    
    return corners

# ブレーキング・アクセル操作の検出
def detect_operations(lap_data):
    operations = {
        'braking': [],
        'strong_accel': [],
        'partial_accel': []
    }
    
    if 'Gf. X' not in lap_data.columns or 'RPM' not in lap_data.columns:
        return operations
    
    # ブレーキング検出: G-Force X < -0.25 が連続2点以上
    in_braking = False
    braking_start_idx = None
    
    for i in range(len(lap_data) - 1):
        if not in_braking and lap_data['Gf. X'].iloc[i] < -0.2 and lap_data['Gf. X'].iloc[i+1] < -0.2:
            in_braking = True
            braking_start_idx = i
        elif in_braking and lap_data['Gf. X'].iloc[i] >= -0.2:
            in_braking = False
            if braking_start_idx is not None:
                operations['braking'].append({
                    'start_idx': braking_start_idx,
                    'end_idx': i - 1,
                    'data': lap_data.iloc[braking_start_idx:i]
                })
    
    # 最後のブレーキングが検出中だった場合
    if in_braking and braking_start_idx is not None:
        operations['braking'].append({
            'start_idx': braking_start_idx,
            'end_idx': len(lap_data) - 1,
            'data': lap_data.iloc[braking_start_idx:]
        })
    
    # 強アクセル検出: G-Force X > 0.2 かつ RPM上昇率 > 0
    for i in range(len(lap_data) - 1):
        if lap_data['Gf. X'].iloc[i] > 0.15 and lap_data['RPM'].iloc[i+1] > lap_data['RPM'].iloc[i]:
            operations['strong_accel'].append({
                'idx': i,
                'data': lap_data.iloc[i:i+2]
            })
    
    # 部分アクセル検出: 0.05 < G-Force X < 0.2 かつ RPM維持または微増
    for i in range(len(lap_data) - 1):
        if 0.03 < lap_data['Gf. X'].iloc[i] < 0.15 and lap_data['RPM'].iloc[i+1] >= lap_data['RPM'].iloc[i]:
            operations['partial_accel'].append({
                'idx': i,
                'data': lap_data.iloc[i:i+2]
            })
    
    return operations

# メイン処理関数
def analyze_driving_characteristics(file_path):
    print("ファイル読み込み中...")
    df = load_telemetry_data(file_path)
    
    print("データ前処理中...")
    df = preprocess_data(df)
    
    print("ラップデータ処理中...")
    laps = group_laps(df)
    
    print("ラップ分類中...")
    lap_times, best_lap_time, lap_categories = classify_laps(laps)
    
    results = {
        'dataframe': df,
        'laps': laps,
        'lap_times': lap_times,
        'best_lap_time': best_lap_time,
        'lap_categories': lap_categories,
        'corners': {},
        'operations': {}
    }
    
    print("各ラップの特性分析中...")
    for lap_num, lap_data in laps.items():
        print(f"ラップ {lap_num} の分析中...")
        results['corners'][lap_num] = detect_corners(lap_data)
        results['operations'][lap_num] = detect_operations(lap_data)
    
    return results


# 分析結果をJSONとして保存
def save_results_to_json(results, output_path):
    try:
        export_data = {
            "dataframe": results['dataframe'].to_dict(orient='records'),
            "laps": {
                lap_num: df.to_dict(orient='records')
                for lap_num, df in results['laps'].items()
            },
            "lap_times": results.get("lap_times", {}),
            "best_lap_time": results.get("best_lap_time"),
            "lap_categories": results.get("lap_categories", {}),
            "corners": {
                lap: [
                    {
                        "start_idx": c["start_idx"],
                        "end_idx": c["end_idx"],
                        "type": c["type"],
                        "data": c["data"].to_dict(orient='records')
                    } for c in corners
                ] for lap, corners in results.get("corners", {}).items()
            },
            "operations": {
                lap: {
                    "braking": [
                        {
                            "start_idx": op["start_idx"],
                            "end_idx": op["end_idx"],
                            "data": op["data"].to_dict(orient='records')
                        } for op in ops["braking"]
                    ],
                    "strong_accel": [
                        {
                            "idx": op["idx"],
                            "data": op["data"].to_dict(orient='records')
                        } for op in ops["strong_accel"]
                    ],
                    "partial_accel": [
                        {
                            "idx": op["idx"],
                            "data": op["data"].to_dict(orient='records')
                        } for op in ops["partial_accel"]
                    ]
                } for lap, ops in results.get("operations", {}).items()
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ JSON形式で保存されました: {output_path}")

    except Exception as e:
        print(f"❌ JSON保存中にエラーが発生しました: {e}")


# 分析レポートをファイルに保存
def save_analysis_report(results, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=== カートレーシングテレメトリー分析レポート ===\n\n")
        f.write(f"分析日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"総ラップ数: {len(results['laps'])}\n")
        f.write(f"ベストラップタイム: {results['best_lap_time']:.3f}秒\n\n")
        
        # カテゴリ別のラップ数
        categories = {'success': 0, 'average': 0, 'miss': 0}
        for lap, info in results['lap_categories'].items():
            categories[info['category']] += 1
        
        f.write(f"成功ラップ数: {categories['success']}\n")
        f.write(f"アベレージラップ数: {categories['average']}\n")
        f.write(f"ミスラップ数: {categories['miss']}\n\n")
        
        # ラップごとの詳細情報
        f.write("=== ラップ詳細 ===\n")
        for lap, info in sorted(results['lap_categories'].items()):
            f.write(f"ラップ {lap}: {info['time']:.3f}秒 ({info['category']}), "
                   f"ベストとの差: +{info['diff_from_best']:.3f}秒\n")
    
    print(f"分析レポートが保存されました: {output_file}")

# メイン実行部分
if __name__ == "__main__":
    # ディレクトリパスを指定
    directory_path = r"C:\Users\MasatoOkada\Documents\Python Scripts\Alfano Analysis App\data"
    
    # ディレクトリ内のCSVファイルを一覧
    csv_files = list_csv_files(directory_path)
    
    if not csv_files:
        print(f"指定ディレクトリ '{directory_path}' にCSVファイルがありません。")
        exit()
    
    # 利用可能なCSVファイルを表示
    print("利用可能なCSVファイル:")
    for i, file in enumerate(csv_files):
        print(f"{i+1}. {file}")
    
    # ファイル選択（インタラクティブモードの場合）
    try:
        file_index = int(input("\n分析するファイルの番号を入力してください: ")) - 1
        if 0 <= file_index < len(csv_files):
            selected_file = csv_files[file_index]
        else:
            print("無効な番号です。最初のファイルを使用します。")
            selected_file = csv_files[0]
    except:
        print("入力エラーです。最初のファイルを使用します。")
        selected_file = csv_files[0]
    
    file_path = os.path.join(directory_path, selected_file)
    print(f"選択されたファイル: {file_path}")
    
    try:
        # データ分析を実行
        results = analyze_driving_characteristics(file_path)
        
        # 分析結果のサマリー表示
        print("\n=== 分析結果サマリー ===")
        print(f"総ラップ数: {len(results['laps'])}")
        print(f"ベストラップタイム: {results['best_lap_time']:.3f}秒")
        
        # カテゴリ別のラップ数
        categories = {'success': 0, 'average': 0, 'miss': 0}
        for lap, info in results['lap_categories'].items():
            categories[info['category']] += 1
        
        print(f"成功ラップ数: {categories['success']}")
        print(f"アベレージラップ数: {categories['average']}")
        print(f"ミスラップ数: {categories['miss']}")
        
        # 各カテゴリから代表的なラップを選択
        selected_laps = []
        for category in ['success', 'average', 'miss']:
            category_laps = [lap for lap, info in results['lap_categories'].items() 
                             if info['category'] == category]
            if category_laps:
                selected_laps.append(category_laps[0])
        
        # JSONファイルとして保存
        json_output_path = os.path.join(
            os.path.dirname(file_path), 
            f"analysis_data_{os.path.basename(file_path).split('.')[0]}.json"
        )
        save_results_to_json(results, json_output_path)

        
        # 分析レポートを保存
        output_file = os.path.join(os.path.dirname(file_path), f"analysis_report_{os.path.basename(file_path).split('.')[0]}.txt")
        save_analysis_report(results, output_file)
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()  # 詳細なエラー情報を表示