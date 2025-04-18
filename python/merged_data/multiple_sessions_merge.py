import pandas as pd
import os
import re
from pathlib import Path
import glob

def extract_session_info(filename):
    """
    ファイル名から、SN番号、日付、時刻を抽出する
    
    Args:
        filename: ファイル名
    
    Returns:
        (sn, date, time) の形式のタプル、または None（パターンに一致しない場合）
    """
    basename = os.path.basename(filename)
    parts = basename.split('_')
    
    # dashware形式のファイル名の場合（例: dashware_SN13239_120425_15H18_...）
    if len(parts) >= 4 and parts[0].lower() == 'dashware' and parts[1].startswith('SN'):
        return (parts[1], parts[2], parts[3])
    
    # lapdata形式のファイル名の場合（例: LAP_1_ALFANO6_LAP_SN13239_120425_13H49_...）
    if len(parts) >= 7 and parts[0].startswith('LAP') and parts[4].startswith('SN'):
        return (parts[4], parts[5], parts[6])
    
    return None

def get_lap_number(filename):
    """
    ファイル名からLap番号を抽出する
    
    Args:
        filename: ファイル名
    
    Returns:
        Lap番号（整数）、または None（パターンに一致しない場合）
    """
    match = re.search(r"LAP_(\d+)_", filename)
    if match:
        return int(match.group(1))
    return None

def load_and_format_dashware_csv(file_path):
    # 2行目: ヘッダー, 3行目: 単位
    df = pd.read_csv(file_path, header=[1, 2])

    # 列名整形（重複防止）
    def format_column(name, unit):
        name = name.strip()
        if pd.isna(unit) or unit.strip() == "":
            return name
        unit = unit.strip()
        if unit.startswith("[") and unit.endswith("]"):
            return f"{name} {unit}"
        else:
            return f"{name} [{unit}]"

    df.columns = [format_column(col[0], col[1]) for col in df.columns]

    # A〜D列の空白補完
    for col in df.columns[:4]:
        df[col] = df[col].ffill()

    return df

def process_single_session(dashware_path, lap_files, session_name=None):
    """
    単一セッションのdashwareファイルとLAPファイルを処理する
    
    Args:
        dashware_path: dashwareファイルのパス
        lap_files: 対応するLAPファイルのパスのリスト
        session_name: セッション名（オプション）
    
    Returns:
        結合されたデータフレーム
    """
    print(f"処理中: {os.path.basename(dashware_path)} と {len(lap_files)}個のLAPファイル")
    
    # セッション情報がない場合、ファイル名から抽出
    if not session_name:
        dashware_info = extract_session_info(dashware_path)
        if dashware_info:
            dash_sn, dash_date, dash_time = dashware_info
            session_name = f"{dash_sn}_{dash_date}_{dash_time}"
        else:
            session_name = os.path.splitext(os.path.basename(dashware_path))[0]
    
    # Dashwareデータ読み込み
    dashware_df = load_and_format_dashware_csv(dashware_path)
    
    # LAPファイルをLap番号順に並べ替え
    lap_entries = []
    for filepath in lap_files:
        lap_num = get_lap_number(os.path.basename(filepath))
        if lap_num is not None:
            lap_entries.append((lap_num, filepath))
    
    lap_entries.sort(key=lambda x: x[0])
    
    if not lap_entries:
        print(f"警告: 有効なLAPファイルが見つかりませんでした: {session_name}")
        return None
    
    final_df_list = []
    
    for lap_num, filepath in lap_entries:
        # dashwareからラップ番号に対応する行を抽出
        dash_segment = dashware_df[dashware_df.iloc[:, 0] == lap_num].copy().reset_index(drop=True)
        
        if dash_segment.empty:
            print(f"警告: ラップ番号 {lap_num} に対応するdashwareデータがありません")
            continue
        
        # Lap列を明示的に挿入
        dash_segment.insert(0, "Lap", lap_num)
        
        # セッション名列を追加
        dash_segment.insert(0, "Session", session_name)
        
        # LAPファイル読み込み
        try:
            lap_segment = pd.read_csv(filepath).reset_index(drop=True)
            merged = pd.concat([dash_segment, lap_segment], axis=1)
            final_df_list.append(merged)
        except Exception as e:
            print(f"エラー: LAPファイル {os.path.basename(filepath)} の読み込みに失敗しました: {e}")
    
    if final_df_list:
        final_df = pd.concat(final_df_list, ignore_index=True)
        return final_df
    else:
        return None

def find_matching_data_in_folder(base_folder):
    """
    フォルダ内のすべてのdashwareファイルとLAPファイルを検索し、
    SN番号、日付、時刻でグループ化する
    
    Args:
        base_folder: 検索するベースフォルダ
    
    Returns:
        {(sn, date, time): (dashware_path, [lap_files])} の形式の辞書
    """
    session_data = {}
    dashware_files = []
    lap_files = []
    
    # すべてのCSVファイルを検索
    for root, _, files in os.walk(base_folder):
        for file in files:
            if file.endswith('.csv'):
                full_path = os.path.join(root, file)
                if file.lower().startswith('dashware'):
                    dashware_files.append(full_path)
                elif file.lower().startswith('lap_'):
                    lap_files.append(full_path)
    
    print(f"検出されたファイル: dashware {len(dashware_files)}個, LAP {len(lap_files)}個")
    
    # dashwareファイルごとに情報を抽出
    for dashware_path in dashware_files:
        dash_info = extract_session_info(dashware_path)
        if dash_info:
            session_data[dash_info] = (dashware_path, [])
    
    # LAPファイルをセッションに関連付け
    for lap_path in lap_files:
        lap_info = extract_session_info(lap_path)
        if lap_info and lap_info in session_data:
            # 対応するセッションが見つかった場合、LAPファイルを追加
            session_data[lap_info][1].append(lap_path)
    
    # LAPファイルがないセッションを除外
    session_data = {k: v for k, v in session_data.items() if v[1]}
    
    print(f"有効なセッション数: {len(session_data)}")
    for key, (dashware, laps) in session_data.items():
        print(f"  - セッション {key}: dashware 1個, LAP {len(laps)}個")
    
    return session_data

def process_all_sessions(base_folder):
    """
    ベースフォルダ内のすべてのセッションを処理し、単一のデータフレームに結合する
    
    Args:
        base_folder: 検索するベースフォルダ
    
    Returns:
        結合されたデータフレーム
    """
    # 対応するdashwareとLAPファイルを検索
    session_data = find_matching_data_in_folder(base_folder)
    
    if not session_data:
        print("一致するデータペアが見つかりませんでした。")
        return None
    
    all_sessions_df_list = []
    
    # 各セッションを処理
    for (sn, date, time), (dashware_path, lap_files) in session_data.items():
        session_name = f"{sn}_{date}_{time}"
        
        # 単一セッションの処理
        df_combined = process_single_session(dashware_path, lap_files, session_name)
        
        if df_combined is not None:
            # A列（Lap列）の空白行を削除
            lap_col = df_combined.columns[1] if "Session" in df_combined.columns else df_combined.columns[0]
            df_combined = df_combined[df_combined[lap_col].notna()]
            df_combined = df_combined[df_combined[lap_col].astype(str).str.strip() != ""]
            
            all_sessions_df_list.append(df_combined)
        else:
            print(f"警告: セッション {session_name} にデータがありません")
    
    if all_sessions_df_list:
        # 全セッションを結合
        final_df = pd.concat(all_sessions_df_list, ignore_index=True)
        return final_df
    else:
        return None

# メイン処理
if __name__ == "__main__":
    # 対象となるベースフォルダを指定
    base_folder = r"C:\Users\MasatoOkada\Documents\Python Scripts\Alfano Analysis App\python\raw_data"
    
    # 出力先フォルダを指定
    output_folder = r"C:\Users\MasatoOkada\Documents\Python Scripts\Alfano Analysis App\python\merged_data"
    
    # 出力フォルダが存在しない場合は作成
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"出力フォルダを作成しました: {output_folder}")
    
    print(f"ベースフォルダ: {base_folder}")
    print(f"出力フォルダ: {output_folder}")
    
    # 全セッションの処理
    combined_df = process_all_sessions(base_folder)
    
    if combined_df is not None:
        # 出力ファイルパスを指定
        output_filename = "all_sessions_combined.csv"
        output_path = os.path.join(output_folder, output_filename)
        
        # 保存
        combined_df.to_csv(output_path, index=False)
        print(f"✅ 全セッションの結合処理が完了しました：{output_path}")
        print(f"  - 合計行数: {len(combined_df)}")
        print(f"  - セッション数: {combined_df['Session'].nunique()}")
    else:
        print("❌ 処理するデータがありませんでした")