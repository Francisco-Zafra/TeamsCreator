import streamlit as st
import textwrap
import pandas as pd
from repository import (
    all_players, active_players_desc_media, upsert_player,
    toggle_activo, delete_player
)
from team_balance import greedy_two_teams, combinatorial_two_teams

# --- Helper de recarga compatible ---
def _rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

def header():
    st.set_page_config(page_title="WEFA Teams", page_icon="⚽", layout="wide")
    with open("assets/style.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    st.title("WEFA | Gestor de jugadores y creación de equipos")

import streamlit as st
import pandas as pd
from repository import (
    all_players, active_players_desc_media, upsert_player,
    toggle_activo, delete_player
)
from team_balance import greedy_two_teams, combinatorial_two_teams

# --- Helper de recarga compatible ---
def _rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

def header():
    st.set_page_config(page_title="WEFA Teams", page_icon="⚽", layout="wide")
    with open("assets/style.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    st.title("WEFA | Gestor de jugadores y creación de equipos")

def tab_players():
    import streamlit as st
    import pandas as pd
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
    # OJO: incluimos toggle_activo aquí dentro para usarlo en los botones de mover
    from repository import all_players, upsert_player, delete_player, toggle_activo

    st.subheader("Gestión de jugadores")

    # --- CSS: tipografía un poco mayor y padding ---
    st.markdown("""
    <style>
    .ag-theme-streamlit .ag-root-wrapper,
    .ag-theme-streamlit .ag-cell,
    .ag-theme-streamlit .ag-header-cell-label {
      font-size: 15px;
      line-height: 1.25;
    }
    .ag-theme-streamlit .ag-cell {
      padding-top: 6px;
      padding-bottom: 6px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Datos
    df = all_players().copy()
    # Dividimos por activo, pero ya NO mostramos la columna 'activo' en las tablas
    df_active = df[df["activo"] == 1].reset_index(drop=True)
    df_inactive = df[df["activo"] == 0].reset_index(drop=True)

    def build_grid(df_section: pd.DataFrame, key: str, height: int = 420):
        """Grid AgGrid: sort, filter, edición inline y selección por checkbox (sin columna 'activo')."""
        if df_section.empty:
            st.info("No hay jugadores en esta lista.")
            return df_section, []

        # Vista SIN la columna 'activo'
        view = df_section[["id","nombre","rit","tir","pas","reg","def","fis","media"]].copy()

        gb = GridOptionsBuilder.from_dataframe(view)
        gb.configure_default_column(resizable=True, sortable=True, filter=True, editable=False)

        # id oculto; media no editable; resto editable
        gb.configure_column("id", header_name="ID", hide=True, editable=False)

        # Checkboxes en la columna 'nombre' + checkbox maestro
        gb.configure_column(
            "nombre",
            header_name="Nombre",
            editable=True,
            checkboxSelection=True,
            headerCheckboxSelection=True,
            headerCheckboxSelectionFilteredOnly=True
        )

        for col in ["rit","tir","pas","reg","def","fis"]:
            gb.configure_column(col, header_name=col.capitalize(), editable=True, type=["numericColumn"])
        gb.configure_column("media", header_name="Media", editable=False, type=["numericColumn"])

        # Selección múltiple por checkbox
        gb.configure_selection(selection_mode="multiple", use_checkbox=True)
        gb.configure_grid_options(suppressRowClickSelection=True, rowSelection="multiple")

        grid_options = gb.build()

        grid_response = AgGrid(
            view,
            gridOptions=grid_options,
            theme="streamlit",
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.MODEL_CHANGED | GridUpdateMode.SELECTION_CHANGED,
            fit_columns_on_grid_load=True,
            enable_enterprise_modules=False,
            allow_unsafe_jscode=False,
            height=height,
            key=f"grid_{key}",
        )

        edited_df = pd.DataFrame(grid_response["data"])
        selected_rows = grid_response.get("selected_rows", []) or []
        return edited_df, selected_rows

    # ---- Activos ----
    st.markdown("### Jugadores Activos")
    edited_active, selected_active = build_grid(df_active, key="active")

    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("→ Pasar a inactivos"):
            if selected_active:
                for r in selected_active:
                    toggle_activo(int(r["id"]), False)
                st.success(f"Movidos a inactivos: {len(selected_active)}")
                st.rerun()
            else:
                st.warning("Selecciona al menos una fila.")
    with c2:
        if st.button("🗑️ Eliminar seleccionados (Activos)"):
            if selected_active:
                for r in selected_active:
                    delete_player(int(r["id"]))
                st.success(f"Eliminado(s): {len(selected_active)} jugador(es).")
                st.rerun()
            else:
                st.warning("Selecciona al menos una fila.")

    # ---- Inactivos ----
    st.markdown("### Jugadores Inactivos")
    edited_inactive, selected_inactive = build_grid(df_inactive, key="inactive")

    c3, c4 = st.columns([1,1])
    with c3:
        if st.button("← Pasar a activos"):
            if selected_inactive:
                for r in selected_inactive:
                    toggle_activo(int(r["id"]), True)
                st.success(f"Movidos a activos: {len(selected_inactive)}")
                st.rerun()
            else:
                st.warning("Selecciona al menos una fila.")
    with c4:
        if st.button("🗑️ Eliminar seleccionados (Inactivos)"):
            if selected_inactive:
                for r in selected_inactive:
                    delete_player(int(r["id"]))
                st.success(f"Eliminado(s): {len(selected_inactive)} jugador(es).")
                st.rerun()
            else:
                st.warning("Selecciona al menos una fila.")

    # ---- Persistencia de ediciones inline (recalcula media en servidor) ----
    def persist_changes(original: pd.DataFrame, edited: pd.DataFrame) -> bool:
        if edited.empty:
            return False
        orig = original.set_index("id")
        edt  = edited.set_index("id")
        common = orig.index.intersection(edt.index)
        changed = False
        for i in common:
            o, e = orig.loc[i], edt.loc[i]
            # Ya NO comparamos 'activo' porque lo gestionan los botones de mover
            fields = ["nombre","rit","tir","pas","reg","def","fis"]
            if any(str(o[k]) != str(e[k]) for k in fields):
                upsert_player({
                    "nombre": str(e["nombre"]).strip(),
                    "rit": int(e["rit"]), "tir": int(e["tir"]), "pas": int(e["pas"]),
                    "reg": int(e["reg"]), "def": int(e["def"]), "fis": int(e["fis"]),
                    # no tocar 'activo' aquí
                }, player_id=int(i))
                changed = True
        return changed

    changed_any  = persist_changes(df_active, edited_active)
    changed_any |= persist_changes(df_inactive, edited_inactive)
    if changed_any:
        st.success("Cambios guardados.")
        st.rerun()

    # ---- Formulario SOLO para añadir ----
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("### Añadir jugador")

    with st.form("player_form_add", clear_on_submit=True):
        nombre = st.text_input("Nombre", value="")
        colz = st.columns(6)
        rit = colz[0].number_input("Rit", 0, 99, 50)
        tir = colz[1].number_input("Tir", 0, 99, 50)
        pas = colz[2].number_input("Pas", 0, 99, 50)
        reg = colz[3].number_input("Reg", 0, 99, 50)
        deff = colz[4].number_input("Def", 0, 99, 50)
        fis = colz[5].number_input("Fís", 0, 99, 50)
        activo_nuevo = st.checkbox("Crear como ACTIVO", value=True)

        submitted = st.form_submit_button("Guardar nuevo")
        if submitted:
            if not nombre.strip():
                st.error("El nombre es obligatorio.")
            else:
                media = upsert_player({
                    "nombre": nombre.strip(),
                    "rit": int(rit), "tir": int(tir), "pas": int(pas),
                    "reg": int(reg), "def": int(deff), "fis": int(fis),
                    "activo": 1 if bool(activo_nuevo) else 0,
                }, player_id=None)  # siempre INSERT
                st.success(f"Jugador añadido. Media: {media:.2f}")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)



def _team_table(col, team, title, captain_id=None):
    import pandas as pd
    with col:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write(f"### {title}")
        if not team:
            st.write("_Vacío_")
        else:
            rows = []
            for p in team:
                nombre = p["nombre"]
                if captain_id is not None and p.get("id") == captain_id:
                    nombre = f"{nombre} 👑"
                rows.append({
                    "Nombre": nombre,
                    "Media": p["media"],
                    "Rit": p["rit"],
                    "Tir": p["tir"],
                    "Pas": p["pas"],
                    "Reg": p["reg"],
                    "Def": p["def"],
                    "Fís": p["fis"],
                })
            st.dataframe(
                pd.DataFrame(rows).set_index("Nombre"),
                use_container_width=True, hide_index=False
            )
        st.markdown('</div>', unsafe_allow_html=True)

def tab_teams():
    import streamlit as st
    import random
    from itertools import combinations
    from html import escape

    st.subheader("Creación de equipos")
    players_df = active_players_desc_media()
    if players_df.empty:
        st.info("No hay jugadores activos. Activa jugadores en la pestaña de Jugadores.")
        return

    players = players_df.to_dict(orient="records")
    n = len(players)
    if n < 2:
        st.warning("Se necesitan al menos 2 jugadores activos.")
        return

    # --- Opciones de equipos con emoji ---
    TEAM_CHOICES = [
        {"name": "Avispas F.C.",   "emoji": "🐝", "label": "🐝 Avispas F.C."},
        {"name": "C.D. Jabalies",  "emoji": "🐗", "label": "🐗 C.D. Jabalies"},
        {"name": "Pingüinardos",   "emoji": "🐧", "label": "🐧 Pingüinardos"},
        {"name": "Beetles",        "emoji": "🪲", "label": "🪲 Beetles"},
        {"name": "TiburOnes",      "emoji": "🦈", "label": "🦈 TiburOnes"},
        {"name": "Pandas F.C.",    "emoji": "🐼", "label": "🐼 Pandas F.C."},
        {"name": "Real Flamingo",  "emoji": "🦩", "label": "🦩 Real Flamingo"},
        {"name": "Patos C.F.",     "emoji": "🦆", "label": "🦆 Patos C.F."},
    ]

    # --- Selección de capitanes + nombre de equipo ---
    opts_caps = [{"id": None, "label": "— Ninguno —"}] + [
        {"id": p["id"], "label": f"{p['nombre']} (media {p['media']:.2f})"} for p in players
    ]

    colC1, colC2 = st.columns(2)
    with colC1:
        a1, a2 = st.columns([2, 2])
        capA_sel = a1.selectbox("Capitán equipo A", options=opts_caps,
                                format_func=lambda o: o["label"], index=0, key="capA")
        teamA_sel = a2.selectbox("Nombre del equipo A", options=TEAM_CHOICES,
                                 format_func=lambda o: o["label"], index=0, key="teamA")
    with colC2:
        b1, b2 = st.columns([2, 2])
        capB_sel = b1.selectbox("Capitán equipo B", options=opts_caps,
                                format_func=lambda o: o["label"], index=0, key="capB")
        teamB_sel = b2.selectbox("Nombre del equipo B", options=TEAM_CHOICES,
                                 format_func=lambda o: o["label"], index=1, key="teamB")

    capA_id = capA_sel["id"]
    capB_id = capB_sel["id"]
    teamA_label = teamA_sel["label"]  # "🐝 Avispas F.C."
    teamB_label = teamB_sel["label"]  # "🐗 C.D. Jabalies"

    if capA_id is not None and capB_id is not None and capA_id == capB_id:
        st.error("El capitán del equipo A y el del equipo B no pueden ser el mismo jugador.")
        return

    # --- Tamaños usando TODOS los activos ---
    if n % 2 == 0:
        sizeA = n // 2
        sizeB = n // 2
        extra_note = None
    else:
        owner = st.radio("Equipo con 1 jugador extra (por número impar)",
                         [teamA_label, teamB_label], horizontal=True, index=0)
        if owner == teamA_label:
            sizeA = n // 2 + 1
            sizeB = n - sizeA
        else:
            sizeA = n // 2
            sizeB = n - sizeA
        extra_note = f"{owner} tendrá {max(sizeA, sizeB)} jugadores."

    # --- Umbral ---
    umbral = st.number_input(
        "Umbral de diferencia media (combinatorio)",
        min_value=0.0, max_value=20.0, value=1.0, step=0.1
    )

    # Estado para aleatoriedad por clic
    if "teams_seed" not in st.session_state:
        st.session_state["teams_seed"] = 0
    cols_btn = st.columns([1,1,2])
    with cols_btn[0]:
        if st.button("🔄 Actualizar combinación"):
            st.session_state["teams_seed"] += 1
    with cols_btn[1]:
        if st.button("📸 Vista para foto"):
            st.session_state["share_open"] = True
            st.session_state["__open_from"] = "teams"

    seed = st.session_state["teams_seed"]

    # --- Generador de parejas válidas (con capitanes fijos) ---
    def compute_valid_pairs(players_list, size_a, size_b, capA, capB, thr, seed_val):
        rng = random.Random(seed_val)
        plist = list(players_list)
        ids = [p["id"] for p in plist]
        id_to_obj = {p["id"]: p for p in plist}

        valid = []
        for combo_ids in combinations(ids, size_a):
            setA = set(combo_ids)
            if capA is not None and capA not in setA:
                continue
            if capB is not None and capB in setA:
                continue

            teamA = [id_to_obj[i] for i in setA]
            setB = [i for i in ids if i not in setA]
            if len(setB) != size_b:
                continue
            teamB = [id_to_obj[i] for i in setB]

            if capB is not None and capB not in setB:
                continue

            avg1 = sum(p["media"] for p in teamA) / len(teamA)
            avg2 = sum(p["media"] for p in teamB) / len(teamB)
            if abs(avg1 - avg2) <= thr:
                valid.append((teamA, teamB))

        if not valid:
            return [], []
        return rng.choice(valid)

    # Helper: capitán primero
    def _put_captain_first(team, captain_id):
        if captain_id is None or not team:
            return team
        for i, p in enumerate(team):
            if p["id"] == captain_id:
                if i == 0:
                    return team
                return [team[i]] + [x for j, x in enumerate(team) if j != i]
        return team

    # --- Calcular equipos ---
    t1, t2 = compute_valid_pairs(
        players_list=players,
        size_a=sizeA,
        size_b=sizeB,
        capA=capA_id,
        capB=capB_id,
        thr=float(umbral),
        seed_val=seed
    )

    if not t1 and not t2:
        msg = "No se encontró una combinación que cumpla el umbral"
        msg += f" ({extra_note})." if extra_note else "."
        st.warning(msg)
        return

    # Capitán primero
    t1 = _put_captain_first(t1, capA_id)
    t2 = _put_captain_first(t2, capB_id)

    # Métricas (arriba)
    sum1, sum2 = sum(p['media'] for p in t1), sum(p['media'] for p in t2)
    avg1 = (sum1/len(t1)) if t1 else 0
    avg2 = (sum2/len(t2)) if t2 else 0
    diff = abs(avg1 - avg2)

    c1, c2, c3 = st.columns([1,1,1])
    c1.metric("Jugadores activos", n)
    c2.metric("Diferencia de promedios", f"{diff:.2f}")
    c3.metric("Promedios", f"{avg1:.2f} vs {avg2:.2f}")
    if extra_note:
        st.caption(f"ℹ️ {extra_note}")

    # Tablas normales (se quedan igual)
    col1, col2 = st.columns(2)
    _team_table(col1, t1, f"{teamA_label} ❤️", captain_id=capA_id)
    _team_table(col2, t2, f"{teamB_label} 💙", captain_id=capB_id)


    # =========================
    #     VISTA PARA FOTO
    #  (campo vertical + escudos laterales)
    # =========================
    import streamlit.components.v1 as components
    from pathlib import Path
    from base64 import b64encode

    # ← Abre SOLO una vez por clic (evita que reaparezca en otros reruns)
    open_once = st.session_state.pop("share_open", False)
    if open_once:
        # RNG coherente con la combinación actual (para repartir filas 2–3)
        rng = random.Random(st.session_state.get("teams_seed", 0) + 137)

        # --- Rutas de escudos (pon tus archivos en assets/escudos/...) ---
        ESCUDOS_DIR = Path("../Escudos")
        FILE_MAP = {
            "Avispas F.C.":   "avispas.jpg",
            "C.D. Jabalies":  "jabalies.jpg",
            "Pingüinardos":   "pinguinardos.jpg",
            "Beetles":        "beetles.jpg",
            "TiburOnes":      "tiburones.jpg",
            "Pandas F.C.":    "pandas.jpg",
            "Real Flamingo":  "real_flamingo.jpg",
            "Patos C.F.":     "patos.jpg",
        }

        def _badge_data_uri(name: str):
            fname = FILE_MAP.get(name)
            if not fname:
                return None
            p = ESCUDOS_DIR / fname
            if not p.exists():
                return None
            try:
                data = p.read_bytes()
                ext = p.suffix.lower().lstrip(".")
                if ext in ("jpg", "jpeg"):
                    mime = "image/jpeg"
                elif ext == "svg":
                    mime = "image/svg+xml"
                else:
                    mime = "image/png"
                return f"data:{mime};base64,{b64encode(data).decode('ascii')}"
            except Exception:
                return None

        # Tenemos los objetos de selección con name/emoji/label
        teamA_name = teamA_sel["name"]
        teamB_name = teamB_sel["name"]
        badgeA = _badge_data_uri(teamA_name)
        badgeB = _badge_data_uri(teamB_name)
        emojiA = teamA_sel["emoji"]
        emojiB = teamB_sel["emoji"]

        # --- helpers SOLO para el modal (orden y 4 filas fijas) ---
        def _order_with_captain(team, captain_id, place: str):
            if not team or captain_id is None:
                return team
            idx = next((i for i, p in enumerate(team) if p.get("id") == captain_id), None)
            if idx is None:
                return team
            cap = team[idx]
            others = [p for j, p in enumerate(team) if j != idx]
            return ([cap] + others) if place == "first" else (others + [cap])

        def _four_rows_split(ordered_players):
            N = len(ordered_players)
            if N == 0:
                return [[], [], [], []]
            c1 = 1 if N >= 1 else 0
            c4 = 1 if N >= 2 else 0
            remaining = max(0, N - (c1 + c4))
            if remaining == 0:
                c2, c3 = 0, 0
            elif remaining == 1:
                c2, c3 = (1, 0) if rng.randint(0, 1) == 0 else (0, 1)
            else:
                c2 = rng.randint(1, remaining - 1)
                c3 = remaining - c2
            i = 0
            row1 = ordered_players[i:i+c1]; i += c1
            row2 = ordered_players[i:i+c2]; i += c2
            row3 = ordered_players[i:i+c3]; i += c3
            row4 = ordered_players[i:i+c4]
            return [row1, row2, row3, row4]

        def _split_rows_modal(team, captain_id, place):
            ordered = _order_with_captain(team, captain_id, place)
            return _four_rows_split(ordered)

        def _render_row_modal(players_row, accent_class, captain_id):
            chips = []
            for p in players_row:
                name = escape(p["nombre"])
                if captain_id is not None and p.get("id") == captain_id:
                    name = f"{name} 👑"
                chips.append(f'<div class="chip {accent_class}">{name}</div>')
            return f'<div class="line">{"".join(chips)}</div>'

        # side = "top" o "bottom"; place = "first"/"last"
        def _render_side_modal(team, accent, captain_id, side, place):
            rows = _split_rows_modal(team, captain_id, place)
            lines_html = "\n".join(_render_row_modal(r, accent, captain_id) for r in rows)
            return f'<div class="side {side}">{lines_html}</div>'

        # --- CSS del campo vertical + posiciones de escudos ---
        pitch_css = """
        <style>
        .wrap { width: min(900px, 96vw); margin: 0 auto; }
        .pitch-card { border-radius:16px; overflow:hidden; box-shadow:0 14px 36px rgba(0,0,0,.4); }

        .pitch { position: relative; background: linear-gradient(180deg,#066d3c,#034d2b); height: 640px; }
        .pitch::before { content:""; position:absolute; inset:8px; border:3px solid rgba(255,255,255,0.9); border-radius:12px; }
        .midline { position:absolute; left:8px; right:8px; top:50%; height:2px; background: rgba(255,255,255,0.7); transform: translateY(-50%); }
        .circle.center { position:absolute; top:50%; left:50%; width:110px; height:110px; border-radius:999px; border:3px solid rgba(255,255,255,0.7); transform: translate(-50%,-50%); }
        .box_v { position:absolute; left:20%; right:20%; height:90px; border:3px solid rgba(255,255,255,0.7); }
        .box_v.top    { top: 8px;    border-bottom:none; border-radius:12px 12px 0 0; }
        .box_v.bottom { bottom: 8px; border-top:none;    border-radius:0 0 12px 12px; }

        .team-banner { position:absolute; left:50%; transform:translateX(-50%); padding:8px 12px; color:#fff; font-weight:900; letter-spacing:.2px; border-radius:10px; box-shadow:0 8px 20px rgba(0,0,0,.25); }
        .team-banner.top { top:14px; } .team-banner.bottom { bottom:14px; }
        .red-banner  { background: linear-gradient(90deg,#ef4444,#991b1b); }
        .blue-banner { background: linear-gradient(90deg,#3b82f6,#1e3a8a); }

        .side { position:absolute; left:12px; right:12px; display:flex; flex-direction:column; justify-content:space-evenly; align-items:center; pointer-events:none; }
        .side.top    { top: 60px; bottom: calc(50% + 10px); }
        .side.bottom { top: calc(50% + 10px); bottom: 60px; }

        .line { display:flex; gap:10px; flex-wrap:wrap; justify-content:center; max-width: 92%; min-height: 36px; }
        .chip { color:#fff; padding:7px 12px; border-radius:999px; font-weight:800; border:2px solid rgba(255,255,255,.45); box-shadow:0 6px 14px rgba(0,0,0,.25); user-select:none; }
        .chip.red  { background: linear-gradient(135deg,#ef4444,#991b1b); }
        .chip.blue { background: linear-gradient(135deg,#3b82f6,#1e3a8a); }

        /* Escudos laterales */
        .badge { position:absolute; width:78px; height:auto; opacity:.96; filter: drop-shadow(0 6px 14px rgba(0,0,0,.35)); }
        .badge.top.left     { top: 13%; left: 6%; }
        .badge.top.right    { top: 13%; right: 6%; }
        .badge.bottom.left  { bottom: 13%; left: 6%; }
        .badge.bottom.right { bottom: 13%; right: 6%; }

        /* Fallback cuando no hay imagen: círculo con emoji */
        .badge.faux {
          display:flex; align-items:center; justify-content:center;
          background: rgba(255,255,255,.15);
          border:2px solid rgba(255,255,255,.6);
          border-radius:999px;
          color:#fff; font-size:34px; width:78px; height:78px;
        }

        @media (max-width: 520px){
          .pitch { height: 560px; }
          .chip { font-size:14px; padding:6px 10px; }
          .badge { width:64px; }
          .badge.faux { width:64px; height:64px; font-size:28px; }
        }
        </style>
        """

        # --- HTML: A (rojo) ARRIBA capi al FINAL; B (azul) ABAJO capi al PRINCIPIO + ESCUDOS ---
        # Helpers para insertar la etiqueta del escudo (imagen o emoji fallback)
        def _badge_tag(src, pos_classes, emoji):
            if src:
                return f'<img class="badge {pos_classes}" src="{src}" alt="badge" />'
            # fallback si no hay archivo: un circulito con el emoji
            return f'<div class="badge faux {pos_classes}">{escape(emoji)}</div>'

        badgeA_left  = _badge_tag(badgeA, "top left",  emojiA)
        badgeA_right = _badge_tag(badgeA, "top right", emojiA)
        badgeB_left  = _badge_tag(badgeB, "bottom left",  emojiB)
        badgeB_right = _badge_tag(badgeB, "bottom right", emojiB)

        pitch_html = f"""
        <div class="wrap">
          <div class="pitch-card">
            <div class="pitch">
              <div class="midline"></div>
              <div class="circle center"></div>

              <div class="box_v top"></div>
              <div class="box_v bottom"></div>

              <div class="team-banner red-banner top">{escape(teamA_label)}</div>
              <div class="team-banner blue-banner bottom">{escape(teamB_label)}</div>

              {badgeA_left}{badgeA_right}{badgeB_left}{badgeB_right}

              { _render_side_modal(t1, "red",  capA_id, side="top",    place="last") }
              { _render_side_modal(t2, "blue", capB_id, side="bottom", place="first") }
            </div>
          </div>
        </div>
        """

        if hasattr(st, "dialog"):
            @st.dialog("📸 Vista para foto", width="large")
            def _photo_modal():
                components.html(pitch_css + pitch_html, height=840, scrolling=False)
                colA, colB = st.columns(2)
                with colA:
                    if st.button("❌ Cerrar", use_container_width=True):
                        # nada que mantener: el open_once ya se consumió
                        st.rerun()
                with colB:
                    st.caption("Consejo: haz la captura con la herramienta del sistema.")
            _photo_modal()
        else:
            components.html(pitch_css + pitch_html, height=840, scrolling=False)
            st.info("Tu versión de Streamlit no soporta `st.dialog`. Mostrando la vista embebida.")
            if st.button("❌ Cerrar"):
                st.rerun()
