import json
from flask import Flask,render_template,request,redirect,flash,url_for


def loadClubs():
    with open('clubs.json') as c:
         listOfClubs = json.load(c)['clubs']
         return listOfClubs


def loadCompetitions():
    with open('competitions.json') as comps:
         listOfCompetitions = json.load(comps)['competitions']
         return listOfCompetitions


app = Flask(__name__)
app.secret_key = 'something_special'

competitions = loadCompetitions()
clubs = loadClubs()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/showSummary',methods=['POST'])
def showSummary():
    club = [club for club in clubs if club['email'] == request.form['email']][0]
    return render_template('welcome.html',club=club,competitions=competitions)


@app.route('/book/<competition>/<club>')
def book(competition,club):
    foundClub = [c for c in clubs if c['name'] == club][0]
    foundCompetition = [c for c in competitions if c['name'] == competition][0]
    if foundClub and foundCompetition:
        return render_template('booking.html',club=foundClub,competition=foundCompetition)
    else:
        flash("Something went wrong-please try again")
        return render_template('welcome.html', club=club, competitions=competitions)


@app.route('/purchasePlaces', methods=['POST'])
def purchasePlaces():
    # Récupération sûre des champs du formulaire
    comp_name = request.form.get('competition', '')
    club_name = request.form.get('club', '')
    raw_places = request.form.get('places', '').strip()

    # Recherche des objets
    competition = next((c for c in competitions if c['name'] == comp_name), None)
    club = next((c for c in clubs if c['name'] == club_name), None)

    if not competition or not club:
        flash("Erreur : club ou compétition introuvable.")
        return redirect(url_for('index'))

    # Parsing du nombre de places demandé
    try:
        places_required = int(raw_places)
    except ValueError:
        places_required = -1  # force une erreur en dessous

    # Normalisation des quantités
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

    # --- Suivi cumulatif par club et par compétition (en mémoire) ---
    # Permet de faire respecter le plafond de 12 au total, même en plusieurs commandes.
    bookings = competition.setdefault('bookings', {})  # ex: {"Simply Lift": 5}
    already_booked = int(bookings.get(club['name'], 0))

    # --- Règles et validations ---
    if places_required <= 0:
        flash("Erreur : le nombre de places doit être un entier positif.")
        return render_template('welcome.html', club=club, competitions=competitions)

    # Plafond de 12 AU TOTAL pour ce club dans cette compétition
    if already_booked + places_required > 12:
        restant_autorise = 12 - already_booked
        if restant_autorise < 0:
            restant_autorise = 0
        msg = (
            "Erreur : un club ne peut pas réserver plus de 12 places au total "
            f"pour « {competition['name']} ». Réservations déjà effectuées : {already_booked}. "
            f"Vous pouvez encore réserver au plus {restant_autorise} place(s)."
        )
        flash(msg)
        return render_template('welcome.html', club=club, competitions=competitions)

    # Disponibilité
    if places_required > available_places:
        flash(
            f"Erreur : il ne reste que {available_places} place(s) disponible(s) "
            f"pour « {competition['name']} »."
        )
        return render_template('welcome.html', club=club, competitions=competitions)

    # Points du club
    if places_required > club_points:
        flash(
            f"Erreur : points insuffisants. Solde du club : {club_points} point(s). "
            f"Demande : {places_required} place(s)."
        )
        return render_template('welcome.html', club=club, competitions=competitions)

    # --- Succès : appliquer les mises à jour ---
    competition['numberOfPlaces'] = available_places - places_required
    club['points'] = club_points - places_required
    bookings[club['name']] = already_booked + places_required

    flash(
        f"Réservation réussie ! Vous avez réservé {places_required} place(s) pour « {competition['name']} ». "
        f"Places restantes : {competition['numberOfPlaces']}. "
        f"Points restants pour {club['name']} : {club['points']}."
    )
    return render_template('welcome.html', club=club, competitions=competitions)

# TODO: Add route for points display


@app.route('/logout')
def logout():
    return redirect(url_for('index'))