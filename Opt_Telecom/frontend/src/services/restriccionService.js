// frontend/src/services/restriccionService.js
import api from './api';

const restriccionService = {
  getAllRestricciones: () => api.get('restricciones/'),
  getRestriccionById: (id) => api.get(`restricciones/${id}/`),
  createRestriccion: (data) => api.post('restricciones/', data),
  updateRestriccion: (id, data) => api.put(`restricciones/${id}/`, data),
  deleteRestriccion: (id) => api.delete(`restricciones/${id}/`),
};

export default restriccionService;