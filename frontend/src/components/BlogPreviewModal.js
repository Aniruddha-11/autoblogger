import React from 'react';
import './BlogPreviewModal.css';

const BlogPreviewModal = ({ blog, onClose, onDownload }) => {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>📄 Blog Preview: {blog.keyword}</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        
        <div className="modal-body">
          <div className="blog-metadata">
            <div className="metadata-row">
              <span className="label">Title:</span>
              <span className="value">{blog.metadata?.title || 'No title'}</span>
            </div>
            <div className="metadata-row">
              <span className="label">Slug:</span>
              <span className="value">/{blog.metadata?.slug || 'no-slug'}</span>
            </div>
            <div className="metadata-row">
              <span className="label">Word Count:</span>
              <span className="value">{blog.metadata?.word_count || 0} words</span>
            </div>
            <div className="metadata-row">
              <span className="label">Images:</span>
              <span className="value">{blog.metadata?.images_count || 0} images integrated</span>
            </div>
            <div className="metadata-row">
              <span className="label">Status:</span>
              <span className={`value status-${blog.metadata?.status}`}>
                {blog.metadata?.status || 'unknown'}
              </span>
            </div>
          </div>

          <div className="blog-preview-container">
            <h4>Blog Content Preview:</h4>
            <div className="preview-frame">
              <iframe
                srcDoc={blog.html}
                title={`Preview: ${blog.keyword}`}
                width="100%"
                height="400"
                frameBorder="0"
                sandbox="allow-same-origin"
              />
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <div className="download-options">
            <button
              onClick={() => onDownload('html')}
              className="download-option-btn html"
            >
              📄 Download HTML
            </button>
            <button
              onClick={() => onDownload('txt')}
              className="download-option-btn txt"
            >
              📝 Download Text
            </button>
            <button
              onClick={() => onDownload('json')}
              className="download-option-btn json"
            >
              📊 Download JSON
            </button>
          </div>
          <button onClick={onClose} className="close-modal-btn">
            Close Preview
          </button>
        </div>
      </div>
    </div>
  );
};

export default BlogPreviewModal;