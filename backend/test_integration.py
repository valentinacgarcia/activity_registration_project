import pytest
import json
import sys
import os

# Agregar el directorio padre al path para importar los modelos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import Activity, Visitor, Registration, db, app

class TestIntegration:
    """Tests de integración - Flujo completo"""
    
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
                capacity=3,
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

    def test_should_complete_full_registration_flow_successfully(self):
        """I1: Llamada HTTP/Service simulada para inscripción válida"""
        registration_data = {
            'participants': [{
                'name': 'Juan Pérez',
                'dni': '12345678',
                'age': 25,
                'clothing_size': 'M'
            }],
            'terms_accepted': True,
            'participants_count': 1,
            'schedule': '09:00'
        }
        
        response = self.client.post(
            f'/api/activities/{self.activity_id}/register',
            data=json.dumps(registration_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'Registro exitoso' in data['message']

    def test_should_return_error_response_for_invalid_activity(self):
        """I2: Llamada con actividad inexistente"""
        registration_data = {
            'participants': [{
                'name': 'Juan Pérez',
                'dni': '12345678',
                'age': 25,
                'clothing_size': 'M'
            }],
            'terms_accepted': True,
            'participants_count': 1,
            'schedule': '09:00'
        }
        
        response = self.client.post(
            '/api/activities/999/register',  # ID inexistente
            data=json.dumps(registration_data),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'Actividad no encontrada' in data['error']

    def test_should_return_validation_error_for_missing_data(self):
        """I3: Petición con datos incompletos"""
        registration_data = {
            'participants': [{
                'name': '',  # Nombre vacío
                'dni': '',   # DNI vacío
                'age': 0,    # Edad inválida
                'clothing_size': 'M'
            }],
            'terms_accepted': True,
            'participants_count': 1,
            'schedule': '09:00'
        }
        
        response = self.client.post(
            f'/api/activities/{self.activity_id}/register',
            data=json.dumps(registration_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'Datos del participante' in data['error']

    def test_should_rollback_registration_on_failure(self):
        """I4: Simula error durante el registro para comprobar que no se guarda nada"""
        with self.app.app_context():
            # Primero, llenar los cupos disponibles
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
                    activity_id=self.activity_id,
                    visitor_id=visitor.id,
                    schedule='09:00'
                )
                db.session.add(registration)
            
            db.session.commit()
            
            # Contar registros antes del intento
            initial_count = Registration.query.count()
            
            # Intentar registrar un visitante más (debería fallar por cupos)
            registration_data = {
                'participants': [{
                    'name': 'Visitante Extra',
                    'dni': '99999999',
                    'age': 25,
                    'clothing_size': 'M'
                }],
                'terms_accepted': True,
                'participants_count': 1,
                'schedule': '09:00'
            }
            
            response = self.client.post(
                f'/api/activities/{self.activity_id}/register',
                data=json.dumps(registration_data),
                content_type='application/json'
            )
            
            # Verificar que falló
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data['success'] == False
            assert 'No hay cupos disponibles' in data['error']
            
            # Verificar que no se agregó ningún registro nuevo
            final_count = Registration.query.count()
            assert final_count == initial_count
            
            # Verificar que no se creó el visitante fallido
            failed_visitor = Visitor.query.filter_by(dni='99999999').first()
            assert failed_visitor is None
