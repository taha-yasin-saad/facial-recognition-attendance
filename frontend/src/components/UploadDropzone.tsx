import React, { useCallback, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion } from 'framer-motion';

interface UploadDropzoneProps {
  onFilesSelected: (files: File[]) => void;
  multiple?: boolean;
}

const UploadDropzone: React.FC<UploadDropzoneProps> = ({ onFilesSelected, multiple = true }) => {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      onFilesSelected(acceptedFiles);
    },
    [onFilesSelected]
  );
  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, multiple });

  return (
    <div
      {...getRootProps()}
      className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-accent transition-colors"
    >
      <input {...getInputProps()} accept="image/*" />
      <p className="text-gray-500">
        {isDragActive ? 'Drop the files here...' : 'Drag & drop images here, or click to select'}
      </p>
    </div>
  );
};

export default UploadDropzone;
