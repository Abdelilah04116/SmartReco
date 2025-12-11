import { useState, useEffect } from 'react';
import apiService, { TemplateDescriptor } from '../services/api';

interface TemplateSelectorProps {
  onSelect: (template: TemplateDescriptor | null) => void;
  selected?: string | null;
}

const TemplateSelector = ({ onSelect, selected }: TemplateSelectorProps) => {
  const [templates, setTemplates] = useState<TemplateDescriptor[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadTemplates = async () => {
      setLoading(true);
      try {
        const result = await apiService.listTemplates();
        setTemplates(result.templates);
      } catch (err) {
        console.error('Failed to load templates:', err);
      } finally {
        setLoading(false);
      }
    };
    loadTemplates();
  }, []);

  if (loading) {
    return <div className="text-sm text-gray-500">Chargement des templates...</div>;
  }

  return (
    <div className="flex gap-2 flex-wrap">
      <button
        onClick={() => onSelect(null)}
        className={`px-3 py-1 text-sm rounded ${
          !selected
            ? 'bg-blue-600 text-white'
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
        }`}
      >
        Auto
      </button>
      {templates.map((template) => (
        <button
          key={template.id}
          onClick={() => onSelect(template)}
          className={`px-3 py-1 text-sm rounded ${
            selected === template.id
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
          title={template.description}
        >
          {template.name}
        </button>
      ))}
    </div>
  );
};

export default TemplateSelector;

