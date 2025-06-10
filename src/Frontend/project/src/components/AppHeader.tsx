import React from 'react';
import { motion } from 'framer-motion';
import { FileText } from 'lucide-react';

export const AppHeader: React.FC = () => {
  return (
    <motion.header 
      className="bg-white shadow-sm py-4"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="container mx-auto px-4 flex items-center justify-center">
        <FileText className="text-blue-600 mr-2" size={24} aria-hidden="true" />
        <span className="text-xl font-semibold text-gray-800">PDF To Accessible HTML Converter</span>
      </div>
    </motion.header>
  );
};