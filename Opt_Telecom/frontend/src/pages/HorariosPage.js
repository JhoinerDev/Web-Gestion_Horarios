// src/pages/HorariosPage.js
import React from 'react';
import { Box, Typography } from '@mui/material'; // Asegúrate de estas importaciones

const HorariosPage = () => { // Cambia el nombre del componente a HorariosPage
    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>Gestión de Horarios</Typography>
            <p>Este es el contenido principal de la sección de Horarios.</p>
            <p>Aquí se integrará el formulario para añadir horarios y la vista de calendario semanal.</p>
        </Box>
    );
};
export default HorariosPage;