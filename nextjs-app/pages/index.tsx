// pages/index.tsx
import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { LayoutGrid, Table, PieChart as PieChartIcon } from 'lucide-react';
import SummaryTab from '../components/SummaryTab';
import DataTab from '../components/DataTab';
import ClustersTab from '../components/ClustersTab';
import SectorTab from '../components/SectorTab';
import {
  AnalysisData,
  SectorSummaryItem,
  LapData
} from '../types/types';

export default function Home() {
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [sectorData, setSectorData] = useState<SectorSummaryItem[] | null>(null);
  const [sectorGeoJson, setSectorGeoJson] = useState<LapData[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'summary' | 'data' | 'clusters' | 'sector'>('summary');

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
        setSectorData(data.sector_summary || null);
        setSectorGeoJson(data.sector_geojson || null); // 👈 追加
      })
      .catch(err => {
        console.error(err);
        setSectorData(null);
        setSectorGeoJson(null); // 👈 念のため null 代入
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
            <button onClick={() => setActiveTab('summary')} className={`flex items-center gap-2 px-4 py-3 transition-colors ${activeTab === 'summary' ? 'bg-blue-600 text-white' : 'hover:bg-gray-700 text-gray-300'}`}>
              <LayoutGrid size={18} />概要
            </button>
            <button onClick={() => setActiveTab('data')} className={`flex items-center gap-2 px-4 py-3 transition-colors ${activeTab === 'data' ? 'bg-blue-600 text-white' : 'hover:bg-gray-700 text-gray-300'}`}>
              <Table size={18} />データ
            </button>
            {analysisData.clusters && (
              <button onClick={() => setActiveTab('clusters')} className={`flex items-center gap-2 px-4 py-3 transition-colors ${activeTab === 'clusters' ? 'bg-blue-600 text-white' : 'hover:bg-gray-700 text-gray-300'}`}>
                <PieChartIcon size={18} />クラスター
              </button>
            )}
            <button onClick={() => setActiveTab('sector')} className={`flex items-center gap-2 px-4 py-3 transition-colors ${activeTab === 'sector' ? 'bg-blue-600 text-white' : 'hover:bg-gray-700 text-gray-300'}`}>
              <PieChartIcon size={18} />セクター
            </button>
          </div>

          <div className="p-6">
            {activeTab === 'summary' && <SummaryTab analysisData={analysisData} />}
            {activeTab === 'data' && <DataTab analysisData={analysisData} />}
            {activeTab === 'clusters' && analysisData.clusters && <ClustersTab analysisData={analysisData} />}
            {activeTab === 'sector' && <SectorTab sectorData={sectorData} sectorGeoJson={sectorGeoJson} />} {/* 👈 追加 */}
          </div>
        </div>
      </div>
    </div>
  );
}
