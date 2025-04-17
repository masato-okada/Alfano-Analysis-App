import pandas as pd
import os
import re

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

def merge_lap_segments_preserving_order(dashware_df, lapdata_folder):
    lap_entries = []

    for filename in os.listdir(lapdata_folder):
        if filename.endswith(".csv"):
            match = re.search(r"LAP_(\d+)", filename)
            if match:
                lap_num = int(match.group(1))
                filepath = os.path.join(lapdata_folder, filename)
                lap_entries.append((lap_num, filepath))

    lap_entries.sort(key=lambda x: x[0])  # Lap番号順に並べ替え

    final_df_list = []

    for lap_num, filepath in lap_entries:
        dash_segment = dashware_df[dashware_df.iloc[:, 0] == lap_num].copy().reset_index(drop=True)

        # Lap列を明示的に挿入
        dash_segment.insert(0, "Lap", lap_num)

        lap_segment = pd.read_csv(filepath).reset_index(drop=True)
        merged = pd.concat([dash_segment, lap_segment], axis=1)
        final_df_list.append(merged)

    final_df = pd.concat(final_df_list, ignore_index=True)
    return final_df


# 🔧 使用パスの指定
dashware_path = r"C:\Users\MasatoOkada\Documents\Python Scripts\Alfano Analysis App\python\test2\dashware_SN13239_120425_13H49_AKIRA 1__P__MOBARA__01_08_24_12_3351.csv"
lap_folder = r"C:\Users\MasatoOkada\Documents\Python Scripts\Alfano Analysis App\python\test2\Lapdata"

# Dashware整形処理（保存せずそのまま利用）
dashware_df = load_and_format_dashware_csv(dashware_path)

# Lap別ファイルとの結合処理
df_combined = merge_lap_segments_preserving_order(dashware_df, lap_folder)

# A列（Lap列）の空白行を削除
lap_col = df_combined.columns[0]
df_combined = df_combined[df_combined[lap_col].notna()]
df_combined = df_combined[df_combined[lap_col].astype(str).str.strip() != ""]

# 保存
output_path = os.path.join(os.path.dirname(lap_folder), "dashware_lap_combined_filled.csv")
df_combined.to_csv(output_path, index=False)

print(f"✅ Lapごとの結合とA列補正を含めた処理が完了しました：{output_path}")
