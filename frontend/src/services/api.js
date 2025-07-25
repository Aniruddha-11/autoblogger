import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

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

  // ✅ New metadata endpoints
  generateMetadata: async (keywordId) => {
    const response = await api.post(`/generate-metadata/${keywordId}`);
    return response.data;
  },

  getBlogSummary: async (keywordId) => {
    const response = await api.get(`/blog-summary/${keywordId}`);
    return response.data;
  },

  downloadBlog: async (keywordId) => {
    const response = await api.get(`/download-blog/${keywordId}`, {
      responseType: 'blob',
    });
    return response.data;
  },
};

export default api;
