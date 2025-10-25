# 🏃‍♀️ Sistema de Registro de Actividades - Parque EcoHarmony

Un sistema completo de registro de actividades deportivas y de bienestar con frontend y backend, implementando TDD (Test-Driven Development) con todos los tests requeridos.

## 📋 Características

- **Backend**: API REST con Flask y SQLAlchemy
- **Frontend**: Interfaz web moderna y responsiva
- **Base de datos**: SQLite para desarrollo
- **Validaciones**: Edad mínima por actividad, DNI único por horario, validación de horarios pasados
- **Horarios**: Sistema de turnos cada 30 minutos entre 09:00 y 18:00
- **Tests**: 39 tests implementados siguiendo TDD
  - 7 Domain Tests (validación de entidades)
  - 10 Service Tests (lógica de negocio)
  - 4 Integration Tests (flujo completo)
  - 11 Acceptance Tests (casos de uso del usuario)
  - 7 Tests adicionales (validaciones específicas)

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

### Acceptance Tests (CP-01 a CP-08)
- ✅ `test_1_successful_registration_with_clothing_required()` - Registro exitoso con Tirolesa
- ✅ `test_2_no_available_slots_fails()` - Sin cupos disponibles (falla)
- ✅ `test_3_clothing_size_not_required_passes()` - Actividad sin vestimenta (Jardinería)
- ✅ `test_4_invalid_schedule_fails()` - Horario que ya pasó (falla)
- ✅ `test_5_terms_not_accepted_fails()` - Términos no aceptados (falla)
- ✅ `test_6_required_clothing_size_missing_fails()` - Falta talla requerida (falla)
- ✅ `test_7_multiple_participants_successful()` - Inscripción múltiple exitosa
- ✅ `test_8_multiple_participants_exceeds_capacity_fails()` - Múltiples participantes exceden capacidad
- ✅ `test_9_no_schedule_selected_fails()` - Sin horario seleccionado
- ✅ `test_10_invalid_time_range_fails()` - Horario fuera del rango válido
- ✅ `test_11_invalid_dni_format_fails()` - DNI no numérico

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

# Verificar estilo de código
flake8 .

# Iniciar servidor
python app.py
```

El backend estará disponible en `http://localhost:5000`

**Nota**: La base de datos se regenera automáticamente con:
- **Horarios**: Cada 30 minutos entre 09:00-18:00
- **Cupos por turno**: Palestra/Jardinería (12), Safari (8), Tirolesa (10)
- **Edades mínimas**: Tirolesa (8+), Palestra (12+)
- **Vestimenta**: Solo Tirolesa y Palestra requieren talla

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
- Gestionar horarios disponibles (cada 30 minutos entre 09:00-18:00)
- Configurar edades mínimas por actividad
- Establecer cupos por turno (Palestra/Jardinería: 12, Safari: 8, Tirolesa: 10)

### Para Visitantes
- Ver actividades disponibles
- Seleccionar horario preferido
- Registrarse con datos personales (nombre, DNI, edad, talla si es requerida)
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

## 🔍 Escenarios Cubiertos

1. **Registro exitoso**: Visitante válido se registra en actividad con cupos
2. **Validación de cupos**: No permite registros cuando no hay cupos
3. **Validación de datos**: Rechaza datos incompletos o inválidos
4. **Términos y condiciones**: Obligatorio aceptar términos
5. **Vestimenta requerida**: Valida talla cuando es necesaria
6. **Múltiples visitantes**: Maneja grupos de visitantes
7. **Transacciones**: Rollback en caso de error
8. **Edad mínima**: Valida edad según actividad (Tirolesa: 8+, Palestra: 12+)
9. **DNI único por horario**: No permite mismo DNI en mismo horario
10. **Horarios pasados**: Bloquea registros en horarios ya transcurridos
11. **DNI numérico**: Solo acepta DNIs con números
12. **Horarios válidos**: Solo permite horarios entre 09:00-18:00
13. **Selección de horario**: Obligatorio seleccionar un horario
14. **Validación dual**: Frontend y backend con las mismas reglas
15. **Mensajes de error**: Visibles debajo de cada campo para móviles

## 🎨 Frontend

- Diseño moderno y responsivo
- Interfaz intuitiva para selección de actividades
- **Validación en tiempo real** con mensajes visibles debajo de cada campo
- **Desplegables de horarios** con cupos disponibles por turno
- **Validación de edad** específica por actividad
- **Campo de hora actual** para validación de horarios pasados
- **Mensajes de error específicos** para cada validación
- **Registro de múltiples participantes** con validación individual
- **Selección única de horario** (al seleccionar uno, se deselecciona el anterior)
- **Indicadores de cupos** solo cuando se selecciona un horario
- **Deshabilitación de horarios** cuando están llenos o ya pasaron
- Mensajes de error y éxito claros
- Compatible con dispositivos móviles

## 🔒 Seguridad

- **Validación dual**: Frontend y backend con las mismas reglas
- **Transacciones atómicas** en base de datos
- **Manejo de errores robusto** con mensajes descriptivos
- **CORS configurado** para desarrollo
- **Validación de horarios** para prevenir registros en horarios pasados
- **DNI único por horario** para evitar duplicados
- **Validación de edad** para cumplir requisitos de seguridad
- **DNI numérico**: Solo acepta DNIs con números (7-8 dígitos)
- **Validación de horarios**: Solo permite horarios entre 09:00-18:00
- **Prevención de registros duplicados** por DNI en mismo horario
- **Validación de tiempo real** para horarios pasados

## 🛠️ Configuración de Desarrollo

### Estilo de Código
- **Python**: PEP 8 con flake8
- **JavaScript**: camelCase para variables, PascalCase para clases
- **HTML/CSS**: Indentación de 4 espacios
- **Archivos de configuración**: `.flake8`, `.editorconfig`, `.gitignore`

### Estructura de Archivos
```
activity_registration_project/
├── .gitignore              # Archivos a ignorar
├── .editorconfig           # Configuración de editor
├── backend/
│   ├── .flake8            # Configuración de linting
│   ├── app.py             # Aplicación Flask principal
│   ├── seed_data.py       # Datos de ejemplo
│   ├── requirements.txt   # Dependencias
│   ├── test_domain.py     # Domain Tests (D1-D7)
│   ├── test_service.py    # Service Tests (S1-S10)
│   ├── test_integration.py # Integration Tests (I1-I4)
│   ├── test_acceptance.py # Acceptance Tests (CP-01 a CP-08 + adicionales)
│   └── pytest.ini        # Configuración de pytest
├── frontend/
│   └── index.html        # Interfaz web
└── README.md            # Documentación
```