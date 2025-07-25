import React, { useState, useRef, useEffect } from 'react';
import { batchAPI } from '../services/api';
import BatchMonitor from './BatchMonitor';
import SessionManager from '../utils/SessionManager';
import './BatchUpload.css';

const BatchUpload = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [currentJobId, setCurrentJobId] = useState(null);
  const [error, setError] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [sessionRestored, setSessionRestored] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    // Restore batch session on component mount
    restoreBatchSession();
  }, []);

  const restoreBatchSession = async () => {
    try {
      const session = SessionManager.getBatchSession();
      
      if (session && session.jobId) {
        console.log('Restoring batch session:', session);
        
        setCurrentJobId(session.jobId);
        setSessionRestored(true);
        
        // Check if the batch job is still active
        try {
          await batchAPI.getBatchStatus(session.jobId);
          // If successful, the job exists
        } catch (error) {
          // If job not found, clear the session
          console.log('Batch job no longer exists, clearing session');
          SessionManager.clearBatchSession();
          setCurrentJobId(null);
          setSessionRestored(false);
        }
      }
    } catch (error) {
      console.error('Error restoring batch session:', error);
    }
  };

  const handleFileSelect = (file) => {
    if (file && (file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
      setSelectedFile(file);
      setError('');
    } else {
      setError('Please select a valid Excel file (.xlsx or .xls)');
      setSelectedFile(null);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    handleFileSelect(file);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const file = e.dataTransfer.files[0];
    handleFileSelect(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first');
      return;
    }

    setUploading(true);
    setError('');

    try {
      const response = await batchAPI.uploadBatch(selectedFile);
      const jobId = response.job_id;
      
      setCurrentJobId(jobId);
      setSelectedFile(null);
      
      // Save batch session
      SessionManager.saveBatchSession({
        jobId: jobId,
        status: 'started',
        filename: selectedFile.name,
        totalKeywords: response.total_keywords
      });
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      setError(error.response?.data?.error || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleMonitorClose = () => {
    const confirmed = window.confirm(
      'Are you sure you want to close the monitor? The batch processing will continue in the background.'
    );
    
    if (confirmed) {
      setCurrentJobId(null);
      setSessionRestored(false);
      // Keep the session saved so user can return later
    }
  };

  const downloadTemplate = () => {
    const csvContent = `Automated Welding,smart welding,robotic welding,precision welding,welding automation
MIG Welding Technology,MIG welding process,gas metal arc welding,automated MIG,MIG welding benefits
TIG Welding Precision,TIG welding process,tungsten welding,precision TIG,TIG welding applications
Welding Quality Control,quality assurance,defect detection,inspection methods,quality standards
Industrial Welding Solutions,manufacturing welding,heavy industry,production welding,industrial automation`;
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'batch_keywords_template.csv';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  if (currentJobId) {
    return (
      <BatchMonitor 
        jobId={currentJobId} 
        onClose={handleMonitorClose}
        isRestored={sessionRestored}
      />
    );
  }

  return (
    <div className="batch-upload-container">
      {sessionRestored && (
        <div className="session-restored-banner">
          <p>🔄 Welcome back! Your batch session is ready to continue.</p>
        </div>
      )}

      <div className="batch-upload-header">
        <h2>🚀 Batch Blog Generation</h2>
        <p>Upload an Excel file with multiple keyword sets to generate blogs automatically</p>
      </div>

      {/* Rest of your existing BatchUpload component JSX */}
      <div className="template-section">
        <h3>📋 Excel File Format</h3>
        <div className="format-info">
          <p>Your Excel file should have this structure:</p>
          <table className="format-table">
            <thead>
              <tr>
                <th>Column A<br/>(Main Keyword)</th>
                <th>Column B<br/>(Keyword 1)</th>
                <th>Column C<br/>(Keyword 2)</th>
                <th>Column D<br/>(Keyword 3)</th>
                <th>Column E<br/>(Keyword 4)</th>
                <th>Column F<br/>(Keyword 5)</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>automated welding</td>
                <td>smart welding</td>
                <td>robotic welding</td>
                <td>precision welding</td>
                <td>welding automation</td>
                <td>(optional)</td>
              </tr>
              <tr>
                <td>MIG welding technology</td>
                <td>MIG welding process</td>
                <td>gas metal arc welding</td>
                <td>automated MIG</td>
                <td>MIG welding benefits</td>
                <td>(optional)</td>
              </tr>
            </tbody>
          </table>
          <button onClick={downloadTemplate} className="template-download-btn">
            📥 Download Sample Template
          </button>
        </div>
      </div>

      <div className="upload-section">
        <h3>📁 Upload Your Excel File</h3>
        
        <div 
          className={`file-drop-zone ${dragActive ? 'active' : ''} ${selectedFile ? 'has-file' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.xls"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          
          {selectedFile ? (
            <div className="file-selected">
              <div className="file-icon">📊</div>
              <div className="file-info">
                <p className="file-name">{selectedFile.name}</p>
                <p className="file-size">{(selectedFile.size / 1024).toFixed(1)} KB</p>
              </div>
            </div>
          ) : (
            <div className="file-drop-prompt">
              <div className="upload-icon">📤</div>
              <p>Drag and drop your Excel file here</p>
              <p>or <span className="click-text">click to browse</span></p>
              <small>Supports .xlsx and .xls files</small>
            </div>
          )}
        </div>

        {error && (
          <div className="error-message">{error}</div>
        )}

        <div className="upload-actions">
          {selectedFile && (
            <button 
              onClick={() => {
                setSelectedFile(null);
                if (fileInputRef.current) fileInputRef.current.value = '';
              }}
              className="clear-file-btn"
            >
              🗑️ Clear File
            </button>
          )}
          
          <button 
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
            className="upload-btn"
          >
            {uploading ? (
              <>
                <span className="spinner-small"></span>
                Starting Batch...
              </>
            ) : (
              '🚀 Start Batch Processing'
            )}
          </button>
        </div>
      </div>

      {/* Process info section remains the same */}
    </div>
  );
};

export default BatchUpload;