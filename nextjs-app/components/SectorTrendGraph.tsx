// components/SectorTrendGraph.tsx
import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { LapData } from '../types';

interface SectorTrendGraphProps {
  sectorGeoJson: LapData[];
}

const SectorTrendGraph: React.FC<SectorTrendGraphProps> = ({ sectorGeoJson }) => {
  // グラフ用にデータ変換（lap: "Lap 1", Sector1: 0.58, ...）
  const graphData = sectorGeoJson.map((lap) => ({
    lap: `Lap ${lap.lap}`,
    ...lap.sectorTimes,
  }));
  console.log("Graph Data:", graphData);
  console.log("sectorGeoJson sample:", sectorGeoJson[0]);

  return (
    <div className="bg-gray-800 border border-gray-600 rounded-lg p-4 mb-10">      
      <h3 className="text-xl font-bold text-white mb-4">セクタータイムの推移</h3>
      <ResponsiveContainer width="100%" height={800}>
        <LineChart data={graphData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="lap" stroke="#ccc" />
          <YAxis stroke="#ccc" unit="s" />
          <Tooltip />
          <Legend />
          {[1, 2, 3, 4, 5].map(sectorId => (
            <Line
              key={sectorId}
              type="monotone"
              dataKey={`Sector${sectorId}`}
              stroke={`hsl(${sectorId * 60}, 70%, 50%)`}
              strokeWidth={2}
              dot={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SectorTrendGraph;
