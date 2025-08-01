import React, { useState, useEffect } from 'react';
import { blogAPI } from '../services/api';
import './MetadataGenerator.css';

const MetadataGenerator = ({ keywordId, onComplete }) => {
  const [generating, setGenerating] = useState(false);
  const [metadata, setMetadata] = useState(null);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const [finalHtml, setFinalHtml] = useState('');

  useEffect(() => {
    loadBlogSummary();
  }, [keywordId]);

  const loadBlogSummary = async () => {
    try {
      const response = await blogAPI.getBlogSummary(keywordId);
      setSummary(response.data.data);
    } catch (error) {
      console.error('Error loading blog summary:', error);
    }
  };

  const handleGenerateMetadata = async () => {
    setGenerating(true);
    setError('');

    console.log('Starting metadata generation for keyword:', keywordId);

    try {
      const response = await blogAPI.generateMetadata(keywordId);
      console.log('Metadata response:', response);

      if (response.data && response.data.metadata) {
        setMetadata(response.data.metadata);
        setFinalHtml(response.data.final_html);

        // Reload summary
        loadBlogSummary();

        if (onComplete) {
          onComplete(response.data);
        }
      } else {
        console.error('Invalid response structure:', response);
        setError('Invalid response from server');
      }
    } catch (error) {
      console.error('Metadata generation error:', error);
      const errorMessage = error.response?.data?.error || error.message || 'Error generating metadata';
      setError(errorMessage);
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async (format = 'html') => {
    try {
      const response = await fetch(`/api/download-blog/${keywordId}/${format}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${metadata?.slug || 'blog'}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      setError(`Error downloading blog as ${format}`);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Copied to clipboard!');
    });
  };

  if (metadata) {
    return (
      <div className="metadata-complete">
        <h3>✅ Blog Ready for Publishing!</h3>

        <div className="metadata-summary">
          <h4>Blog Metadata</h4>

          <div className="metadata-item">
            <label>Post Title:</label>
            <div className="metadata-value">
              {metadata.post_title}
              <button className="copy-btn" onClick={() => copyToClipboard(metadata.post_title)}>📋</button>
            </div>
          </div>

          <div className="metadata-item">
            <label>Meta Title (SEO):</label>
            <div className="metadata-value">
              {metadata.meta_title}
              <button className="copy-btn" onClick={() => copyToClipboard(metadata.meta_title)}>📋</button>
            </div>
          </div>

          <div className="metadata-item">
            <label>URL Slug:</label>
            <div className="metadata-value">
              /{metadata.slug}
              <button className="copy-btn" onClick={() => copyToClipboard(metadata.slug)}>📋</button>
            </div>
          </div>

          <div className="metadata-item">
            <label>Meta Description:</label>
            <div className="metadata-value">
              {metadata.meta_description}
              <button className="copy-btn" onClick={() => copyToClipboard(metadata.meta_description)}>📋</button>
            </div>
          </div>

          <div className="metadata-item">
            <label>Post Description:</label>
            <div className="metadata-value">
              {metadata.post_description}
              <button className="copy-btn" onClick={() => copyToClipboard(metadata.post_description)}>📋</button>
            </div>
          </div>

          <div className="metadata-item">
            <label>Featured Image:</label>
            <div className="metadata-value">
              {metadata.featured_image?.url ? (
                <div>
                  <img src={metadata.featured_image.url} alt={metadata.featured_image.alt_text} style={{ maxWidth: '200px', marginBottom: '10px' }} />
                  <br />
                  <small>{metadata.featured_image.url}</small>
                  <button className="copy-btn" onClick={() => copyToClipboard(metadata.featured_image.url)}>📋</button>
                </div>
              ) : (
                'No featured image'
              )}
            </div>
          </div>

          <div className="metadata-item">
            <label>Keywords:</label>
            <div className="metadata-value">
              {metadata.meta_keywords}
            </div>
          </div>
        </div>

        {summary && (
          <div className="blog-stats">
            <h4>Blog Statistics</h4>
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-label">Word Count</span>
                <span className="stat-value">{summary.word_count}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Images</span>
                <span className="stat-value">{summary.images_integrated}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Quality Enhanced</span>
                <span className="stat-value">{summary.quality_enhanced ? 'Yes' : 'No'}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Status</span>
                <span className="stat-value ready">{summary.status}</span>
              </div>
            </div>
          </div>
        )}

        <div className="final-actions">
          <button className="preview-btn" onClick={() => setShowPreview(!showPreview)}>
            {showPreview ? 'Hide Preview' : 'Preview Blog'}
          </button>

          <button className="download-btn" onClick={() => handleDownload('html')}>
            📥 Download HTML
          </button>

          <button className="download-btn" onClick={() => handleDownload('txt')}>
            📄 Download as Text
          </button>

          <button className="download-btn" onClick={() => handleDownload('json')}>
            📊 Download Metadata JSON
          </button>

          <button className="copy-html-btn" onClick={() => copyToClipboard(finalHtml)}>
            📋 Copy HTML
          </button>
        </div>

        {showPreview && (
          <div className="blog-preview">
            <h4>Blog Preview</h4>
            <div className="preview-frame">
              <iframe
                srcDoc={finalHtml}
                title="Final Blog Preview"
                width="100%"
                height="800"
                frameBorder="0"
                sandbox="allow-same-origin"
              />
            </div>
          </div>
        )}

        <div className="success-message">
          <h4>🎉 Congratulations!</h4>
          <p>Your blog is ready to publish. You can:</p>
          <ul>
            <li>Download the HTML file and upload to your website</li>
            <li>Copy the HTML and paste into your CMS</li>
            <li>Use the metadata for SEO optimization</li>
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div className="metadata-generator-container">
      <h3>Step 6: Generate Title, Slug & Metadata</h3>
      <p>Generate SEO-optimized metadata and prepare your blog for publishing.</p>

      {error && (
        <div className="error-message">{error}</div>
      )}

      {summary && (
        <div className="pre-generation-summary">
          <h4>Current Blog Status</h4>
          <p>Word Count: {summary.word_count} words</p>
          <p>Images: {summary.images_integrated}</p>
          <p>Quality Enhanced: {summary.quality_enhanced ? 'Yes' : 'No'}</p>
        </div>
      )}

      <div className="generation-info">
        <h4>What will be generated:</h4>
        <ul>
          <li>SEO-optimized page title (50-70 characters)</li>
          <li>URL-friendly slug</li>
          <li>Meta description (150-160 characters)</li>
          <li>Meta keywords</li>
          <li>Open Graph tags for social sharing</li>
          <li>Schema.org structured data</li>
          <li>Final publish-ready HTML with all metadata</li>
        </ul>
      </div>

      <button
        onClick={handleGenerateMetadata}
        disabled={generating}
        className="generate-metadata-btn"
      >
        {generating ? (
          <>
            <span className="spinner-small"></span>
            Generating Metadata...
          </>
        ) : (
          '🚀 Generate Metadata & Finalize'
        )}
      </button>
    </div>
  );
};

export default MetadataGenerator;