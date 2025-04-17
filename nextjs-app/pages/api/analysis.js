// pages/api/analysis.js

import fs from 'fs';
import path from 'path';

export default function handler(req, res) {
  try {
    // 本番環境では、Pythonスクリプトを実行するロジックを追加するか
    // すでに生成されたJSONファイルを読み込みます
    const dataFilePath = path.join(process.cwd(), 'public', 'analysis_results.json');
    
    // ファイルが存在しない場合はサンプルデータを返す
    if (!fs.existsSync(dataFilePath)) {
      // サンプルデータ（テスト用）
      const sampleData = {
        summary: {
          rows: 120,
          columns: 8,
          missing_values: 5
        },
        columns: ['id', 'age', 'income', 'score', 'category', 'region', 'timestamp', 'status'],
        data_sample: [
          { id: 1, age: 32, income: 78000, score: 0.85, category: 'A', region: 'East', timestamp: '2023-06-15', status: 'active' },
          { id: 2, age: 45, income: 65000, score: 0.72, category: 'B', region: 'West', timestamp: '2023-05-22', status: 'active' },
          { id: 3, age: 28, income: 52000, score: 0.91, category: 'A', region: 'North', timestamp: '2023-07-01', status: 'inactive' },
          { id: 4, age: 39, income: 86000, score: 0.65, category: 'C', region: 'South', timestamp: '2023-06-30', status: 'active' },
          { id: 5, age: 51, income: 94000, score: 0.78, category: 'B', region: 'East', timestamp: '2023-06-10', status: 'inactive' }
        ],
        clusters: {
          count: 3,
          sizes: { '0': 42, '1': 35, '2': 43 },
          cluster_means: {
            'age': { '0': 35.2, '1': 48.7, '2': 29.1 },
            'income': { '0': 72500, '1': 88400, '2': 51200 },
            'score': { '0': 0.82, '1': 0.69, '2': 0.88 }
          }
        }
      };
      return res.status(200).json(sampleData);
    }
    
    // 実際のデータファイルを読み込む
    const fileContents = fs.readFileSync(dataFilePath, 'utf8');
    const data = JSON.parse(fileContents);
    
    res.status(200).json(data);
  } catch (error) {
    console.error('API error:', error);
    res.status(500).json({ error: 'データの取得に失敗しました' });
  }
}