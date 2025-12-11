import { PlotResult } from '../services/api';

interface Props {
  plots: PlotResult[];
}

const PlotGallery = ({ plots }: Props) => {
  if (!plots.length) return null;
  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h2 className="text-lg font-semibold text-slate-800 mb-4">3. Auto-generated plots</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {plots.map((plot) => (
          <div key={plot.title} className="border rounded-lg p-3 bg-slate-50">
            <p className="font-semibold text-slate-800 mb-2">{plot.title}</p>
            <img
              src={`data:image/png;base64,${plot.image_base64}`}
              alt={plot.title}
              className="w-full rounded-md border"
            />
            <p className="text-xs text-slate-500 mt-1">{plot.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PlotGallery;


