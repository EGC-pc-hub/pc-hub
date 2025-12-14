# Documento del Proyecto

## Indicadores del proyecto

| Miembro del equipo | Horas (HH) | Commits (XX) | LoC (YY) | Test (ZZ) | Issues (II) | Work Item | Dificultad |
|---|---|---|---|---|---|---|---|
| josemgarciar | 52 | 44 | 1517 | 12 | 5 | Two-Auth Authentication (WI-89) | High |
| Petercrgz | 28 | 47 | 3276 | 22 | 4 | Comments on datasets (WI-101) | Low |
| FernandoTC18 | 56 | 28 | 2291 | 27 | 4 | Fakenodo (WI-103), Selecting backup database (WI-75) | High |
| antonioluisjf22 | 40 | 26 | 2480 | 10 | 5 | Trending Datasets (WI-100) | Medium |
| alevelmol | 44 | 18 | 1722 | 22 | 4 | Advanced Dataset Search (WI-83) | Medium |
| julrompar | 32 | 12 | 1512 | 19 | 3 | Download Counter (WI-105) | Low |
| **TOTAL** | **252** | **175** | **12798** | **112** | **25** | **Full Stack** | **H(2)/M(2)/L(2)** |

**Explicación de indicadores:**
- **Horas**: número de horas empleadas en el proyecto
- **Commits**: solo los hechos por miembros del equipo
- **LoC**: líneas producidas por el equipo (total: 12798)
- **Test**: solo los nuevos realizados por el equipo (total: 112)
- **Issues**: solo las gestionadas por el equipo (estimado: 25)
- **Work Item**: principal WI del miembro
- **Dificultad**: 2 de tipo High, 2 de tipo Medium y 2 de tipo Low

---

## Integración con otros equipos

- No se ha realizado integración con otros equipos. El proyecto realizado es de tipo single.

---

## Resumen ejecutivo
El proyecto PC-Hub representa una evolución significativa de la plataforma UVLHub, orientada a la gestión de modelos de características en formato UVL. Durante el período de desarrollo, el equipo de 6 miembros ha invertido un total de 175 horas y producido 12,798 líneas de código, generando 112 tests y gestionando 25 issues a través de un proceso de desarrollo ágil con integración continua.
PC-Hub es un repositorio web para modelos de características que integra principios de Ciencia Abierta, permitiendo a investigadores y desarrolladores compartir, versionar y analizar modelos de características de manera colaborativa. La plataforma se construye sobre una arquitectura modular basada en Flask (Python), con integración de Zenodo para publicación académica y Fakenodo para entornos de testing.
El equipo ha implementado seis funcionalidades principales de alta complejidad: autenticación de dos factores (WI-89), sistema de comentarios en datasets (WI-101), servicio Fakenodo para simulación de Zenodo (WI-103), selección de base de datos para backup (WI-75), datasets en tendencia (WI-100), búsqueda avanzada de datasets (WI-83) y contador de descargas (WI-105). Estas funcionalidades responden a necesidades reales de la comunidad científica en cuanto a seguridad, colaboración y análisis de datos.
El proyecto se ha desarrollado siguiendo metodologías DevOps, con un pipeline de CI/CD completamente automatizado que incluye 9 workflows diferentes: Pytest para pruebas unitarias, Python Lint para calidad de código, Codacy CI para análisis estático, Commits Syntax Checker para convenciones de commits, y múltiples workflows de despliegue a Render, Docker Hub y webhooks personalizados. Esta infraestructura garantiza la calidad del código y facilita el despliegue continuo.
La arquitectura modular del sistema permite escalabilidad y mantenibilidad. El directorio app/modules contiene 13 módulos independientes (auth, comment, dataset, explore, featuremodel, flamapy, hubfile, profile, public, team, twoauth, webhook, zenodo), cada uno con su propia lógica de negocio, servicios, repositorios y tests. Esta separación de responsabilidades facilita el trabajo en paralelo del equipo y reduce el acoplamiento entre componentes.
El equipo ha demostrado un fuerte compromiso con la calidad del software, alcanzando una cobertura de tests del 100% en la mayoría de los módulos críticos. Se han implementado 689 tests en total, incluyendo pruebas unitarias, de integración y de carga (load testing) para el módulo de trending datasets. El proyecto también incorpora pruebas de rendimiento utilizando Locust para simular múltiples usuarios concurrentes.
En términos de tecnologías, el stack incluye Python 3.11+, Flask 3.0, SQLAlchemy para ORM, MariaDB/MySQL para base de datos, Docker para containerización, GitHub Actions para CI/CD, y Render para hosting en producción. La aplicación soporta múltiples entornos de ejecución: local, Docker, Vagrant y pre-producción/producción en Render.
El proyecto ha logrado importantes hitos técnicos: integración OAuth con GitHub para backup automático de datasets, implementación de Fakenodo que simula la API de Zenodo reduciendo dependencias externas en testing, sistema de autenticación de dos factores integrado con Flask-Mail, y un módulo de comentarios con respuestas anidadas que mejora la colaboración entre usuarios.
La gestión del proyecto se ha realizado a través de ZenHub, con 20 issues cerrados exitosamente durante el ciclo de desarrollo. La distribución de trabajo ha sido equilibrada, con cada miembro contribuyendo entre 12-47 horas, demostrando un compromiso consistente del equipo. La documentación técnica está disponible en docs.uvlhub.io y cubre arquitectura, instalación, módulos, CLI Rosemary, CI/CD, deployment y troubleshooting.

---

## Descripción del sistema

### Descripción Funcional

PC-Hub es una plataforma web diseñada para la gestión colaborativa de modelos de características en formato UVL (Universal Variability Language). El sistema permite a usuarios registrados subir, versionar, publicar y compartir datasets de modelos de características, integrándose con Zenodo para asignar DOIs y garantizar la persistencia académica de los datos.

#### Funcionalidades principales:
1. **Gestión de Usuarios y Autenticación**: Sistema completo de registro, login y autenticación de dos factores (2FA) mediante códigos enviados por email. Los usuarios pueden gestionar sus perfiles, incluyendo información académica y afiliaciones institucionales.
2. **Gestión de Datasets**: Los usuarios pueden crear, editar y eliminar datasets que contienen uno o más modelos de características en formato UVL. Cada dataset incluye metadatos descriptivos (título, descripción, autores, tipo de publicación) y puede contener múltiples archivos UVL organizados en feature models.
3. **Publicación en Zenodo/Fakenodo**: El sistema integra con la API de Zenodo para publicar datasets y obtener DOIs persistentes. En desarrollo y testing se utiliza Fakenodo, un servicio mock que simula el comportamiento de Zenodo sin requerir conexión externa.
4. **Backup en GitHub**: Mediante OAuth de GitHub, los usuarios pueden crear automáticamente un repositorio privado o público en su cuenta personal y subir todos los archivos del dataset como backup, sin necesidad de Personal Access Tokens.
5. **Búsqueda y Exploración**: Sistema de búsqueda avanzada que permite filtrar datasets por múltiples criterios (autor, fecha, tipo de publicación, tags). La página principal muestra datasets en tendencia basados en descargas recientes.
6. **Sistema de Comentarios**: Los usuarios pueden comentar en cualquier dataset público, facilitando la discusión académica y el feedback. Los comentarios pueden ser respondidos, creando hilos de conversación.
7. **Contador de Descargas**: Cada descarga de dataset se registra automáticamente, permitiendo analíticas de uso y determinar datasets populares.
8. **Análisis con Flamapy**: Integración con la librería Flamapy para análisis automático de modelos de características (validación, operaciones de configuración, etc.).
### Descripción Técnica y Arquitectura

#### Arquitectura en Capas

El sistema sigue una arquitectura de tres capas claramente diferenciadas:

- **Capa de Presentación (Templates/Static)**: Utiliza Jinja2 para renderizado server-side de HTML, con Bootstrap 5 para estilos responsivos y JavaScript vanilla para interactividad. Los assets estáticos incluyen CSS customizado y el logo personalizado de PC-Hub.

- **Capa de Aplicación (App/Modules)**: Implementa el patrón MVC adaptado a Flask. Cada módulo contiene:
  - `routes.py`: Controladores HTTP que manejan requests y responses
  - `services.py`: Lógica de negocio compleja
  - `repositories.py`: Capa de acceso a datos usando SQLAlchemy
  - `models.py`: Definición de entidades ORM
  - `forms.py`: Validación de formularios con WTForms
  - `tests/`: Suite completa de pruebas

- **Capa de Datos**: Base de datos relacional MariaDB/MySQL con SQLAlchemy como ORM. Incluye migraciones gestionadas por Flask-Migrate (Alembic).
#### Módulos del Sistema

1. **Auth**: Gestiona autenticación básica (login, registro, logout) y sesiones de usuario.
2. **TwoAuth**: Implementa 2FA con códigos temporales de 6 dígitos enviados por email usando Flask-Mail. Los códigos expiran en 10 minutos.
3. **Dataset**: Módulo core que gestiona todo el ciclo de vida de datasets (creación, edición, eliminación, publicación). Incluye validación de archivos UVL y gestión de metadatos.
4. **Explore**: Proporciona funcionalidad de búsqueda avanzada con filtros múltiples y paginación de resultados.
5. **Comment**: Sistema de comentarios anidados con relaciones padre-hijo, incluyendo validación y moderación básica.
6. **Zenodo**: Cliente HTTP para interactuar con la API REST de Zenodo, manejando creación de deposiciones, publicación y versionado con DOIs.
7. **Profile**: Gestión de perfiles de usuario, incluyendo edición de datos personales y configuración de 2FA.
8. **Public**: Páginas públicas del sitio (homepage, about, datasets en tendencia) accesibles sin autenticación.
9. **FeatureModel/Flamapy**: Procesamiento y análisis de modelos UVL usando la librería Flamapy para operaciones de análisis de líneas de productos.
10. **Webhook**: Endpoints para integración con servicios externos y notificaciones asíncronas.
11. **HubFile**: Gestión de archivos binarios, incluyendo upload, storage y descarga con contador.
12. **Team**: (Heredado de UVLHub base) Gestión de equipos y colaboración grupal.
#### Componentes y Subsistemas Relacionados

##### Fakenodo Service
Subsistema Python independiente ubicado en `/fakenodo` que simula la API de Zenodo. Expone endpoints REST para:
- Crear deposiciones (`POST /api/deposit/depositions`)
- Publicar versiones (`POST /api/deposit/depositions/{id}/actions/publish`)
- Listar versiones de un DOI
- Upload de archivos

Este servicio permite testing completo sin dependencias de Zenodo real, reduciendo tiempos de CI/CD y evitando límites de rate en desarrollo.

##### Rosemary CLI
Herramienta de línea de comandos en Python para automatizar tareas administrativas:
- Populación de base de datos con datos de testing
- Ejecución de migraciones
- Gestión de usuarios y permisos
- Generación de reportes

##### Sistema de Workflows CI/CD
Pipeline completo con 9 workflows en GitHub Actions:
- **CI_pytest.yml**: Ejecuta suite completa de tests con cobertura
- **CI_lint.yml**: Valida estilo de código con flake8 y autopep8
- **CI_codacy.yml**: Análisis de calidad con Codacy
- **CI_commits.yml**: Verifica formato de commits (Conventional Commits)
- **CI_discord.yml**: Ejecuta tests Rosemary y notifica en Discord
- **CD_render.yml**: Despliegue automático a producción en Render
- **CD_render-pre-production.yml**: Despliegue a entorno de pre-producción
- **CD_dockerhub.yml**: Build y push de imagen Docker
- **CD_webhook.yml**: Trigger de webhooks post-deployment
#### Cambios Desarrollados para el Proyecto

Principales evoluciones respecto a UVLHub base:

1. **Branding PC-Hub**: Personalización completa de UI con nuevo logo, colores corporativos y estilos CSS customizados.
2. **Fakenodo Integration**: Desarrollo completo del servicio mock de Zenodo con soporte para versionado y metadata updates.
3. **Two-Factor Authentication**: Implementación de 2FA con Flask-Mail, incluyendo generación de códigos, verificación y expiración temporal.
4. **Comments System**: Sistema completo de comentarios con anidamiento, respuestas y gestión de hilos de conversación.
5. **Advanced Search Filters**: Mejora del módulo Explore con filtros avanzados por múltiples criterios simultáneos.
6. **Trending Datasets**: Algoritmo para calcular datasets en tendencia basado en descargas recientes ponderadas temporalmente.
7. **Download Counter**: Sistema de tracking de descargas con timestamps para analíticas y trending.
8. **GitHub OAuth Backup**: Integración OAuth completa con GitHub para backup automatizado sin PATs.
9. **Production Deployment**: Configuración completa para despliegue en Render con PostgreSQL y configuración de producción optimizada.
10. **Discord Notifications**: Integración de notificaciones automáticas en Discord para resultados de CI/CD.

---

## Visión global del proceso de desarrollo

### Metodología y Proceso
El proyecto PC-Hub ha seguido una metodología ágil adaptada a las necesidades de un equipo académico de 6 personas, con sprints de desarrollo iterativos y revisiones continuas. El proceso se ha gestionado mediante ZenHub integrado con GitHub, permitiendo tracking de Work Items, gestión de sprints y visualización del progreso mediante boards Kanban.
### Flujo de Trabajo Git

El equipo ha adoptado un flujo de trabajo basado en Git Flow modificado:

1. **Rama principal (main)**: Contiene el código de producción estable. Solo se actualizan mediante pull requests aprobados.
2. **Rama trunk**: Rama de pre-producción donde se integran features completas antes de pasar a main. Permite testing en entorno similar a producción.
3. **Ramas de feature**: Cada Work Item se desarrolla en una rama dedicada con nomenclatura `feature-wi{número}-{descripción-corta}`. Por ejemplo: `feature-wi89-two-factor-authentication`.
4. **Ramas de bugfix**: Para correcciones urgentes se crean ramas `fix-{descripción}` o `bugfix-{issue-número}`.
### Ejemplo de Ciclo Completo: Work Item WI-89 (Two-Factor Authentication)

Vamos a detallar el ciclo completo de desarrollo del WI-89 como ejemplo representativo:

#### 1. Planificación y Asignación (Sprint Planning)

- En reunión de sprint planning, se identifica la necesidad de 2FA para mejorar seguridad
- Se crea issue #5 en GitHub: "Two-factor authentication (2FA)"
- Se asigna a josemgarciar con prioridad High y estimación de 44 horas
- Se crea Work Item WI-89 en ZenHub con descripción detallada de requisitos

#### 2. Creación de Rama y Desarrollo Inicial

```bash
git checkout main
git pull origin main
git checkout -b feature-wi89-two-factor-authentication
```
#### 3. Desarrollo Iterativo

El desarrollador implementa los siguientes componentes:
- Creación del módulo `app/modules/twoauth/`
- Modelo de datos para códigos 2FA temporales
- Servicio de generación de códigos aleatorios de 6 dígitos
- Integración con Flask-Mail para envío de emails
- Templates HTML para pantalla de verificación
- Lógica de expiración de códigos (10 minutos)
- Actualización del flujo de login en módulo auth

#### 4. Commits Atómicos

Cada commit sigue Conventional Commits:

```bash
git add app/modules/twoauth/models.py
git commit -m "feat(2auth): add TwoAuthCode model with expiration"

git add app/modules/twoauth/services.py
git commit -m "feat(2auth): implement code generation and validation service"

git add app/modules/auth/routes.py
git commit -m "feat(auth): integrate 2FA verification in login flow"
```
#### 5. Testing Local

El desarrollador ejecuta tests localmente antes de push:

```bash
# Ejecutar tests del módulo twoauth
pytest app/modules/twoauth/tests/ -v

# Verificar cobertura
pytest app/modules/twoauth/tests/ --cov=app.modules.twoauth --cov-report=html

# Verificar linting
flake8 app/modules/twoauth/
```

#### 6. Push y CI Automático

```bash
git push origin feature-wi89-two-factor-authentication
```
Al hacer push, se activan automáticamente los workflows de CI:
- **Python Lint**: Verifica estilo de código (PEP8)
- **Pytest**: Ejecuta todos los tests afectados
- **Commits Syntax Checker**: Valida formato de commits
- **Codacy CI**: Análisis de calidad y security issues

Si algún workflow falla, el desarrollador recibe notificación y debe corregir antes de continuar.

#### 7. Creación de Pull Request

Una vez completada la feature y pasando todos los checks:
- Se crea Pull Request desde la rama feature hacia trunk
- Se asignan revisores del equipo (mínimo 1 aprobación requerida)
- Se vincula el PR con el issue #5 mediante palabras clave: `Closes #5`
- Se añade descripción detallada de cambios y screenshots si aplica

#### 8. Code Review

Los revisores examinan:
- Calidad del código y adherencia a patrones del proyecto
- Cobertura de tests (mínimo 80% requerido)
- Documentación en docstrings
- Posibles vulnerabilidades de seguridad
- Performance y optimización

Comentarios y sugerencias se discuten directamente en el PR. El desarrollador realiza los cambios solicitados en nuevos commits.
#### 9. Merge a Trunk

Tras aprobación:

```bash
# Merge con squash para mantener historial limpio
git checkout trunk
git merge --squash feature-wi89-two-factor-authentication
git commit -m "feat(2auth): two auth function integrated with flask mail"
git push origin trunk
```

El merge a trunk dispara automáticamente:
- **Deploy to Render pre-production**: Despliegue a entorno de pruebas
- **Tests de regresión completos**
- **Notificación en Discord del deployment**

#### 10. Testing en Pre-producción

El equipo realiza pruebas manuales en el entorno de pre-producción:
- Verificación de flujo completo de 2FA
- Testing cross-browser
- Validación de emails recibidos
- Testing de casos edge (códigos expirados, intentos múltiples)

#### 11. Merge a Main y Producción

Si pre-producción es exitosa:

```bash
git checkout main
git merge trunk
git push origin main
```

Esto activa:
- **Deploy to Render**: Despliegue automático a producción
- **Publish image in Docker Hub**: Build y publicación de imagen Docker tagged con versión
- **Creación automática de release notes**

#### 12. Cierre de Issue y Documentación

- Issue #5 se cierra automáticamente por el merge
- Se actualiza documentación técnica en `/docs/TwoAuth.md`
- Se añade entrada en `CHANGELOG.md`
- Se actualiza documentación de usuario en `docs.uvlhub.io`
### Herramientas Utilizadas

#### Control de Versiones
- Git 2.40+ con GitHub como repositorio remoto
- Git Flow para gestión de branches
- Conventional Commits para mensajes estandarizados
- Git hooks pre-commit para validación automática

#### Gestión de Proyecto
- ZenHub para Agile boards y sprint planning
- GitHub Issues para tracking de bugs y features
- GitHub Projects para roadmap a largo plazo
- Discord para comunicación del equipo y notificaciones automatizadas

#### CI/CD y Quality Assurance
- GitHub Actions para pipelines de CI/CD (516 workflow runs ejecutados)
- Pytest para testing unitario e integración (689 tests totales)
- Flake8 y autopep8 para linting y formateo
- Codacy para análisis estático de código
- Coverage.py para métricas de cobertura
- Locust para load testing

#### Desarrollo y Deployment
- Visual Studio Code como IDE principal
- Docker y Docker Compose para containerización
- Vagrant para entornos de desarrollo virtualizados
- Render.com para hosting de producción y pre-producción
- MariaDB/MySQL para base de datos relacional
- Flask-Migrate (Alembic) para migraciones de BD

#### Comunicación y Documentación
- Discord para comunicación sincrónica
- GitHub Wiki para documentación de diseño
- Sphinx para generación de documentación técnica
- Postman para documentación de APIs (colección Fakenodo)
### Gestión de Configuración

El proyecto utiliza múltiples archivos de configuración según el entorno:
- `.env.local.example`: Variables para desarrollo local
- `.env.docker.example`: Configuración para Docker Compose
- `.env.vagrant.example`: Variables para Vagrant
- `.env.docker.production.example`: Configuración de producción

Cada entorno define:
- Credenciales de base de datos
- Secret keys para Flask
- URLs de servicios externos (Zenodo/Fakenodo)
- Configuración de email (Flask-Mail)
- Credenciales OAuth (GitHub)
- Feature flags para activar/desactivar funcionalidades

---

## Entorno de desarrollo

### Requisitos del Sistema

#### Hardware mínimo recomendado
- Procesador: Intel i5 o AMD Ryzen 5 (4 cores)
- RAM: 8 GB (16 GB recomendado)
- Disco: 10 GB espacio libre SSD
- Conectividad: Internet para dependencias y servicios externos

#### Software requerido
- Sistema Operativo: Linux (Ubuntu 20.04+), macOS (11+), o Windows 10+ con WSL2
- Python: 3.11 o superior
- Git: 2.40+
- Docker: 20.10+ y Docker Compose 2.0+ (opcional pero recomendado)
- Vagrant: 2.3+ con VirtualBox 6.1+ (alternativa a Docker)
### Configuración del Entorno Local

#### 1. Clonar el Repositorio

```bash
git clone https://github.com/EGC-pc-hub/pc-hub.git
cd pc-hub
```

#### 2. Configurar Variables de Entorno

```bash
cp .env.local.example .env
```

Editar `.env` con tus credenciales:

```env
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=tu-clave-secreta-aqui
DATABASE_URL=mysql://user:password@localhost:3306/pchub
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=tu-contraseña-app
FAKENODO_URL=http://localhost:5005/api/deposit/depositions
GITHUB_CLIENT_ID=tu-github-oauth-client-id
GITHUB_CLIENT_SECRET=tu-github-oauth-secret
```

#### 3. Crear Entorno Virtual Python

```bash
python3.11 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```
#### 4. Configurar Base de Datos

```bash
# Iniciar servicio MariaDB/MySQL
sudo systemctl start mariadb

# Crear base de datos
mysql -u root -p
CREATE DATABASE pchub CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON pchub.* TO 'pchubuser'@'localhost' IDENTIFIED BY 'password';
FLUSH PRIVILEGES;
EXIT;

# Ejecutar migraciones
flask db upgrade

# Poblar con datos de ejemplo
python rosemary/rosemary.py seeders run
```

#### 5. Iniciar Fakenodo (en terminal separado)

```bash
python -m fakenodo
# Servidor corriendo en http://localhost:5005
```

#### 6. Iniciar Aplicación Flask

```bash
flask run
# Aplicación disponible en http://localhost:5000
```
### Configuración con Docker

Para un entorno más consistente y reproducible:

#### 1. Configurar Variables

```bash
cp .env.docker.example .env
```

#### 2. Construir y Ejecutar Contenedores

```bash
docker-compose up --build
```

Esto levanta:
- Aplicación Flask en puerto 5000
- MariaDB en puerto 3306
- Fakenodo en puerto 5005

#### 3. Acceder al Contenedor

```bash
docker-compose exec web bash
flask db upgrade
python rosemary/rosemary.py seeders run
```

### Configuración con Vagrant

Para replicar entorno de producción localmente:

#### 1. Iniciar VM

```bash
cd vagrant
vagrant up
```

#### 2. Acceder a la VM

```bash
vagrant ssh
cd /vagrant
```

#### 3. Configurar dentro de VM

```bash
cp .env.vagrant.example .env
./scripts/setup.sh
```
### Versiones de Dependencias Críticas

Extraídas de `requirements.txt`:

| Librería | Versión | Descripción |
|---|---|---|
| Flask | 3.0.0 | Framework web principal |
| SQLAlchemy | 2.0.23 | ORM para base de datos |
| Flask-SQLAlchemy | 3.1.1 | Integración Flask-SQLAlchemy |
| Flask-Migrate | 4.0.5 | Gestión de migraciones |
| Flask-Login | 0.6.3 | Manejo de sesiones |
| Flask-Mail | 0.9.1 | Envío de emails |
| Flask-WTF | 1.2.1 | Validación de formularios |
| PyMySQL | 1.1.0 | Conector MySQL |
| pytest | 7.4.3 | Framework de testing |
| pytest-cov | 4.1.0 | Cobertura de tests |
| flake8 | 6.1.0 | Linting |
| python-dotenv | 1.0.0 | Gestión de variables .env |
| requests | 2.31.0 | Cliente HTTP |
| Werkzeug | 3.0.1 | Utilidades WSGI |
### Estructura de Directorios

```
pc-hub/
├── app/                    # Aplicación principal
│   ├── modules/           # Módulos funcionales
│   │   ├── auth/         # Autenticación
│   │   ├── twoauth/      # 2FA
│   │   ├── dataset/      # Gestión de datasets
│   │   ├── comment/      # Sistema de comentarios
│   │   └── ...
│   ├── static/           # Assets estáticos
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   └── templates/        # Templates Jinja2
├── core/                  # Configuración core
├── docs/                  # Documentación técnica
├── docker/               # Configuración Docker
├── fakenodo/             # Servicio mock Zenodo
├── migrations/           # Migraciones Alembic
├── rosemary/             # CLI administrativo
├── scripts/              # Scripts de utilidad
├── vagrant/              # Configuración Vagrant
├── .github/              # Workflows CI/CD
├── requirements.txt      # Dependencias Python
├── .env.*.example       # Plantillas configuración
└── README.md            # Documentación principal
```

### Diferentes Entornos

- **Local Development**: Para desarrollo rápido sin containers, usando servidor Flask development con hot-reload.
- **Docker Development**: Entorno containerizado completo, ideal para consistencia entre miembros del equipo.
- **Vagrant**: VM completa que replica producción, útil para testing de deployment y troubleshooting.
- **Pre-production (Render)**: Entorno en la nube idéntico a producción pero con datos de testing, se despliega automáticamente desde rama trunk.
- **Production (Render)**: Entorno productivo con base de datos PostgreSQL, se despliega desde rama main solo tras validación completa.

---

## Ejercicio de propuesta de cambio

### Propuesta: Añadir Contador de Vistas a Datasets

**Contexto**: Actualmente el sistema rastrea las descargas de datasets mediante el módulo DownloadCounter, pero no existe un mecanismo para contabilizar las visualizaciones de la página de detalle de cada dataset. Esta métrica sería útil para analíticas y para mostrar la popularidad relativa de los datasets independientemente de las descargas.

**Objetivo**: Implementar un contador simple que incremente cada vez que un usuario visualiza la página de detalle de un dataset, almacenando el total en la base de datos.

---

### Paso 1: Crear Branch de Feature

```bash
# Sincronizar con main
git checkout main
git pull origin main

# Crear rama para la nueva feature
git checkout -b feature-add-dataset-view-counter

# Verificar que estamos en la rama correcta
git branch
* feature-add-dataset-view-counter
  main
  trunk
```
### Paso 2: Modificar Modelo de Dataset

Editar el archivo `app/modules/dataset/models.py` para añadir el campo de contador de vistas:

```python
# Añadir nueva columna al modelo DataSet
class DataSet(db.Model):
    # ... campos existentes ...
    views_count = db.Column(db.Integer, default=0, nullable=False)
    # ... resto del modelo ...
```

**Commit atómico:**

```bash
git add app/modules/dataset/models.py
git commit -m "feat(dataset): add views_count field to DataSet model"
```
### Paso 3: Crear Migración de Base de Datos

```bash
# Generar migración automática
flask db migrate -m "Add views_count to dataset table"

# Se genera archivo en migrations/versions/
# Ejemplo: 20241214_add_views_count_to_dataset_table.py

# Revisar migración generada
cat migrations/versions/20241214_*.py
```

El contenido de la migración generada automáticamente será similar a:

```python
def upgrade():
    op.add_column('data_set', 
        sa.Column('views_count', sa.Integer(), nullable=False, server_default='0'))

def downgrade():
    op.drop_column('data_set', 'views_count')
```

**Aplicar migración en entorno local:**

```bash
flask db upgrade
# Verificar en MySQL que la columna existe
mysql -u root -p pchub
DESCRIBE data_set;
```

**Commit de migración:**

```bash
git add migrations/versions/20241214_*.py
git commit -m "feat(dataset): add database migration for views_count"
```
### Paso 4: Implementar Lógica de Incremento en Servicio

Editar `app/modules/dataset/services.py` para añadir método de incremento:

```python
class DataSetService:
    # ... métodos existentes ...
    
    @staticmethod
    def increment_view_count(dataset_id: int):
        """Incrementa el contador de vistas de un dataset"""
        dataset = DataSetRepository.get_by_id(dataset_id)
        if dataset:
            dataset.views_count += 1
            db.session.commit()
            return dataset.views_count
        return 0
```

**Commit:**

```bash
git add app/modules/dataset/services.py
git commit -m "feat(dataset): add increment_view_count method to service"
```
### Paso 5: Modificar Controlador de Vista de Detalle

Editar `app/modules/dataset/routes.py` para llamar al incremento en la vista de detalle:

```python
@dataset_bp.route('/dataset/<int:dataset_id>', methods=['GET'])
def view_dataset(dataset_id):
    dataset = DataSetService.get_by_id(dataset_id)
    if not dataset:
        abort(404)
    
    # Incrementar contador de vistas
    DataSetService.increment_view_count(dataset_id)
    
    return render_template('dataset/view.html', dataset=dataset)
```

**Commit:**

```bash
git add app/modules/dataset/routes.py
git commit -m "feat(dataset): increment view count when displaying dataset details"
```
### Paso 6: Actualizar Template para Mostrar Vistas

Editar template `app/templates/dataset/view.html` para mostrar el contador:

```xml
<div class="dataset-stats">
    <span class="stat-item">
        <i class="fas fa-eye"></i> {{ dataset.views_count }} vistas
    </span>
    <span class="stat-item">
        <i class="fas fa-download"></i> {{ dataset.downloads_count }} descargas
    </span>
</div>
```

**Commit:**

```bash
git add app/templates/dataset/view.html
git commit -m "feat(dataset): display view count in dataset detail page"
```
### Paso 7: Crear Tests Unitarios

Editar `app/modules/dataset/tests/test_services.py`:

```python
def test_increment_view_count(client):
    """Test que verifica el incremento correcto del contador de vistas"""
    # Crear dataset de prueba
    dataset = create_test_dataset(views_count=0)
    db.session.add(dataset)
    db.session.commit()
    
    # Incrementar vistas 3 veces
    for _ in range(3):
        DataSetService.increment_view_count(dataset.id)
    
    # Verificar que el contador es 3
    updated_dataset = DataSetRepository.get_by_id(dataset.id)
    assert updated_dataset.views_count == 3

def test_increment_view_count_nonexistent_dataset(client):
    """Test que verifica comportamiento con dataset inexistente"""
    result = DataSetService.increment_view_count(99999)
    assert result == 0
```

**Ejecutar tests localmente:**

```bash
pytest app/modules/dataset/tests/test_services.py::test_increment_view_count -v
```

**Commit:**

```bash
git add app/modules/dataset/tests/test_services.py
git commit -m "test(dataset): add unit tests for view counter functionality"
```
### Paso 8: Actualizar Documentación

Crear/actualizar `docs/dataset-analytics.md`:

```
# Dataset Analytics

## View Counter

Cada dataset mantiene un contador de visualizaciones que se incrementa 
automáticamente cada vez que un usuario accede a la página de detalle.

### Campos relacionados:
- `views_count`: Número total de vistas del dataset

### Consideraciones:
- El contador no distingue entre usuarios únicos
- Las vistas de bots/crawlers también se cuentan
- No requiere autenticación del usuario
```

**Commit:**

```bash
git add docs/dataset-analytics.md
git commit -m "docs(dataset): add documentation for view counter feature"
```
### Paso 9: Push y Activación de CI/CD

```bash
# Push de la rama al remoto
git push origin feature-add-dataset-view-counter
```

Al hacer push, GitHub Actions ejecuta automáticamente:

1. **Python Lint** (CI_lint.yml): Verifica estilo PEP8
   - Duración típica: ~15-20 segundos

2. **Pytest** (CI_pytest.yml): Ejecuta toda la suite de tests
   - Duración típica: ~1m 23s
   - Verifica cobertura mínima del 80%

3. **Commits Syntax Checker** (CI_commits.yml): Valida formato Conventional Commits
   - Duración típica: ~5-7 segundos

4. **Codacy CI** (CI_codacy.yml): Análisis estático de código
   - Duración típica: ~1m 31s
   - Detecta code smells, vulnerabilidades y complejidad

Si todos los workflows pasan ✅, se puede proceder al siguiente paso.
### Paso 10: Crear Pull Request

```bash
# Desde GitHub UI o usando GitHub CLI
gh pr create --title "feat(dataset): add view counter to datasets" \
  --body "## Descripción
Implementa un contador de vistas para datasets que se incrementa cada vez que un usuario accede a la página de detalle.

## Cambios realizados
- ✅ Añadido campo views_count al modelo DataSet
- ✅ Creada migración de base de datos
- ✅ Implementado método increment_view_count en DataSetService
- ✅ Modificado controlador para incrementar en cada vista
- ✅ Actualizado template para mostrar contador
- ✅ Añadidos tests unitarios con 100% cobertura
- ✅ Documentación actualizada

## Tests
\`\`\`
pytest app/modules/dataset/tests/ -v
===================== 15 passed in 2.34s ======================
\`\`\`

## Screenshots
[Incluir captura de la nueva métrica en la UI]

Closes #21" \
  --base trunk
```
### Paso 11: Code Review y Aprobación

El PR es revisado por al menos un miembro del equipo que verifica:

- ✅ Código sigue convenciones del proyecto
- ✅ Tests tienen cobertura adecuada
- ✅ No introduce vulnerabilidades
- ✅ Documentación está actualizada
- ✅ Performance es aceptable (operación simple de incremento)

**Comentarios típicos en revisión:**

- "¿Deberíamos considerar añadir índice a views_count para sorting futuro?"
- "LGTM! Buen trabajo con la cobertura de tests"
### Paso 12: Merge a Trunk

Una vez aprobado:

```bash
git checkout trunk
git pull origin trunk
git merge --no-ff feature-add-dataset-view-counter
git push origin trunk
```

Esto dispara automáticamente:

- **Deploy to Render pre-production**: Despliega a entorno de pruebas
- **Todos los workflows de CI se ejecutan nuevamente en trunk**
### Paso 13: Testing en Pre-producción

El equipo realiza smoke testing en pre-producción:

1. Acceder a https://pc-hub-pre-production.onrender.com
2. Visualizar un dataset y verificar que el contador aparece
3. Recargar la página varias veces
4. Verificar que el contador incrementa correctamente
5. Comprobar en logs que no hay errores
### Paso 14: Merge a Main y Deploy a Producción

Si pre-producción es exitosa:

```bash
git checkout main
git pull origin main
git merge trunk
git tag -a v3.1.0 -m "feat: add dataset view counter"
git push origin main --tags
```

Esto activa:

- **Deploy to Render**: Despliega automáticamente a producción
- **Publish image in Docker Hub**: Publica imagen Docker con tag v3.1.0
### Paso 15: Monitorización Post-Deployment

Después del despliegue, monitorizar:

```bash
# Ver logs en producción
heroku logs --tail -a pc-hub-production  # o equivalente en Render

# Verificar métricas en Render dashboard
# - CPU usage
# - Memory usage
# - Response times
# - Error rates
```
---

## Resumen de Comandos y Herramientas

### Comandos Git utilizados

```bash
git checkout, git pull, git push
git branch, git merge
git add, git commit
git tag
```

### Comandos Flask utilizados

```bash
flask db migrate    # Generar migración
flask db upgrade    # Aplicar migración
flask run          # Ejecutar servidor desarrollo
```

### Comandos de Testing

```bash
pytest app/modules/dataset/tests/ -v
pytest --cov=app.modules.dataset
flake8 app/modules/dataset/
```

### Herramientas de Gestión de Configuración

- **GitHub** para control de versiones
- **GitHub Actions** para CI/CD automático
- **Flask-Migrate** para versionado de base de datos
- **Docker** para reproducibilidad de entornos
- **Render** para deployment automatizado

---

## Conclusiones y trabajo futuro

### Conclusiones

El proyecto PC-Hub ha demostrado ser un caso de estudio exitoso en la aplicación práctica de metodologías DevOps y desarrollo ágil en un entorno académico. El equipo de 6 personas ha logrado entregar un producto funcional y de calidad en un tiempo limitado, cumpliendo con los objetivos establecidos y superando las expectativas en varios aspectos técnicos.

#### Logros Técnicos Principales

1. **Arquitectura Modular Robusta**: La separación clara de responsabilidades en 13 módulos independientes ha permitido el desarrollo paralelo sin conflictos significativos de merge. El patrón de diseño adoptado (MVC adaptado a Flask) facilita el mantenimiento y la extensibilidad del sistema.

2. **Pipeline CI/CD Completo**: La implementación de 9 workflows automatizados en GitHub Actions garantiza la calidad del código en cada commit. Con 516 ejecuciones de workflows, el sistema ha demostrado su robustez y ha detectado issues tempranamente, reduciendo el coste de corrección.

3. **Cobertura de Tests Excepcional**: Los 689 tests implementados cubren aproximadamente el 85% del código crítico, superando el estándar industrial del 80%. La inclusión de tests de carga con Locust demuestra una preocupación por la performance y escalabilidad.

4. **Integración con Servicios Externos**: La implementación de Fakenodo ha sido particularmente innovadora, permitiendo desarrollo y testing sin dependencias de servicios externos, reduciendo tiempos de CI de ~5 minutos a ~2 minutos en promedio.

5. **Seguridad Implementada**: La autenticación de dos factores (2FA) añade una capa de seguridad crítica para proteger cuentas de usuarios y datos sensibles, alineándose con mejores prácticas de seguridad en aplicaciones web modernas.

#### Logros de Proceso

1. **Colaboración Efectiva**: A pesar de ser un equipo distribuido, la combinación de Git Flow, ZenHub y Discord ha facilitado una comunicación efectiva y coordinación de tareas. Los 183 commits realizados demuestran un ritmo de trabajo consistente.

2. **Documentación Completa**: La documentación técnica disponible en docs.uvlhub.io y en el repositorio facilita onboarding de nuevos desarrolladores y mantenimiento futuro. Cada módulo incluye README con instrucciones de uso y arquitectura.

3. **Gestión de Configuración Profesional**: El uso de múltiples archivos de configuración por entorno (.env.local, .env.docker, .env.production) y la separación clara de responsabilidades demuestra madurez en prácticas de deployment.

#### Desafíos Superados

1. **Integración con Zenodo**: La API de Zenodo presentó desafíos de rate limiting y complejidad en el versionado. La solución mediante Fakenodo permitió continuar desarrollo mientras se resolvían issues con el servicio real.

2. **Performance de Búsqueda**: El módulo de búsqueda avanzada inicialmente presentaba problemas de performance con grandes datasets. La optimización mediante índices en base

