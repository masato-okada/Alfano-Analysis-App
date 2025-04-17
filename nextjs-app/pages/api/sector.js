import fs from 'fs';
import path from 'path';

export default function handler(req, res) {
  try {
    const filePath = path.join(process.cwd(), 'public', 'sector_data.json');
    if (!fs.existsSync(filePath)) {
      return res.status(404).json({ error: 'sector_data.json が見つかりません' });
    }

    const raw = fs.readFileSync(filePath, 'utf8');
    const laps = JSON.parse(raw);

    // 各セクター番号ごとに集計
    const summary = {};

    laps.forEach(lap => {
      const sectorTimes = lap.sectorTimes;
      Object.entries(sectorTimes).forEach(([sectorName, time]) => {
        const sector = parseInt(sectorName.replace('Sector', ''));
        if (!summary[sector]) {
          summary[sector] = {
            sector,
            times: [],
          };
        }
        summary[sector].times.push(time);
      });
    });

    // 平均・最大・最小の統計を計算
    const sector_summary = Object.values(summary).map(sector => {
      const times = sector.times;
      const mean_time = times.reduce((a, b) => a + b, 0) / times.length;
      const max_time = Math.max(...times);
      const min_time = Math.min(...times);
      return {
        sector: sector.sector,
        mean_time,
        max_time,
        min_time,
        mean_speed: 0,
        max_speed: 0,
        min_speed: 0,
      };
    });

    res.status(200).json({ sector_summary });

  } catch (err) {
    console.error('Sector API error:', err);
    res.status(500).json({ error: 'セクター分析の読み込みに失敗しました' });
  }
}
