import React, { useState, useEffect } from 'react';
import { scrapingAPI } from '../services/api';
import ImageSearch from './ImageSearch';
import './ScrapingButton.css';

const ScrapingButton = ({ keywordId, onScrapingComplete, currentStep }) => {
  const [scraping, setScraping] = useState(false);
  const [scrapingStatus, setScrapingStatus] = useState('');
  const [error, setError] = useState('');
  const [scrapedData, setScrapedData] = useState(null);
  const [showImageSearch, setShowImageSearch] = useState(false);

  useEffect(() => {
    checkScrapingStatus();
  }, [keywordId]);

  useEffect(() => {
    // Show image search if we're on step 3 or higher
    if (currentStep >= 3 && scrapedData) {
      setShowImageSearch(true);
    }
  }, [currentStep, scrapedData]);

  const checkScrapingStatus = async () => {
    try {
      const response = await scrapingAPI.getScrapedData(keywordId);
      if (response.data) {
        setScrapedData(response.data);
        setScrapingStatus('completed');
        if (currentStep >= 3) {
          setShowImageSearch(true);
        }
      }
    } catch (error) {
      setScrapingStatus('ready');
    }
  };

  const handleScraping = async () => {
    setScraping(true);
    setError('');
    setScrapingStatus('Initializing scraper...');

    try {
      const progressMessages = [
        'Searching for welding industry content...',
        'Analyzing Smart Weld related articles...',
        'Collecting manufacturing insights...',
        'Processing welding methodology data...',
        'Finalizing content collection...'
      ];

      for (let i = 0; i < progressMessages.length; i++) {
        setTimeout(() => {
          if (scraping) {
            setScrapingStatus(progressMessages[i]);
          }
        }, i * 2000);
      }

      const response = await scrapingAPI.scrapeContent(keywordId);
      
      setScrapedData(response.data);
      setScrapingStatus('completed');
      setScraping(false);
      setShowImageSearch(true);
      
      if (onScrapingComplete) {
        onScrapingComplete(response.data);
      }
    } catch (error) {
      setError(error.response?.data?.error || 'Error during scraping');
      setScraping(false);
      setScrapingStatus('failed');
    }
  };

  const handleImagesFound = (imagesData) => {
    // Update session step
    const session = JSON.parse(localStorage.getItem('currentSession') || '{}');
    session.step = 4;
    localStorage.setItem('currentSession', JSON.stringify(session));
  };

  if (scrapingStatus === 'completed' && scrapedData) {
    return (
      <>
        <div className="scraping-complete">
          <h3>✅ Scraping Completed</h3>
          <div className="scraping-stats">
            <p>Total results collected: {scrapedData.content?.total_results || 0}</p>
            <p>Scraped at: {new Date(scrapedData.created_at).toLocaleString()}</p>
          </div>
        </div>
        
        {showImageSearch && (
          <ImageSearch 
            keywordId={keywordId}
            onImagesFound={handleImagesFound}
          />
        )}
      </>
    );
  }

  return (
    <div className="scraping-container">
      <h3>Step 2: Scrape Content</h3>
      <p>Click to start scraping welding industry content related to your keywords.</p>
      
      {error && (
        <div className="error-message">{error}</div>
      )}

      {scraping ? (
        <div className="scraping-progress">
          <div className="spinner"></div>
          <p>{scrapingStatus}</p>
        </div>
      ) : (
        <button 
          onClick={handleScraping} 
          className="scrape-button"
          disabled={scrapingStatus === 'completed'}
        >
          Start Scraping
        </button>
      )}
    </div>
  );
};

export default ScrapingButton;