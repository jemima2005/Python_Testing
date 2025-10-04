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


@app.route('/purchasePlaces',methods=['POST'])
def purchasePlaces():
    competition = [c for c in competitions if c['name'] == request.form['competition']][0]
    club = [c for c in clubs if c['name'] == request.form['club']][0]
    placesRequired = int(request.form['places'])
    competition['numberOfPlaces'] = int(competition['numberOfPlaces'])-placesRequired
    flash('Great-booking complete!')
    return render_template('welcome.html', club=club, competitions=competitions)


# TODO: Add route for points display


@app.route('/logout')
def logout():
    return redirect(url_for('index'))