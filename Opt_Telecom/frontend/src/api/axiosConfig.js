// src/api/axiosConfig.js
import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000/api/', // La URL base de tu backend Django
    timeout: 10000, // 10 segundos de timeout para las peticiones
    headers: {
        'Content-Type': 'application/json',
    },
});

export default api;