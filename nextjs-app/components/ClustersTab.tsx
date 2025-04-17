import React from 'react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Legend,
  Bar
} from 'recharts';
import { PieChart as PieChartIcon } from 'lucide-react';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

export default function ClustersTab({ analysisData }: { analysisData: any }) {
  return (
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
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                >
                  {Object.keys(analysisData.clusters.sizes).map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: 'white' }} />
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
                  const entry: { [key: string]: string | number } = { name: feature };
                  Object.entries(values).forEach(([cluster, value]) => {
                    entry[`クラスター ${cluster}`] = parseFloat(value.toFixed(2));
                  });
                  return entry;
                })}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" tick={{ fill: 'white' }} />
                <YAxis tick={{ fill: 'white' }} />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: 'white' }} />
                <Legend wrapperStyle={{ color: 'white' }} />
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
  );
}
