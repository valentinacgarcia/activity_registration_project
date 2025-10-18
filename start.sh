#!/bin/bash

echo "🏃‍♀️ Iniciando Sistema de Registro de Actividades"
echo "================================================"

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado. Por favor instálalo primero."
    exit 1
fi

# Verificar si pip está instalado
if ! command -v pip &> /dev/null; then
    echo "❌ pip no está instalado. Por favor instálalo primero."
    exit 1
fi

echo "📦 Configurando backend..."
cd backend

# Activar entorno virtual
if [ -d "venv" ]; then
    echo "🔧 Activando entorno virtual..."
    source venv/bin/activate
else
    echo "❌ Entorno virtual no encontrado. Creando uno nuevo..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Instalando dependencias..."
    pip install -r requirements.txt
fi

echo "🌱 Poblando base de datos con datos de ejemplo..."
python seed_data.py

echo "🧪 Ejecutando todos los tests..."
python -m pytest -v

if [ $? -eq 0 ]; then
    echo "✅ Todos los tests pasaron correctamente!"
else
    echo "❌ Algunos tests fallaron. Revisa los errores arriba."
    exit 1
fi

echo ""
echo "🚀 Iniciando servidor backend en puerto 5000..."
echo "📱 Abre http://localhost:8000 en tu navegador para el frontend"
echo "🔧 API disponible en http://localhost:5000"
echo ""
echo "Para detener el servidor, presiona Ctrl+C"
echo ""

# Iniciar el servidor Flask en background
python app.py &
BACKEND_PID=$!

# Esperar un momento para que el backend se inicie
sleep 3

# Iniciar servidor HTTP simple para el frontend
cd ../frontend
python -m http.server 8000 &
FRONTEND_PID=$!

# Función para limpiar procesos al salir
cleanup() {
    echo ""
    echo "🛑 Deteniendo servidores..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servidores detenidos"
    exit 0
}

# Capturar Ctrl+C
trap cleanup SIGINT

echo "✅ Sistema iniciado correctamente!"
echo "🌐 Frontend: http://localhost:8000"
echo "🔧 Backend API: http://localhost:5000"
echo ""
echo "Presiona Ctrl+C para detener ambos servidores"

# Mantener el script corriendo
wait
