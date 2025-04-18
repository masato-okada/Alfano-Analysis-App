// components/EngineTab.tsx（拡張版 - 表示切替 + 比率表示 + 合計/平均 + ツールチップ付き + ギア比分析）
import React, { useState, useEffect } from 'react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  LineChart,
  Line,
  ReferenceDot,
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend 
} from 'recharts';

interface RPMDistributionProps {
  sectorRPMData: {
    sector: number;
    bins: string[];
    averageCounts: number[];
    averageCountsPerLap: number[];
    bestLapCounts: number[];
  }[];
}

const EngineTab: React.FC<RPMDistributionProps> = ({ sectorRPMData }) => {
  const [viewMode, setViewMode] = useState<'total' | 'perLap'>('perLap');
  const [showRatio, setShowRatio] = useState<boolean>(false);
  const [gearData, setGearData] = useState<{
    overallSuggestedGear: number;
    sectorResults: {
      sector: number;
      bestGear: number;
      scores: { gear: number; score: number }[];
    }[];
  } | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetch("/api/gear-analysis")
      .then((res) => {
        if (!res.ok) {
          throw new Error(`API returned status ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        setGearData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch gear data", err);
        setError(err.message || "データの取得に失敗しました");
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-blue-400">エンジン特性分析（RPM分布）</h2>
        <div className="flex gap-2 items-center">
          <div className="space-x-1">
            <button
              className={`px-3 py-1 rounded-md text-sm font-semibold transition ${
                viewMode === 'perLap' ? 'bg-blue-500 text-white' : 'bg-gray-700 text-gray-300'
              }`}
              onClick={() => setViewMode('perLap')}
            >ラップ平均</button>
            <button
              className={`px-3 py-1 rounded-md text-sm font-semibold transition ${
                viewMode === 'total' ? 'bg-blue-500 text-white' : 'bg-gray-700 text-gray-300'
              }`}
              onClick={() => setViewMode('total')}
            >合計</button>
          </div>
          <div className="relative group">
            <button
              className={`px-3 py-1 rounded-md text-sm font-semibold transition ${
                showRatio ? 'bg-purple-500 text-white' : 'bg-gray-700 text-gray-300'
              }`}
              onClick={() => setShowRatio(!showRatio)}
            >{showRatio ? '数値' : '比率(%)'}</button>
            <div className="absolute z-10 hidden group-hover:block bg-gray-800 text-gray-200 text-xs rounded-md p-2 mt-1 w-52 shadow-lg">
              <p className="leading-snug">
                切替により各RPM帯の<br />
                出現数（数値）または割合（%）を表示します。
              </p>
            </div>
          </div>
        </div>
      </div>

      {sectorRPMData.map((sectorData) => {
        const baseValues = viewMode === 'total' ? sectorData.averageCounts : sectorData.averageCountsPerLap;
        const totalBase = showRatio ? baseValues.reduce((sum, val) => sum + val, 0) || 1 : 1;
        const totalBest = showRatio ? sectorData.bestLapCounts.reduce((sum, val) => sum + val, 0) || 1 : 1;

        const chartData = sectorData.bins.map((bin, i) => ({
          rpm: bin,
          平均: showRatio ? Math.round((baseValues[i] / totalBase) * 100) : baseValues[i],
          最速ラップ: showRatio ? Math.round((sectorData.bestLapCounts[i] / totalBest) * 100) : sectorData.bestLapCounts[i],
        }));

        return (
          <div key={sectorData.sector} className="bg-gray-900 p-4 rounded-lg shadow">
            <h3 className="text-xl font-semibold text-purple-300 mb-2">セクター {sectorData.sector}</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <XAxis dataKey="rpm" stroke="#ccc" />
                <YAxis stroke="#ccc" unit={showRatio ? '%' : ''} />
                <Tooltip formatter={(value: any) => showRatio ? `${value}%` : value} />
                <Legend />
                <Bar dataKey="平均" fill="#8884d8" />
                <Bar dataKey="最速ラップ" fill="#ff4d4f" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        );
      })}

      {/* ギア比分析セクション - ローディング状態とエラー状態の処理を追加 */}
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-green-400">ギア比シミュレーション</h2>
        
        {loading && (
          <div className="bg-gray-900 p-6 rounded-lg shadow text-center">
            <div className="animate-pulse text-blue-300">
              <svg className="inline w-8 h-8 mr-2 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span className="text-lg">データを取得中...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-900 p-4 rounded-lg shadow">
            <h3 className="text-xl font-semibold text-red-300 mb-2">エラー</h3>
            <p className="text-white">{error}</p>
            <button 
              className="mt-3 px-4 py-2 bg-red-700 text-white rounded hover:bg-red-600 transition"
              onClick={() => {
                setLoading(true);
                setError(null);
                fetch("/api/gear-analysis")
                  .then(res => res.json())
                  .then(data => {
                    setGearData(data);
                    setLoading(false);
                  })
                  .catch(err => {
                    console.error("再試行に失敗しました", err);
                    setError("再試行に失敗しました: " + (err.message || "不明なエラー"));
                    setLoading(false);
                  });
              }}
            >
              再試行
            </button>
          </div>
        )}

        {!loading && !error && gearData && gearData.sectorResults && (
          <>
            <div className="bg-gray-900 p-4 rounded-lg shadow">
              <h3 className="text-xl font-semibold text-green-300 mb-2">ギア比シミュレーション結果</h3>
              {gearData.sectorResults.map((sector) => (
                <div key={sector.sector} className="mb-6">
                  <h4 className="text-md font-semibold text-blue-400 mb-1">セクター {sector.sector}</h4>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={sector.scores}>
                      <XAxis dataKey="gear" stroke="#ccc" />
                      <YAxis stroke="#ccc" />
                      <Tooltip />
                      <Line type="monotone" dataKey="score" stroke="#8884d8" strokeWidth={2} />
                      <ReferenceDot
                        x={sector.bestGear}
                        y={sector.scores.find((s) => s.gear === sector.bestGear)?.score}
                        r={6}
                        fill="#ff4d4f"
                        stroke="none"
                        label={{
                          value: `最適: ${sector.bestGear}T`,
                          position: "top",
                          fill: "#ff4d4f",
                          fontSize: 12,
                        }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ))}
            </div>
            <div className="bg-gray-800 p-4 rounded-lg shadow">
              <h4 className="text-lg text-white font-bold">全体推奨ギア比：</h4>
              <p className="text-2xl text-yellow-400 font-mono mt-2">
                🔧 {gearData.overallSuggestedGear.toFixed(1)}T
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default EngineTab;