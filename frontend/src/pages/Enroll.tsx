import React, { useState, useEffect } from "react";
import api from "../api";
import { useParams } from "react-router-dom";
import UploadDropzone from "../components/UploadDropzone";
import MotionButton from "../components/MotionButton";
import { motion } from "framer-motion";
import { useToast } from "../components/ToastProvider";

const Enroll: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [dept, setDept] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);

  useEffect(() => {
    if (id && id !== "0") {
      // fetch employee details if needed
      // placeholder
    }
  }, [id]);

  const { showToast } = useToast();

  const submitEmployee = async () => {
    if (id === "0") {
      try {
        await api.post("/employees", { employee_code: code, full_name: name, department: dept });
        setMessage("Employee created successfully");
        showToast("Employee created", 'success');
        setCode("");
        setName("");
        setDept("");
      } catch (err) {
        setMessage("Failed to create employee");
        showToast("Failed to create employee", 'error');
      }
    }
  };

  const submitEnroll = async () => {
    if (!files.length) return;
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    try {
      const resp = await api.post(`/employees/${id}/enroll`, form, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (ev) => {
          if (ev.total) {
            setUploadProgress(Math.round((ev.loaded * 100) / ev.total));
          }
        },
      });
      setMessage("Images uploaded successfully");
      showToast("Images uploaded", 'success');
      setUploadProgress(0);
      setFiles([]);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      const msg = detail ? `Image upload failed: ${detail}` : "Image upload failed";
      setMessage(msg);
      showToast(msg, 'error');
      setUploadProgress(0);
    }
  };

  return (
    <div className="max-w-lg mx-auto">
      <motion.h2 className="text-2xl font-semibold mb-4">Enroll</motion.h2>
      {message && <p className="mb-4 text-center text-error">{message}</p>}
      {id === "0" && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-4"
        >
          <input
            className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-accent"
            placeholder="Full Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-accent"
            placeholder="Employee Code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
          />
          <input
            className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-accent"
            placeholder="Department"
            value={dept}
            onChange={(e) => setDept(e.target.value)}
          />
          <MotionButton
            className="w-full bg-accent text-white"
            onClick={submitEmployee}
          >
            Create Employee
          </MotionButton>
        </motion.div>
      )}
      {id !== "0" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <UploadDropzone onFilesSelected={(f) => setFiles(f)} />
          {files.length > 0 && (
            <div className="mt-4">
              <p className="mb-2">{files.length} file(s) selected</p>
              <MotionButton
                className="bg-accent text-white"
                onClick={submitEnroll}
              >
                Upload
              </MotionButton>
            </div>
          )}
          {uploadProgress > 0 && (
            <div className="mt-4">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="h-2 bg-accent rounded-full"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-sm mt-1">{uploadProgress}%</p>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
};

export default Enroll;
