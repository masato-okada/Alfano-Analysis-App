import React from 'react';
import { LayoutGrid, Table, PieChart as PieChartIcon, Database } from 'lucide-react';

export default function SummaryTab({ analysisData }: { analysisData: any }) {
  return (
    <div>
      <h2 className="text-2xl font-semibold mb-6 text-gray-100 flex items-center gap-3">
        <LayoutGrid className="text-blue-400" />
        データ概要
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[{ label: '行数', value: analysisData.summary.rows, icon: <Database className="text-blue-400" /> },
          { label: '列数', value: analysisData.summary.columns, icon: <Table className="text-green-400" /> },
          { label: '欠損値', value: analysisData.summary.missing_values, icon: <PieChartIcon className="text-red-400" /> }
        ].map((item, index) => (
          <div key={index} className="bg-gray-700/50 rounded-lg p-5 border border-gray-700 flex items-center gap-4 hover:bg-gray-700/70 transition-all">
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
          {analysisData.columns.map((column: string, index: number) => (
            <div key={index} className="bg-gray-800 rounded px-3 py-2 text-gray-300 text-sm text-center hover:bg-gray-700 transition-colors">
              {column}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
