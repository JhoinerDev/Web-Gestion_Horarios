# **Sistema de Gestión de Horarios Académicos**

Este proyecto es un sistema integral para la gestión y optimización de horarios académicos en instituciones educativas, desarrollado con un enfoque en la facilidad de uso y una interfaz moderna. El sistema permite la administración de profesores, aulas, materias, y la creación visual de horarios, así como la generación de reportes y la importación de datos desde fuentes externas.

## **🚀 Características Principales**

* **Gestión de Entidades**: Administra de forma centralizada profesores, aulas y materias.  
* **Creación de Horarios**: Interfaz intuitiva para la creación y visualización de horarios semanales.  
* Vista de Calendario Semanal: Visualización clara de los horarios asignados en un formato de calendario.  
  \*  
* Módulos de Reporte (Pendiente): Secciones dedicadas a generar informes específicos (SOA, Nómina, Base de Datos) basados en los horarios.  
  \*  
* Importación desde Excel: Funcionalidad para importar datos de horarios desde archivos Excel.  
  \*  
* **Interfaz de Usuario Profesional**: Diseño moderno y responsivo utilizando Material-UI.

## **🛠️ Tecnologías Utilizadas**

### **Frontend (React.js)**

* **React**: Biblioteca principal para la construcción de la interfaz de usuario.  
* **Material-UI (MUI)**: Framework de componentes React para un diseño Material Design.  
* **React Router DOM**: Para la gestión de rutas y navegación dentro de la aplicación.  
* **React Query (@tanstack/react-query)**: Para la gestión del estado del servidor, caché de datos y peticiones HTTP.  
* **Axios**: Cliente HTTP basado en promesas para realizar peticiones al backend.  
* **React Big Calendar**: Componente de calendario para la visualización de horarios.  
* **Moment.js**: Biblioteca para el manejo y formateo de fechas y horas.  
* **Zustand**: (Opcional, si lo implementas) Pequeño y rápido gestor de estados para React.

### **Backend (Django / Django REST Framework)**

* **Django**: Framework web de alto nivel para un desarrollo rápido y limpio.  
* **Django REST Framework (DRF)**: Para construir APIs RESTful robustas y escalables.  
* **PostgreSQL/SQLite**: Base de datos utilizada para almacenar la información (asumido).

## **📂 Estructura del Proyecto**

.  
├── backend/                  \# Carpeta del proyecto Django  
│   ├── core/  
│   │   ├── models.py         \# Definiciones de modelos de base de datos  
│   │   ├── serializers.py    \# Serializadores para la API REST  
│   │   └── views.py          \# Lógica de las vistas de la API (CRUD, importación, generación)  
│   └── ...                   \# Otros archivos de configuración de Django  
└── frontend/                 \# Carpeta del proyecto React  
    ├── public/  
    ├── src/  
    │   ├── api/              \# Configuración de Axios para las peticiones al backend  
    │   │   └── axiosConfig.js  
    │   ├── components/       \# Componentes reutilizables (Layout, detalles del sidebar, etc.)  
    │   │   ├── Layout.js     \# Componente principal de diseño con barras de navegación  
    │   │   ├── SOADetails.js  
    │   │   ├── NominaDetails.js  
    │   │   └── BDDetails.js  
    │   ├── pages/            \# Componentes que representan páginas completas de la aplicación  
    │   │   ├── HorariosPage.js \# Página principal de gestión de horarios (con formulario y calendario)  
    │   │   ├── ProfesoresPage.js  
    │   │   ├── MateriasPage.js  
    │   │   ├── AulasPage.js  
    │   │   ├── RestriccionesPage.js  
    │   │   ├── SolicitudesPage.js  
    │   │   ├── ImportarExcelPage.js  
    │   │   └── VersionesPage.js  
    │   ├── App.js            \# Configuración principal de las rutas de React  
    │   └── index.js          \# Punto de entrada de la aplicación React (configuración de tema y React Query)  
    └── package.json  
    └── ...                   \# Otros archivos de configuración del frontend (ej. .env)

## **⚙️ Configuración y Ejecución del Proyecto**

### **Requisitos**

* Node.js (v14 o superior recomendado)  
* npm (v6 o superior) o Yarn (v1.22 o superior)  
* Python (v3.8 o superior recomendado)  
* pip (gestor de paquetes de Python)

### **Pasos para el Backend (Django)**

1. **Navegar al directorio del backend:**  
   cd backend

2. **Crear y activar un entorno virtual:**  
   python \-m venv venv  
   \# En Windows:  
   \# .\\venv\\Scripts\\activate  
   \# En macOS/Linux:  
   \# source venv/bin/activate

3. **Instalar dependencias de Python:**  
   pip install \-r requirements.txt \# Asegúrate de tener un archivo requirements.txt con tus dependencias de Django y DRF

4. **Aplicar migraciones de la base de datos:**  
   python manage.py migrate

5. **Crear un superusuario (opcional, para acceder al panel de administración de Django):**  
   python manage.py createsuperuser

6. **Iniciar el servidor Django:**  
   python manage.py runserver

   El API estará disponible en http://localhost:8000/api/ (o la URL que hayas configurado en settings.py).

### **Pasos para el Frontend (React.js)**

1. **Navegar al directorio del frontend:**  
   cd frontend

2. **Instalar dependencias:**  
   npm install  
   \# o si usas yarn:  
   \# yarn install

3. Configurar Axios:  
   Asegúrate de que la URL base en frontend/src/api/axiosConfig.js apunte a tu backend de Django (normalmente http://localhost:8000/api/):  
   // frontend/src/api/axiosConfig.js  
   import axios from 'axios';

   const api \= axios.create({  
       baseURL: 'http://localhost:8000/api/', // \<-- Verifica esta URL  
       timeout: 10000,  
       headers: { 'Content-Type': 'application/json' },  
   });

   export default api;

4. **Iniciar la aplicación React:**  
   npm start  
   \# o si usas yarn:  
   \# yarn start

   La aplicación se abrirá automáticamente en tu navegador en http://localhost:3000.

## **🤝 Contribución**

¡Las contribuciones son bienvenidas\! Si deseas contribuir a este proyecto, por favor sigue estos pasos:

1. Haz un fork del repositorio.  
2. Crea una nueva rama (git checkout \-b feature/nueva-funcionalidad).  
3. Realiza tus cambios y commitea (git commit \-m 'feat: Añadir nueva funcionalidad X').  
4. Haz push a tu rama (git push origin feature/nueva-funcionalidad).  
5. Abre un Pull Request.

## **📄 Licencia**

Este proyecto está bajo la Licencia MIT. Consulta el archivo LICENSE para más detalles.

## **📧 Contacto**

Para cualquier pregunta o comentario, puedes contactar a:

* **Tu Nombre/Alias:** \[Tu Nombre o Alias Aquí\]  
* **Correo Electrónico:** \[Tu Correo Electrónico Aquí\]