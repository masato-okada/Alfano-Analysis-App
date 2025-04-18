// pages/api/engine.ts - RPM分布（ラップ平均付き）
import fs from 'fs';
import path from 'path';
import type { NextApiRequest, NextApiResponse } from 'next';

interface SectorRPMData {
  sector: number;
  bins: string[];
  averageCounts: number[];
  averageCountsPerLap: number[];
  bestLapCounts: number[];
}

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    const mainPath = path.join(process.cwd(), 'public', 'all_sessions_combined.json');
    const sectorPath = path.join(process.cwd(), 'public', 'sector_data.json');

    const df = JSON.parse(fs.readFileSync(mainPath, 'utf8'));
    const sectorData = JSON.parse(fs.readFileSync(sectorPath, 'utf8'));

    const binWidth = 250;
    const rpmBins = Array.from({ length: (13000 - 6000) / binWidth }, (_, i) => 6000 + i * binWidth);
    const binLabels = rpmBins.map(b => `${b}-${b + binWidth}`);

    const bestLapMap: Record<number, { lap: number; time: number }> = {};
    for (const entry of sectorData) {
      const lap = entry.lap;
      const sectorTimes = entry.sectorTimes || {};
      for (const [sectorName, time] of Object.entries(sectorTimes)) {
        const sectorId = parseInt(sectorName.replace('Sector', ''));
        if (!bestLapMap[sectorId] || time < bestLapMap[sectorId].time) {
          bestLapMap[sectorId] = { lap, time };
        }
      }
    }

    const result: SectorRPMData[] = [];
    const sectors = Array.from(new Set(df.map((row: any) => row.Sector))).sort((a, b) => a - b);

    for (const sector of sectors) {
      const sectorRows = df.filter((r: any) => r.Sector === sector && r.RPM);
      const bestLap = bestLapMap[sector]?.lap;

      const allRPMs = sectorRows.map((r: any) => r.RPM);
      const bestRPMs = sectorRows.filter((r: any) => r.Lap === bestLap).map((r: any) => r.RPM);

      const avgHist = new Array(binLabels.length).fill(0);
      const bestHist = new Array(binLabels.length).fill(0);

      for (const rpm of allRPMs) {
        const i = Math.floor((rpm - 6000) / binWidth);
        if (i >= 0 && i < avgHist.length) avgHist[i]++;
      }

      for (const rpm of bestRPMs) {
        const i = Math.floor((rpm - 6000) / binWidth);
        if (i >= 0 && i < bestHist.length) bestHist[i]++;
      }

      // ラップ数で割ってラップ平均を計算
      const lapSet = new Set(sectorRows.map((r: any) => r.Lap));
      const lapCount = lapSet.size || 1;
      const avgPerLap = avgHist.map(val => Math.round(val / lapCount));

      result.push({
        sector,
        bins: binLabels,
        averageCounts: avgHist,
        averageCountsPerLap: avgPerLap,
        bestLapCounts: bestHist
      });
    }

    res.status(200).json(result);
  } catch (err) {
    console.error('[API ERROR] /api/engine:', err);
    res.status(500).json({ error: 'エンジン特性データの解析に失敗しました。' });
  }
}