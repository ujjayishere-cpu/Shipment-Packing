from flask import Flask, render_template, request, jsonify, send_file
import sqlite3, pandas as pd
from datetime import datetime

app = Flask(__name__)
DB = 'data/scans.db'

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''
      CREATE TABLE IF NOT EXISTS scans (
        id INTEGER PRIMARY KEY,
        pallet TEXT,
        order_no TEXT, phase TEXT, part TEXT,
        qty INTEGER, timestamp TEXT
      )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html', company="John Silva")

@app.route('/scan', methods=['POST'])
def scan():
    data = request.json
    pallet = data['pallet']
    order = data['order_no']
    phase = data['phase']
    part = data['part']
    qty = data.get('qty', 1)
    ts = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''
      INSERT INTO scans (pallet, order_no, phase, part, qty, timestamp)
      VALUES (?, ?, ?, ?, ?, ?)
    ''', (pallet, order, phase, part, qty, ts))
    conn.commit()
    conn.close()
    return jsonify(status="ok")

@app.route('/export')
def export():
    df = pd.read_sql('SELECT * FROM scans', sqlite3.connect(DB))
    out = 'data/scans.xlsx'
    df.to_excel(out, index=False)
    return send_file(out, download_name='scans.xlsx')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
