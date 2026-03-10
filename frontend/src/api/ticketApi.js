/**
 * Ticket API service.
 */
import api from './axiosConfig';

const TICKETS_URL = '/tickets';

const ticketApi = {
  // ---- Tickets ----
  list(params = {}) {
    return api.get(`${TICKETS_URL}/`, { params });
  },

  get(id) {
    return api.get(`${TICKETS_URL}/${id}/`);
  },

  create(data) {
    return api.post(`${TICKETS_URL}/`, data);
  },

  update(id, data) {
    return api.patch(`${TICKETS_URL}/${id}/`, data);
  },

  delete(id) {
    return api.delete(`${TICKETS_URL}/${id}/`);
  },

  assign(id, data) {
    return api.post(`${TICKETS_URL}/${id}/assign/`, data);
  },

  close(id) {
    return api.post(`${TICKETS_URL}/${id}/close/`);
  },

  escalate(id) {
    return api.post(`${TICKETS_URL}/${id}/escalate/`);
  },

  getMyTickets(params = {}) {
    return api.get(`${TICKETS_URL}/my_tickets/`, { params });
  },

  getUnassigned(params = {}) {
    return api.get(`${TICKETS_URL}/unassigned/`, { params });
  },

  getStats() {
    return api.get(`${TICKETS_URL}/stats/`);
  },

  // ---- Messages ----
  listMessages(ticketId, params = {}) {
    return api.get(`${TICKETS_URL}/${ticketId}/messages/`, { params });
  },

  createMessage(ticketId, data) {
    return api.post(`${TICKETS_URL}/${ticketId}/messages/`, data);
  },

  // ---- Tags / Priorities / Statuses ----
  listTags() {
    return api.get(`${TICKETS_URL}/tags/`);
  },

  createTag(data) {
    return api.post(`${TICKETS_URL}/tags/`, data);
  },

  listPriorities() {
    return api.get(`${TICKETS_URL}/priorities/`);
  },

  listStatuses() {
    return api.get(`${TICKETS_URL}/statuses/`);
  },
};

export default ticketApi;
