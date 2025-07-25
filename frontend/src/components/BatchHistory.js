import React, { useState, useEffect } from 'react';
import { batchAPI } from '../services/api';
import BatchMonitor from './BatchMonitor';
import './BatchHistory.css';

const BatchHistory = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedJobId, setSelectedJobId] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    loadBatchJobs();
  }, []);

  const loadBatchJobs = async () => {
    try {
      const response = await batchAPI.getAllBatchJobs();
      setJobs(response.data);
      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.error || 'Error loading batch jobs');
      setLoading(false);
    }
  };

  const formatStatus = (status) => {
    return status.replace(/_/g, ' ').toUpperCase();
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed_successfully': return '#28a745';
      case 'completed_with_errors': return '#ffc107';
      case 'failed': return '#dc3545';
      case 'processing': return '#007bff';
      default: return '#6c757d';
    }
  };

  if (selectedJobId) {
    return (
      <BatchMonitor 
        jobId={selectedJobId} 
        onClose={() => setSelectedJobId(null)} 
      />
    );
  }

  if (loading) {
    return (
      <div className="batch-history-container">
        <div className="loading">
          <div className="spinner-large"></div>
          <p>Loading batch history...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="batch-history-container">
      <div className="history-header">
        <h2>📊 Batch Processing History</h2>
        <button onClick={loadBatchJobs} className="refresh-btn">
          🔄 Refresh
        </button>
      </div>

      {error && (
        <div className="error-message">{error}</div>
      )}

      {jobs.length === 0 ? (
        <div className="no-jobs">
          <h3>No batch jobs found</h3>
          <p>Start your first batch processing job to see it here.</p>
        </div>
      ) : (
        <div className="jobs-grid">
          {jobs.map((job) => (
            <div 
              key={job.job_id} 
              className="job-card"
              onClick={() => setSelectedJobId(job.job_id)}
            >
              <div className="job-header">
                <div className="job-id">{job.job_id}</div>
                <div 
                  className="job-status"
                  style={{ color: getStatusColor(job.status) }}
                >
                  {formatStatus(job.status)}
                </div>
              </div>
              
              <div className="job-details">
                <p><strong>File:</strong> {job.filename}</p>
                <p><strong>Keywords:</strong> {job.total_keywords}</p>
                <p><strong>Processed:</strong> {job.processed || 0}</p>
                <p><strong>Failed:</strong> {job.failed || 0}</p>
                <p><strong>Started:</strong> {new Date(job.created_at).toLocaleString()}</p>
              </div>
              
              <div className="job-progress">
                <div className="progress-bar">
                  <div 
                    className="progress-fill"
                    style={{ 
                      width: `${job.progress_percentage || 0}%`,
                      backgroundColor: getStatusColor(job.status)
                    }}
                  ></div>
                </div>
                <span className="progress-text">
                  {job.progress_percentage || 0}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default BatchHistory;