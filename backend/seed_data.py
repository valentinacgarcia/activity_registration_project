#!/usr/bin/env python3
"""
Script para poblar la base de datos con datos de ejemplo
"""

from app import app, db, Activity

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
        activities = [
            Activity(
                name="Tirolesa",
                capacity=8,
                schedules=["09:00", "11:00", "15:00", "17:00"],
                requirements={"nivel": "intermedio", "equipamiento": "arnés y casco"},
                requires_clothing=True
            ),
            Activity(
                name="Safari",
                capacity=15,
                schedules=["10:00", "14:00", "16:00"],
                requirements={"nivel": "todos", "equipamiento": "binoculares"},
                requires_clothing=False
            ),
            Activity(
                name="Palestra",
                capacity=6,
                schedules=["09:30", "11:30", "15:30", "17:30"],
                requirements={"nivel": "principiante", "equipamiento": "zapatos de escalada"},
                requires_clothing=True
            ),
            Activity(
                name="Jardinería",
                capacity=12,
                schedules=["08:00", "10:00", "14:00", "16:00"],
                requirements={"nivel": "todos", "equipamiento": "guantes y herramientas"},
                requires_clothing=True
            )
        ]
        
        for activity in activities:
            db.session.add(activity)
        
        db.session.commit()
        print(f"✅ Se crearon {len(activities)} actividades de ejemplo")
        print("\nActividades creadas:")
        for activity in activities:
            print(f"  - {activity.name} (Cupos: {activity.capacity})")

if __name__ == "__main__":
    seed_data()
