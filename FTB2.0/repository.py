from typing import Dict, Any, Optional
from contextlib import closing
import pandas as pd
from db import get_conn

def df(sql: str, params: tuple = ()) -> pd.DataFrame:
    with closing(get_conn()) as conn:
        return pd.read_sql_query(sql, conn, params=params)

def execute(sql: str, params: tuple = ()) -> None:
    with closing(get_conn()) as conn:
        conn.execute(sql, params)
        conn.commit()

def upsert_player(data: Dict[str, Any], player_id: Optional[int] = None) -> float:
    stats = [int(data[k]) for k in ["rit","tir","pas","reg","def","fis"]]
    media = round(sum(stats) / len(stats), 2)
    if player_id is None:
        execute("""INSERT INTO players(nombre,rit,tir,pas,reg,def,fis,media,activo)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (data["nombre"],*stats,media,int(data.get("activo",1))))
    else:
        execute("""UPDATE players
                   SET nombre=?, rit=?, tir=?, pas=?, reg=?, def=?, fis=?, media=?, activo=?
                   WHERE id=?""",
                (data["nombre"],*stats,media,int(data.get("activo",1)),player_id))
    return media

def delete_player(player_id: int) -> None:
    execute("DELETE FROM players WHERE id=?", (player_id,))

def toggle_activo(player_id: int, new_value: bool) -> None:
    execute("UPDATE players SET activo=? WHERE id=?", (1 if new_value else 0, player_id))

def all_players(order: str = "nombre") -> pd.DataFrame:
    return df(f"SELECT * FROM players ORDER BY {order}")

def active_players_desc_media() -> pd.DataFrame:
    return df("SELECT * FROM players WHERE activo=1 ORDER BY media DESC")
