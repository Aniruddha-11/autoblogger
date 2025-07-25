import React, { useState, useEffect } from 'react';
import { batchAPI } from '../services/api';
import BlogPreviewModal from './BlogPreviewModal';
import './BatchMonitor.css';

const BatchMonitor = ({ jobId, onClose, isRestored }) => {
  const [status, setStatus] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [previewBlog, setPreviewBlog] = useState(null);
  const [processingStages, setProcessingStages] = useState({});

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await batchAPI.getBatchStatus(jobId);
        setStatus(response);
        
        if (response.results) {
          setResults(response.results);
          
          // Update processing stages for better UX
          const stages = {};
          response.results.forEach(result => {
            if (result.status === 'processing') {
              stages[result.main_keyword] = getProcessingStage(response.current_keyword, result.main_keyword);
            }
          });
          setProcessingStages(stages);
        }
        
        // Stop auto-refresh if job is complete
        if (['completed_successfully', 'completed_with_errors', 'failed'].includes(response.status)) {
          setAutoRefresh(false);
        }
        
        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.error || 'Error fetching status');
        setLoading(false);
      }
    };

    fetchStatus();

    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchStatus, 3000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [jobId, autoRefresh]);

  const getProcessingStage = (currentKeyword, resultKeyword) => {
    if (currentKeyword === resultKeyword) {
      return 'active';
    }
    return 'waiting';
  };

  const getProcessingStageText = (stage, status) => {
    if (status === 'success') return 'Completed';
    if (status === 'failed') return 'Failed';
    
    switch (stage) {
      case 'active':
        return 'Generating Blog...';
      case 'waiting':
        return 'In Queue';
      default:
        return 'Pending';
    }
  };

  const getProcessingIcon = (stage, status) => {
    if (status === 'success') return '✅';
    if (status === 'failed') return '❌';
    
    switch (stage) {
      case 'active':
        return <div className="spinner-inline"></div>;
      case 'waiting':
        return '⏳';
      default:
        return '⏸️';
    }
  };

  // ... existing utility functions (getStatusColor, getStatusIcon, etc.) ...

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed_successfully': return '#28a745';
      case 'completed_with_errors': return '#ffc107';
      case 'failed': return '#dc3545';
      case 'processing': return '#007bff';
      default: return '#6c757d';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed_successfully': return '✅';
      case 'completed_with_errors': return '⚠️';
      case 'failed': return '❌';
      case 'processing': return <div className="spinner-inline"></div>;
      default: return '⏳';
    }
  };

  const formatStatus = (status) => {
    return status.replace(/_/g, ' ').toUpperCase();
  };

  const downloadResults = () => {
    const csvContent = results.map(result => [
      result.main_keyword,
      result.status,
      result.keyword_id || '',
      result.error || '',
      result.completed_at || result.failed_at || ''
    ]).join('\n');
    
    const blob = new Blob([`Main Keyword,Status,Keyword ID,Error,Timestamp\n${csvContent}`], 
      { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `batch_results_${jobId}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const downloadBlog = async (keywordId, format, filename) => {
    try {
      const blob = await batchAPI.downloadBatchBlog(keywordId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      alert(`Error downloading blog: ${error.response?.data?.error || error.message}`);
    }
  };

  const previewBlogContent = async (keywordId, keyword) => {
    try {
      const response = await batchAPI.previewBatchBlog(keywordId);
      setPreviewBlog({
        ...response,
        keyword: keyword,
        keywordId: keywordId
      });
    } catch (error) {
      alert(`Error loading preview: ${error.response?.data?.error || error.message}`);
    }
  };

  if (loading) {
    return (
      <div className="batch-monitor-container">
        <div className="loading-status">
          <div className="spinner-large"></div>
          <p>Loading batch job status...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="batch-monitor-container">
        <div className="error-status">
          <h3>❌ Error Loading Status</h3>
          <p>{error}</p>
          <button onClick={onClose} className="close-btn">Close</button>
        </div>
      </div>
    );
  }

  return (
    <div className="batch-monitor-container">
      <div className="batch-header">
        <div className="header-content">
          <h2>📊 Batch Processing Monitor</h2>
          <button onClick={onClose} className="close-btn">✕</button>
        </div>
        <p className="job-id">Job ID: {jobId}</p>
        {isRestored && (
          <div className="restored-indicator">
            <span>🔄 Session Restored</span>
          </div>
        )}
      </div>

      <div className="status-overview">
        <div className="status-card main-status" style={{ borderColor: getStatusColor(status?.status) }}>
          <div className="status-icon">
            {typeof getStatusIcon(status?.status) === 'string' ? 
              getStatusIcon(status?.status) : 
              <div className="icon-with-spinner">{getStatusIcon(status?.status)}</div>
            }
          </div>
          <div className="status-info">
            <h3>{formatStatus(status?.status || 'unknown')}</h3>
            <p>Current Status</p>
          </div>
        </div>

        <div className="progress-grid">
          <div className="progress-card">
            <div className="progress-number">{status?.total_keywords || 0}</div>
            <div className="progress-label">Total Keywords</div>
          </div>
          <div className="progress-card success">
            <div className="progress-number">{status?.processed || 0}</div>
            <div className="progress-label">Completed</div>
          </div>
          <div className="progress-card error">
            <div className="progress-number">{status?.failed || 0}</div>
            <div className="progress-label">Failed</div>
          </div>
          <div className="progress-card">
            <div className="progress-number">{status?.progress_percentage || 0}%</div>
            <div className="progress-label">Progress</div>
          </div>
        </div>
      </div>

      {status?.progress_percentage !== undefined && (
        <div className="progress-bar-container">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ 
                width: `${status.progress_percentage}%`,
                backgroundColor: getStatusColor(status.status)
              }}
            ></div>
          </div>
          <p className="progress-text">{status.progress_percentage}% Complete</p>
        </div>
      )}

      {status?.current_keyword && status?.status === 'processing' && (
        <div className="current-processing">
          <h4>🔄 Currently Processing:</h4>
          <div className="current-keyword-container">
            <div className="processing-spinner">
              <div className="spinner-medium"></div>
            </div>
            <div className="current-keyword-info">
              <div className="current-keyword">{status.current_keyword}</div>
              <div className="processing-stage">Generating comprehensive blog content...</div>
            </div>
          </div>
          
          <div className="processing-steps">
            <div className="step-indicator">
              <div className="step active">Keywords ✓</div>
              <div className="step active">Scraping ✓</div>
              <div className="step active">Images ✓</div>
              <div className="step processing">
                <span>Blog Generation</span>
                <div className="step-spinner"></div>
              </div>
              <div className="step pending">Image Integration</div>
              <div className="step pending">Metadata</div>
            </div>
          </div>
        </div>
      )}

      {results.length > 0 && (
        <div className="results-section">
          <div className="results-header">
            <h3>📋 Processing Results</h3>
            <button onClick={downloadResults} className="download-results-btn">
              📥 Download Results CSV
            </button>
          </div>
          
          <div className="results-table-container">
            <table className="results-table">
              <thead>
                <tr>
                  <th>Keyword</th>
                  <th>Status</th>
                  <th>Progress</th>
                  <th>Blog ID</th>
                  <th>Timestamp</th>
                  <th>Actions</th>
                  <th>Error</th>
                </tr>
              </thead>
              <tbody>
                {results.map((result, index) => (
                  <tr key={index} className={result.status}>
                    <td className="keyword-cell">{result.main_keyword}</td>
                    <td className="status-cell">
                      <span className={`status-badge ${result.status}`}>
                        {getProcessingIcon(processingStages[result.main_keyword], result.status)}
                        <span className="status-text">{result.status}</span>
                      </span>
                    </td>
                    <td className="progress-cell">
                      <div className="progress-text-small">
                        {getProcessingStageText(processingStages[result.main_keyword], result.status)}
                      </div>
                    </td>
                    <td className="id-cell">
                      {result.keyword_id ? (
                        <code>{result.keyword_id.substring(0, 8)}...</code>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="time-cell">
                      {result.completed_at || result.failed_at ? 
                        new Date(result.completed_at || result.failed_at).toLocaleString() : 
                        '-'
                      }
                    </td>
                    <td className="actions-cell">
                      {result.status === 'success' && result.keyword_id ? (
                        <div className="blog-actions">
                          <button
                            onClick={() => previewBlogContent(result.keyword_id, result.main_keyword)}
                            className="action-btn preview-btn"
                            title="Preview Blog"
                          >
                            👁️
                          </button>
                          <button
                            onClick={() => downloadBlog(result.keyword_id, 'html', result.main_keyword.replace(/\s+/g, '-'))}
                            className="action-btn download-btn"
                            title="Download HTML"
                          >
                            📄
                          </button>
                          <button
                            onClick={() => downloadBlog(result.keyword_id, 'txt', result.main_keyword.replace(/\s+/g, '-'))}
                            className="action-btn download-btn"
                            title="Download Text"
                          >
                            📝
                          </button>
                          <button
                            onClick={() => downloadBlog(result.keyword_id, 'json', result.main_keyword.replace(/\s+/g, '-'))}
                            className="action-btn download-btn"
                            title="Download JSON"
                          >
                            📊
                          </button>
                        </div>
                      ) : result.status === 'processing' || (status?.current_keyword === result.main_keyword && status?.status === 'processing') ? (
                        <div className="processing-indicator">
                          <div className="spinner-small"></div>
                          <span>Processing...</span>
                        </div>
                      ) : (
                        <span className="no-actions">-</span>
                      )}
                    </td>
                    <td className="error-cell">
                      {result.error ? (
                        <span className="error-text" title={result.error}>
                          {result.error.length > 30 ? 
                            result.error.substring(0, 30) + '...' : 
                            result.error
                          }
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {autoRefresh && (
        <div className="auto-refresh-indicator">
          <div className="refresh-spinner"></div>
          <span>Auto-refreshing every 3 seconds...</span>
        </div>
      )}

      {!autoRefresh && status && (
        <div className="final-summary">
          <h3>🎉 Batch Processing Complete!</h3>
          <div className="summary-stats">
            <p>✅ Successfully processed: <strong>{status.processed}</strong> keyword sets</p>
            {status.failed > 0 && (
              <p>❌ Failed: <strong>{status.failed}</strong> keyword sets</p>
            )}
            <p>📊 Completed at: <strong>{status.updated_at ? 
              new Date(status.updated_at).toLocaleString() : 'N/A'}</strong></p>
          </div>
          
          {status.processed > 0 && (
            <div className="bulk-download-section">
              <h4>📦 Bulk Download Options</h4>
              <p>Individual blog downloads are available in the results table above.</p>
            </div>
          )}
        </div>
      )}

      {previewBlog && (
        <BlogPreviewModal
          blog={previewBlog}
          onClose={() => setPreviewBlog(null)}
          onDownload={(format) => downloadBlog(previewBlog.keywordId, format, previewBlog.keyword.replace(/\s+/g, '-'))}
        />
      )}
    </div>
  );
};

export default BatchMonitor;