import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, url_for


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


# --- Routes principales ---
@app.route('/')
def index():
    return render_template('index.html')


# 🔹 Connexion par email
@app.route('/showSummary', methods=['POST'])
def showSummary():
    email = request.form['email'].strip().lower()
    club = next((club for club in clubs if club['email'].lower() == email), None)
    if club:
        return render_template('welcome.html', club=club, competitions=competitions)
    else:
        flash("Email invalide. Veuillez réessayer.")
        return redirect(url_for('index'))


# 🔹 Accès à la page de réservation
@app.route('/book/<competition>/<club>')
def book(competition, club):
    foundClub = next((c for c in clubs if c['name'] == club), None)
    foundCompetition = next((c for c in competitions if c['name'] == competition), None)

    if not foundClub:
        flash(f"Erreur : club '{club}' introuvable.")
        return redirect(url_for('index'))

    if not foundCompetition:
        flash(f"Erreur : compétition '{competition}' introuvable.")
        return render_template('welcome.html', club=foundClub, competitions=competitions)

    try:
        comp_date = datetime.strptime(foundCompetition['date'], "%Y-%m-%d %H:%M:%S")
        if comp_date < datetime.now():
            flash(f"La compétition '{foundCompetition['name']}' est déjà terminée.")
            return render_template('welcome.html', club=foundClub, competitions=competitions)
    except ValueError:
        flash("Erreur : format de date de compétition invalide.")
        return render_template('welcome.html', club=foundClub, competitions=competitions)

    try:
        available_places = int(foundCompetition['numberOfPlaces'])
    except (ValueError, TypeError):
        available_places = 0

    if available_places <= 0:
        flash(f"Aucune place disponible pour '{foundCompetition['name']}'.")
        return render_template('welcome.html', club=foundClub, competitions=competitions)

    return render_template('booking.html', club=foundClub, competition=foundCompetition)


# 🔹 Achat de places
@app.route('/purchasePlaces', methods=['POST'])
def purchasePlaces():
    comp_name = request.form.get('competition', '')
    club_name = request.form.get('club', '')
    raw_places = request.form.get('places', '').strip()

    competition = next((c for c in competitions if c['name'] == comp_name), None)
    club = next((c for c in clubs if c['name'] == club_name), None)

    if not competition or not club:
        flash("Erreur : club ou compétition introuvable.")
        return redirect(url_for('index'))

    try:
        places_required = int(raw_places)
    except ValueError:
        places_required = -1

    try:
        available_places = int(competition['numberOfPlaces'])
    except (ValueError, TypeError):
        flash("Erreur de données : nombre de places invalide pour cette compétition.")
        return render_template('welcome.html', club=club, competitions=competitions)

    try:
        club_points = int(club['points'])
    except (ValueError, TypeError):
        flash("Erreur de données : solde de points invalide pour ce club.")
        return render_template('welcome.html', club=club, competitions=competitions)

    bookings = competition.setdefault('bookings', {})
    already_booked = int(bookings.get(club['name'], 0))

    if places_required <= 0:
        flash("Erreur : le nombre de places doit être un entier positif.")
        return render_template('welcome.html', club=club, competitions=competitions)

    if already_booked + places_required > 12:
        restant_autorise = max(0, 12 - already_booked)
        msg = (
            f"Erreur : un club ne peut pas réserver plus de 12 places au total pour « {competition['name']} ». "
            f"Réservations déjà effectuées : {already_booked}. "
            f"Vous pouvez encore réserver au plus {restant_autorise} place(s)."
        )
        flash(msg)
        return render_template('welcome.html', club=club, competitions=competitions)

    if places_required > available_places:
        flash(
            f"Erreur : il ne reste que {available_places} place(s) disponible(s) "
            f"pour « {competition['name']} »."
        )
        return render_template('welcome.html', club=club, competitions=competitions)

    if places_required > club_points:
        flash(
            f"Erreur : points insuffisants. Solde du club : {club_points} point(s). "
            f"Demande : {places_required} place(s)."
        )
        return render_template('welcome.html', club=club, competitions=competitions)

    # --- Succès ---
    competition['numberOfPlaces'] = available_places - places_required
    club['points'] = club_points - places_required
    bookings[club['name']] = already_booked + places_required

    flash(
        f"Réservation réussie ! Vous avez réservé {places_required} place(s) pour « {competition['name']} ». "
        f"Places restantes : {competition['numberOfPlaces']}. "
        f"Points restants pour {club['name']} : {club['points']}."
    )
    return render_template('welcome.html', club=club, competitions=competitions)


# 🔹 (Phase 2) Affichage des points publics — à ajouter plus tard
# @app.route('/points')
# def showPoints():
#     return render_template('points.html', clubs=clubs)


# 🔹 Déconnexion
@app.route('/logout')
def logout():
    return redirect(url_for('index'))
