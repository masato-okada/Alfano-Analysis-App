// pages/index.tsx
import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, 
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  ResponsiveContainer, Cell
} from 'recharts';

import { 
  LayoutGrid, 
  Table, 
  PieChart as PieChartIcon, 
  Database 
} from 'lucide-react';

interface AnalysisSummary {
  rows: number;
  columns: number;
  missing_values: number;
}

interface DataSample {
  [key: string]: string | number;
}

interface ClusterSizes {
  [key: string]: number;
}

interface ClusterMeans {
  [key: string]: {
    [key: string]: number;
  };
}

interface SectorSummaryItem {
  sector: number;
  mean_time: number;
  max_time: number;
  min_time: number;
  mean_speed: number;
  max_speed: number;
  min_speed: number;
}

interface AnalysisData {
  summary: AnalysisSummary;
  columns: string[];
  data_sample: DataSample[];
  clusters?: {
    count: number;
    sizes: ClusterSizes;
    cluster_means: ClusterMeans;
  };
  sector_summary?: SectorSummaryItem[]; // ← ★ ここに追加
}

interface SectorPoint {
  x: number;
  y: number;
  Time_sec: number;
  Sector: number;
}

interface LapData {
  lap: number;
  sectorTimes: Record<string, number>;
  points: SectorPoint[];
}


export default function Home() {
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [sectorData, setSectorData] = useState<SectorSummaryItem[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'summary' | 'data' | 'clusters' | 'sector'>('summary');

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

  useEffect(() => {
    fetch('/api/analysis')
      .then(response => {
        if (!response.ok) throw new Error('データの取得に失敗しました');
        return response.json();
      })
      .then(data => {
        setAnalysisData(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err instanceof Error ? err.message : 'エラーが発生しました');
        setLoading(false);
      });
  }, []);
  useEffect(() => {
    fetch('/api/sector')
      .then(res => {
        if (!res.ok) throw new Error('セクター分析データの取得に失敗');
        return res.json();
      })
      .then(data => {
        setSectorData(data.sector_summary);
      })
      .catch(err => {
        console.error(err);
        setSectorData(null);
      });
  }, []);
  

  if (loading) return <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black flex items-center justify-center text-gray-300 text-xl animate-pulse">データを読み込み中...</div>;
  if (error) return <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black flex items-center justify-center text-red-500 text-xl">エラー: {error}</div>;
  if (!analysisData) return <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black flex items-center justify-center text-gray-300 text-xl">データがありません</div>;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-gray-100">
      <Head>
        <title>Alfanoデータ分析ダッシュボード</title>
        <meta name="description" content="Alfanoデータの分析結果を表示するダッシュボード" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <header className="mb-10">
          <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-600 mb-2">
            Alfanoデータ分析ダッシュボード
          </h1>
          <p className="text-gray-400 text-lg">包括的なデータ洞察</p>
        </header>

        <div className="bg-gray-800 rounded-xl shadow-2xl border border-gray-700 overflow-hidden">
          <div className="flex border-b border-gray-700">
            <button 
              onClick={() => setActiveTab('summary')} 
              className={`flex items-center gap-2 px-4 py-3 transition-colors ${
                activeTab === 'summary' 
                  ? 'bg-blue-600 text-white' 
                  : 'hover:bg-gray-700 text-gray-300'
              }`}
            >
              <LayoutGrid size={18} />概要
            </button>
            <button 
              onClick={() => setActiveTab('data')} 
              className={`flex items-center gap-2 px-4 py-3 transition-colors ${
                activeTab === 'data' 
                  ? 'bg-blue-600 text-white' 
                  : 'hover:bg-gray-700 text-gray-300'
              }`}
            >
              <Table size={18} />データサンプル
            </button>
            {analysisData.clusters && (
              <button 
                onClick={() => setActiveTab('clusters')} 
                className={`flex items-center gap-2 px-4 py-3 transition-colors ${
                  activeTab === 'clusters' 
                    ? 'bg-blue-600 text-white' 
                    : 'hover:bg-gray-700 text-gray-300'
                }`}
              >
                <PieChartIcon size={18} />クラスター分析
              </button>
              
            )}

              <button 
                onClick={() => setActiveTab('sector')} 
                className={`flex items-center gap-2 px-4 py-3 transition-colors ${
                  activeTab === 'sector' 
                    ? 'bg-blue-600 text-white' 
                    : 'hover:bg-gray-700 text-gray-300'
                }`}
              >
                <PieChartIcon size={18} />セクター分析
              </button>

          </div>

          <div className="p-6">
            {activeTab === 'summary' && (
              <div>
                <h2 className="text-2xl font-semibold mb-6 text-gray-100 flex items-center gap-3">
                  <LayoutGrid className="text-blue-400" />
                  データ概要
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {[
                    { 
                      label: '行数', 
                      value: analysisData.summary.rows, 
                      icon: <Database className="text-blue-400" /> 
                    },
                    { 
                      label: '列数', 
                      value: analysisData.summary.columns, 
                      icon: <Table className="text-green-400" /> 
                    },
                    { 
                      label: '欠損値', 
                      value: analysisData.summary.missing_values, 
                      icon: <PieChartIcon className="text-red-400" /> 
                    }
                  ].map((item, index) => (
                    <div 
                      key={index} 
                      className="bg-gray-700/50 rounded-lg p-5 border border-gray-700 flex items-center gap-4 hover:bg-gray-700/70 transition-all"
                    >
                      {item.icon}
                      <div>
                        <p className="text-gray-400 text-sm mb-1">{item.label}</p>
                        <p className="text-3xl font-bold text-white">{item.value}</p>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="mt-8">
                  <h3 className="text-xl font-semibold mb-4 text-gray-200">列一覧</h3>
                  <div className="bg-gray-700/50 rounded-lg p-4 grid grid-cols-2 md:grid-cols-4 gap-3">
                    {analysisData.columns.map((column, index) => (
                      <div 
                        key={index} 
                        className="bg-gray-800 rounded px-3 py-2 text-gray-300 text-sm text-center hover:bg-gray-700 transition-colors"
                      >
                        {column}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
            
            {activeTab === 'data' && (
              <div>
                <h2 className="text-2xl font-semibold mb-6 text-gray-100 flex items-center gap-3">
                  <Table className="text-green-400" />
                  データサンプル
                </h2>
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse bg-gray-700/50 rounded-lg overflow-hidden">
                    <thead>
                      <tr className="bg-gray-800 text-gray-300">
                        {analysisData.columns.map((column, index) => (
                          <th 
                            key={index} 
                            className="border-b border-gray-600 p-3 text-left text-sm font-semibold"
                          >
                            {column}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {analysisData.data_sample.map((row, rowIndex) => (
                        <tr 
                          key={rowIndex} 
                          className="hover:bg-gray-700/50 transition-colors"
                        >
                          {analysisData.columns.map((column, colIndex) => (
                            <td 
                              key={colIndex} 
                              className="border-b border-gray-700 p-3 text-gray-300 text-sm"
                            >
                              {row[column]}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            
            {activeTab === 'clusters' && analysisData.clusters && (
              <div>
                <h2 className="text-2xl font-semibold mb-6 text-gray-100 flex items-center gap-3">
                  <PieChartIcon className="text-purple-400" />
                  クラスター分析結果
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div>
                    <h3 className="text-xl font-semibold mb-4 text-gray-200">クラスターサイズ</h3>
                    <div className="bg-gray-700/50 rounded-lg p-6 h-[400px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={Object.entries(analysisData.clusters.sizes).map(([cluster, size]) => ({
                              name: `クラスター ${cluster}`,
                              value: size
                            }))}
                            cx="50%"
                            cy="50%"
                            outerRadius="80%"
                            fill="#8884d8"
                            dataKey="value"
                            label={({name, percent}) => `${name} (${(percent * 100).toFixed(0)}%)`}
                            labelStyle={{ fill: 'white', fontSize: '12px' }}
                          >
                            {Object.keys(analysisData.clusters.sizes).map((entry, index) => (
                              <Cell 
                                key={`cell-${index}`} 
                                fill={COLORS[index % COLORS.length]} 
                              />
                            ))}
                          </Pie>
                          <Tooltip 
                            contentStyle={{ 
                              backgroundColor: '#1f2937', 
                              borderColor: '#374151',
                              color: 'white'
                            }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-xl font-semibold mb-4 text-gray-200">クラスター特性</h3>
                    <div className="bg-gray-700/50 rounded-lg p-6 h-[400px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={Object.entries(analysisData.clusters.cluster_means).map(([feature, values]) => {
                            const entry: {[key: string]: string | number} = { name: feature };
                            Object.entries(values).forEach(([cluster, value]) => {
                              entry[`クラスター ${cluster}`] = parseFloat(value.toFixed(2));
                            });
                            return entry;
                          })}
                          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                        >
                          <CartesianGrid 
                            strokeDasharray="3 3" 
                            stroke="#374151" 
                          />
                          <XAxis 
                            dataKey="name" 
                            tick={{ fill: 'white' }} 
                          />
                          <YAxis 
                            tick={{ fill: 'white' }} 
                          />
                          <Tooltip 
                            contentStyle={{ 
                              backgroundColor: '#1f2937', 
                              borderColor: '#374151',
                              color: 'white'
                            }}
                          />
                          <Legend 
                            wrapperStyle={{ color: 'white' }}
                          />
                          {Object.keys(analysisData.clusters.cluster_means[Object.keys(analysisData.clusters.cluster_means)[0]]).map((cluster, index) => (
                            <Bar
                              key={`bar-${index}`}
                              dataKey={`クラスター ${cluster}`}
                              fill={COLORS[index % COLORS.length]}
                            />
                          ))}
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'sector' && sectorData && (
              <div>
                <h2 className="text-2xl font-semibold mb-6 text-gray-100 flex items-center gap-3">
                  <PieChartIcon className="text-yellow-400" />
                  セクター分析
                </h2>
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse bg-gray-700/50 rounded-lg overflow-hidden">
                    <thead>
                      <tr className="bg-gray-800 text-gray-300">
                        {['Sector', 'Mean Time (s)', 'Max Time', 'Min Time', 'Mean Speed (km/h)', 'Max Speed', 'Min Speed'].map((header, index) => (
                          <th key={index} className="border-b border-gray-600 p-3 text-left text-sm font-semibold">
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
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}