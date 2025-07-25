import axios from 'axios';

const API_BASE_URL = 'http://34.29.184.54/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const keywordAPI = {
  createKeywords: async (mainKeyword, keywords) => {
    const response = await api.post('/keywords', {
      main_keyword: mainKeyword,
      keywords: keywords,
    });
    return response.data;
  },

  getKeywordBatch: async (keywordId) => {
    const response = await api.get(`/keywords/${keywordId}`);
    return response.data;
  },

  getAllKeywords: async () => {
    const response = await api.get('/keywords');
    return response.data;
  },
};

export const scrapingAPI = {
  scrapeContent: async (keywordId) => {
    const response = await api.post(`/scrape/${keywordId}`);
    return response.data;
  },

  getScrapedData: async (keywordId) => {
    const response = await api.get(`/scraped-data/${keywordId}`);
    return response.data;
  },
};

export const imageAPI = {
  searchImages: async (keywordId) => {
    const response = await api.post(`/search-images/${keywordId}`);
    return response.data;
  },

  getImages: async (keywordId) => {
    const response = await api.get(`/images/${keywordId}`);
    return response.data;
  },
};

export const blogAPI = {
  startBlogGeneration: async (keywordId) => {
    const response = await api.post(`/generate-blog/${keywordId}/start`);
    return response.data;
  },

  generateBlogStep: async (keywordId, stepData) => {
    const response = await api.post(`/generate-blog/${keywordId}/step`, stepData);
    return response.data;
  },

  getBlog: async (keywordId) => {
    const response = await api.get(`/blog/${keywordId}`);
    return response.data;
  },

  integrateImages: async (keywordId, imageData) => {
    const response = await api.post(`/integrate-images/${keywordId}`, imageData);
    return response.data;
  },

  getImageIntegrationStatus: async (keywordId) => {
    const response = await api.get(`/image-integration-status/${keywordId}`);
    return response.data;
  },

  getBlogWithImages: async (keywordId) => {
    const response = await api.get(`/blog-with-images/${keywordId}`);
    return response.data;
  },

  // Metadata endpoints
  generateMetadata: async (keywordId) => {
    const response = await api.post(`/generate-metadata/${keywordId}`);
    return response; // Return full response, not just response.data
  },

  getBlogSummary: async (keywordId) => {
    const response = await api.get(`/blog-summary/${keywordId}`);
    return response.data;
  },

  // Download endpoints for manual mode
  downloadBlog: async (keywordId, format = 'html') => {
    const response = await api.get(`/download-blog/${keywordId}/${format}`, {
      responseType: 'blob',
    });
    return response.data;
  },
};

// Batch Processing API
export const batchAPI = {
  // Upload Excel file for batch processing
  uploadBatch: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/batch-upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 30000, // 30 second timeout for file upload
    });
    return response.data;
  },
  
  // Get batch processing status
  getBatchStatus: async (jobId) => {
    const response = await api.get(`/batch-status/${jobId}`);
    return response.data;
  },
  
  // Get batch processing results
  getBatchResults: async (jobId) => {
    const response = await api.get(`/batch-results/${jobId}`);
    return response.data;
  },
  
  // Get all batch jobs history
  getAllBatchJobs: async () => {
    const response = await api.get('/batch-jobs');
    return response.data;
  },

  // Preview individual blog from batch
  previewBatchBlog: async (keywordId) => {
    const response = await api.get(`/batch-blog-preview/${keywordId}`);
    return response.data;
  },

  // Download individual blog from batch
  downloadBatchBlog: async (keywordId, format = 'html') => {
    const response = await api.get(`/batch-download-blog/${keywordId}/${format}`, {
      responseType: 'blob',
      timeout: 30000, // 30 second timeout for downloads
    });
    return response.data;
  },

  // Bulk download all completed blogs from a batch (if implemented)
  downloadAllBatchBlogs: async (jobId, format = 'html') => {
    const response = await api.get(`/batch-download-all/${jobId}/${format}`, {
      responseType: 'blob',
      timeout: 60000, // 60 second timeout for bulk downloads
    });
    return response.data;
  },
};

// API Key Management
export const apiKeyAPI = {
  // Get current API keys status
  getApiKeys: async () => {
    const response = await api.get('/api-keys');
    return response.data;
  },

  // Update API keys
  updateApiKeys: async (apiKeys) => {
    const response = await api.post('/api-keys', {
      gemini_key: apiKeys.gemini,
      brave_key: apiKeys.brave
    });
    return response.data;
  },

  // Check API key status and quotas
  checkApiKeyStatus: async () => {
    const response = await api.get('/api-keys/status');
    return response.data;
  },

  // Test API keys
  testApiKeys: async () => {
    const response = await api.post('/api-keys/test');
    return response.data;
  }
};

// Helper function to handle API errors consistently
export const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error status
    const errorMessage = error.response.data?.error || error.response.data?.message || 'Server error';
    const statusCode = error.response.status;
    
    console.error(`API Error ${statusCode}:`, errorMessage);
    
    // Handle specific error codes
    switch (statusCode) {
      case 400:
        throw new Error(`Bad Request: ${errorMessage}`);
      case 401:
        throw new Error('Unauthorized access');
      case 403:
        throw new Error('Access forbidden');
      case 404:
        throw new Error('Resource not found');
      case 429:
        throw new Error('Too many requests. Please try again later.');
      case 500:
        throw new Error(`Server error: ${errorMessage}`);
      default:
        throw new Error(`Error ${statusCode}: ${errorMessage}`);
    }
  } else if (error.request) {
    // Network error
    console.error('Network Error:', error.request);
    throw new Error('Network error. Please check your connection.');
  } else {
    // Other error
    console.error('Error:', error.message);
    throw new Error(error.message || 'Unknown error occurred');
  }
};

// Add request interceptor for consistent error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    handleApiError(error);
    return Promise.reject(error);
  }
);

// Add request interceptor to log requests in development
if (process.env.NODE_ENV === 'development') {
  api.interceptors.request.use(
    (config) => {
      console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
      return config;
    },
    (error) => {
      console.error('Request Error:', error);
      return Promise.reject(error);
    }
  );
}

export default api;