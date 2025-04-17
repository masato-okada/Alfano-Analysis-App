import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import json
import os

# Alfanoデータ解析処理
def analyze_alfano_data(file_path):
    # データ読み込み（セミコロン区切り）
    df = pd.read_csv(file_path, sep=';')

    # ID列を先頭に追加
    df.insert(0, 'id', range(1, len(df) + 1))

    print("データ形状:", df.shape)
    print("\nデータ型情報:")
    print(df.info())
    print("\n基本統計量:")
    print(df.describe())

    print("\n欠損値の数:")
    print(df.isnull().sum())

    # 数値データのみ抽出
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

    # 欠損値を0で補完
    df_filled = df[numeric_columns].fillna(0)

    # 相関ヒートマップ作成
    if len(numeric_columns) > 1:
        correlation = df[numeric_columns].corr()
        plt.figure(figsize=(10, 8))
        sns.heatmap(correlation, annot=True, cmap='coolwarm', fmt=".2f")
        plt.title('相関ヒートマップ')
        plt.savefig('correlation_heatmap.png')
        print("\n相関ヒートマップを保存しました")

    # クラスタリング
    if len(numeric_columns) >= 2:
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(df_filled)

        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(scaled_data)

        kmeans = KMeans(n_clusters=3, random_state=42)
        cluster_labels = kmeans.fit_predict(scaled_data)

        plt.figure(figsize=(10, 8))
        scatter = plt.scatter(pca_result[:, 0], pca_result[:, 1], c=cluster_labels, cmap='viridis')
        plt.colorbar(scatter)
        plt.title('Alfanoデータのクラスタリング結果')
        plt.xlabel('PCA 第1主成分')
        plt.ylabel('PCA 第2主成分')
        plt.savefig('clustering_result.png')
        print("\nクラスタリング結果を保存しました")

        df['cluster'] = cluster_labels

    # JSON出力データ作成
    result = {
        'summary': {
            'rows': df.shape[0],
            'columns': df.shape[1],
            'missing_values': int(df.isnull().sum().sum())
        },
        'columns': df.columns.tolist(),
        'data_sample': df.head(5).to_dict('records')
    }

    if len(numeric_columns) >= 2:
        cluster_means = df.groupby('cluster')[numeric_columns].mean().T.to_dict()
        cluster_sizes = df['cluster'].value_counts().sort_index().to_dict()

        result['clusters'] = {
            'count': len(cluster_sizes),
            'sizes': cluster_sizes,
            'cluster_means': cluster_means
        }

    return result

# numpy型変換対応
def convert(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)

# メイン処理
if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(base_dir, 'data', 'alfano_data.csv')
    output_path = os.path.join(base_dir, 'python', 'analysis_results.json')

    results = analyze_alfano_data(file_path)

    # NaN → 0 に変換（再帰的に処理）
    def replace_nan_with_zero(obj):
        if isinstance(obj, dict):
            return {k: replace_nan_with_zero(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_nan_with_zero(v) for v in obj]
        elif isinstance(obj, float) and np.isnan(v := obj):
            return 0
        return obj

    results = replace_nan_with_zero(results)

    # JSON出力（NaN禁止で安全）
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=convert, allow_nan=False)

    print("\n分析結果を python/analysis_results.json に保存しました")
