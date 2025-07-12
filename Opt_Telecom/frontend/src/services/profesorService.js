// frontend/src/services/profesorService.js
import api from './api';

const profesorService = {
  getAllProfesores: () => api.get('profesores/'),
  getProfesorById: (id) => api.get(`profesores/${id}/`),
  createProfesor: (data) => api.post('profesores/', data),
  updateProfesor: (id, data) => api.put(`profesores/${id}/`, data),
  deleteProfesor: (id) => api.delete(`profesores/${id}/`),
};

export default profesorService;