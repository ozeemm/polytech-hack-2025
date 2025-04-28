from flask import Flask, jsonify
import sqlite3
import json


app = Flask(__name__)

@app.route("/")
def index():
    conn = sqlite3.connect('Hack.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM DataWithClean Limit 5")
    rows = cursor.fetchall()
    conn.close()

    result = [dict(row) for row in rows]

    return jsonify(result)