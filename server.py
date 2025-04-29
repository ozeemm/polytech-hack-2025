from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3

from geojson_func import *

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect('Hack.db')
    conn.row_factory = sqlite3.Row
    return conn



@app.route("/api/getTransportFilters", methods=["GET"])
def index():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT vehicle_type, route FROM DataWithClean ORDER BY vehicle_type, route")
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]

        names = {'bus': 'Автобус', 'minibus': 'Маршрутка','tramway': 'Трамвай','trolleybus': 'Троллейбус'}

        res = dict() 
        for item in result:
            if item["vehicle_type"] not in res:
                res[item["vehicle_type"]] = dict()
                res[item["vehicle_type"]]["key"] = item["vehicle_type"]
                res[item["vehicle_type"]]["title"] = names[item["vehicle_type"]]
                res[item["vehicle_type"]]["routes"] = list()
            res[item["vehicle_type"]]["routes"].append(item["route"])
        
        AllFilters = list()
        for key in res.keys():
            AllFilters.append(res[key])

        return AllFilters

@app.route("/api/getDatesFilters", methods=["GET"])
def getDistDates():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("Select Distinct strftime('%m', signal_time) as month, strftime('%Y', signal_time) as year FROM DataWithClean")
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]

        return result


@app.route("/", methods=["POST"])
def index1():
    data = request.json

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM DataWithClean WHERE route = ? ORDER BY uuid, signal_time", (data["RouteID"],))
        rows = cursor.fetchall()

        result = [dict(row) for row in rows]

        return get_speed_colored_route_geojson(result)
    
@app.route("/api/Filter", methods=["POST"])
def ReturnWithFilters():
    data = request.json

    st = data["timeStart"]
    et = data["timeEnd"]

    monthes = ""
    for date in data["dates"]:
        monthes+="'" + date.split("-")[1] + "', "
    monthes = monthes[:-2]
    years = ""
    for date in data["dates"]:
        years+= "'" + date.split("-")[0] + "', "
    years = years[:-2]


    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""Select strftime('%m', signal_time) as month, 
                            strftime('%Y', signal_time) as year, time(signal_time) as time, 
                            uuid, lat, lon, vehicle_type, route, speed, direction, signal_time
                            FROM DataWithClean
                            WHERE time > ? AND time < ? 
                            AND month IN ({monthes}) AND year IN ({years})          
                            ORDER BY uuid, signal_time;""", (st, et,))
        
        rows = cursor.fetchall()

        result = [dict(row) for row in rows]

        busResult = list()
        for item in result:
            if item["vehicle_type"] == "bus":
                if item["route"] in data["routes"]["bus"]:
                    busResult.append(item)
        
        tramResult = list()
        for item in result:
            if item["vehicle_type"] == "tramway":
                if item["route"] in data["routes"]["tramway"]:
                    tramResult.append(item)
        
        trolResult = list()
        for item in result:
            if item["vehicle_type"] == "trolleybus":
                if item["route"] in data["routes"]["trolleybus"]:
                    trolResult.append(item)

        miniBusResult = list()
        for item in result:
            if item["vehicle_type"] == "minibus":
                if item["route"] in data["routes"]["minibus"]:
                    miniBusResult.append(item)

        AllTransport = busResult + tramResult + trolResult + miniBusResult


        return  transfer_nearest_properties(generate_geojson(AllTransport, data["colorMode"]))

if __name__ == "__main__":
    app.run(debug=True)