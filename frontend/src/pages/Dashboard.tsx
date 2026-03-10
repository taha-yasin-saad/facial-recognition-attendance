import React, { useEffect, useState } from 'react';
import StatCard from '../components/StatCard';
import { Users, CheckCircle2, Clock } from 'lucide-react';
import { motion } from 'framer-motion';
import Skeleton from '../components/Skeleton';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState({ total: 0, today: 0, late: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    // placeholder fetch, could call backend endpoints
    setTimeout(() => {
      setStats({ total: 123, today: 45, late: 3 });
      setLoading(false);
    }, 500);
  }, []);

  return (
    <div className="space-y-6">
      <motion.div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {loading ? (
          <>
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
          </>
        ) : (
          <>
            <StatCard title="Total Employees" value={stats.total} icon={<Users />} />
            <StatCard title="Today Check-ins" value={stats.today} icon={<CheckCircle2 />} />
            <StatCard title="Late Today" value={stats.late} icon={<Clock />} />
          </>
        )}
      </motion.div>
      <motion.div>
        <h3 className="text-lg font-semibold mb-2">Recent Activity</h3>
        <ul className="space-y-2">
          <li className="p-4 bg-white dark:bg-gray-800 rounded shadow">John Doe checked in</li>
          <li className="p-4 bg-white dark:bg-gray-800 rounded shadow">Jane Smith enrolled</li>
        </ul>
      </motion.div>
    </div>
  );
};

export default Dashboard;
