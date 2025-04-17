import React from 'react';
import { LapData } from '../types';
import { motion } from 'framer-motion';

interface SectorMapProps {
  geoData: LapData[];
}

const COLORS = ['#FF5733', '#33B5FF', '#33FFB5', '#FFD700', '#9D33FF'];

const SectorMap: React.FC<SectorMapProps> = ({ geoData }) => {
  if (!geoData || geoData.length === 0) return null;

  // --- 全体の座標範囲を取得して中心化・縮小用の情報を準備 ---
  const allPoints = geoData.flatMap(lap => lap.points);
  const xs = allPoints.map(p => p.x);
  const ys = allPoints.map(p => p.y);

  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);

  const centerX = (minX + maxX) / 2;
  const centerY = (minY + maxY) / 2;
  const scale = 1 / 500000; // ← 座標スケールに合わせて調整可

  const normalize = (val: number, center: number) => (val - center) * scale;

  return (
    <svg viewBox="-100 -100 200 200" className="w-full h-96 bg-gray-900 border border-gray-600 rounded-lg">
      {geoData.map((lap, lapIndex) => {
        const sectors = [...new Set(lap.points.map(p => p.Sector))];
        console.log(`Lap ${lapIndex + 1} sectors:`, sectors);

        return (
          <g key={lapIndex}>
            {Array.from({ length: 5 }, (_, i) => i + 1).map(sectorId => {
              const points = lap.points.filter(p => Number(p.Sector) === sectorId);
              if (points.length === 0) return null;

              console.log(`Lap ${lapIndex + 1} - Sector ${sectorId}: ${points.length} points`);

              const pathData = points
                .map((p, idx) => {
                  const x = normalize(p.x, centerX);
                  const y = -normalize(p.y, centerY); // Y軸はSVGの都合で反転
                  return `${idx === 0 ? 'M' : 'L'} ${x} ${y}`;
                })
                .join(' ');

              return (
                <motion.path
                  key={sectorId}
                  d={pathData}
                  stroke={COLORS[(sectorId - 1) % COLORS.length]}
                  strokeWidth={2}
                  fill="none"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 1, ease: 'easeInOut', delay: lapIndex * 0.5 + sectorId * 0.2 }}
                  opacity={0.7}
                />
              );
            })}
          </g>
        );
      })}
    </svg>
  );
};

export default SectorMap;
