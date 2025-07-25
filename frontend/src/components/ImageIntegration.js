import React, { useState, useEffect } from 'react';
import { imageAPI, blogAPI } from '../services/api';
import MetadataGenerator from './MetadataGenerator';
import './ImageIntegration.css';

const ImageIntegration = ({ keywordId, onIntegrationComplete }) => {
  const [loading, setLoading] = useState(true);
  const [images, setImages] = useState([]);
  const [selectedImages, setSelectedImages] = useState([]);
  const [integrating, setIntegrating] = useState(false);
  const [integrationComplete, setIntegrationComplete] = useState(false);
  const [previewHtml, setPreviewHtml] = useState('');
  const [error, setError] = useState('');
  const [showMetadataGenerator, setShowMetadataGenerator] = useState(false);

  useEffect(() => {
    loadImagesAndCheckStatus();
  }, [keywordId]);

  const loadImagesAndCheckStatus = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Check if already integrated
      try {
        const statusResponse = await blogAPI.getImageIntegrationStatus(keywordId);
        if (statusResponse.data && statusResponse.data.integration_complete) {
          setIntegrationComplete(true);
          setLoading(false);
          return;
        }
      } catch (statusError) {
        console.log('No integration status yet');
      }

      // Load images
      const imageResponse = await imageAPI.getImages(keywordId);
      console.log('Image response:', imageResponse);
      
      if (imageResponse.data && imageResponse.data.images) {
        const allImages = [];
        
        // Handle the nested structure properly
        const imagesData = imageResponse.data.images;
        
        // Check if images are in the expected format
        if (imagesData.images && typeof imagesData.images === 'object') {
          Object.entries(imagesData.images).forEach(([keyword, keywordImages]) => {
            if (Array.isArray(keywordImages)) {
              keywordImages.forEach((img, idx) => {
                if (img && img.url) {
                  allImages.push({
                    url: img.url || img.thumbnail || '',
                    alt_text: img.alt_text || img.title || `${keyword} image ${idx + 1}`,
                    title: img.title || img.alt_text || '',
                    source: img.source || 'Web',
                    uniqueId: `${img.url}_${keyword}_${idx}`,
                    keyword: keyword,
                    recommended: idx === 0
                  });
                }
              });
            }
          });
        }
        
        console.log('Processed images:', allImages);
        
        if (allImages.length === 0) {
          setError('No images found. Please complete the image search step first.');
        } else {
          setImages(allImages);
          
          const recommended = allImages
            .filter(img => img.recommended)
            .slice(0, 4)
            .map(img => img.uniqueId);
          setSelectedImages(recommended);
        }
      } else {
        setError('No images found. Please complete the image search step first.');
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Error loading images:', error);
      setError(error.response?.data?.error || 'Error loading images. Please ensure image search is completed.');
      setLoading(false);
    }
  };

  const toggleImageSelection = (imageId) => {
    setSelectedImages(prev => {
      if (prev.includes(imageId)) {
        return prev.filter(id => id !== imageId);
      } else {
        if (prev.length >= 4) {
          alert('Maximum 4 images can be selected');
          return prev;
        }
        return [...prev, imageId];
      }
    });
  };

  const getImagePosition = (index) => {
    const positions = [
      'Featured Image (After Opening)',
      'Content Image 1 (After Section 2)',
      'Content Image 2 (After Section 4)',
      'CTA Background Image'
    ];
    return positions[index] || 'Additional Image';
  };

  const handleIntegration = async () => {
    setIntegrating(true);
    setError('');

    try {
      const response = await blogAPI.integrateImages(keywordId, {
        selected_images: selectedImages
      });

      console.log('Integration response:', response); // Debug log

      // Defensive data access
      const responseData = response?.data || response;
      
      if (responseData) {
        setPreviewHtml(responseData.html_preview || '');
        setIntegrationComplete(true);
        
        if (onIntegrationComplete) {
          onIntegrationComplete(responseData);
        }
      } else {
        throw new Error('No response data received from server');
      }
    } catch (error) {
      console.error('Integration error:', error);
      console.error('Full error object:', error.response); // Additional debug info
      setError(error.response?.data?.error || error.message || 'Error integrating images');
    } finally {
      setIntegrating(false);
    }
  };

  const renderSelectedImagesPreview = () => {
    const selected = images.filter(img => selectedImages.includes(img.uniqueId));
    
    return (
      <div className="selected-images-preview">
        <h4>Selected Images Layout:</h4>
        <div className="layout-preview">
          {selected.map((img, idx) => (
            <div key={img.uniqueId} className="layout-item">
              <div className="position-label">{getImagePosition(idx)}</div>
              <img 
                src={img.url} 
                alt={img.alt_text}
                onError={(e) => {
                  e.target.src = 'https://via.placeholder.com/200x120?text=Image+Not+Found';
                }}
              />
              <p className="position-description">{img.alt_text}</p>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="image-integration-container">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading images...</p>
        </div>
      </div>
    );
  }

  if (integrationComplete) {
    return (
      <div className="integration-complete">
        <h3>✅ Image Integration Complete</h3>
        <p>Images have been successfully integrated into your blog post.</p>

        {previewHtml && (
          <div className="html-preview">
            <h4>Preview:</h4>
            <div className="preview-frame">
              <iframe 
                srcDoc={previewHtml}
                title="Blog Preview"
                width="100%"
                height="600"
                frameBorder="0"
                sandbox="allow-same-origin"
              />
            </div>
          </div>
        )}

        {!showMetadataGenerator && (
          <button 
            className="next-button"
            onClick={() => setShowMetadataGenerator(true)}
          >
            Generate Metadata (Step 6)
          </button>
        )}

        {showMetadataGenerator && (
          <MetadataGenerator 
            keywordId={keywordId}
            onComplete={(data) => {
              console.log('Blog completed:', data);
            }}
          />
        )}
      </div>
    );
  }

  return (
    <div className="image-integration-container">
      <h3>Step 5: Integrate Images into Blog</h3>
      <p>Select up to 4 images to include in your blog post. Images will be placed strategically throughout the content.</p>

      {error && (
        <div className="error-message">{error}</div>
      )}

      {images.length === 0 ? (
        <div className="no-images">
          <p>No images available. Please complete the image search step first.</p>
        </div>
      ) : (
        <>
          <div className="image-selection-grid">
            {images.map((image) => (
              <div 
                key={image.uniqueId}
                className={`image-card ${selectedImages.includes(image.uniqueId) ? 'selected' : ''}`}
                onClick={() => toggleImageSelection(image.uniqueId)}
              >
                <div className="image-number">
                  {selectedImages.includes(image.uniqueId) 
                    ? selectedImages.indexOf(image.uniqueId) + 1 
                    : ''}
                </div>
                
                <img 
                  src={image.url} 
                  alt={image.alt_text}
                  onError={(e) => {
                    e.target.src = 'https://via.placeholder.com/250x180?text=Image+Not+Found';
                  }}
                />
                
                <div className="image-details">
                  <p className="alt-text">{image.alt_text}</p>
                  <p className="keyword">Keyword: {image.keyword}</p>
                  {image.recommended && (
                    <span className="recommended-badge">Recommended</span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {selectedImages.length > 0 && renderSelectedImagesPreview()}

          <div className="integration-actions">
            <p className="selection-count">
              {selectedImages.length} of 4 images selected
            </p>
            
            <button 
              onClick={handleIntegration}
              disabled={integrating || selectedImages.length === 0}
              className="integrate-button"
            >
              {integrating ? (
                <>
                  <span className="spinner-small"></span>
                  Integrating Images...
                </>
              ) : (
                'Integrate Selected Images'
              )}
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default ImageIntegration;
