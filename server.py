from flask import Flask, jsonify, request
import sqlite3
import json


app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    conn = sqlite3.connect('Hack.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM DataWithClean WHERE uuid = 27648")
    rows = cursor.fetchall()
    conn.close()

    result = [dict(row) for row in rows]

    return jsonify(result)


@app.route("/", methods=["POST"])
def index1():
    data = request.json
    conn = sqlite3.connect('Hack.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM DataWithClean WHERE route = {data["RouteID"]} LIMIT 1000")
    rows = cursor.fetchall()
    conn.close()

    result = [dict(row) for row in rows]

    return jsonify(result)

