// src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';

// Importa los componentes de Material-UI necesarios para las rutas 404
import { Box, Typography, Button } from '@mui/material';

// Importa las "páginas" o "vistas" de tu aplicación
import ProfesoresPage from './pages/ProfesoresPage';
import MateriasPage from './pages/MateriasPage';
import AulasPage from './pages/AulasPage';
import RestriccionesPage from './pages/RestriccionesPage';
import SolicitudesPage from './pages/SolicitudesPage';
import ImportarExcelPage from './pages/ImportarExcelPage';
import VersionesPage from './pages/VersionesPage';
import HorariosPage from './pages/HorariosPage'; // ¡Importamos el componente de página de Horarios!


// Importa los componentes para las secciones del sidebar (SOA, Nómina, BD)
import SOADetails from './components/SOADetails';
import NominaDetails from './components/NominaDetails';
import BDDetails from './components/BDDetails';

// NOTA: El componente HorariosPageContent ya NO se define aquí.
// Su contenido se ha movido a src/pages/HorariosPage.js.

function App() {
    return (
        <Router>
            <Routes>
                {/* La ruta principal '/' usa el componente Layout */}
                <Route path="/" element={<Layout />}>
                    {/* Redirigir la ruta raíz a /horarios como página de inicio */}
                    <Route index element={<Navigate to="/horarios" replace />} />

                    {/* Rutas para las páginas principales */}
                    <Route path="profesores" element={<ProfesoresPage />} />
                    <Route path="materias" element={<MateriasPage />} />
                    <Route path="aulas" element={<AulasPage />} />
                    <Route path="restricciones" element={<RestriccionesPage />} />
                    <Route path="solicitudes" element={<SolicitudesPage />} />
                    <Route path="importar-excel" element={<ImportarExcelPage />} />
                    <Route path="versiones" element={<VersionesPage />} />

                    {/* Rutas anidadas para la sección de Horarios */}
                    <Route path="horarios">
                        {/* La ruta index de /horarios ahora usa el componente HorariosPage */}
                        <Route index element={<HorariosPage />} />
                        <Route path="soa" element={<SOADetails />} />
                        <Route path="nomina" element={<NominaDetails />} />
                        <Route path="bd" element={<BDDetails />} />
                    </Route>

                    {/* Ruta para manejar cualquier otra URL no definida (404) */}
                    <Route path="*" element={
                        <Box sx={{ p: 3 }}>
                            <Typography variant="h4" gutterBottom>404 - Página no encontrada</Typography>
                            <Typography>La URL que has solicitado no existe.</Typography>
                            <Button variant="contained" onClick={() => window.location.href = '/'}>Ir a Inicio</Button>
                        </Box>
                    } />
                </Route>
            </Routes>
        </Router>
    );
}

export default App;