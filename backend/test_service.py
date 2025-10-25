import pytest
import sys
import os

# Agregar el directorio padre al path para importar los modelos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import Activity, Visitor, Registration, ActivityService, db, app

class TestActivityService:
    """Tests de servicio para la lógica de negocio - TDD principal"""
    
    def setup_method(self):
        """Configuración antes de cada test"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Crear actividad de prueba con horarios válidos (cada 30 min entre 09:00-18:00)
            self.test_activity = Activity(
                name="Palestra",
                capacity=12,  # Capacidad por turno según reglas
                schedules=["09:00", "09:30", "10:00", "10:30", "15:00", "15:30", "16:00", "16:30"],
                requirements={"nivel": "principiante"},
                requires_clothing=True
            )
            db.session.add(self.test_activity)
            db.session.commit()
            self.activity_id = self.test_activity.id

    def teardown_method(self):
        """Limpieza después de cada test"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_should_register_successfully_with_available_seats(self):
        """S1: Inscripción válida (cupos > 0, horario válido, datos completos, términos aceptados)"""
        with self.app.app_context():
            visitor_data = {
                'participants': [{
                    'name': 'Juan Pérez',
                    'dni': '12345678',
                    'age': 25,
                    'clothing_size': 'M'
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:30'  # Hora anterior al horario
            }
            
            result = ActivityService.register_visitor(
                activity_id=self.activity_id,
                visitor_data=visitor_data,
                schedule='15:00'
            )
            
            assert result['success'] == True
            assert 'Registro exitoso' in result['message']

    def test_should_fail_when_no_seats_available(self):
        """S2: Actividad sin cupos disponibles"""
        with self.app.app_context():
            # Llenar los cupos disponibles
            for i in range(12):  # Llenar toda la capacidad
                visitor = Visitor(
                    name=f'Visitante {i+1}',
                    dni=f'1234567{i}',
                    age=25,
                    terms_accepted=True
                )
                db.session.add(visitor)
                db.session.flush()

                registration = Registration(
                    activity_id=self.activity_id,
                    visitor_id=visitor.id,
                    schedule='15:00'
                )
                db.session.add(registration)

            db.session.commit()

            # Intentar registrar un visitante más
            visitor_data = {
                'participants': [{
                    'name': 'Juan Pérez',
                    'dni': '99999999',
                    'age': 25,
                    'clothing_size': 'M'
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:30'  # Hora anterior al horario
            }
            
            result = ActivityService.register_visitor(
                activity_id=self.activity_id,
                visitor_data=visitor_data,
                schedule='15:00'
            )
            
            assert result['success'] == False
            assert 'No hay cupos disponibles' in result['error']

    def test_should_fail_when_age_below_minimum_tirolesa(self):
        """Test: Edad menor a la mínima para Tirolesa (8 años)"""
        with self.app.app_context():
            # Crear actividad Tirolesa
            tirolesa_activity = Activity(
                name="Tirolesa",
                capacity=10,
                schedules=["10:00", "11:00", "16:00", "16:30"],
                requirements={"nivel": "intermedio"},
                requires_clothing=True
            )
            db.session.add(tirolesa_activity)
            db.session.commit()
            
            visitor_data = {
                'participants': [{
                    'name': 'Juan Pérez',
                    'dni': '12345678',
                    'age': 7,  # Menor a 8 años
                    'clothing_size': 'S'
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:30'  # Hora anterior al horario
            }
            
            result = ActivityService.register_visitor(
                activity_id=tirolesa_activity.id,
                visitor_data=visitor_data,
                schedule='16:00'
            )
            
            assert result['success'] == False
            assert 'edad mínima para Tirolesa es 8 años' in result['error']

    def test_should_fail_when_age_below_minimum_palestra(self):
        """Test: Edad menor a la mínima para Palestra (12 años)"""
        with self.app.app_context():
            # Crear actividad Palestra
            palestra_activity = Activity(
                name="Palestra",
                capacity=12,
                schedules=["09:00", "09:30", "15:00", "15:30"],
                requirements={"nivel": "principiante"},
                requires_clothing=True
            )
            db.session.add(palestra_activity)
            db.session.commit()
            
            visitor_data = {
                'participants': [{
                    'name': 'Ana García',
                    'dni': '87654321',
                    'age': 10,  # Menor a 12 años
                    'clothing_size': 'M'
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:30'  # Hora anterior al horario
            }
            
            result = ActivityService.register_visitor(
                activity_id=palestra_activity.id,
                visitor_data=visitor_data,
                schedule='15:00'
            )
            
            assert result['success'] == False
            assert 'edad mínima para Palestra es 12 años' in result['error']

    def test_should_fail_when_dni_already_registered_same_schedule(self):
        """Test: DNI ya registrado en el mismo horario"""
        with self.app.app_context():
            # Primer registro exitoso
            visitor_data_1 = {
                'participants': [{
                    'name': 'Carlos López',
                    'dni': '11111111',
                    'age': 30,
                    'clothing_size': 'L'
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:30'  # Hora anterior al horario
            }
            
            result_1 = ActivityService.register_visitor(
                activity_id=self.activity_id,
                visitor_data=visitor_data_1,
                schedule='15:00'
            )
            
            assert result_1['success'] == True
            
            # Segundo registro con mismo DNI en mismo horario - debe fallar
            visitor_data_2 = {
                'participants': [{
                    'name': 'Carlos López',
                    'dni': '11111111',  # Mismo DNI
                    'age': 30,
                    'clothing_size': 'L'
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:30'  # Hora anterior al horario
            }
            
            result_2 = ActivityService.register_visitor(
                activity_id=self.activity_id,
                visitor_data=visitor_data_2,
                schedule='15:00'  # Mismo horario
            )
            
            assert result_2['success'] == False
            assert 'ya está registrado en el horario 15:00' in result_2['error']

    def test_should_pass_when_dni_registered_different_schedule(self):
        """Test: Mismo DNI permitido en horario diferente"""
        with self.app.app_context():
            # Primer registro en 09:00
            visitor_data_1 = {
                'participants': [{
                    'name': 'María González',
                    'dni': '22222222',
                    'age': 25,
                    'clothing_size': 'M'
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:30'  # Hora anterior al horario
            }
            
            result_1 = ActivityService.register_visitor(
                activity_id=self.activity_id,
                visitor_data=visitor_data_1,
                schedule='15:00'
            )
            
            assert result_1['success'] == True
            
            # Segundo registro con mismo DNI en horario diferente - debe ser exitoso
            visitor_data_2 = {
                'participants': [{
                    'name': 'María González',
                    'dni': '22222222',  # Mismo DNI
                    'age': 25,
                    'clothing_size': 'M'
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:30'  # Hora anterior al horario
            }
            
            result_2 = ActivityService.register_visitor(
                activity_id=self.activity_id,
                visitor_data=visitor_data_2,
                schedule='09:30'  # Horario diferente
            )
            
            assert result_2['success'] == True

    def test_should_fail_when_activity_not_found(self):
        """S3: Actividad inexistente"""
        with self.app.app_context():
            visitor_data = {
                'participants': [{
                    'name': 'Juan Pérez',
                    'dni': '12345678',
                    'age': 25,
                    'clothing_size': 'M'
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:30'  # Hora anterior al horario
            }
            
            result = ActivityService.register_visitor(
                activity_id=999,  # ID inexistente
                visitor_data=visitor_data,
                schedule='15:00'
            )
            
            assert result['success'] == False
            assert 'Actividad no encontrada' in result['error']

    def test_should_fail_when_schedule_not_available(self):
        """S4: Horario fuera de los permitidos"""
        with self.app.app_context():
            visitor_data = {
                'participants': [{
                    'name': 'Juan Pérez',
                    'dni': '12345678',
                    'age': 25,
                    'clothing_size': 'M'
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:30'  # Hora anterior al horario
            }
            
            result = ActivityService.register_visitor(
                activity_id=self.activity_id,
                visitor_data=visitor_data,
                schedule='14:00'  # Horario no disponible
            )
            
            assert result['success'] == False
            assert 'Horario no disponible' in result['error']

    def test_should_fail_when_terms_not_accepted(self):
        """S5: Visitante no acepta términos y condiciones"""
        with self.app.app_context():
            visitor_data = {
                'participants': [{
                    'name': 'Juan Pérez',
                    'dni': '12345678',
                    'age': 25,
                    'clothing_size': 'M'
                }],
                'terms_accepted': False,  # No acepta términos
                'participants_count': 1,
                'current_time': '08:30'  # Hora anterior al horario
            }
            
            result = ActivityService.register_visitor(
                activity_id=self.activity_id,
                visitor_data=visitor_data,
                schedule='15:00'
            )
            
            assert result['success'] == False
            assert 'aceptar los términos y condiciones' in result['error']

    def test_should_fail_when_required_size_missing(self):
        """S6: Actividad requiere vestimenta pero el visitante no cargó talla"""
        with self.app.app_context():
            visitor_data = {
                'participants': [{
                    'name': 'Juan Pérez',
                    'dni': '12345678',
                    'age': 25
                    # clothing_size no especificado
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:30'  # Hora anterior al horario
            }
            
            result = ActivityService.register_visitor(
                activity_id=self.activity_id,
                visitor_data=visitor_data,
                schedule='15:00'
            )
            
            assert result['success'] == False
            assert 'requiere especificar talla' in result['error']

    def test_should_pass_when_size_not_required(self):
        """S7: Actividad no requiere vestimenta, talla omitida"""
        with self.app.app_context():
            # Crear actividad que no requiere vestimenta
            activity_no_clothing = Activity(
                name="Jardinería",
                capacity=5,
                schedules=["17:30", "18:00"],
                requires_clothing=False
            )
            db.session.add(activity_no_clothing)
            db.session.commit()
            
            visitor_data = {
                'participants': [{
                    'name': 'María García',
                    'dni': '87654321',
                    'age': 30
                    # clothing_size no especificado
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:30'  # Hora anterior al horario
            }
            
            result = ActivityService.register_visitor(
                activity_id=activity_no_clothing.id,
                visitor_data=visitor_data,
                schedule='17:30'
            )
            
            assert result['success'] == True
            assert 'Registro exitoso' in result['message']

    def test_should_fail_when_missing_required_data(self):
        """S8: Faltan datos esenciales (nombre, DNI, edad)"""
        with self.app.app_context():
            visitor_data = {
                'participants': [{
                    'name': '',  # Nombre vacío
                    'dni': '',   # DNI vacío
                    'age': 0,    # Edad inválida
                    'clothing_size': 'M'
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:30'  # Hora anterior al horario
            }
            
            result = ActivityService.register_visitor(
                activity_id=self.activity_id,
                visitor_data=visitor_data,
                schedule='15:00'
            )
            
            assert result['success'] == False
            assert 'El nombre del participante 1 es obligatorio' in result['error']

    def test_should_register_multiple_visitors_successfully(self):
        """S9: Inscripción con varios visitantes válidos (cupos suficientes)"""
        with self.app.app_context():
            # Crear actividad con más cupos
            activity_large = Activity(
                name="Safari",
                capacity=5,
                schedules=["19:00"],
                requires_clothing=False
            )
            db.session.add(activity_large)
            db.session.commit()
            
            # Registrar múltiples visitantes
            visitors_data = [
                {
                    'participants': [{
                        'name': 'Visitante 1',
                        'dni': '11111111',
                        'age': 25
                    }],
                    'terms_accepted': True,
                    'participants_count': 1,
                'current_time': '08:30'  # Hora anterior al horario
            },
                {
                    'participants': [{
                        'name': 'Visitante 2',
                        'dni': '22222222',
                        'age': 30
                    }],
                    'terms_accepted': True,
                    'participants_count': 1,
                'current_time': '08:30'  # Hora anterior al horario
            }
            ]

            for visitor_data in visitors_data:
                result = ActivityService.register_visitor(
                    activity_id=activity_large.id,
                    visitor_data=visitor_data,
                    schedule='19:00'
                )
                assert result['success'] == True

    def test_should_fail_when_exceeding_capacity_with_multiple_visitors(self):
        """S10: Grupo mayor al cupo disponible"""
        with self.app.app_context():
            # Crear actividad con cupo limitado
            activity_small = Activity(
                name="Tirolesa",
                capacity=1,
                schedules=["17:30", "18:00"],
                requires_clothing=False
            )
            db.session.add(activity_small)
            db.session.commit()
            
            # Registrar primer visitante (debería funcionar)
            visitor1_data = {
                'participants': [{
                    'name': 'Primer Visitante',
                    'dni': '11111111',
                    'age': 25
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:30'  # Hora anterior al horario
            }
            
            result1 = ActivityService.register_visitor(
                activity_id=activity_small.id,
                visitor_data=visitor1_data,
                schedule='17:30'
            )
            assert result1['success'] == True
            
            # Intentar registrar segundo visitante (debería fallar)
            visitor2_data = {
                'participants': [{
                    'name': 'Segundo Visitante',
                    'dni': '22222222',
                    'age': 30
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:30'  # Hora anterior al horario
            }
            
            result2 = ActivityService.register_visitor(
                activity_id=activity_small.id,
                visitor_data=visitor2_data,
                schedule='17:30'
            )
            assert result2['success'] == False
            assert 'No hay cupos disponibles' in result2['error']