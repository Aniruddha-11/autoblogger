import React, { useState, useEffect, useMemo } from 'react';
import { imageAPI } from '../services/api';
import BlogGenerator from './BlogGenerator';
import './ImageSearch.css';

const ImageSearch = ({ keywordId, onImagesFound }) => {
  const [searching, setSearching] = useState(false);
  const [searchStatus, setSearchStatus] = useState('');
  const [error, setError] = useState('');
  const [imagesData, setImagesData] = useState(null);
  const [selectedImages, setSelectedImages] = useState([]);
  const [showBlogGenerator, setShowBlogGenerator] = useState(false);

  // dedupe or preprocess images to count unique ones
  const processedImages = useMemo(() => {
    if (!imagesData?.images?.images) return [];
    const all = Object.values(imagesData.images.images).flat();
    const seen = new Set();
    return all.filter(img => {
      const key = img.url;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [imagesData]);

  useEffect(() => {
    checkImageStatus();
  }, [keywordId]);

  const checkImageStatus = async () => {
    try {
      const response = await imageAPI.getImages(keywordId);
      if (response.data) {
        setImagesData(response.data);
        setSearchStatus('completed');
      }
    } catch {
      setSearchStatus('ready');
    }
  };

  const handleImageSearch = async () => {
    setSearching(true);
    setError('');
    setSearchStatus('Initializing image search...');

    const progressMessages = [
      'Searching for welding equipment images...',
      'Finding industrial welding photos...',
      'Collecting Smart Weld related visuals...',
      'Analyzing image relevance...',
      'Finalizing image collection...'
    ];

    progressMessages.forEach((msg, i) => {
      setTimeout(() => {
        if (i < progressMessages.length && searching) {
          setSearchStatus(msg);
        }
      }, i * 1500);
    });

    try {
      const response = await imageAPI.searchImages(keywordId);
      setImagesData(response.data);
      setSearchStatus('completed');
      setSearching(false);
      if (onImagesFound) onImagesFound(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Error during image search');
      setSearching(false);
      setSearchStatus('failed');
    }
  };

  const toggleImageSelection = (imageUrl) =>
    setSelectedImages(prev =>
      prev.includes(imageUrl)
        ? prev.filter(u => u !== imageUrl)
        : [...prev, imageUrl]
    );

  const renderImageGrid = () => {
    if (!processedImages.length) return null;
    return (
      <div className="image-grid">
        {processedImages.map((image, idx) => (
          <div
            key={idx}
            className={`image-item ${
              selectedImages.includes(image.url) ? 'selected' : ''
            }`}
            onClick={() => toggleImageSelection(image.url)}
          >
            <img
              src={image.url}
              alt={image.alt_text}
              onError={(e) => {
                e.target.src = 'https://via.placeholder.com/300x200?text=Welding+Image';
              }}
            />
            <div className="image-info">
              <p className="alt-text">{image.alt_text}</p>
              <p className="image-source">
                Source: {image.source || 'Unknown'}
              </p>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const handleBlogGenerated = (blogData) => {
    console.log('Blog generated:', blogData);
    // You might forward this to parent
  };

  if (searchStatus === 'completed' && imagesData) {
    return (
      <>
        <div className="image-search-complete">
          <h3>✅ Image Search Completed</h3>
          <div className="image-stats">
            <p>Total unique images found: {processedImages.length}</p>
            <p>Click on images to select them for your blog</p>
          </div>

          {renderImageGrid()}

          <div className="selected-count">
            Selected: {selectedImages.length} images
          </div>

          <button
            className="next-button"
            onClick={() => setShowBlogGenerator(true)}
            disabled={showBlogGenerator}
          >
            Generate Blog (Step 4)
          </button>
        </div>

        {showBlogGenerator && (
          <BlogGenerator
            keywordId={keywordId}
            selectedImages={selectedImages}
            onBlogGenerated={handleBlogGenerated}
          />
        )}
      </>
    );
  }

  return (
    <div className="image-search-container">
      <h3>Step 3: Search for Images</h3>
      <p>Find relevant welding industry images for your blog content.</p>

      {error && <div className="error-message">{error}</div>}

      {searching ? (
        <div className="searching-progress">
          <div className="spinner" />
          <p>{searchStatus}</p>
        </div>
      ) : (
        <button
          onClick={handleImageSearch}
          className="search-images-button"
          disabled={searchStatus === 'completed'}
        >
          Search Images
        </button>
      )}

      <div className="api-note">
        <p>
          <strong>Note:</strong> For best results, add your Brave API key in
          the backend .env file. Without it, generic welding images will be
          used.
        </p>
      </div>
    </div>
  );
};

export default ImageSearch;
