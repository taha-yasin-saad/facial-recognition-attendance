import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import { motion } from 'framer-motion';

const sidebarItems = [
  { name: 'Dashboard', to: '/admin' },
  { name: 'Employees', to: '/admin/employees' },
  { name: 'Attendance', to: '/admin/attendance' },
];

const AdminLayout: React.FC<{children: React.ReactNode}> = ({ children }) => {
  const [open, setOpen] = useState(true);
  const location = useLocation();

  return (
    <div className="flex h-screen bg-gray-100 dark:bg-gray-800">
      <motion.nav
        animate={{ width: open ? 240 : 64 }}
        className="bg-white dark:bg-gray-900 shadow-lg flex flex-col"
      >
        <div className="h-16 flex items-center justify-between px-4">
          <span className="font-bold text-lg">HR Tech</span>
          <button onClick={() => setOpen(!open)}>
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {sidebarItems.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={
                `block px-4 py-2 mt-2 rounded transition-colors duration-200 ` +
                (location.pathname === item.to
                  ? 'bg-accent text-white'
                  : 'text-gray-700 hover:bg-gray-200 dark:text-gray-300')
              }
            >
              {open ? item.name : item.name.charAt(0)}
            </Link>
          ))}
        </div>
      </motion.nav>
      <div className="flex-1 flex flex-col">
        <header className="h-16 bg-white dark:bg-gray-900 shadow flex items-center px-6 justify-between">
          <input
            type="text"
            placeholder="Search..."
            className="hidden md:block px-3 py-2 rounded border border-gray-300 focus:outline-none focus:ring focus:border-accent"
          />
          <button
            aria-label="Toggle dark mode"
            onClick={() => {
              document.documentElement.classList.toggle('dark');
            }}
            className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700"
          >
            Dark
          </button>
        </header>
        <main className="p-6 overflow-y-auto">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;
