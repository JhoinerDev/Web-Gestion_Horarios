// src/components/Layout.js
import React from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
    AppBar, Toolbar, Typography, Button, Box,
    Drawer, List, ListItem, ListItemButton, ListItemText, Divider
} from '@mui/material';
import { styled } from '@mui/system';

const drawerWidth = 240; // Ancho del sidebar

// Componente raíz que maneja el layout flexbox
const Root = styled(Box)({
    display: 'flex',
});

// AppBar con un z-index para que esté por encima del Drawer
const AppBarStyled = styled(AppBar)(({ theme }) => ({
    zIndex: theme.zIndex.drawer + 1,
}));

// Drawer (Sidebar) con estilo fijo
const DrawerStyled = styled(Drawer)({
    width: drawerWidth,
    flexShrink: 0,
    [`& .MuiDrawer-paper`]: {
        width: drawerWidth,
        boxSizing: 'border-box',
    },
});

// Espacio para compensar la altura de la AppBar
const ToolbarOffset = styled('div')(({ theme }) => theme.mixins.toolbar);

// Contenido principal que ocupa el espacio restante
const Main = styled(Box)(({ theme }) => ({
    flexGrow: 1,
    padding: theme.spacing(3), // Espaciado alrededor del contenido
    marginTop: '64px', // Compensa la altura fija del AppBar (por defecto en MUI)
    overflowY: 'auto', // Permite scroll si el contenido es largo
}));


const Layout = () => {
    const navigate = useNavigate(); // Hook para la navegación
    const location = useLocation(); // Hook para obtener la ruta actual

    // Determina si mostrar el sidebar de horarios.
    // Se muestra si la ruta actual comienza con '/horarios'.
    const showSidebar = location.pathname.startsWith('/horarios');

    return (
        <Root>
            {/* Barra de Navegación Superior (AppBar) */}
            <AppBarStyled position="fixed">
                <Toolbar>
                    <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
                        Sistema de Horarios Académicos
                    </Typography>
                    {/* Botones de navegación principal */}
                    <Button color="inherit" onClick={() => navigate('/profesores')}>Profesores</Button>
                    <Button color="inherit" onClick={() => navigate('/materias')}>Materias</Button>
                    <Button color="inherit" onClick={() => navigate('/aulas')}>Aulas</Button>
                    <Button color="inherit" onClick={() => navigate('/restricciones')}>Restricciones</Button>
                    <Button color="inherit" onClick={() => navigate('/horarios')}>Horarios</Button>
                    <Button color="inherit" onClick={() => navigate('/solicitudes')}>Solicitudes</Button>
                    <Button color="inherit" onClick={() => navigate('/importar-excel')}>Importar Excel</Button>
                    <Button color="inherit" onClick={() => navigate('/versiones')}>Versiones</Button>
                </Toolbar>
            </AppBarStyled>

            {/* Barra Lateral Izquierda (Drawer - se muestra condicionalmente) */}
            {showSidebar && (
                <DrawerStyled
                    variant="permanent" // Siempre visible
                >
                    <ToolbarOffset /> {/* Empuja el contenido del Drawer debajo del AppBar */}
                    <Box sx={{ overflow: 'auto' }}>
                        <List>
                            <ListItem disablePadding>
                                <ListItemButton
                                    selected={location.pathname === '/horarios'} // Resalta si es la ruta actual
                                    onClick={() => navigate('/horarios')}
                                >
                                    <ListItemText primary="Horario Principal" />
                                </ListItemButton>
                            </ListItem>
                            <ListItem disablePadding>
                                <ListItemButton
                                    selected={location.pathname === '/horarios/soa'}
                                    onClick={() => navigate('/horarios/soa')}
                                >
                                    <ListItemText primary="SOA" />
                                </ListItemButton>
                            </ListItem>
                            <ListItem disablePadding>
                                <ListItemButton
                                    selected={location.pathname === '/horarios/nomina'}
                                    onClick={() => navigate('/horarios/nomina')}
                                >
                                    <ListItemText primary="Nómina" />
                                </ListItemButton>
                            </ListItem>
                            <ListItem disablePadding>
                                <ListItemButton
                                    selected={location.pathname === '/horarios/bd'}
                                    onClick={() => navigate('/horarios/bd')}
                                >
                                    <ListItemText primary="Base de Datos" />
                                </ListItemButton>
                            </ListItem>
                        </List>
                        <Divider /> {/* Línea divisoria */}
                        {/* Puedes añadir más secciones o ListItems aquí si es necesario */}
                    </Box>
                </DrawerStyled>
            )}

            {/* Contenido Principal de la Aplicación */}
            <Main component="main" sx={{ ml: showSidebar ? `${drawerWidth}px` : 0 }}>
                <ToolbarOffset /> {/* Otro para el contenido principal para compensar el AppBar */}
                <Outlet /> {/* Aquí se renderizarán los componentes de las rutas hijas (las "páginas" actuales) */}
            </Main>
        </Root>
    );
};

export default Layout;