// components/SectorTab.tsx
import React from 'react';
import type { SectorSummaryItem } from '../types/types';
import { PieChart as PieChartIcon } from 'lucide-react';
import SectorMap from './SectorMap';
import SectorTrendGraph from './SectorTrendGraph';


interface SectorTabProps {
  sectorData: SectorSummaryItem[] | null;
  sectorGeoJson?: LapData[] | null; // ← ここ重要
}


const SectorTab: React.FC<SectorTabProps> = ({ sectorData, sectorGeoJson }) => {
  console.log('🚗 sectorGeoJson:', sectorGeoJson);
  if (!sectorData) {
    return <div className="text-gray-400">セクターデータが見つかりません。</div>;
  }

  return (
    <div>
      <h2 className="text-2xl font-semibold mb-6 text-gray-100 flex items-center gap-3">
        <PieChartIcon className="text-yellow-400" />
        セクター分析
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-10">
        {sectorData.map((sector) => (
            <div key={sector.sector} className="bg-gray-800 border border-gray-700 rounded-lg p-5 shadow hover:shadow-lg transition">
            <h3 className="text-xl font-bold text-blue-400 mb-2">Sector {sector.sector}</h3>
            <p className="text-sm text-gray-400">平均タイム: <span className="text-white font-semibold">{sector.mean_time.toFixed(2)} 秒</span></p>
            <p className="text-sm text-gray-400">最大タイム: <span className="text-white font-semibold">{sector.max_time.toFixed(2)} 秒</span></p>
            <p className="text-sm text-gray-400">最小タイム: <span className="text-white font-semibold">{sector.min_time.toFixed(2)} 秒</span></p>
            <div className="mt-4 border-t border-gray-700 pt-3">
                <p className="text-sm text-gray-400">平均速度: <span className="text-green-400 font-semibold">{sector.mean_speed.toFixed(1)} km/h</span></p>
                <p className="text-sm text-gray-400">最高速度: <span className="text-yellow-400 font-semibold">{sector.max_speed.toFixed(1)} km/h</span></p>
                <p className="text-sm text-gray-400">最低速度: <span className="text-red-400 font-semibold">{sector.min_speed.toFixed(1)} km/h</span></p>
            </div>
            </div>
        ))}
        </div>
        {sectorGeoJson && (
            <div className="mb-8">
                <h3 className="text-xl font-bold text-gray-200 mb-4">セクター別コース図</h3>
                <SectorMap geoData={sectorGeoJson} />
            </div>
            )}

      <div className="overflow-x-auto">
        <table className="w-full border-collapse bg-gray-700/50 rounded-lg overflow-hidden">
          <thead>
            <tr className="bg-gray-800 text-gray-300">
              {['Sector', 'Mean Time (s)', 'Max Time', 'Min Time', 'Mean Speed (km/h)', 'Max Speed', 'Min Speed'].map((header, index) => (
                <th
                  key={index}
                  className="border-b border-gray-600 p-3 text-left text-sm font-semibold"
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sectorData.map((s, i) => (
              <tr key={i} className="hover:bg-gray-700/50 transition-colors">
                <td className="border-b border-gray-700 p-3 text-gray-300 text-sm">{s.sector}</td>
                <td className="border-b border-gray-700 p-3 text-gray-300 text-sm">{s.mean_time.toFixed(2)}</td>
                <td className="border-b border-gray-700 p-3 text-gray-300 text-sm">{s.max_time.toFixed(2)}</td>
                <td className="border-b border-gray-700 p-3 text-gray-300 text-sm">{s.min_time.toFixed(2)}</td>
                <td className="border-b border-gray-700 p-3 text-gray-300 text-sm">{s.mean_speed.toFixed(1)}</td>
                <td className="border-b border-gray-700 p-3 text-gray-300 text-sm">{s.max_speed.toFixed(1)}</td>
                <td className="border-b border-gray-700 p-3 text-gray-300 text-sm">{s.min_speed.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {sectorGeoJson && (
        <SectorTrendGraph sectorGeoJson={sectorGeoJson} />
      )}
    </div>
  );
};

export default SectorTab;