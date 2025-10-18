import pytest
import sys
import os
import json

# Agregar el directorio padre al path para importar los modelos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import Activity, Visitor, Registration, ActivityService, db, app

class TestAcceptanceCriteria:
    """Tests de criterios de aceptación - Pruebas de usuario"""
    
    def setup_method(self):
        """Configuración antes de cada test"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Crear actividades de prueba
            self.activity_with_clothing = Activity(
                name="Palestra",
                capacity=3,
                schedules=["09:00", "11:00"],
                requirements={"nivel": "principiante"},
                requires_clothing=True
            )
            
            self.activity_without_clothing = Activity(
                name="Safari",
                capacity=5,
                schedules=["10:00", "14:00"],
                requirements={"nivel": "todos"},
                requires_clothing=False
            )
            
            db.session.add(self.activity_with_clothing)
            db.session.add(self.activity_without_clothing)
            db.session.commit()
            
            self.activity_with_clothing_id = self.activity_with_clothing.id
            self.activity_without_clothing_id = self.activity_without_clothing.id

    def teardown_method(self):
        """Limpieza después de cada test"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_1_successful_registration_with_clothing_required(self):
        """Prueba 1: Registro exitoso con actividad que requiere vestimenta"""
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
                activity_id=self.activity_with_clothing_id,
                visitor_data=visitor_data,
                schedule='09:00'
            )
            
            assert result['success'] == True
            assert 'Registro exitoso' in result['message']
            
            # Verificar que se creó el registro
            registration = Registration.query.filter_by(
                activity_id=self.activity_with_clothing_id
            ).first()
            assert registration is not None

    def test_2_no_available_slots_fails(self):
        """Prueba 2: Sin cupos disponibles - debe fallar"""
        with self.app.app_context():
            # Llenar todos los cupos
            for i in range(3):
                visitor = Visitor(
                    name=f'Visitante {i+1}',
                    dni=f'1234567{i}',
                    age=25,
                    terms_accepted=True
                )
                db.session.add(visitor)
                db.session.flush()
                
                registration = Registration(
                    activity_id=self.activity_with_clothing_id,
                    visitor_id=visitor.id,
                    schedule='09:00'
                )
                db.session.add(registration)
            
            db.session.commit()
            
            # Intentar registrar un visitante más
            visitor_data = {
                'participants': [{
                    'name': 'Visitante Extra',
                    'dni': '99999999',
                    'age': 30,
                    'clothing_size': 'L'
                }],
                'terms_accepted': True,
                'participants_count': 1
            }
            
            result = ActivityService.register_visitor(
                activity_id=self.activity_with_clothing_id,
                visitor_data=visitor_data,
                schedule='09:00'
            )
            
            assert result['success'] == False
            assert 'No hay cupos disponibles' in result['error']

    def test_3_clothing_size_not_required_passes(self):
        """Prueba 3: Actividad sin vestimenta requerida - debe pasar sin talla"""
        with self.app.app_context():
            visitor_data = {
                'participants': [{
                    'name': 'María García',
                    'dni': '87654321',
                    'age': 30,
                    'clothing_size': None  # Sin talla
                }],
                'terms_accepted': True,
                'participants_count': 1
            }
            
            result = ActivityService.register_visitor(
                activity_id=self.activity_without_clothing_id,
                visitor_data=visitor_data,
                schedule='10:00'
            )
            
            assert result['success'] == True
            assert 'Registro exitoso' in result['message']

    def test_4_invalid_schedule_fails(self):
        """Prueba 4: Horario no disponible - debe fallar"""
        with self.app.app_context():
            visitor_data = {
                'participants': [{
                    'name': 'Carlos López',
                    'dni': '11223344',
                    'age': 35,
                    'clothing_size': 'L'
                }],
                'terms_accepted': True,
                'participants_count': 1
            }
            
            result = ActivityService.register_visitor(
                activity_id=self.activity_with_clothing_id,
                visitor_data=visitor_data,
                schedule='15:00'  # Horario no disponible
            )
            
            assert result['success'] == False
            assert 'Horario no disponible' in result['error']

    def test_5_terms_not_accepted_fails(self):
        """Prueba 5: Términos no aceptados - debe fallar"""
        with self.app.app_context():
            visitor_data = {
                'participants': [{
                    'name': 'Ana Martínez',
                    'dni': '55667788',
                    'age': 28,
                    'clothing_size': 'S'
                }],
                'terms_accepted': False,  # No acepta términos
                'participants_count': 1
            }
            
            result = ActivityService.register_visitor(
                activity_id=self.activity_with_clothing_id,
                visitor_data=visitor_data,
                schedule='09:00'
            )
            
            assert result['success'] == False
            assert 'aceptar los términos y condiciones' in result['error']

    def test_6_required_clothing_size_missing_fails(self):
        """Prueba 6: Talla requerida faltante - debe fallar"""
        with self.app.app_context():
            visitor_data = {
                'participants': [{
                    'name': 'Pedro Rodríguez',
                    'dni': '99887766',
                    'age': 40,
                    'clothing_size': None  # Sin talla cuando es requerida
                }],
                'terms_accepted': True,
                'participants_count': 1
            }
            
            result = ActivityService.register_visitor(
                activity_id=self.activity_with_clothing_id,
                visitor_data=visitor_data,
                schedule='09:00'
            )
            
            assert result['success'] == False
            assert 'requiere especificar talla' in result['error']

    def test_7_multiple_participants_successful(self):
        """Prueba adicional: Múltiples participantes exitoso"""
        with self.app.app_context():
            visitor_data = {
                'participants': [
                    {
                        'name': 'Líder Grupo',
                        'dni': '11111111',
                        'age': 30,
                        'clothing_size': 'M'
                    },
                    {
                        'name': 'Participante 2',
                        'dni': '22222222',
                        'age': 25,
                        'clothing_size': 'L'
                    }
                ],
                'terms_accepted': True,
                'participants_count': 2
            }
            
            result = ActivityService.register_visitor(
                activity_id=self.activity_with_clothing_id,
                visitor_data=visitor_data,
                schedule='11:00'
            )
            
            assert result['success'] == True
            assert 'Registro exitoso' in result['message']
            
            # Verificar que se crearon ambos registros
            registrations = Registration.query.filter_by(
                activity_id=self.activity_with_clothing_id
            ).all()
            assert len(registrations) == 2

    def test_8_multiple_participants_exceeds_capacity_fails(self):
        """Prueba adicional: Múltiples participantes exceden capacidad - debe fallar"""
        with self.app.app_context():
            # Llenar 2 de los 3 cupos disponibles
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
                    activity_id=self.activity_with_clothing_id,
                    visitor_id=visitor.id,
                    schedule='09:00'
                )
                db.session.add(registration)
            
            db.session.commit()
            
            # Intentar registrar 2 personas más (total 4, pero solo hay 1 cupo)
            visitor_data = {
                'participants': [
                    {
                        'name': 'Grupo 1',
                        'dni': '33333333',
                        'age': 30,
                        'clothing_size': 'M'
                    },
                    {
                        'name': 'Grupo 2',
                        'dni': '44444444',
                        'age': 25,
                        'clothing_size': 'L'
                    }
                ],
                'terms_accepted': True,
                'participants_count': 2
            }
            
            result = ActivityService.register_visitor(
                activity_id=self.activity_with_clothing_id,
                visitor_data=visitor_data,
                schedule='09:00'
            )
            
            assert result['success'] == False
            assert 'No hay cupos disponibles' in result['error']
