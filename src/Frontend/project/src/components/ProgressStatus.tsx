import React from 'react';
import { CheckCircleIcon, AlertCircleIcon, LoaderIcon } from 'lucide-react';

type StatusProps = {
  status: 'idle' | 'uploading' | 'processing' | 'success' | 'error';
  errorMessage?: string;
};

const ProgressStatus: React.FC<StatusProps> = ({ status, errorMessage }) => {
  if (status === 'idle') return null;

  return (
    <div 
      className="mt-6 rounded-lg p-4"
      role="status"
      aria-live="polite"
    >
      {(status === 'uploading' || status === 'processing') && (
        <div className="flex items-center text-blue-700 bg-blue-50 p-4 rounded-lg">
          <LoaderIcon className="animate-spin mr-3 h-5 w-5" aria-hidden="true" />
          <span className="font-medium">
            {status === 'uploading' ? 'Envoi du fichier...' : 'Conversion en cours...'}
          </span>
        </div>
      )}

      {status === 'success' && (
        <div className="flex items-center text-green-700 bg-green-50 p-4 rounded-lg">
          <CheckCircleIcon className="mr-3 h-5 w-5" aria-hidden="true" />
          <span className="font-medium">
            Conversion réussie !
          </span>
        </div>
      )}

      {status === 'error' && (
        <div className="flex items-center text-red-700 bg-red-50 p-4 rounded-lg" role="alert">
          <AlertCircleIcon className="mr-3 h-5 w-5" aria-hidden="true" />
          <span className="font-medium">
            {errorMessage || 'Une erreur est survenue lors de la conversion.'}
          </span>
        </div>
      )}
    </div>
  );
};

export default ProgressStatus;