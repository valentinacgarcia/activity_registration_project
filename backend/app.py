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

# Utilidades de horarios
def generate_time_slots(start_time: str = "09:00", end_time: str = "18:00", interval_minutes: int = 30) -> list[str]:
    """Genera slots horarios entre start_time (incluido) y end_time (exclusivo del inicio del siguiente slot)
    en intervalos de interval_minutes. Devuelve strings en formato HH:MM.
    Por ejemplo: 09:00, 09:30, ..., 17:30.
    """
    from datetime import datetime as dt, timedelta

    base_date = "2000-01-01 "
    start_dt = dt.strptime(base_date + start_time, "%Y-%m-%d %H:%M")
    end_dt = dt.strptime(base_date + end_time, "%Y-%m-%d %H:%M")
    slots: list[str] = []
    cursor = start_dt
    while cursor + timedelta(minutes=interval_minutes) <= end_dt:
        slots.append(cursor.strftime("%H:%M"))
        cursor += timedelta(minutes=interval_minutes)
    return slots

VALID_SLOTS_SET = set(generate_time_slots())

def is_valid_slot(time_str: str) -> bool:
    """Valida que el string esté en formato HH:MM y sea un múltiplo de 30 entre 09:00 y 18:00."""
    if not isinstance(time_str, str) or len(time_str) != 5 or time_str[2] != ":":
        return False
    return time_str in VALID_SLOTS_SET

# Reglas por actividad
def get_turn_capacity(activity_name: str) -> int:
    name = (activity_name or "").lower()
    if "palestra" in name or "jardiner" in name:
        return 12
    if "safari" in name:
        return 8
    if "tirolesa" in name:
        return 10
    return 12

def get_min_age(activity_name: str) -> int:
    name = (activity_name or "").lower()
    if "palestra" in name:
        return 12
    if "tirolesa" in name:
        return 8
    return 0

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
        else:
            # validar que todos los horarios cumplan el rango 09:00-18:00 cada 30 minutos
            invalid = [s for s in self.schedules if not is_valid_slot(s)]
            if invalid:
                errors.append(f"Horarios inválidos (deben ser cada 30 minutos entre 09:00 y 18:00): {invalid}")
        
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
    dni = db.Column(db.String(20), nullable=False)
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
            print(f"DEBUG: register_visitor called with activity_id={activity_id}, visitor_data={visitor_data}, schedule={schedule}")
            # Buscar la actividad
            activity = Activity.query.get(activity_id)
            if not activity:
                return {'success': False, 'error': 'Actividad no encontrada'}

            # Validar horario
            if schedule not in activity.schedules:
                return {'success': False, 'error': 'Horario no disponible'}

            # Validar que el horario no sea pasado
            from datetime import datetime as dt
            current_time_str = visitor_data.get('current_time')
            
            # Si no se proporciona current_time, usar la hora actual del servidor
            if not current_time_str:
                now = dt.now()
                current_time_str = now.strftime('%H:%M')
            
            if is_valid_slot(schedule):
                try:
                    base_date = dt.now().strftime('%Y-%m-%d ')
                    now_dt = dt.strptime(base_date + current_time_str, '%Y-%m-%d %H:%M')
                    sched_dt = dt.strptime(base_date + schedule, '%Y-%m-%d %H:%M')
                    if now_dt >= sched_dt:
                        return {'success': False, 'error': f'El horario {schedule} ya pasó (hora actual: {current_time_str})'}
                except Exception:
                    pass

            # Obtener participantes
            participants = visitor_data.get('participants', [])
            participants_count = len(participants)
            
            if participants_count < 1 or participants_count > 10:
                return {'success': False, 'error': 'Cantidad de participantes debe estar entre 1 y 10'}

            # Verificar cupos disponibles por horario (turno)
            turn_capacity = get_turn_capacity(activity.name)
            current_registrations = Registration.query.filter_by(activity_id=activity_id, schedule=schedule).count()
            remaining = turn_capacity - current_registrations
            if remaining < participants_count:
                return {'success': False, 'error': f'No hay cupos disponibles en el horario {schedule}. Quedan {max(0, remaining)} cupos'}

            # Validar términos
            if not visitor_data.get('terms_accepted', False):
                return {'success': False, 'error': 'Debe aceptar los términos y condiciones'}

            # Validar que no haya DNIs duplicados en el mismo horario
            participant_dnis = [p.get('dni') for p in participants if p.get('dni')]
            for dni in participant_dnis:
                # Verificar si este DNI ya está registrado en este horario (cualquier actividad)
                existing_registration = db.session.query(Registration).join(Visitor).filter(
                    Visitor.dni == dni,
                    Registration.schedule == schedule
                ).first()
                
                if existing_registration:
                    return {'success': False, 'error': f'El DNI {dni} ya está registrado en el horario {schedule}'}

            # Validar y crear visitantes
            created_visitors = []
            for i, participant_data in enumerate(participants):
                print(f"DEBUG: Processing participant {i + 1}: {participant_data}")
                # Validar que los datos requeridos estén presentes
                if not participant_data:
                    return {'success': False, 'error': f'Datos del participante {i + 1} están vacíos'}
                
                if not participant_data.get('name'):
                    return {'success': False, 'error': f'El nombre del participante {i + 1} es obligatorio'}
                
                if not participant_data.get('dni'):
                    return {'success': False, 'error': f'El DNI del participante {i + 1} es obligatorio'}
                
                if not participant_data.get('age'):
                    return {'success': False, 'error': f'La edad del participante {i + 1} es obligatoria'}
                
                # Validar talla si es requerida
                if activity.requires_clothing and not participant_data.get('clothing_size'):
                    return {'success': False, 'error': f'La actividad requiere especificar talla de vestimenta para el participante {i + 1}'}

                # Validar edad mínima por actividad
                min_age = get_min_age(activity.name)
                if participant_data.get('age') is None or participant_data.get('age') < min_age:
                    return {'success': False, 'error': f'La edad mínima para {activity.name} es {min_age} años (participante {i + 1})'}

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
    activities_payload = []
    for activity in activities:
        turn_capacity = get_turn_capacity(activity.name)
        # Cupos por turno
        per_schedule = {}
        for s in activity.schedules:
            reg = Registration.query.filter_by(activity_id=activity.id, schedule=s).count()
            per_schedule[s] = {
                'registered_count': reg,
                'available_capacity': max(0, turn_capacity - reg),
                'turn_capacity': turn_capacity
            }

        activity_dict = activity.to_dict()
        activity_dict['per_schedule_capacity'] = per_schedule
        activity_dict['turn_capacity'] = turn_capacity
        activities_payload.append(activity_dict)

    return jsonify(activities_payload)

@app.route('/api/activities', methods=['POST'])
def create_activity():
    data = request.json
    
    # Si no se proporcionan horarios, generar todos los de 30 minutos
    provided_schedules = data.get('schedules')
    default_schedules = generate_time_slots()

    activity = Activity(
        name=data['name'],
        capacity=data['capacity'],
        schedules=provided_schedules if provided_schedules else default_schedules,
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