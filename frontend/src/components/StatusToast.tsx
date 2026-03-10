import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface StatusToastProps {
  message: string;
  type?: 'success' | 'error' | 'info';
  onClose?: () => void;
}

const colors = {
  success: 'bg-success text-white',
  error: 'bg-error text-white',
  info: 'bg-accent text-white',
};

const StatusToast: React.FC<StatusToastProps> = ({ message, type = 'info', onClose }) => {
  useEffect(() => {
    const timer = setTimeout(() => onClose && onClose(), 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <AnimatePresence>
      {message && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          className={`fixed bottom-5 right-5 p-4 rounded shadow-lg ${colors[type]}`}
        >
          {message}
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default StatusToast;
