import React, { useState, useEffect } from 'react';
import { blogAPI } from '../services/api';
import ImageIntegration from './ImageIntegration';
import './BlogGenerator.css';

const BlogGenerator = ({ keywordId, onBlogGenerated }) => {
  const [generating, setGenerating] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [sessionId, setSessionId] = useState(null);
  const [blogData, setBlogData] = useState({});
  const [error, setError] = useState('');
  const [existingBlog, setExistingBlog] = useState(null);
  const [showImageIntegration, setShowImageIntegration] = useState(false);

  const steps = [
    { id: 'start', name: 'Start Generation', action: 'start' },
    { id: 'title_tag', name: 'Generate Title Tag', action: 'step' },
    { id: 'h1_heading', name: 'Generate H1 Heading', action: 'step' },
    { id: 'opening_paragraph', name: 'Generate Opening Paragraph', action: 'step' },
    { id: 'subheadings', name: 'Generate Subheadings', action: 'step' },
    { id: 'content_sections', name: 'Generate Content Sections', action: 'step' },
    { id: 'cta', name: 'Generate Call to Action', action: 'step' },
    { id: 'conclusion', name: 'Generate Conclusion', action: 'step' },
    { id: 'quality_check', name: 'Quality Check & Enhancement', action: 'step' },
    { id: 'finalize', name: 'Finalize Blog', action: 'step' }
  ];

  useEffect(() => {
    checkExistingBlog();
  }, [keywordId]);

  const checkExistingBlog = async () => {
    try {
      const response = await blogAPI.getBlog(keywordId);
      if (response.data) {
        setExistingBlog(response.data);
        setCurrentStep(steps.length);
      }
    } catch (error) {
      // No existing blog
    }
  };

  const handleNextStep = async () => {
    setGenerating(true);
    setError('');

    try {
      const step = steps[currentStep];

      if (step.action === 'start') {
        const response = await blogAPI.startBlogGeneration(keywordId);
        setSessionId(response.session_id);
        setCurrentStep(1);
      } else {
        const response = await blogAPI.generateBlogStep(keywordId, {
          step: step.id,
          session_id: sessionId
        });

        if (response.result) {
          setBlogData(prev => ({
            ...prev,
            ...response.result
          }));
        }

        if (step.id === 'finalize') {
          setExistingBlog(response.result.blog);
          if (onBlogGenerated) {
            onBlogGenerated(response.result.blog);
          }
        }

        setCurrentStep(currentStep + 1);
      }
    } catch (error) {
      setError(error.response?.data?.error || 'Error during generation');
    } finally {
      setGenerating(false);
    }
  };

  const renderStepContent = () => {
    if (currentStep === 0) {
      return (
        <div className="step-content">
          <h4>Ready to Generate Blog</h4>
          <p>Click "Start Generation" to begin creating your blog post step by step.</p>
        </div>
      );
    }

    const completedSteps = Object.entries(blogData);
    if (completedSteps.length === 0) return null;

    return (
      <div className="step-content">
        {blogData.title && (
          <div className="generated-section">
            <h4>Title Tag:</h4>
            <p className="generated-text">{blogData.title}</p>
          </div>
        )}

        {blogData.h1 && (
          <div className="generated-section">
            <h4>H1 Heading:</h4>
            <h1 className="generated-h1">{blogData.h1}</h1>
          </div>
        )}

        {blogData.opening_paragraph && (
          <div className="generated-section">
            <h4>Opening Paragraph:</h4>
            <p className="generated-text">{blogData.opening_paragraph}</p>
          </div>
        )}

        {blogData.subheadings && (
          <div className="generated-section">
            <h4>Subheadings:</h4>
            <ol>
              {blogData.subheadings.map((subheading, idx) => (
                <li key={idx}>{subheading}</li>
              ))}
            </ol>
          </div>
        )}

        {blogData.content_sections && (
          <div className="generated-section">
            <h4>Content Sections:</h4>
            {blogData.content_sections.map((content, idx) => (
              <div key={idx} className="content-preview">
                <h5>{blogData.subheadings[idx]}</h5>
                <p className="generated-text">{content}</p>
              </div>
            ))}
          </div>
        )}

        {blogData.cta && (
          <div className="generated-section">
            <h4>Call to Action:</h4>
            <div className="cta-preview">
              <p className="generated-text">{blogData.cta}</p>
            </div>
          </div>
        )}

        {blogData.conclusion && (
          <div className="generated-section">
            <h4>Conclusion:</h4>
            <p className="generated-text">{blogData.conclusion}</p>
          </div>
        )}

        {/* ✅ Enhanced Quality Report Section */}
        {blogData.quality_report && (
          <div className="generated-section quality-report">
            <h4>Quality Check Report:</h4>
            <div className="quality-metrics">
              <p><strong>Topic Complexity:</strong> {blogData.topic_complexity?.toUpperCase()}</p>
              <p><strong>Target Word Range:</strong> {blogData.target_range}</p>
              <p>
                <strong>Current Word Count:</strong> {blogData.quality_report.word_count}
                {blogData.quality_report.word_count_met ? ' ✅' : ' ❌'}
              </p>

              <div className="keyword-analysis">
                <p><strong>Keyword Usage Analysis:</strong></p>
                <ul>
                  {Object.entries(blogData.quality_report.keyword_usage).map(([keyword, count]) => (
                    <li key={keyword}>
                      <span className="keyword-name">{keyword}:</span> 
                      <span className={count > 0 ? 'used' : 'missing'}>
                        {count} times {count > 0 ? '✅' : '❌'}
                      </span>
                      {blogData.quality_report.keyword_density && (
                        <span className="density">
                          ({blogData.quality_report.keyword_density[keyword]?.toFixed(2)}% density)
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>

              {blogData.enhancement_done && (
                <div className="enhancement-summary">
                  <p className="enhancement-message">✨ Content Enhanced Successfully!</p>
                  <p><strong>Final Word Count:</strong> {blogData.final_word_count} words</p>
                  <p className="quality-score">
                    Content Quality Score: {blogData.enhanced_report?.content_quality_score || 'N/A'}/100
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  if (existingBlog && currentStep >= steps.length) {
    return (
      <>
        <div className="blog-generator-complete">
          <h3>✅ Blog Generated Successfully</h3>
          <div className="blog-preview">
            <h4>{existingBlog.title}</h4>
            <p>Created at: {new Date(existingBlog.created_at).toLocaleString()}</p>
            <p>Word Count: {existingBlog.word_count || 'N/A'} words</p>
            <div className="blog-actions">
              <button 
                onClick={() => {
                  setCurrentStep(0);
                  setExistingBlog(null);
                  setBlogData({});
                }}
                className="regenerate-button"
              >
                Generate New Version
              </button>
              <button 
                className="next-button"
                onClick={() => setShowImageIntegration(true)}
                disabled={showImageIntegration}
              >
                Add Images (Step 5)
              </button>
            </div>
          </div>
        </div>
        
        {showImageIntegration && (
          <ImageIntegration 
            keywordId={keywordId}
            onIntegrationComplete={(data) => {
              console.log('Images integrated:', data);
            }}
          />
        )}
      </>
    );
  }

  return (
    <div className="blog-generator-container">
      <h3>Step 4: Generate Blog Content</h3>

      <div className="progress-indicator">
        {steps.map((step, idx) => (
          <div 
            key={step.id} 
            className={`progress-step ${idx < currentStep ? 'completed' : ''} ${idx === currentStep ? 'active' : ''}`}
          >
            <div className="step-number">{idx + 1}</div>
            <div className="step-name">{step.name}</div>
          </div>
        ))}
      </div>

      {error && <div className="error-message">{error}</div>}

      {renderStepContent()}

      {currentStep < steps.length && (
        <div className="step-actions">
          <button 
            onClick={handleNextStep}
            disabled={generating}
            className="next-step-button"
          >
            {generating ? (
              <>
                <span className="spinner-small"></span>
                Generating...
              </>
            ) : (
              `Next: ${steps[currentStep].name}`
            )}
          </button>
        </div>
      )}
    </div>
  );
};

export default BlogGenerator;