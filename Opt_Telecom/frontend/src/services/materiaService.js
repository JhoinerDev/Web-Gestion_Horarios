// frontend/src/services/materiaService.js
import api from './api';

const materiaService = {
  getAllMaterias: () => api.get('materias/'),
  getMateriaById: (id) => api.get(`materias/${id}/`),
  createMateria: (data) => api.post('materias/', data),
  updateMateria: (id, data) => api.put(`materias/${id}/`, data),
  deleteMateria: (id) => api.delete(`materias/${id}/`),
};

export default materiaService;