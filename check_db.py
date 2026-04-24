import sqlite3

conn = sqlite3.connect('vehicle_log.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute('SELECT COUNT(*) as total FROM vehicle_logs')
total = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM vehicle_logs WHERE event_type='ENTRY'")
entries = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM vehicle_logs WHERE event_type='EXIT'")
exits = cur.fetchone()[0]

print(f'Total DB rows : {total}')
print(f'ENTRY events  : {entries}')
print(f'EXIT events   : {exits}')
print()
print('--- Last 10 events ---')
cur.execute('SELECT id, timestamp, camera_id, event_type, license_plate FROM vehicle_logs ORDER BY timestamp DESC LIMIT 10')
for row in cur.fetchall():
    print(dict(row))

conn.close()
