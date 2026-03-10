import React from 'react';
import { motion } from 'framer-motion';

const KioskLayout: React.FC<{children: React.ReactNode}> = ({ children }) => {
  return (
    <div className="h-screen w-screen bg-gray-900 flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-white dark:bg-gray-800 shadow-xl rounded-lg w-full max-w-3xl p-6"
      >
        {children}
      </motion.div>
    </div>
  );
};

export default KioskLayout;
