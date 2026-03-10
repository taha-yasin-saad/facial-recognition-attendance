import React, { useEffect, useState } from "react";
import api from "../api";
import { Link } from "react-router-dom";
import DataTable from "../components/DataTable";
import MotionButton from "../components/MotionButton";
import { Plus } from "lucide-react";
import AvatarPlaceholder from "../components/AvatarPlaceholder";
import { motion, AnimatePresence } from "framer-motion";
import { useToast } from "../components/ToastProvider";
import Skeleton from "../components/Skeleton";

interface Employee {
  id: number;
  employee_code: string;
  full_name: string;
  department?: string;
  enrolled?: boolean;
}

const Employees: React.FC = () => {
  const [list, setList] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [newName, setNewName] = useState("");
  const [newCode, setNewCode] = useState("");

  const fetch = () => {
    setLoading(true);
    api
      .get("/employees")
      .then((r) => setList(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(fetch, []);

  const { showToast } = useToast();

  const handleCreate = async () => {
    try {
      await api.post("/employees", { full_name: newName, employee_code: newCode });
      setNewName("");
      setNewCode("");
      setShowModal(false);
      fetch();
      showToast("Employee created", 'success');
    } catch (err: any) {
      console.error(err);
      showToast("Failed to create employee", 'error');
    }
  };

  const columns = [
    {
      header: "Name",
      accessor: (row: Employee) => (
        <div className="flex items-center gap-2">
          <AvatarPlaceholder name={row.full_name} size={32} />
          <span>{row.full_name}</span>
        </div>
      ),
    },
    { header: "Code", accessor: "employee_code" },
    {
      header: "Status",
      accessor: (row: Employee) => (
        <span
          className={`px-2 py-1 rounded-full text-xs font-medium ${
            row.enrolled ? 'bg-success text-white' : 'bg-gray-200 text-gray-800'
          }`}
        >
          {row.enrolled ? 'Enrolled' : 'Not Enrolled'}
        </span>
      ),
    },
    {
      header: "Actions",
      accessor: (row: Employee) => (
        <Link to={`/admin/enroll/${row.id}`}>
          <MotionButton className="text-sm px-3 py-1 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600">
            Enroll
          </MotionButton>
        </Link>
      ),
    },
  ];

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Employees</h2>
        <MotionButton
          className="flex items-center gap-1 bg-accent text-white"
          onClick={() => setShowModal(true)}
        >
          <Plus size={16} /> New
        </MotionButton>
      </div>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        {loading ? (
          <div className="space-y-3">
            <Skeleton className="h-10" />
            <Skeleton className="h-10" />
            <Skeleton className="h-10" />
          </div>
        ) : list.length === 0 ? (
          <p className="text-center text-gray-500 py-6">No employees yet</p>
        ) : (
          <DataTable columns={columns} data={list} />
        )}
      </motion.div>

      <AnimatePresence>
        {showModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center"
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg w-full max-w-md"
            >
              <h3 className="text-lg font-semibold mb-4">Create Employee</h3>
              <div className="space-y-3">
                <input
                  className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-accent"
                  placeholder="Full Name"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                />
                <input
                  className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-accent"
                  placeholder="Code"
                  value={newCode}
                  onChange={(e) => setNewCode(e.target.value)}
                />
              </div>
              <div className="mt-4 flex justify-end gap-2">
                <MotionButton
                  className="px-4 py-2"
                  onClick={() => setShowModal(false)}
                >
                  Cancel
                </MotionButton>
                <MotionButton
                  className="px-4 py-2 bg-accent text-white"
                  onClick={handleCreate}
                >
                  Create
                </MotionButton>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Employees;
