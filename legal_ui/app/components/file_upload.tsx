'use client';

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

const FileUpload = () => {
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    const formData = new FormData();
    formData.append('file', file);

    setIsLoading(true);
    setMessage(`Uploading and processing ${file.name}...`);

    try {
      const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/upload/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setMessage(`Template created successfully! (ID: ${response.data.template_id})`);
    } catch (error: any) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
  });

  return (
    <div className="w-full max-w-2xl mx-auto my-10">
      <h2 className="text-3xl font-bold mb-6">1. Teach the AI a New Document</h2>

      <div
        {...getRootProps()}
        className={`upload-area ${isDragActive ? 'border-blue-500 bg-blue-50' : ''}`}
      >
        <input {...getInputProps()} />
        {isDragActive ? (
          <p>Drop your document here...</p>
        ) : (
          <p>Drag and drop a <b>.docx</b> or <b>.pdf</b> file here, or click to select</p>
        )}
      </div>

      {message && (
        <div
          className={`message-box ${
            isLoading
              ? 'message-loading'
              : message.startsWith('....')
              ? 'message-error'
              : 'message-success'
          }`}
        >
          {message}
        </div>
      )}
    </div>
  );
};

export default FileUpload;
