import pandas as pd
import json
import os
from pathlib import Path

def csv_to_json(csv_file_path, json_file_path=None, orient='records', indent=2):
    """
    CSVファイルをJSONファイルに変換する
    
    Args:
        csv_file_path: 入力CSVファイルのパス
        json_file_path: 出力JSONファイルのパス。Noneの場合は.csvを.jsonに置き換える
        orient: pandas.DataFrame.to_jsonのorientパラメータ
               'records': レコードのリスト [{col1:val1, col2:val2}, ...]
               'split': {index: [index], columns: [columns], data: [values]}
               'index': {index1: {col1:val1, col2:val2}, ...}
               'columns': {col1: {index1:val1, index2:val2}, ...}
               'values': 値のみの二次元配列
               'table': {schema: {fields: [...]}, data: [...]}
        indent: インデントのスペース数。None の場合は改行なし
    
    Returns:
        json_file_path: 出力JSONファイルのパス
    """
    # 出力ファイルパスが指定されていない場合、デフォルトのパスを設定
    if json_file_path is None:
        json_file_path = str(Path(csv_file_path).with_suffix('.json'))
    
    # CSVファイルを読み込む
    print(f"CSVファイルを読み込んでいます: {csv_file_path}")
    df = pd.read_csv(csv_file_path)
    
    # 数値型の列を適切に変換
    for col in df.columns:
        # 整数のように見える浮動小数点数を整数に変換
        if df[col].dtype == 'float64':
            # 全ての非NAの値が整数値かどうかチェック
            if (df[col].dropna() == df[col].dropna().astype(int)).all():
                df[col] = df[col].fillna(-99999).astype(int).replace(-99999, None)
    
    # DataFrameをJSON形式に変換
    print(f"DataFrameをJSON形式に変換しています...")
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json_str = df.to_json(orient=orient, force_ascii=False, indent=indent)
        f.write(json_str)
    
    print(f"JSONファイルを保存しました: {json_file_path}")
    print(f"  - レコード数: {len(df)}")
    print(f"  - カラム数: {len(df.columns)}")
    
    return json_file_path

if __name__ == "__main__":
    # 入力CSVファイルパス
    csv_file_path = r"C:\Users\MasatoOkada\Documents\Python Scripts\Alfano Analysis App\python\merged_data\dashware_data_with_sector_column.csv"
    
    # 出力JSONファイルパス
    json_file_path = r"C:\Users\MasatoOkada\Documents\Python Scripts\Alfano Analysis App\nextjs-app\public\all_sessions_combined.json"
    
    # 変換実行
    csv_to_json(csv_file_path, json_file_path)
    
    # JSONファイルのサイズを表示
    file_size_bytes = os.path.getsize(json_file_path)
    file_size_mb = file_size_bytes / (1024 * 1024)
    print(f"JSONファイルのサイズ: {file_size_mb:.2f} MB")