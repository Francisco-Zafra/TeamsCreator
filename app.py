from itertools import combinations
from flask import Flask, render_template, request, redirect
import random
import pandas as pd

app = Flask(__name__)

# Global list of players
players = []

# Load players from CSV if players list is empty
def load_players_from_csv():
    global players
    try:
        data = pd.read_csv('jugadores.csv', sep=';')
        for index, row in data.iterrows():
            player = {
                'name': row['Nombre'],
                'stats': {
                    'ritmo': row['Ritmo'],
                    'tiro': row['Tiro'],
                    'pase': row['Pase'],
                    'regate': row['Regate'],
                    'defensa': row['Defensa'],
                    'fisico': row['Fisico'],
                    'qos': row['QoS']
                }
            }
            players.append(player)
    except FileNotFoundError:
        print("CSV file not found. Add players manually.")

# Ensure players are loaded from CSV if list is empty
if not players:
    load_players_from_csv()

def get_elements_from_list(lst, arr):
    return [element for element in lst if element in arr]

def get_dif_elements_from_list(lst, arr):
    return [element for element in lst if element not in arr]

def generate_all_possible_teams(data):
    num_players = len(data)
    half_size = num_players // 2
    all_combinations = list(combinations(data, half_size))

    for combo in all_combinations:
        team1 = get_elements_from_list(data, list(combo))
        team2 = get_dif_elements_from_list(data, list(combo))
        yield team1, team2

# Calculate team score
def calculate_team_score(team):
    return sum((p['stats']['ritmo'] + p['stats']['tiro'] + p['stats']['pase'] + p['stats']['regate'] +
                p['stats']['defensa'] + p['stats']['fisico'] + p['stats']['qos']) / 7 for p in team) / len(team)

# Add a new player
@app.route('/add_player', methods=['POST'])
def add_player():
    name = request.form['name']
    stats = {
        'ritmo': int(request.form['ritmo']),
        'tiro': int(request.form['tiro']),
        'pase': int(request.form['pase']),
        'regate': int(request.form['regate']),
        'defensa': int(request.form['defensa']),
        'fisico': int(request.form['fisico']),
        'qos': int(request.form['qos'])
    }
    player = {'name': name, 'stats': stats}
    players.append(player)
    return redirect('/')

# Remove a player by name
@app.route('/remove_player/<string:name>', methods=['POST'])
def remove_player(name):
    global players
    players = [player for player in players if player['name'] != name]
    return redirect('/')

# Create balanced teams
@app.route('/create_teams')
def create_teams():
    if len(players) < 2:
        return "Not enough players to create teams.", 400

    # Shuffle players and create two teams
    random.shuffle(players)
    team1 = None
    team2 = None

    score1 = None
    score2 = None

    for team1_tmp, team2_tmp in generate_all_possible_teams(players):
        media1 = calculate_team_score(team1_tmp)
        media2 = calculate_team_score(team2_tmp)
        eq = abs(media1 - media2)
        if eq < 1.5:
            team1 = team1_tmp
            team2 = team2_tmp

            score1 = round(media1, 1)
            score2 = round(media2, 1)

            break

    return render_template('teams.html', team1=team1, team2=team2, score1=score1, score2=score2)

# Clear all players
@app.route('/clear_players')
def clear_players():
    global players
    players = []
    return redirect('/')

# Reload players from CSV
@app.route('/reload_players')
def reload_players():
    global players
    players = []
    load_players_from_csv()
    return redirect('/')

# Homepage route displaying player pool
@app.route('/')
def index():
    # Load players from CSV if empty
    if not players:
        load_players_from_csv()
    return render_template('index.html', players=players)

