#!/usr/bin/env python3
"""
Script para poblar la base de datos con datos de ejemplo
"""

from app import app, db, Activity, generate_time_slots

def seed_data():
    """Poblar la base de datos con actividades de ejemplo"""
    with app.app_context():
        # Crear la base de datos si no existe
        db.create_all()
        
        # Verificar si ya hay datos
        if Activity.query.count() > 0:
            print("La base de datos ya contiene datos. Saltando...")
            return
        
        # Crear actividades de ejemplo según los criterios de aceptación
        # Slots de 30 minutos entre 09:00 y 18:00
        slots = generate_time_slots()

        # Todas las actividades con todos los slots del día
        activities = [
            Activity(
                name="Tirolesa",
                capacity=8,
                schedules=slots,
                requirements={"nivel": "intermedio", "equipamiento": "arnés y casco"},
                requires_clothing=True
            ),
            Activity(
                name="Safari",
                capacity=15,
                schedules=slots,
                requirements={"nivel": "todos", "equipamiento": "binoculares"},
                requires_clothing=False
            ),
            Activity(
                name="Palestra",
                capacity=6,
                schedules=slots,
                requirements={"nivel": "principiante", "equipamiento": "zapatos de escalada"},
                requires_clothing=True
            ),
            Activity(
                name="Jardinería",
                capacity=12,
                schedules=slots,
                requirements={"nivel": "todos", "equipamiento": "guantes y herramientas"},
                requires_clothing=False
            )
        ]
        
        for activity in activities:
            db.session.add(activity)
        
        db.session.commit()
        print(f"Se crearon {len(activities)} actividades de ejemplo")
        print("\nActividades creadas:")
        for activity in activities:
            print(f"  - {activity.name} (Cupos: {activity.capacity})")

if __name__ == "__main__":
    seed_data()