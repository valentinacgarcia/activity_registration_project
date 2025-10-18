# 🏃‍♀️ Sistema de Registro de Actividades

Un sistema completo de registro de actividades deportivas y de bienestar con frontend y backend, implementando TDD (Test-Driven Development) con todos los tests requeridos.

## 📋 Características

- **Backend**: API REST con Flask y SQLAlchemy
- **Frontend**: Interfaz web moderna y responsiva
- **Base de datos**: SQLite para desarrollo
- **Tests**: 21 tests implementados siguiendo TDD
  - 7 Domain Tests (validación de entidades)
  - 10 Service Tests (lógica de negocio)
  - 4 Integration Tests (flujo completo)

## 🧪 Tests Implementados

### Domain Tests (D1-D7)
- ✅ `test_should_create_valid_activity()` - Creación de actividad válida
- ✅ `test_should_not_allow_negative_capacity()` - Validación de cupos negativos
- ✅ `test_should_require_activity_name()` - Nombre obligatorio
- ✅ `test_should_validate_schedule_list_not_empty()` - Al menos un horario
- ✅ `test_should_create_valid_visitor()` - Visitante válido
- ✅ `test_should_reject_visitor_without_dni()` - DNI obligatorio
- ✅ `test_should_reject_invalid_age()` - Edad válida

### Service Tests (S1-S10)
- ✅ `test_should_register_successfully_with_available_seats()` - Registro exitoso
- ✅ `test_should_fail_when_no_seats_available()` - Sin cupos disponibles
- ✅ `test_should_fail_when_activity_not_found()` - Actividad inexistente
- ✅ `test_should_fail_when_schedule_not_available()` - Horario no disponible
- ✅ `test_should_fail_when_terms_not_accepted()` - Términos no aceptados
- ✅ `test_should_fail_when_required_size_missing()` - Talla requerida faltante
- ✅ `test_should_pass_when_size_not_required()` - Talla no requerida
- ✅ `test_should_fail_when_missing_required_data()` - Datos faltantes
- ✅ `test_should_register_multiple_visitors_successfully()` - Múltiples visitantes
- ✅ `test_should_fail_when_exceeding_capacity_with_multiple_visitors()` - Exceder capacidad

### Integration Tests (I1-I4)
- ✅ `test_should_complete_full_registration_flow_successfully()` - Flujo completo exitoso
- ✅ `test_should_return_error_response_for_invalid_activity()` - Actividad inexistente
- ✅ `test_should_return_validation_error_for_missing_data()` - Datos incompletos
- ✅ `test_should_rollback_registration_on_failure()` - Rollback en fallo

## 🚀 Instalación y Uso

### Prerrequisitos
- Python 3.8+
- Navegador web moderno

### 1. Configurar Backend

```bash
cd backend

# Instalar dependencias
pip install -r requirements.txt

# Poblar base de datos con datos de ejemplo
python seed_data.py

# Ejecutar tests
pytest -v

# Iniciar servidor
python app.py
```

El backend estará disponible en `http://localhost:5000`

### 2. Configurar Frontend

```bash
cd frontend

# Abrir en navegador
# Simplemente abre index.html en tu navegador
# O usa un servidor local:
python -m http.server 8000
```

El frontend estará disponible en `http://localhost:8000`

## 🔧 API Endpoints

### Actividades
- `GET /api/activities` - Listar todas las actividades
- `POST /api/activities` - Crear nueva actividad

### Registro
- `POST /api/activities/{id}/register` - Registrar visitante en actividad

### Visitantes
- `GET /api/visitors` - Listar todos los visitantes

## 📊 Estructura del Proyecto

```
activity_registration_project/
├── backend/
│   ├── app.py                 # Aplicación Flask principal
│   ├── test_domain.py         # Domain Tests (D1-D7)
│   ├── test_service.py        # Service Tests (S1-S10)
│   ├── test_integration.py    # Integration Tests (I1-I4)
│   ├── seed_data.py           # Script para datos de ejemplo
│   ├── requirements.txt       # Dependencias Python
│   └── pytest.ini            # Configuración de pytest
├── frontend/
│   └── index.html            # Interfaz web
└── README.md                 # Este archivo
```

## 🎯 Funcionalidades del Sistema

### Para Administradores
- Crear actividades con cupos, horarios y requisitos
- Ver todas las actividades y sus registros
- Gestionar horarios disponibles

### Para Visitantes
- Ver actividades disponibles
- Seleccionar horario preferido
- Registrarse con datos personales
- Aceptar términos y condiciones
- Especificar talla si es requerida

## 🧪 Ejecutar Tests

```bash
# Ejecutar todos los tests
pytest -v

# Ejecutar tests específicos
pytest test_domain.py -v      # Domain Tests
pytest test_service.py -v     # Service Tests  
pytest test_integration.py -v # Integration Tests

# Ejecutar con cobertura
pytest --cov=app -v
```

## 🔍 Casos de Uso Cubiertos

1. **Registro exitoso**: Visitante válido se registra en actividad con cupos
2. **Validación de cupos**: No permite registros cuando no hay cupos
3. **Validación de datos**: Rechaza datos incompletos o inválidos
4. **Términos y condiciones**: Obligatorio aceptar términos
5. **Vestimenta requerida**: Valida talla cuando es necesaria
6. **Múltiples visitantes**: Maneja grupos de visitantes
7. **Transacciones**: Rollback en caso de error

## 🎨 Frontend

- Diseño moderno y responsivo
- Interfaz intuitiva para selección de actividades
- Validación en tiempo real
- Mensajes de error y éxito claros
- Compatible con dispositivos móviles

## 🔒 Seguridad

- Validación de datos en frontend y backend
- Transacciones atómicas en base de datos
- Manejo de errores robusto
- CORS configurado para desarrollo

## 📈 Próximas Mejoras

- Autenticación de usuarios
- Panel de administración
- Notificaciones por email
- Reportes de asistencia
- Integración con sistemas de pago
