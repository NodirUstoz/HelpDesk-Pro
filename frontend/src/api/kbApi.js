/**
 * Knowledge Base API service.
 */
import api from './axiosConfig';

const KB_URL = '/kb';

const kbApi = {
  // ---- Categories ----
  listCategories(params = {}) {
    return api.get(`${KB_URL}/categories/`, { params });
  },

  getCategory(id) {
    return api.get(`${KB_URL}/categories/${id}/`);
  },

  createCategory(data) {
    return api.post(`${KB_URL}/categories/`, data);
  },

  updateCategory(id, data) {
    return api.patch(`${KB_URL}/categories/${id}/`, data);
  },

  deleteCategory(id) {
    return api.delete(`${KB_URL}/categories/${id}/`);
  },

  // ---- Articles ----
  listArticles(params = {}) {
    return api.get(`${KB_URL}/articles/`, { params });
  },

  getArticle(idOrSlug) {
    return api.get(`${KB_URL}/articles/${idOrSlug}/`);
  },

  createArticle(data) {
    return api.post(`${KB_URL}/articles/`, data);
  },

  updateArticle(id, data) {
    return api.patch(`${KB_URL}/articles/${id}/`, data);
  },

  deleteArticle(id) {
    return api.delete(`${KB_URL}/articles/${id}/`);
  },

  searchArticles(query, params = {}) {
    return api.get(`${KB_URL}/articles/search/`, {
      params: { q: query, ...params },
    });
  },

  getFeaturedArticles() {
    return api.get(`${KB_URL}/articles/featured/`);
  },

  getPopularArticles() {
    return api.get(`${KB_URL}/articles/popular/`);
  },

  // ---- Feedback ----
  submitFeedback(data) {
    return api.post(`${KB_URL}/feedback/`, data);
  },

  listFeedback(articleId) {
    return api.get(`${KB_URL}/feedback/`, {
      params: { article_id: articleId },
    });
  },
};

export default kbApi;
