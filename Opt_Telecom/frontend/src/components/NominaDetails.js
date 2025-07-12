import React from 'react';
import { Box, Typography } from '@mui/material';

const NominaDetails = () => {
    return (
        <Box>
            <Typography variant="h5">Detalles de Nómina</Typography>
            <Typography variant="body1">Aquí se mostrarán los datos de nómina de los profesores basados en los horarios asignados (ej. horas, número de cuenta).</Typography>
        </Box>
    );
};
export default NominaDetails;