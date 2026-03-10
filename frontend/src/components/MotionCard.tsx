import { motion } from 'framer-motion';
import React from 'react';

const MotionCard: React.FC<{children: React.ReactNode}> = ({ children }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -10 }}
    className="bg-white dark:bg-gray-800 rounded-xl shadow p-6 mb-6"
  >
    {children}
  </motion.div>
);

export default MotionCard;
