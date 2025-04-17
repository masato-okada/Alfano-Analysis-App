export default function DataTab({ analysisData }: { analysisData: any }) {
    return (
      <div>
        <h2 className="text-2xl font-semibold mb-6 text-gray-100 flex items-center gap-3">
          データサンプル
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse bg-gray-700/50 rounded-lg overflow-hidden">
            <thead>
              <tr className="bg-gray-800 text-gray-300">
                {analysisData.columns.map((column: string, index: number) => (
                  <th key={index} className="border-b border-gray-600 p-3 text-left text-sm font-semibold">{column}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {analysisData.data_sample.map((row: any, rowIndex: number) => (
                <tr key={rowIndex} className="hover:bg-gray-700/50 transition-colors">
                  {analysisData.columns.map((column: string, colIndex: number) => (
                    <td key={colIndex} className="border-b border-gray-700 p-3 text-gray-300 text-sm">
                      {row[column]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }
  