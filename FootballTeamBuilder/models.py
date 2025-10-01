import sqlite3

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS jugadores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT,
                    ritmo INTEGER,
                    tiro INTEGER,
                    pase INTEGER,
                    regate INTEGER,
                    defensa INTEGER,
                    fisico INTEGER,
                    activo INTEGER DEFAULT 1
                )""")
    conn.commit()
    conn.close()

def get_all_players(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id, nombre, ritmo, tiro, pase, regate, defensa, fisico, activo, (ritmo+tiro+pase+regate+defensa+fisico)/6.0 as media FROM jugadores ORDER BY activo DESC, nombre ASC")
    rows = c.fetchall()
    conn.close()
    return rows

def add_player(db_path, data):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''INSERT INTO jugadores (nombre, ritmo, tiro, pase, regate, defensa, fisico) 
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (data['nombre'], data['ritmo'], data['tiro'], data['pase'],
               data['regate'], data['defensa'], data['fisico']))
    conn.commit()
    conn.close()

def update_player(db_path, player_id, data):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''UPDATE jugadores SET nombre=?, ritmo=?, tiro=?, pase=?, regate=?, defensa=?, fisico=? 
                 WHERE id=?''',
              (data['nombre'], data['ritmo'], data['tiro'], data['pase'],
               data['regate'], data['defensa'], data['fisico'], player_id))
    conn.commit()
    conn.close()

def delete_player(db_path, player_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM jugadores WHERE id=?", (player_id,))
    conn.commit()
    conn.close()

def toggle_player_active(db_path, player_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("UPDATE jugadores SET activo = 1 - activo WHERE id=?", (player_id,))
    conn.commit()
    conn.close()
