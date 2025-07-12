import React from 'react';
import { Box, Typography } from '@mui/material'; // Esto es correcto
const BDDetails = () => {
    return (
        <Box>
            <Typography variant="h5">Detalles de Base de Datos</Typography>
            <Typography variant="body1">Información y herramientas relacionadas con la base de datos del sistema.</Typography>
        </Box>
    );
};
export default BDDetails;