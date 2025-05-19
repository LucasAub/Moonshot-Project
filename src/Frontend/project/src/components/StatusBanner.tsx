import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, AlertCircle, RefreshCw, Loader } from 'lucide-react';
import { ConversionStatus } from '../types/conversion';

interface StatusBannerProps {
  status: ConversionStatus;
  errorMessage?: string;
  onReset: () => void;
}

export const StatusBanner: React.FC<StatusBannerProps> = ({ 
  status, 
  errorMessage = 'An error occurred during conversion',
  onReset 
}) => {
  const statusConfig = {
    processing: {
      icon: <Loader className="mr-2 animate-spin" size={20} aria-hidden="true" />,
      color: 'bg-blue-100 text-blue-800 border-blue-200',
      message: 'Processing your PDF file. This may take a moment...',
      role: 'status',
      showReset: false
    },
    success: {
      icon: <CheckCircle className="mr-2" size={20} aria-hidden="true" />,
      color: 'bg-green-100 text-green-800 border-green-200',
      message: 'Conversion successful! You can preview or download the HTML below.',
      role: 'status',
      showReset: true
    },
    error: {
      icon: <AlertCircle className="mr-2" size={20} aria-hidden="true" />,
      color: 'bg-red-100 text-red-800 border-red-200',
      message: errorMessage,
      role: 'alert',
      showReset: true
    },
    idle: {
      icon: null,
      color: '',
      message: '',
      role: 'status',
      showReset: false
    }
  };

  const config = statusConfig[status];

  return (
    <motion.div
      className={`p-4 mb-6 rounded-lg border ${config.color} flex items-start justify-between`}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      role={config.role}
    >
      <div className="flex items-center">
        {config.icon}
        <span>{config.message}</span>
      </div>
      
      {config.showReset && (
        <button
          className="ml-4 flex items-center text-sm hover:underline focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 rounded"
          onClick={onReset}
          aria-label="Reset and upload another file"
        >
          <RefreshCw size={16} className="mr-1" aria-hidden="true" />
          Try Another
        </button>
      )}
    </motion.div>
  );
};