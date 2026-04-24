"""
Vehicle Records System — Live Web Dashboard
Run:  python dashboard.py
Open: http://localhost:5000

Served by Waitress — a production-grade WSGI server (no Flask dev warnings).
"""

import sqlite3
import os
from flask import Flask, render_template_string, jsonify
from waitress import serve          # production WSGI server

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'vehicle_log.db')

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vehicle Records System — Live Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:       #0d1117;
    --surface:  #161b22;
    --border:   #30363d;
    --accent:   #58a6ff;
    --green:    #3fb950;
    --red:      #f85149;
    --yellow:   #e3b341;
    --text:     #e6edf3;
    --muted:    #8b949e;
  }

  body {
    font-family: 'Inter', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    padding: 24px;
  }

  header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 32px;
  }
  .logo {
    width: 44px; height: 44px;
    background: linear-gradient(135deg, #1f6feb, #58a6ff);
    border-radius: 12px;
    display: grid; place-items: center;
    font-size: 22px;
  }
  h1 { font-size: 1.4rem; font-weight: 700; }
  .subtitle { font-size: 0.8rem; color: var(--muted); margin-top: 2px; }

  .live-badge {
    margin-left: auto;
    display: flex; align-items: center; gap: 6px;
    background: rgba(63,185,80,0.12);
    border: 1px solid rgba(63,185,80,0.4);
    color: var(--green);
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 0.75rem; font-weight: 600;
  }
  .dot {
    width: 8px; height: 8px;
    background: var(--green);
    border-radius: 50%;
    animation: pulse 1.4s infinite;
  }
  @keyframes pulse {
    0%,100% { opacity: 1; transform: scale(1); }
    50%      { opacity: 0.5; transform: scale(0.7); }
  }

  /* Stats cards */
  .stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    margin-bottom: 28px;
  }
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 22px;
    position: relative;
    overflow: hidden;
  }
  .card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
  }
  .card.total::before  { background: var(--accent); }
  .card.entry::before  { background: var(--green); }
  .card.exit::before   { background: var(--red); }
  .card.recent::before { background: var(--yellow); }

  .card-label {
    font-size: 0.72rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em;
    color: var(--muted); margin-bottom: 10px;
  }
  .card-value {
    font-size: 2.4rem; font-weight: 700; line-height: 1;
  }
  .card.total  .card-value { color: var(--accent); }
  .card.entry  .card-value { color: var(--green); }
  .card.exit   .card-value { color: var(--red); }
  .card.recent .card-value { color: var(--yellow); }
  .card-sub {
    font-size: 0.72rem; color: var(--muted); margin-top: 6px;
  }

  /* Table section */
  .table-header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 12px;
  }
  .table-title { font-size: 0.95rem; font-weight: 600; }
  .refresh-info { font-size: 0.72rem; color: var(--muted); }

  .table-wrap {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
  }
  table { width: 100%; border-collapse: collapse; }
  thead tr { background: #1c2128; }
  th {
    padding: 11px 16px;
    text-align: left;
    font-size: 0.72rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.07em;
    color: var(--muted);
    border-bottom: 1px solid var(--border);
  }
  td {
    padding: 12px 16px;
    font-size: 0.82rem;
    border-bottom: 1px solid #21262d;
  }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(255,255,255,0.03); }

  .badge {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 3px 10px; border-radius: 20px;
    font-size: 0.72rem; font-weight: 700;
    text-transform: uppercase;
  }
  .badge.entry { background: rgba(63,185,80,0.15); color: var(--green); }
  .badge.exit  { background: rgba(248,81,73,0.15);  color: var(--red); }

  .id-chip {
    background: rgba(88,166,255,0.12);
    color: var(--accent);
    padding: 2px 8px; border-radius: 6px;
    font-size: 0.75rem; font-weight: 600; font-family: monospace;
  }
  .plate-chip {
    background: rgba(227,179,65,0.12);
    color: var(--yellow);
    padding: 2px 8px; border-radius: 6px;
    font-size: 0.75rem; font-weight: 600; font-family: monospace;
  }
  .na { color: var(--muted); font-size: 0.75rem; }
  .ts { color: var(--muted); font-size: 0.78rem; font-family: monospace; }

  .empty {
    text-align: center; padding: 48px;
    color: var(--muted); font-size: 0.85rem;
  }

  footer {
    margin-top: 28px; text-align: center;
    font-size: 0.72rem; color: var(--muted);
  }
</style>
</head>
<body>

<header>
  <div class="logo">🚗</div>
  <div>
    <h1>Vehicle Records System</h1>
    <div class="subtitle">Real-time surveillance &amp; entry/exit logging</div>
  </div>
  <div class="live-badge"><div class="dot"></div> LIVE</div>
</header>

<div class="stats" id="stats">
  <div class="card total">
    <div class="card-label">Total Events</div>
    <div class="card-value" id="stat-total">—</div>
    <div class="card-sub">All time in database</div>
  </div>
  <div class="card entry">
    <div class="card-label">Total Entries</div>
    <div class="card-value" id="stat-entry">—</div>
    <div class="card-sub">Vehicles entered</div>
  </div>
  <div class="card exit">
    <div class="card-label">Total Exits</div>
    <div class="card-value" id="stat-exit">—</div>
    <div class="card-sub">Vehicles exited</div>
  </div>
  <div class="card recent">
    <div class="card-label">Last Updated</div>
    <div class="card-value" id="stat-time" style="font-size:1.1rem; margin-top:6px;">—</div>
    <div class="card-sub">Auto-refreshes every 3s</div>
  </div>
</div>

<div class="table-header">
  <div class="table-title">📋 Recent Vehicle Events</div>
  <div class="refresh-info" id="refresh-info">Fetching...</div>
</div>

<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>Timestamp</th>
        <th>Camera</th>
        <th>Event</th>
        <th>License Plate</th>
      </tr>
    </thead>
    <tbody id="log-body">
      <tr><td colspan="5" class="empty">Loading data...</td></tr>
    </tbody>
  </table>
</div>

<footer>Vehicle Records System &mdash; Built with Python, YOLOv8, OpenCV &amp; SQLite</footer>

<script>
  function fetchData() {
    fetch('/api/logs')
      .then(r => r.json())
      .then(data => {
        document.getElementById('stat-total').textContent = data.total;
        document.getElementById('stat-entry').textContent = data.entries;
        document.getElementById('stat-exit').textContent  = data.exits;
        document.getElementById('stat-time').textContent  =
          new Date().toLocaleTimeString();
        document.getElementById('refresh-info').textContent =
          `Showing last ${data.logs.length} events · refreshed just now`;

        const tbody = document.getElementById('log-body');
        if (data.logs.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" class="empty">No events yet — run <code>python src/main.py</code> first.</td></tr>';
          return;
        }

        tbody.innerHTML = data.logs.map(row => `
          <tr>
            <td><span class="id-chip">${row.id}</span></td>
            <td class="ts">${row.timestamp}</td>
            <td>${row.camera_id}</td>
            <td>
              <span class="badge ${row.event_type.toLowerCase()}">
                ${row.event_type === 'ENTRY' ? '↘' : '↗'} ${row.event_type}
              </span>
            </td>
            <td>${row.license_plate
                  ? `<span class="plate-chip">${row.license_plate}</span>`
                  : '<span class="na">N/A</span>'}</td>
          </tr>`).join('');
      })
      .catch(() => {
        document.getElementById('refresh-info').textContent = 'Connection error — retrying...';
      });
  }

  fetchData();
  setInterval(fetchData, 3000);   // auto-refresh every 3 seconds
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/logs')
def api_logs():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM vehicle_logs")
        total = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM vehicle_logs WHERE event_type='ENTRY'")
        entries = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM vehicle_logs WHERE event_type='EXIT'")
        exits = cur.fetchone()[0]

        cur.execute(
            "SELECT id, timestamp, camera_id, event_type, license_plate "
            "FROM vehicle_logs ORDER BY timestamp DESC LIMIT 50"
        )
        logs = [dict(r) for r in cur.fetchall()]
        conn.close()

        return jsonify(total=total, entries=entries, exits=exits, logs=logs)
    except Exception as e:
        return jsonify(error=str(e), total=0, entries=0, exits=0, logs=[])

if __name__ == '__main__':
    HOST = '0.0.0.0'   # accessible on local network too
    PORT = 8080         # port 5000 is used by FaceAttend — using 8080 here

    print("\n" + "="*55)
    print("  Vehicle Records Dashboard")
    print("  Powered by Waitress (production WSGI server)")
    print("="*55)
    print(f"  Local    : http://localhost:8080")
    print(f"  Network  : http://YOUR_IP:8080  (share with recruiter on same network)")
    print(f"  Data     : auto-refreshes every 3 seconds from SQLite DB")
    print("  Stop     : Ctrl+C")
    print("="*55 + "\n")

    # Waitress — production-grade, no dev warnings, multi-threaded
    serve(app, host=HOST, port=PORT, threads=4)

