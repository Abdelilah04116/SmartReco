export type ChartType = 'bar' | 'pie' | 'line' | 'area' | 'scatter' | 'histogram' | 'box';

interface ChartSelectorProps {
  selectedCharts: ChartType[];
  onChartsChange: (charts: ChartType[]) => void;
  availableCharts?: ChartType[];
}

const ChartSelector = ({ selectedCharts, onChartsChange, availableCharts }: ChartSelectorProps) => {
  const allCharts: ChartType[] = availableCharts || ['bar', 'pie', 'line', 'area', 'scatter', 'histogram', 'box'];
  
  const chartLabels: Record<ChartType, string> = {
    bar: 'Bar Chart',
    pie: 'Pie Chart',
    line: 'Line Chart',
    area: 'Area Chart',
    scatter: 'Scatter Plot',
    histogram: 'Histogram',
    box: 'Box Plot',
  };

  const toggleChart = (chart: ChartType) => {
    if (selectedCharts.includes(chart)) {
      onChartsChange(selectedCharts.filter(c => c !== chart));
    } else {
      onChartsChange([...selectedCharts, chart]);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-semibold mb-3">Select Chart Types</h3>
      <div className="flex flex-wrap gap-2">
        {allCharts.map((chart) => (
          <button
            key={chart}
            onClick={() => toggleChart(chart)}
            className={`px-4 py-2 rounded transition-colors ${
              selectedCharts.includes(chart)
                ? 'bg-primary-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {chartLabels[chart]}
          </button>
        ))}
      </div>
      {selectedCharts.length === 0 && (
        <p className="text-sm text-gray-500 mt-2">Select at least one chart type to display</p>
      )}
    </div>
  );
};

export default ChartSelector;

