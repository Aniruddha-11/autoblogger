import React, { useState, useEffect } from 'react';
import { keywordAPI } from '../services/api';
import ScrapingButton from './ScrapingButton';
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

  useEffect(() => {
    // Load session from localStorage
    const savedSession = localStorage.getItem('currentSession');
    if (savedSession) {
      const session = JSON.parse(savedSession);
      setCurrentBatchId(session.batchId);
      setShowScraping(true);
      setCurrentStep(session.step || 1);
    }
    
    fetchSavedKeywords();
  }, []);

  useEffect(() => {
    // Save session to localStorage
    if (currentBatchId) {
      localStorage.setItem('currentSession', JSON.stringify({
        batchId: currentBatchId,
        step: currentStep
      }));
    }
  }, [currentBatchId, currentStep]);

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
      setMessage('Keywords saved successfully!');
      setCurrentBatchId(response.data._id);
      setShowScraping(true);
      setCurrentStep(2);
      
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
    fetchSavedKeywords();
  };

  const handleSelectBatch = (batchId) => {
    setCurrentBatchId(batchId);
    setShowScraping(true);
    
    // Clear any previous session and start new
    localStorage.setItem('currentSession', JSON.stringify({
      batchId: batchId,
      step: 2
    }));
    setCurrentStep(2);
  };

  const clearSession = () => {
    localStorage.removeItem('currentSession');
    setCurrentBatchId(null);
    setShowScraping(false);
    setCurrentStep(1);
  };

  return (
    <div className="keyword-input-container">
      {currentBatchId && (
        <div className="session-info">
          <p>Current Session: {currentBatchId}</p>
          <button onClick={clearSession} className="clear-session">Start New Session</button>
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
            />
          ))}
        </div>

        <button type="submit" disabled={loading || currentBatchId}>
          {loading ? 'Saving...' : 'Save Keywords'}
        </button>
      </form>

      {message && (
        <div className={`message ${message.includes('success') ? 'success' : 'error'}`}>
          {message}
        </div>
      )}

      {showScraping && currentBatchId && (
        <ScrapingButton 
          keywordId={currentBatchId}
          onScrapingComplete={handleScrapingComplete}
          currentStep={currentStep}
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