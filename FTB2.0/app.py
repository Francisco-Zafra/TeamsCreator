from db import init_db, get_conn
from repository import upsert_player
import streamlit as st
from ui import header, tab_players, tab_teams

def seed_if_empty():
    from contextlib import closing
    with closing(get_conn()) as conn:
        c = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        if c == 0:
            upsert_player({
                "nombre": "Guti's Boyfriend",
                "rit": 83, "tir": 83, "pas": 83, "reg": 83, "def": 83, "fis": 83, "activo": 1
            })

def main():
    header()
    init_db()
    seed_if_empty()
    tab1, tab2 = st.tabs(["📋 Jugadores", "🧮 Creación de equipos"])
    with tab1: tab_players()
    with tab2: tab_teams()

if __name__ == "__main__":
    main()
