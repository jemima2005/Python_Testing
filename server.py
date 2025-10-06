import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, url_for, session

# --- Chargement des données ---
def loadClubs():
    with open('clubs.json') as c:
        return json.load(c)['clubs']

def loadCompetitions():
    with open('competitions.json') as comps:
        return json.load(comps)['competitions']

# --- Configuration Flask ---
app = Flask(__name__)
app.secret_key = 'something_special'

competitions = loadCompetitions()
clubs = loadClubs()

# --- Page d’accueil ---
@app.route('/')
def index():
    # Si déjà connecté, rediriger directement
    if 'club_email' in session:
        club = next((c for c in clubs if c['email'] == session['club_email']), None)
        if club:
            return redirect(url_for('showSummary'))
    return render_template('index.html')


# --- Connexion ---
@app.route('/showSummary', methods=['POST', 'GET'])
def showSummary():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        club = next((club for club in clubs if club['email'].lower() == email), None)

        if not email:
            flash("Veuillez entrer votre adresse email.")
            return redirect(url_for('index'))

        if not club:
            flash("Email invalide. Veuillez réessayer.")
            return redirect(url_for('index'))

        # ✅ Enregistrer la session utilisateur
        session['club_email'] = club['email']
        flash(f"Bienvenue {club['name']} ! Vous êtes connecté à votre espace.")
        return redirect(url_for('showSummary'))

    # Si déjà connecté (GET)
    if 'club_email' in session:
        club = next((c for c in clubs if c['email'] == session['club_email']), None)
        if club:
            return render_template('welcome.html', club=club, competitions=competitions, clubs=clubs)

    flash("Veuillez vous connecter pour accéder à votre tableau de bord.")
    return redirect(url_for('index'))


# --- Déconnexion ---
@app.route('/logout')
def logout():
    if 'club_email' in session:
        session.pop('club_email', None)
        flash("Déconnexion réussie. À bientôt 👋")
    return redirect(url_for('index'))
