// frontend/src/services/aulaService.js
import api from './api';

const aulaService = {
  getAllAulas: () => api.get('aulas/'),
  getAulaById: (id) => api.get(`aulas/${id}/`),
  createAula: (data) => api.post('aulas/', data),
  updateAula: (id, data) => api.put(`aulas/${id}/`, data),
  deleteAula: (id) => api.delete(`aulas/${id}/`),
};

export default aulaService;