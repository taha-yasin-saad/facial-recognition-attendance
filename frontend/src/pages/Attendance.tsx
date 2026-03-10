import React, { useState, useEffect } from "react";
import api from "../api";
import DataTable from "../components/DataTable";
import FilterChips from "../components/FilterChips";
import MotionButton from "../components/MotionButton";
import { Download } from "lucide-react";
import { motion } from 'framer-motion';
import { useToast } from "../components/ToastProvider";
import Skeleton from "../components/Skeleton";

interface Record {
  id: number;
  employee_id: number;
  timestamp: string;
  type: string;
  confidence: number;
  device_id?: string;
  face_distance: number;
}

const Attendance: React.FC = () => {
  const [records, setRecords] = useState<Record[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<string>("All");

  const { showToast } = useToast();
  const fetch = () => {
    setLoading(true);
    api.get("/attendance").then((r) => setRecords(r.data)).catch(() => {
      showToast("Failed to load attendance", 'error');
    }).finally(() => setLoading(false));
  };
  useEffect(fetch, []);

  const filtered =
    filter === "All"
      ? records
      : records.filter((r) => (filter === "Today" ? true : true));

  const columns = [
    { header: "ID", accessor: "id" },
    { header: "Employee", accessor: "employee_id" },
    { header: "Time", accessor: "timestamp" },
    { header: "Type", accessor: "type" },
    { header: "Conf.", accessor: "confidence" },
    { header: "Device", accessor: "device_id" },
  ];

  const chips = [
    { label: "All", active: filter === "All", onClick: () => setFilter("All") },
    { label: "Today", active: filter === "Today", onClick: () => setFilter("Today") },
    { label: "This Week", active: filter === "This Week", onClick: () => setFilter("This Week") },
  ];

  const handleExport = () => {
    window.open("/attendance/export.csv", "_blank");
    showToast("Exporting CSV", 'info');
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Attendance</h2>
        <MotionButton className="flex items-center gap-1 bg-accent text-white" onClick={handleExport}>
          <Download size={16} /> Export
        </MotionButton>
      </div>
      <FilterChips chips={chips} />
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        {loading ? (
          <div className="space-y-3">
            <Skeleton className="h-10" />
            <Skeleton className="h-10" />
            <Skeleton className="h-10" />
          </div>
        ) : filtered.length === 0 ? (
          <p className="text-center text-gray-500 py-6">No attendance records</p>
        ) : (
          <DataTable columns={columns} data={filtered} />
        )}
      </motion.div>
    </div>
  );
};

export default Attendance;
