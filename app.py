from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import sqlite3
import os

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect('buses_managua.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Tabla de buses
    c.execute('''
        CREATE TABLE IF NOT EXISTS buses (
            bus_id TEXT PRIMARY KEY,
            lat REAL,
            lng REAL,
            last_update TEXT,
            driver_phone TEXT,
            route_name TEXT,
            status TEXT DEFAULT 'activo'
        )
    ''')
    
    # Tabla de paradas
    c.execute('''
        CREATE TABLE IF NOT EXISTS stops (
            stop_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            lat REAL,
            lng REAL,
            order_num INTEGER,
            route_name TEXT
        )
    ''')
    
    # Insertar paradas de Managua
    stops_data = [
        # Ruta SIS
        ('Terminal San Isidro', 12.1900, -86.3000, 1, 'SIS'),
        ('San Isidro Sur', 12.1850, -86.2950, 2, 'SIS'),
        ('Mini Agencia Ponce', 12.1800, -86.2900, 3, 'SIS'),
        ('Cementerio San Isidro', 12.1750, -86.2850, 4, 'SIS'),
        ('Iglesia San Isidro', 12.1700, -86.2800, 5, 'SIS'),
        ('San Isidro Norte', 12.1650, -86.2750, 6, 'SIS'),
        ('Bosques Del Terraza', 12.1600, -86.2700, 7, 'SIS'),
        ('Galerias Santo Domingo', 12.1400, -86.2500, 8, 'SIS'),
        ('Movistar', 12.1350, -86.2480, 9, 'SIS'),
        ('Metrocentro', 12.1150, -86.2380, 10, 'SIS'),
        ('Rotonda Ruben Dario', 12.1100, -86.2350, 11, 'SIS'),
        ('Policia Distrito I', 12.0900, -86.2250, 12, 'SIS'),
        # Ruta Masaya-Managua
        ('Terminal Masaya', 11.9740, -86.0950, 1, 'Masaya-Managua'),
        ('El Nido', 11.9800, -86.1000, 2, 'Masaya-Managua'),
        ('Semáforos La Inca', 12.0000, -86.1100, 3, 'Masaya-Managua'),
        ('ENATREL', 12.1545, -86.1456, 4, 'Masaya-Managua'),
        ('Monte Fresco', 12.1550, -86.1470, 5, 'Masaya-Managua'),
        ('Mercado Mayoreo', 12.1600, -86.1500, 6, 'Masaya-Managua'),
    ]
    
    for stop in stops_data:
        c.execute('''
            INSERT OR IGNORE INTO stops (name, lat, lng, order_num, route_name)
            VALUES (?, ?, ?, ?, ?)
        ''', stop)
    
    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada")

# Inicializar base de datos
init_database()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/driver')
def driver():
    return render_template('driver.html')

@app.route('/api/update_location', methods=['POST'])
def update_location():
    try:
        data = request.json
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO buses 
            (bus_id, lat, lng, last_update, driver_phone, route_name, status)
            VALUES (?, ?, ?, ?, ?, ?, 'activo')
        ''', (data['bus_id'], data['lat'], data['lng'], 
              datetime.now().isoformat(), data['driver_phone'], data['route_name']))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/get_buses')
def get_buses():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        time_threshold = (datetime.now() - timedelta(minutes=3)).isoformat()
        c.execute('''
            SELECT bus_id, lat, lng, last_update, route_name 
            FROM buses 
            WHERE last_update > ? AND status = 'activo'
        ''', (time_threshold,))
        buses = [dict(row) for row in c.fetchall()]
        conn.close()
        return jsonify(buses)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_stops')
def get_stops():
    try:
        route = request.args.get('route', 'SIS')
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            SELECT stop_id, name, lat, lng, order_num, route_name 
            FROM stops WHERE route_name = ? ORDER BY order_num
        ''', (route,))
        stops = [dict(row) for row in c.fetchall()]
        conn.close()
        return jsonify(stops)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
