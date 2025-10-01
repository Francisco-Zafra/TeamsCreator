from flask import Flask, render_template, request, redirect, url_for
from models import init_db, get_all_players, add_player, update_player, delete_player, toggle_player_active
from utils import generate_balanced_teams

app = Flask(__name__)
app.config['DATABASE'] = 'squad.db'
app.jinja_env.globals.update(enumerate=enumerate)

@app.route("/")
def index():
    players = get_all_players(app.config['DATABASE'])
    return render_template("jugadores.html", players=players)

@app.route("/add", methods=["POST"])
def add():
    data = request.form
    add_player(app.config['DATABASE'], data)
    return redirect(url_for('index'))

@app.route("/edit/<int:player_id>", methods=["POST"])
def edit(player_id):
    data = request.form
    update_player(app.config['DATABASE'], player_id, data)
    return redirect(url_for('index'))

@app.route("/delete/<int:player_id>")
def delete(player_id):
    delete_player(app.config['DATABASE'], player_id)
    return redirect(url_for('index'))

@app.route("/toggle/<int:player_id>")
def toggle(player_id):
    toggle_player_active(app.config['DATABASE'], player_id)
    return redirect(url_for('index'))

@app.route("/equipos", methods=["GET", "POST"])
def equipos():
    equipos = []
    if request.method == "POST":
        umbral = float(request.form.get("umbral", 1))
        num_por_equipo = int(request.form.get("num_por_equipo", 5))
        equipos = generate_balanced_teams(app.config['DATABASE'], umbral, num_por_equipo)
    return render_template("equipos.html", equipos=equipos)

@app.route("/edit_form/<int:player_id>")
def edit_form(player_id):
    players = get_all_players(app.config['DATABASE'])
    player = next((p for p in players if p[0] == player_id), None)
    return render_template("jugadores.html", players=players, editing=player)


if __name__ == "__main__":
    init_db('squad.db')  # Se asegura de que la BD está lista antes de iniciar
    app.run(debug=True)
