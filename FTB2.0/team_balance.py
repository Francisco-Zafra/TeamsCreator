from typing import List, Dict, Any, Tuple
from itertools import combinations
import random

def greedy_two_teams(players: List[Dict[str, Any]]) -> Tuple[list, list]:
    """
    Asigna por orden de mayor a menor media al equipo con menor suma actual.
    """
    p = sorted(players, key=lambda x: x["media"], reverse=True)
    t1, t2 = [], []
    s1 = s2 = 0.0
    for pl in p:
        if s1 <= s2:
            t1.append(pl); s1 += pl["media"]
        else:
            t2.append(pl); s2 += pl["media"]
    return t1, t2

def combinatorial_two_teams(players: List[Dict[str, Any]], umbral: float, num_per_team: int):
    """
    Explora combinaciones de tamaño fijo y devuelve una pareja de equipos cuya diferencia
    de medias sea <= umbral (elige aleatoriamente entre las válidas). Devuelve ([],[]) si no hay.
    """
    if len(players) < num_per_team * 2:
        return [], []
    valid = []
    compact = [(i, p["nombre"], float(p["media"])) for i, p in enumerate(players)]
    for combo in combinations(compact, num_per_team):
        remaining = [x for x in compact if x not in combo]
        for other in combinations(remaining, num_per_team):
            m1 = sum(x[2] for x in combo) / num_per_team
            m2 = sum(x[2] for x in other) / num_per_team
            if abs(m1 - m2) <= umbral:
                ids1 = {x[0] for x in combo}
                ids2 = {x[0] for x in other}
                team1 = [players[i] for i in ids1]
                team2 = [players[i] for i in ids2]
                valid.append((team1, team2))
    return random.choice(valid) if valid else ([], [])
