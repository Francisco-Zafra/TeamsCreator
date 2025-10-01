from itertools import combinations
import sqlite3
import random

def generate_balanced_teams(db_path, umbral, num_per_team):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id, nombre, (ritmo+tiro+pase+regate+defensa+fisico)/6.0 as media FROM jugadores WHERE activo=1")
    players = c.fetchall()
    conn.close()

    if len(players) < num_per_team * 2:
        return []

    valid_teams = []
    for combo in combinations(players, num_per_team):
        rest = [p for p in players if p not in combo]
        for other in combinations(rest, num_per_team):
            media1 = sum([p[2] for p in combo]) / num_per_team
            media2 = sum([p[2] for p in other]) / num_per_team
            if abs(media1 - media2) <= umbral:
                valid_teams.append((combo, other))

    return random.choice(valid_teams) if valid_teams else []
