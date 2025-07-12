// frontend/src/services/horarioService.js
import api from './api';

const horarioService = {
  getAllHorarios: () => api.get('horarios/'),
  getHorarioById: (id) => api.get(`horarios/${id}/`),
  createHorario: (data) => api.post('horarios/', data),
  updateHorario: (id, data) => api.put(`horarios/${id}/`, data),
  deleteHorario: (id) => api.delete(`horarios/${id}/`),
  
  // ¡CAMBIO AQUÍ! Ajustar el endpoint para la generación de horarios
  generateHorarios: () => api.post('generar-horarios/'), // Ruta correcta según tus pruebas
  
  deleteAllHorarios: () => api.delete('horarios/eliminar_horarios/'), // Revisa si esta URL es correcta en tu backend
  
  // ¡CAMBIO AQUÍ! Ajustar el endpoint para la subida de Excel
  uploadExcel: (formData) => api.post('importar-horarios-excel/', formData, { // Ruta correcta según tus pruebas
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
};

export default horarioService;