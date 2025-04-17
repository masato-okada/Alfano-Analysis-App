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
    # データ読み込み
    df = pd.read_csv(file_path)
    
    print("データ形状:", df.shape)
    print("\nデータ型情報:")
    print(df.info())
    print("\n基本統計量:")
    print(df.describe())
    
    print("\n欠損値の数:")
    print(df.isnull().sum())

    # 数値データのみ抽出
    numeric_columns = df.select_dtypes(include=[np.number]).columns

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
        scaled_data = scaler.fit_transform(df[numeric_columns])
        
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
            'missing_values': df.isnull().sum().sum()
        },
        'columns': df.columns.tolist(),
        'data_sample': df.head(5).to_dict('records')
    }

    if len(numeric_columns) >= 2:
        result['clusters'] = {
            'count': len(np.unique(cluster_labels)),
            'sizes': pd.Series(cluster_labels).value_counts().to_dict(),
            'cluster_means': df.groupby('cluster').mean().to_dict()
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
    # ファイルパス指定（相対パス）
    base_dir = os.path.dirname(os.path.dirname(__file__))  # 1つ上の階層
    file_path = os.path.join(base_dir, 'data', 'alfano_data.csv')

    results = analyze_alfano_data(file_path)

    with open('analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=convert)

    print("\n分析結果をanalysis_results.jsonに保存しました")
