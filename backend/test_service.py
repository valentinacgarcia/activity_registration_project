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
            
            # Crear actividad de prueba
            self.test_activity = Activity(
                name="Yoga Matutino",
                capacity=2,
                schedules=["09:00", "10:00"],
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
                'participants_count': 1
            }
            
            result = ActivityService.register_visitor(
                activity_id=self.activity_id,
                visitor_data=visitor_data,
                schedule='09:00'
            )
            
            assert result['success'] == True
            assert 'Registro exitoso' in result['message']

    def test_should_fail_when_no_seats_available(self):
        """S2: Actividad sin cupos disponibles"""
        with self.app.app_context():
            # Llenar los cupos disponibles
            for i in range(2):
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
                    schedule='09:00'
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
                'participants_count': 1
            }
            
            result = ActivityService.register_visitor(
                activity_id=self.activity_id,
                visitor_data=visitor_data,
                schedule='09:00'
            )
            
            assert result['success'] == False
            assert 'No hay cupos disponibles' in result['error']

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
                'participants_count': 1
            }
            
            result = ActivityService.register_visitor(
                activity_id=999,  # ID inexistente
                visitor_data=visitor_data,
                schedule='09:00'
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
                'participants_count': 1
            }
            
            result = ActivityService.register_visitor(
                activity_id=self.activity_id,
                visitor_data=visitor_data,
                schedule='15:00'  # Horario no disponible
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
                'participants_count': 1
            }
            
            result = ActivityService.register_visitor(
                activity_id=self.activity_id,
                visitor_data=visitor_data,
                schedule='09:00'
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
                'participants_count': 1
            }
            
            result = ActivityService.register_visitor(
                activity_id=self.activity_id,
                visitor_data=visitor_data,
                schedule='09:00'
            )
            
            assert result['success'] == False
            assert 'requiere especificar talla' in result['error']

    def test_should_pass_when_size_not_required(self):
        """S7: Actividad no requiere vestimenta, talla omitida"""
        with self.app.app_context():
            # Crear actividad que no requiere vestimenta
            activity_no_clothing = Activity(
                name="Meditación",
                capacity=5,
                schedules=["18:00"],
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
                'participants_count': 1
            }
            
            result = ActivityService.register_visitor(
                activity_id=activity_no_clothing.id,
                visitor_data=visitor_data,
                schedule='18:00'
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
                'participants_count': 1
            }
            
            result = ActivityService.register_visitor(
                activity_id=self.activity_id,
                visitor_data=visitor_data,
                schedule='09:00'
            )
            
            assert result['success'] == False
            assert 'Datos del participante' in result['error']

    def test_should_register_multiple_visitors_successfully(self):
        """S9: Inscripción con varios visitantes válidos (cupos suficientes)"""
        with self.app.app_context():
            # Crear actividad con más cupos
            activity_large = Activity(
                name="Pilates Grupal",
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
                    'participants_count': 1
                },
                {
                    'participants': [{
                        'name': 'Visitante 2',
                        'dni': '22222222',
                        'age': 30
                    }],
                    'terms_accepted': True,
                    'participants_count': 1
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
                name="Yoga Intensivo",
                capacity=1,
                schedules=["20:00"],
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
                'participants_count': 1
            }
            
            result1 = ActivityService.register_visitor(
                activity_id=activity_small.id,
                visitor_data=visitor1_data,
                schedule='20:00'
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
                'participants_count': 1
            }
            
            result2 = ActivityService.register_visitor(
                activity_id=activity_small.id,
                visitor_data=visitor2_data,
                schedule='20:00'
            )
            assert result2['success'] == False
            assert 'No hay cupos disponibles' in result2['error']
