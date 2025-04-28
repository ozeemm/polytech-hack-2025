import pandas as pd
import matplotlib.cm as cm
import matplotlib.colors as mcolors

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect('Hack.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_speed_colored_route_geojson(data):
    points = pd.DataFrame(data)

    speed_min = points['speed'].min()
    speed_max = points['speed'].max()
    norm = mcolors.Normalize(vmin=speed_min, vmax=speed_max)
    colormap = cm.RdYlGn
    
    geojson_data = {
        "type": "FeatureCollection",
        "speed_min": speed_min,
        "speed_max": speed_max,
        "features": []
    }

    # Для каждого отрезка (между точками) добавляем его в GeoJSON
    for i in range(len(points) - 1):
        point1 = points.iloc[i]
        point2 = points.iloc[i + 1]

        # Цвет по скорости
        speed = point1['speed']  # Берем скорость из первой точки отрезка
        rgba = colormap(norm(speed))  # Получаем RGBA цвет
        hex_color = mcolors.to_hex(rgba)  # Преобразуем в HEX

        # Создаём GeoJSON объект для отрезка
        feature = {
            "type": "Feature",
            "properties": {
                "speed": speed,
                "color": hex_color
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [point1['lon'], point1['lat']],
                    [point2['lon'], point2['lat']]
                ]
            }
        }
        geojson_data["features"].append(feature)

    return geojson_data

@app.route("/", methods=["GET"])
def index():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM DataWithClean WHERE uuid = 27648")
        rows = cursor.fetchall()

        result = [dict(row) for row in rows]

        return jsonify(result)


@app.route("/", methods=["POST"])
def index1():
    data = request.json

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM DataWithClean WHERE route = ? ORDER BY uuid, signal_time", (data["RouteID"],))
        rows = cursor.fetchall()

        result = [dict(row) for row in rows]

        return get_speed_colored_route_geojson(result)

if __name__ == "__main__":
    app.run(debug=True)