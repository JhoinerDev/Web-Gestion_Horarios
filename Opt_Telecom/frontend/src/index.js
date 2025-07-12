// src/index.js
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css'; // Si tienes estilos globales, mantenlos aquí
import App from './App';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline'; // Para resetear los estilos CSS del navegador

// Crea un cliente de React Query
const queryClient = new QueryClient();

// Puedes definir un tema Material-UI personalizado aquí
const theme = createTheme({
    palette: {
        primary: {
            main: '#1976d2', // Un azul Material-UI estándar
        },
        secondary: {
            main: '#dc004e', // Un rojo rosado Material-UI estándar
        },
    },
    // Puedes personalizar la tipografía, espaciado, etc.
    // typography: {
    //   fontFamily: 'Roboto, Arial, sans-serif',
    // },
    // spacing: 8, // Puedes cambiar la unidad base de espaciado
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <React.StrictMode>
        <QueryClientProvider client={queryClient}>
            <ThemeProvider theme={theme}>
                <CssBaseline /> {/* Aplica un reinicio CSS básico para una apariencia consistente */}
                <App />
                <ReactQueryDevtools initialIsOpen={false} /> {/* Herramientas de desarrollo de React Query */}
            </ThemeProvider>
        </QueryClientProvider>
    </React.StrictMode>
);


