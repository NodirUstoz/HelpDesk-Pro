/**
 * Agent API service.
 */
import api from './axiosConfig';

const agentApi = {
  // ---- Agent profiles (from accounts app) ----
  listAgents(params = {}) {
    return api.get('/auth/agents/', { params });
  },

  getAgent(id) {
    return api.get(`/auth/agents/${id}/`);
  },

  setAvailability(id, availability) {
    return api.post(`/auth/agents/${id}/set_availability/`, { availability });
  },

  getAvailableAgents() {
    return api.get('/auth/agents/available/');
  },

  // ---- Skills ----
  listSkills(params = {}) {
    return api.get('/agents/skills/', { params });
  },

  createSkill(data) {
    return api.post('/agents/skills/', data);
  },

  updateSkill(id, data) {
    return api.patch(`/agents/skills/${id}/`, data);
  },

  deleteSkill(id) {
    return api.delete(`/agents/skills/${id}/`);
  },

  verifySkill(id) {
    return api.post(`/agents/skills/${id}/verify/`);
  },

  // ---- Availability schedule ----
  listAvailability(params = {}) {
    return api.get('/agents/availability/', { params });
  },

  createAvailability(data) {
    return api.post('/agents/availability/', data);
  },

  updateAvailability(id, data) {
    return api.patch(`/agents/availability/${id}/`, data);
  },

  deleteAvailability(id) {
    return api.delete(`/agents/availability/${id}/`);
  },

  getCurrentlyAvailable() {
    return api.get('/agents/availability/currently_available/');
  },

  // ---- Performance ----
  listPerformance(params = {}) {
    return api.get('/agents/performance/', { params });
  },

  getPerformanceSummary(agentId, days = 30) {
    return api.get('/agents/performance/summary/', {
      params: { agent_id: agentId, days },
    });
  },

  getLeaderboard(days = 30, limit = 10) {
    return api.get('/agents/performance/leaderboard/', {
      params: { days, limit },
    });
  },
};

export default agentApi;
