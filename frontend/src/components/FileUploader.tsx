import { ChangeEvent, useState } from 'react';
import { Button, LinearProgress } from '@mui/material';

interface Props {
  onUpload: (file: File) => Promise<void> | void;
}

const FileUploader = ({ onUpload }: Props) => {
  const [uploading, setUploading] = useState(false);

  const handleFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    await onUpload(file);
    setUploading(false);
  };

  return (
    <div className="bg-white rounded-xl shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-800">1. Upload CSV</h2>
          <p className="text-sm text-slate-500">Any CSV is accepted. We auto-detect encoding.</p>
        </div>
        <Button variant="contained" component="label" disabled={uploading}>
          {uploading ? 'Uploading...' : 'Choose CSV'}
          <input hidden accept=".csv" type="file" onChange={handleFile} />
        </Button>
      </div>
      {uploading && <LinearProgress className="mt-4" />}
    </div>
  );
};

export default FileUploader;




