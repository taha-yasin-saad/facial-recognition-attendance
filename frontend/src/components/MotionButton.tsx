import { motion } from 'framer-motion';
import React from 'react';

interface MotionButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
}

const MotionButton: React.FC<MotionButtonProps> = ({ children, className = '', ...props }) => (
  <motion.button
    whileHover={{ scale: 1.03 }}
    whileTap={{ scale: 0.97 }}
    className={
      `inline-flex items-center justify-center px-4 py-2 rounded-lg font-semibold focus:outline-none focus:ring-2 focus:ring-accent ` +
      className
    }
    {...props}
  >
    {children}
  </motion.button>
);

export default MotionButton;
