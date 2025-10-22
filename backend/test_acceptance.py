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
            # Crear actividad Tirolesa para este test
            tirolesa = Activity(
                name="Tirolesa",
                capacity=10,
                schedules=["15:00"],
                requirements={"nivel": "todos"},
                requires_clothing=True
            )
            db.session.add(tirolesa)
            db.session.commit()
            
            visitor_data = {
                'participants': [{
                    'name': 'Juan Pérez',
                    'dni': '12345678',
                    'age': 25,
                    'clothing_size': 'M'
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:30'
            }
            
            result = ActivityService.register_visitor(
                activity_id=tirolesa.id,
                visitor_data=visitor_data,
                schedule='15:00'
            )
            
            assert result['success'] == True
            assert 'Registro exitoso' in result['message']
            
            # Verificar que se creó el registro
            registration = Registration.query.filter_by(
                activity_id=tirolesa.id
            ).first()
            assert registration is not None

    def test_2_no_available_slots_fails(self):
        """Prueba 2: Sin cupos disponibles - debe fallar"""
        with self.app.app_context():
            # Crear actividad Tirolesa y llenar todos los cupos
            tirolesa = Activity(
                name="Tirolesa",
                capacity=12,
                schedules=["15:00"],
                requirements={"nivel": "todos"},
                requires_clothing=True
            )
            db.session.add(tirolesa)
            db.session.commit()
            
            # Llenar todos los cupos
            for i in range(12):
                visitor = Visitor(
                    name=f'Visitante {i+1}',
                    dni=f'1234567{i}',
                    age=25,
                    terms_accepted=True
                )
                db.session.add(visitor)
                db.session.flush()
                
                registration = Registration(
                    activity_id=tirolesa.id,
                    visitor_id=visitor.id,
                    schedule='15:00'
                )
                db.session.add(registration)
            
            db.session.commit()
            
            # Intentar registrar un visitante más
            visitor_data = {
                'participants': [{
                    'name': 'Marco Polo',
                    'dni': '49999999',
                    'age': 20,
                    'clothing_size': 'L'
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:30'
            }
            
            result = ActivityService.register_visitor(
                activity_id=tirolesa.id,
                visitor_data=visitor_data,
                schedule='15:00'
            )
            
            assert result['success'] == False
            assert 'No hay cupos disponibles' in result['error']

    def test_3_clothing_size_not_required_passes(self):
        """Prueba 3: Actividad sin vestimenta requerida - debe pasar sin talla"""
        with self.app.app_context():
            # Crear actividad Jardinería
            jardineria = Activity(
                name="Jardinería",
                capacity=12,
                schedules=["16:00"],
                requirements={"nivel": "todos"},
                requires_clothing=False
            )
            db.session.add(jardineria)
            db.session.commit()
            
            visitor_data = {
                'participants': [{
                    'name': 'María García',
                    'dni': '34567890',
                    'age': 30,
                    'clothing_size': None  # Sin talla
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:30'
            }
            
            result = ActivityService.register_visitor(
                activity_id=jardineria.id,
                visitor_data=visitor_data,
                schedule='16:00'
            )
            
            assert result['success'] == True
            assert 'Registro exitoso' in result['message']

    def test_4_invalid_schedule_fails(self):
        """Prueba 4: Horario no disponible - debe fallar"""
        with self.app.app_context():
            # Crear actividad Tirolesa
            tirolesa = Activity(
                name="Tirolesa",
                capacity=10,
                schedules=["14:00"],
                requirements={"nivel": "todos"},
                requires_clothing=True
            )
            db.session.add(tirolesa)
            db.session.commit()
            
            visitor_data = {
                'participants': [{
                    'name': 'Carlos López',
                    'dni': '31223344',
                    'age': 35,
                    'clothing_size': 'L'
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '16:30'  # Hora posterior al horario
            }
            
            result = ActivityService.register_visitor(
                activity_id=tirolesa.id,
                visitor_data=visitor_data,
                schedule='14:00'  # Horario que ya pasó
            )
            
            assert result['success'] == False
            assert 'ya pasó' in result['error']

    def test_5_terms_not_accepted_fails(self):
        """Prueba 5: Términos no aceptados - debe fallar"""
        with self.app.app_context():
            # Crear actividad Tirolesa
            tirolesa = Activity(
                name="Tirolesa",
                capacity=10,
                schedules=["15:00"],
                requirements={"nivel": "todos"},
                requires_clothing=True
            )
            db.session.add(tirolesa)
            db.session.commit()
            
            visitor_data = {
                'participants': [{
                    'name': 'Ana Martínez',
                    'dni': '55667788',
                    'age': 18,
                    'clothing_size': 'S'
                }],
                'terms_accepted': False,  # No acepta términos
                'participants_count': 1,
                'current_time': '08:30'
            }
            
            result = ActivityService.register_visitor(
                activity_id=tirolesa.id,
                visitor_data=visitor_data,
                schedule='15:00'
            )
            
            assert result['success'] == False
            assert 'aceptar los términos y condiciones' in result['error']

    def test_6_required_clothing_size_missing_fails(self):
        """Prueba 6: Talla requerida faltante - debe fallar"""
        with self.app.app_context():
            # Crear actividad Tirolesa
            tirolesa = Activity(
                name="Tirolesa",
                capacity=10,
                schedules=["15:00"],
                requirements={"nivel": "todos"},
                requires_clothing=True
            )
            db.session.add(tirolesa)
            db.session.commit()
            
            visitor_data = {
                'participants': [{
                    'name': 'Pedro Rodríguez',
                    'dni': '49887766',
                    'age': 20,
                    'clothing_size': None  # Sin talla cuando es requerida
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:30'
            }
            
            result = ActivityService.register_visitor(
                activity_id=tirolesa.id,
                visitor_data=visitor_data,
                schedule='15:00'
            )
            
            assert result['success'] == False
            assert 'requiere especificar talla' in result['error']

    def test_7_multiple_participants_successful(self):
        """Prueba adicional: Múltiples participantes exitoso"""
        with self.app.app_context():
            # Crear actividad Tirolesa
            tirolesa = Activity(
                name="Tirolesa",
                capacity=10,
                schedules=["11:00"],
                requirements={"nivel": "todos"},
                requires_clothing=True
            )
            db.session.add(tirolesa)
            db.session.commit()
            
            visitor_data = {
                'participants': [
                    {
                        'name': 'Macarena Pasos',
                        'dni': '41111111',
                        'age': 20,
                        'clothing_size': 'M'
                    },
                    {
                        'name': 'Camila Pasos',
                        'dni': '42222222',
                        'age': 19,
                        'clothing_size': 'L'
                    }
                ],
                'terms_accepted': True,
                'participants_count': 2,
                'current_time': '08:30'
            }
            
            result = ActivityService.register_visitor(
                activity_id=tirolesa.id,
                visitor_data=visitor_data,
                schedule='11:00'
            )
            
            assert result['success'] == True
            assert 'Registro exitoso' in result['message']
            
            # Verificar que se crearon ambos registros
            registrations = Registration.query.filter_by(
                activity_id=tirolesa.id
            ).all()
            assert len(registrations) == 2

    def test_8_multiple_participants_exceeds_capacity_fails(self):
        """Prueba adicional: Múltiples participantes exceden capacidad - debe fallar"""
        with self.app.app_context():
            # Crear actividad Tirolesa
            tirolesa = Activity(
                name="Tirolesa",
                capacity=12,
                schedules=["15:00"],
                requirements={"nivel": "todos"},
                requires_clothing=True
            )
            db.session.add(tirolesa)
            db.session.commit()
            
            # Llenar 11 de los 12 cupos disponibles
            for i in range(11):
                visitor = Visitor(
                    name=f'Visitante {i+1}',
                    dni=f'1234567{i}',
                    age=25,
                    terms_accepted=True
                )
                db.session.add(visitor)
                db.session.flush()
                
                registration = Registration(
                    activity_id=tirolesa.id,
                    visitor_id=visitor.id,
                    schedule='15:00'
                )
                db.session.add(registration)
            
            db.session.commit()
            
            # Intentar registrar 2 personas más (total 2, pero solo hay 1 cupo)
            visitor_data = {
                'participants': [
                    {
                        'name': 'Liliana Mirasol',
                        'dni': '33333333',
                        'age': 30,
                        'clothing_size': 'M'
                    },
                    {
                        'name': 'Narella Villa',
                        'dni': '44444444',
                        'age': 21,
                        'clothing_size': 'L'
                    }
                ],
                'terms_accepted': True,
                'participants_count': 2,
                'current_time': '08:30'
            }
            
            result = ActivityService.register_visitor(
                activity_id=tirolesa.id,
                visitor_data=visitor_data,
                schedule='15:00'
            )
            
            assert result['success'] == False
            assert 'No hay cupos disponibles' in result['error']

    def test_9_no_schedule_selected_fails(self):
        """Prueba 9: Sin horario seleccionado - debe fallar"""
        with self.app.app_context():
            # Crear actividad Tirolesa
            tirolesa = Activity(
                name="Tirolesa",
                capacity=10,
                schedules=["15:00"],
                requirements={"nivel": "todos"},
                requires_clothing=True
            )
            db.session.add(tirolesa)
            db.session.commit()
            
            visitor_data = {
                'participants': [{
                    'name': 'María González',
                    'dni': '12345678',
                    'age': 25,
                    'clothing_size': 'M'
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:30'
            }
            
            result = ActivityService.register_visitor(
                activity_id=tirolesa.id,
                visitor_data=visitor_data,
                schedule=''  # Horario vacío
            )
            
            assert result['success'] == False
            assert 'Horario no disponible' in result['error']

    def test_10_invalid_time_range_fails(self):
        """Prueba 10: Horario fuera del rango válido (antes de las 9:00) - debe fallar"""
        with self.app.app_context():
            # Crear actividad Tirolesa
            tirolesa = Activity(
                name="Tirolesa",
                capacity=10,
                schedules=["15:00"],
                requirements={"nivel": "todos"},
                requires_clothing=True
            )
            db.session.add(tirolesa)
            db.session.commit()
            
            # Test con horario antes de las 9:00
            visitor_data_early = {
                'participants': [{
                    'name': 'Juan Pérez',
                    'dni': '11111111',
                    'age': 25,
                    'clothing_size': 'M'
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:00'
            }
            
            result_early = ActivityService.register_visitor(
                activity_id=tirolesa.id,
                visitor_data=visitor_data_early,
                schedule='08:30'  # Horario antes de las 9:00
            )
            
            assert result_early['success'] == False
            assert 'Horario no disponible' in result_early['error']

    def test_11_invalid_dni_format_fails(self):
        """Prueba 11: DNI no numérico - debe fallar"""
        with self.app.app_context():
            # Crear actividad Tirolesa
            tirolesa = Activity(
                name="Tirolesa",
                capacity=10,
                schedules=["15:00"],
                requirements={"nivel": "todos"},
                requires_clothing=True
            )
            db.session.add(tirolesa)
            db.session.commit()
            
            visitor_data = {
                'participants': [{
                    'name': 'Carlos López',
                    'dni': 'ABC12345',  # DNI con letras
                    'age': 25,
                    'clothing_size': 'M'
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'current_time': '08:30'
            }
            
            result = ActivityService.register_visitor(
                activity_id=tirolesa.id,
                visitor_data=visitor_data,
                schedule='15:00'
            )
            
            assert result['success'] == False
            assert 'solo números' in result['details'][0]