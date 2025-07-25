import React, { useState, useEffect } from 'react';
import { keywordAPI } from '../services/api';
import ScrapingButton from './ScrapingButton';
import SessionManager from '../utils/SessionManager';
import './KeywordInput.css';

const KeywordInput = () => {
  const [mainKeyword, setMainKeyword] = useState('');
  const [keywords, setKeywords] = useState(['', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [savedKeywords, setSavedKeywords] = useState([]);
  const [currentBatchId, setCurrentBatchId] = useState(null);
  const [showScraping, setShowScraping] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [sessionRestored, setSessionRestored] = useState(false);

  useEffect(() => {
    // Restore session on component mount
    restoreSession();
    fetchSavedKeywords();
  }, []);

  const restoreSession = async () => {
    try {
      const session = SessionManager.getManualSession();
      
      if (session && session.keywordId) {
        console.log('Restoring manual session:', session);
        
        setCurrentBatchId(session.keywordId);
        setCurrentStep(session.currentStep || 2);
        setShowScraping(true);
        setSessionRestored(true);
        
        setMessage(`Session restored! Continuing from step ${session.currentStep || 2}`);
        
        // Clear message after 3 seconds
        setTimeout(() => setMessage(''), 3000);
      }
    } catch (error) {
      console.error('Error restoring session:', error);
    }
  };

  const fetchSavedKeywords = async () => {
    try {
      const response = await keywordAPI.getAllKeywords();
      setSavedKeywords(response.data);
    } catch (error) {
      console.error('Error fetching keywords:', error);
    }
  };

  const handleKeywordChange = (index, value) => {
    const newKeywords = [...keywords];
    newKeywords[index] = value;
    setKeywords(newKeywords);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const filteredKeywords = keywords.filter(k => k.trim() !== '');
    
    if (!mainKeyword.trim()) {
      setMessage('Please enter a main keyword');
      return;
    }
    
    if (filteredKeywords.length < 4 || filteredKeywords.length > 5) {
      setMessage('Please provide 4-5 keywords');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const response = await keywordAPI.createKeywords(mainKeyword, filteredKeywords);
      const keywordId = response.data._id;
      
      setMessage('Keywords saved successfully!');
      setCurrentBatchId(keywordId);
      setShowScraping(true);
      setCurrentStep(2);
      
      // Save session
      SessionManager.saveManualSession({
        keywordId: keywordId,
        currentStep: 2,
        mainKeyword: mainKeyword,
        keywords: filteredKeywords,
        stepData: {
          1: { completed: true, data: response.data }
        }
      });
      
      // Reset form
      setMainKeyword('');
      setKeywords(['', '', '', '', '']);
      
      fetchSavedKeywords();
    } catch (error) {
      setMessage(error.response?.data?.error || 'Error saving keywords');
    } finally {
      setLoading(false);
    }
  };

  const handleScrapingComplete = (scrapedData) => {
    setCurrentStep(3);
    
    // Update session
    SessionManager.updateManualStep(currentBatchId, 3, {
      completed: true,
      data: scrapedData
    });
    
    fetchSavedKeywords();
  };

  const handleSelectBatch = (batchId) => {
    setCurrentBatchId(batchId);
    setShowScraping(true);
    setCurrentStep(2);
    
    // Save new session
    SessionManager.saveManualSession({
      keywordId: batchId,
      currentStep: 2
    });
  };

  const clearSession = () => {
    const confirmed = window.confirm(
      'Are you sure you want to clear the current session? This will lose your progress.'
    );
    
    if (!confirmed) return;
    
    SessionManager.clearManualSession();
    setCurrentBatchId(null);
    setShowScraping(false);
    setCurrentStep(1);
    setSessionRestored(false);
    setMessage('Session cleared. You can start a new workflow.');
  };

  return (
    <div className="keyword-input-container">
      {currentBatchId && (
        <div className={`session-info ${sessionRestored ? 'restored' : ''}`}>
          <div className="session-details">
            <p>📋 Active Session: {currentBatchId.substring(0, 8)}...{currentBatchId.substring(-4)}</p>
            <p>📍 Current Step: {currentStep}</p>
            {sessionRestored && <p className="session-restored">✅ Session Restored</p>}
          </div>
          <div className="session-actions">
            <button onClick={clearSession} className="clear-session">
              🗑️ Clear Session
            </button>
          </div>
        </div>
      )}

      <h2>Step 1: Enter Keywords</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="main-keyword">Main Keyword:</label>
          <input
            id="main-keyword"
            type="text"
            value={mainKeyword}
            onChange={(e) => setMainKeyword(e.target.value)}
            placeholder="e.g., Smart Weld Technology"
            required
            disabled={currentBatchId && currentStep > 1}
          />
        </div>

        <div className="form-group">
          <label>Additional Keywords (4-5):</label>
          {keywords.map((keyword, index) => (
            <input
              key={index}
              type="text"
              value={keyword}
              onChange={(e) => handleKeywordChange(index, e.target.value)}
              placeholder={`Keyword ${index + 1}`}
              className="keyword-input"
              disabled={currentBatchId && currentStep > 1}
            />
          ))}
        </div>

        <button 
          type="submit" 
          disabled={loading || (currentBatchId && currentStep > 1)}
        >
          {loading ? 'Saving...' : 'Save Keywords'}
        </button>
      </form>

      {message && (
        <div className={`message ${message.includes('success') || message.includes('restored') ? 'success' : 'error'}`}>
          {message}
        </div>
      )}

      {showScraping && currentBatchId && (
        <ScrapingButton 
          keywordId={currentBatchId}
          onScrapingComplete={handleScrapingComplete}
          currentStep={currentStep}
          onStepChange={(step) => {
            setCurrentStep(step);
            SessionManager.updateManualStep(currentBatchId, step);
          }}
        />
      )}

      {savedKeywords.length > 0 && (
        <div className="saved-keywords">
          <h3>Recent Keyword Batches</h3>
          <ul>
            {savedKeywords.map((batch) => (
              <li 
                key={batch._id} 
                onClick={() => handleSelectBatch(batch._id)}
                className={currentBatchId === batch._id ? 'active' : ''}
              >
                <div>
                  <strong>{batch.main_keyword}</strong> - {batch.keywords.join(', ')}
                  <span className="status-badge" data-status={batch.status}>
                    {batch.status || 'created'}
                  </span>
                </div>
                <span className="date">
                  {new Date(batch.created_at).toLocaleDateString()}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default KeywordInput;