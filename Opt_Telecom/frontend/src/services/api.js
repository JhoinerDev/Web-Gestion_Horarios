// frontend/src/services/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/', // ¡IMPORTANTE! Asegúrate de que esta URL sea la de tu backend Django
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;