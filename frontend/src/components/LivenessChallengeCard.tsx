import React from 'react';
import { motion } from 'framer-motion';

interface LivenessChallengeCardProps {
  type: string;
  passed?: boolean;
  reason?: string;
}

const LivenessChallengeCard: React.FC<LivenessChallengeCardProps> = ({ type, passed, reason }) => {
  const statusText = passed === undefined ? 'Pending' : passed ? 'Passed' : 'Failed';
  const statusColor = passed === undefined ? 'text-gray-500' : passed ? 'text-success' : 'text-error';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-gray-800 rounded-xl shadow p-4 mb-4 flex items-center justify-between"
    >
      <div>
        <p className="font-medium">Challenge</p>
        <p className="text-lg font-semibold capitalize">{type.toLowerCase()}</p>
      </div>
      <div className={`font-semibold ${statusColor}`}>{statusText}</div>
      {reason && <p className="text-sm text-error ml-4">{reason}</p>}
    </motion.div>
  );
};

export default LivenessChallengeCard;
