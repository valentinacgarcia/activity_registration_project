from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///activities.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)

# Modelos
class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    schedules = db.Column(db.JSON, nullable=False)  # Lista de horarios
    requirements = db.Column(db.JSON, nullable=False)  # Requisitos como dict
    requires_clothing = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, name, capacity, schedules, requirements=None, requires_clothing=False):
        self.name = name
        self.capacity = capacity
        self.schedules = schedules
        self.requirements = requirements or {}
        self.requires_clothing = requires_clothing

    def validate(self):
        """Valida los datos de la actividad"""
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append("El nombre de la actividad es obligatorio")
        
        if self.capacity is None or self.capacity < 0:
            errors.append("La capacidad debe ser un número positivo")
        
        if not self.schedules or len(self.schedules) == 0:
            errors.append("La actividad debe tener al menos un horario")
        
        return errors

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'capacity': self.capacity,
            'schedules': self.schedules,
            'requirements': self.requirements,
            'requires_clothing': self.requires_clothing
        }

class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dni = db.Column(db.String(20), nullable=False, unique=True)
    age = db.Column(db.Integer, nullable=False)
    clothing_size = db.Column(db.String(10))
    terms_accepted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, name, dni, age, clothing_size=None, terms_accepted=False):
        self.name = name
        self.dni = dni
        self.age = age
        self.clothing_size = clothing_size
        self.terms_accepted = terms_accepted

    def validate(self):
        """Valida los datos del visitante"""
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append("El nombre es obligatorio")
        
        if not self.dni or not self.dni.strip():
            errors.append("El DNI es obligatorio")
        
        if self.age is None or self.age <= 0:
            errors.append("La edad debe ser un número positivo")
        
        return errors

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'dni': self.dni,
            'age': self.age,
            'clothing_size': self.clothing_size,
            'terms_accepted': self.terms_accepted
        }

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=False)
    visitor_id = db.Column(db.Integer, db.ForeignKey('visitor.id'), nullable=False)
    schedule = db.Column(db.String(50), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    activity = db.relationship('Activity', backref=db.backref('registrations', lazy=True))
    visitor = db.relationship('Visitor', backref=db.backref('registrations', lazy=True))

# Servicios
class ActivityService:
    @staticmethod
    def register_visitor(activity_id, visitor_data, schedule):
        """Registra un visitante en una actividad"""
        try:
            # Buscar la actividad
            activity = Activity.query.get(activity_id)
            if not activity:
                return {'success': False, 'error': 'Actividad no encontrada'}

            # Validar horario
            if schedule not in activity.schedules:
                return {'success': False, 'error': 'Horario no disponible'}

            # Obtener participantes
            participants = visitor_data.get('participants', [])
            participants_count = len(participants)
            
            if participants_count < 1 or participants_count > 10:
                return {'success': False, 'error': 'Cantidad de participantes debe estar entre 1 y 10'}

            # Verificar cupos disponibles
            current_registrations = Registration.query.filter_by(activity_id=activity_id).count()
            if current_registrations + participants_count > activity.capacity:
                return {'success': False, 'error': f'No hay cupos disponibles. Solo quedan {activity.capacity - current_registrations} cupos'}

            # Validar términos
            if not visitor_data.get('terms_accepted', False):
                return {'success': False, 'error': 'Debe aceptar los términos y condiciones'}

            # Validar y crear visitantes
            created_visitors = []
            for i, participant_data in enumerate(participants):
                # Validar talla si es requerida
                if activity.requires_clothing and not participant_data.get('clothing_size'):
                    return {'success': False, 'error': f'La actividad requiere especificar talla de vestimenta para el participante {i + 1}'}

                # Crear visitante
                visitor = Visitor(
                    name=participant_data['name'],
                    dni=participant_data['dni'],
                    age=participant_data['age'],
                    clothing_size=participant_data.get('clothing_size'),
                    terms_accepted=visitor_data.get('terms_accepted', False)
                )

                # Validar visitante
                visitor_errors = visitor.validate()
                if visitor_errors:
                    return {'success': False, 'error': f'Datos del participante {i + 1} inválidos', 'details': visitor_errors}

                db.session.add(visitor)
                db.session.flush()  # Para obtener el ID del visitante
                created_visitors.append(visitor)

            # Crear registros para cada participante
            for visitor in created_visitors:
                registration = Registration(
                    activity_id=activity_id,
                    visitor_id=visitor.id,
                    schedule=schedule
                )
                db.session.add(registration)
            
            db.session.commit()

            return {'success': True, 'message': 'Registro exitoso'}

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Error interno: {str(e)}'}

# Rutas de la API
@app.route('/api/activities', methods=['GET'])
def get_activities():
    activities = Activity.query.all()
    activities_with_capacity = []
    
    for activity in activities:
        activity_dict = activity.to_dict()
        # Contar registros existentes para esta actividad
        registered_count = Registration.query.filter_by(activity_id=activity.id).count()
        available_capacity = activity.capacity - registered_count
        
        # Agregar información de cupos disponibles
        activity_dict['available_capacity'] = max(0, available_capacity)
        activity_dict['registered_count'] = registered_count
        
        activities_with_capacity.append(activity_dict)
    
    return jsonify(activities_with_capacity)

@app.route('/api/activities', methods=['POST'])
def create_activity():
    data = request.json
    
    activity = Activity(
        name=data['name'],
        capacity=data['capacity'],
        schedules=data['schedules'],
        requirements=data.get('requirements', {}),
        requires_clothing=data.get('requires_clothing', False)
    )
    
    errors = activity.validate()
    if errors:
        return jsonify({'error': 'Datos inválidos', 'details': errors}), 400
    
    db.session.add(activity)
    db.session.commit()
    
    return jsonify(activity.to_dict()), 201

@app.route('/api/activities/<int:activity_id>/register', methods=['POST'])
def register_visitor(activity_id):
    data = request.json
    
    # Adaptar formato: si viene con 'visitor' (formato antiguo), convertir a nuevo formato
    if 'visitor' in data:
        # Formato antiguo: convertir a nuevo formato
        visitor_data = {
            'participants': [data['visitor']],
            'terms_accepted': data['visitor'].get('terms_accepted', True),
            'participants_count': 1
        }
        schedule = data['schedule']
    else:
        # Formato nuevo: usar directamente
        visitor_data = data
        schedule = data.get('schedule', '09:00')
    
    result = ActivityService.register_visitor(
        activity_id=activity_id,
        visitor_data=visitor_data,
        schedule=schedule
    )
    
    if result['success']:
        return jsonify(result), 200
    else:
        status_code = 404 if 'no encontrada' in result['error'] else 400
        return jsonify(result), status_code

@app.route('/api/visitors', methods=['GET'])
def get_visitors():
    visitors = Visitor.query.all()
    return jsonify([visitor.to_dict() for visitor in visitors])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
