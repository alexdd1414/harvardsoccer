import os, json, requests

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from ast import literal_eval

from helpers import apology, login_required



# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
# app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("postgres://uhovkwoeadpayo:42b0da8ed28de3c07a2f96a3f2990a46b36e5448ab97cf529f9996ae43ec9afe@ec2-23-21-86-22.compute-1.amazonaws.com:5432/d4ngn96c9f013c")

# render the homepage of the website
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/players", methods=["GET"])
def players():
    """pull up database of players with images"""
    # load all the players who registered from the database
    all_players = db.execute("SELECT * FROM players")
    # create new dict for the player interests
    players_dict = {}
    #  loop through all the interest in the interest table
    for player in all_players:
        interest_list = []
        #load all the interest from the interest table for a given user id
        all_interests = db.execute("SELECT * FROM interests WHERE id=:id", id=player["id"])
        # append all the interest for a user into the interest list
        for interest in all_interests:
            interest_list.append(interest["interest"])
        # add interest list into a dict for all the players with unique IDs
        players_dict[player["id"]] = interest_list

    return render_template("players.html", players=all_players, players_dict=players_dict)


@app.route("/search", methods=["GET", "POST"])
def search():
    """Rank and display players by how well they fit search criteria"""
    if request.method == "POST":

        # Get grad year input
        fresh = request.form.get("2022")
        soph = request.form.get("2021")
        junior = request.form.get("2020")
        senior = request.form.get("2019")
        grad = request.form.get("grad")

        # Put grad year selections into a set
        years_input = set([fresh, soph, junior, senior, grad])

        # Remove instances of "None"
        years = [int(x) for x in years_input if x is not None]

        # Get interest inputs
        sports = request.form.get("Sports")
        health = request.form.get("Health")
        business = request.form.get("Business")
        government = request.form.get("Government")
        law = request.form.get("Law")
        education = request.form.get("Education")
        technology = request.form.get("Technology")
        entrepreneurship = request.form.get("Entrepreneurship")
        finance = request.form.get("Finance")
        media = request.form.get("Media")

        # Put grad year selections into a set
        interests_input = set([sports, health, business, government, law, education, technology, entrepreneurship, finance, media])

        # Remove instances of "None"
        interests = [x for x in interests_input if x is not None]

        # If "All" is selected (and thus value is not text and can be converted to int), make concentration empty
        try:
            concentration_input = int(request.form.get("concentration"))
            concentration = {}
        # If concentration is selected, make list of dicts readable by python
        except:
            concentration = literal_eval(request.form.get("concentration"))

        # Get all players to search from
        all_players = db.execute("SELECT name, year, concentration, id FROM players")

        # Reset match ranking system
        db.execute("UPDATE players SET points=0")

        # Iterate through each player and tally matches with form inputs
        for player in all_players:
            # Make points
            points = 0

            # If grad selected, make graduate be represented by an int
            if player["year"] == "Graduate":
                player_year = 1

            else:
                player_year = player["year"]

            # If grad year matches, give point
            if player_year in years:
                points += 1

            # If concentration match can be made, give point
            try:
                if player["concentration"] == concentration["concentration"]:
                    points += 1

            # If "All" was chosen, ignore concentration
            except:
                pass

            # Get interests for the player
            player_interests = db.execute("SELECT interest FROM interests WHERE id=:id", id=player["id"])

            # Make an empty list
            player_interest_list = []

            # Add player's interests to the list
            for interest in player_interests:
                player_interest_list.append(interest["interest"])

            # If any interest for player matches a selected one, give point
            if any(i in interests for i in player_interest_list):
                points += 1

            # Add player points to table
            db.execute("UPDATE players SET points=:points WHERE id=:id", points=points, id=player["id"])

        # Get 3 point profile matches
        best_match = db.execute("SELECT * FROM players WHERE points=3")

        # Get 2 point profile matches
        better_match = db.execute("SELECT * FROM players WHERE points=2")

        # Get 1 point profile matches
        good_match = db.execute("SELECT * FROM players WHERE points=1")

        # Get 0 point profile matches
        no_match = db.execute("SELECT * FROM players WHERE points=0")

        # render quoted page if successful
        return render_template("results.html", best_match=best_match, better_match=better_match, good_match=good_match, no_match=no_match)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        all_concentrations = db.execute("SELECT DISTINCT concentration FROM players")
        return render_template("search.html", concentrations=all_concentrations)

# https://www.pythonforbeginners.com/requests/using-requests-in-python
# https://kite.com/python/docs/flask.json.jsonify
# https://www.youtube.com/watch?v=9N6a-VLBa2I
# the above links helped us learn about Google maps API and convering python dicts to JSON
@app.route("/maps", methods=["GET"])
def maps():

    """ Generate a dict of player name, address, and map coordinates """

    # get hometown of everyone in the database
    hometowns = db.execute("SELECT hometown FROM players")

    locations = []
    # loop through the homtowns and append them to a list
    for i in range(len(hometowns)):
        location = hometowns[i]["hometown"]
        locations.append(location)

    # load in the names of the same users
    fullnames = db.execute("SELECT name FROM players")
    names = []
    # append their names to a list
    for i in range(len(fullnames)):
        name = fullnames[i]["name"]
        names.append(name)

    # create new empty list for cities and states
    cities = []
    states = []

    # split the city and state string in the list into separate strings and append each to their respective list
    for i in range(len(locations)):
        city,state = locations[i].split(", ")
        cities.append(city)
        states.append(state)

    player = {}
    # loop through all the users in the database
    for i in range(len(states)):
        # create a dict within the larger players dict
        player[i] = dict.fromkeys(['name','lat','lng','address'])
        # if there is a space city
        if cities[i].find(" "):
            # replace spae with a plus so the state can be added to the link sent to the google maps Geocoder API
            cities[i].replace(" ", "+")
            # get the coordinates of the hometown entered from the geocoder google maps API
            result = requests.get("https://maps.googleapis.com/maps/api/geocode/json?address=" + "+" + cities[i] + "," + "+" + states[i] + "&key=AIzaSyBuBPQeZU7Q-DP86AdYBcPpvytAAb_UGIE")
            # convert response to a JSON object
            data = json.loads(result.text)
            # index into the elements to get the desired elements and add those the inner python dict
            player[i]['lat'] = data["results"][0]["geometry"]["location"]["lat"]
            player[i]['lng'] = data["results"][0]["geometry"]["location"]["lng"]
            player[i]['address'] = data["results"][0]["formatted_address"]
            # index into the list of names and add that to the dict too
            player[i]['name'] = names[i]
        # if there is no space in the city name, do the same process with replacing any space of characters with '+'
        else:
            result = requests.get("https://maps.googleapis.com/maps/api/geocode/json?address=" + "+" + cities[i] + "+" + states[i] + "&key=AIzaSyBuBPQeZU7Q-DP86AdYBcPpvytAAb_UGIE")
            data = json.loads(result.text)
            player[i]['lat'] = data["results"][0]["geometry"]["location"]["lat"]
            player[i]['lng'] = data["results"][0]["geometr y"]["location"]["lng"]
            player[i]['address'] = data["results"][0]["formatted_address"]
            player[i]['name'] = names[i]

    # return the python dict with desire dict to the maps.html page
    return render_template("maps.html", player=player)



# render about us page
@app.route("/us", methods=["GET"])
def us():
    return render_template("us.html")


# render about harvard soccer page
@app.route("/harvard", methods=["GET"])
def harvard():
    return render_template("harvard.html")

# register the user to the player database
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        # get email and password from user
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # check to make sure the user input a value into every registration field
        if not email:
            return apology("You must input a Harvard email")

        elif not password:
            return apology("You must input a password")

        elif not confirmation:
            return apology("You must confirm password")

        # check to make sure the password is the same as the password confirmation
        elif not password == confirmation:
            return apology("Password does not match confirmation")

        # add the user to the database
        # scramble users password using the hash function
        registrant = db.execute("INSERT INTO users (email, hash) VALUES (:email, :hash_pass)", email=email, hash_pass=generate_password_hash(password))


        # return error is the email is taken
        if not registrant:
            return ("This email is taken")

        # once user is registered automatically log them in
        session["user_id"] = registrant

        flash('Registered!')

        # go to homepage
        return render_template("form.html", email=email)


    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/check", methods=["GET"])
def check():
    """Return true if email available, else false, in JSON format"""

    # get email from register form
    email_entry = request.args.get("email")
    # check to see if that email matches one in the database
    email = db.execute("SELECT * FROM users WHERE email = :email_entry", email_entry=email_entry)

    # email entry is at least longer than one letter
    if len(email_entry) >= 1:
        # email is not a match with a previously registered user
        if not email:
            return jsonify(True)
        # email already exists
        else:
            return jsonify(False)

    # not long enough
    else:
        return jsonify(False)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure email was submitted
        if not request.form.get("email"):
            return apology("must provide email", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for email
        rows = db.execute("SELECT * FROM users WHERE email = :email",
                          email=request.form.get("email"))

        # Ensure email exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid email and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        info = db.execute("SELECT name, team, year, concentration, hometown, internship, postgrad, longterm, linkedin, image FROM players WHERE id=:id", id=session["user_id"])
        email= db.execute("SELECT email FROM users WHERE id=:id", id=session["user_id"])

        player_interests = db.execute("SELECT interest FROM interests WHERE id=:id", id=session["user_id"])

        # Make an empty list
        player_interest_list = []

        # Add player's interests to the list
        for interest in player_interests:
            player_interest_list.append(interest["interest"])

        interests = player_interest_list

        # Redirect user to home page
        return render_template("settings.html", player=info, email=email[0]["email"], interest=interest)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/change", methods=["GET", "POST"])
@login_required
def change():
    """Change Profile"""

    if request.method == "POST":
        #select email from the users table
        email = db.execute("SELECT email FROM users WHERE id=:id", id=session["user_id"])

        # get all the user inputs from the change form
        name = request.form.get("name")
        team = request.form.get("team")
        year = request.form.get("year")
        concentration = request.form.get("concentration")
        hometown = request.form.get("hometown")
        internship = request.form.get("internship")
        postgrad = request.form.get("postgrad")
        longterm = request.form.get("longterm")
        linkedin = request.form.get("linkedin")
        image = request.form.get("image")
        plans = request.form.get("plans")
        # update the users data with their new inputs
        db.execute("UPDATE players SET name=:name, team=:team, year=:year, concentration=:concentration, hometown=:hometown, internship=:internship, postgrad=:postgrad, longterm=:longterm, linkedin=:linkedin, image=:image, plans=:plans WHERE id=:id",
                    name=name, team=team, year=year, concentration=concentration, hometown=hometown, internship=internship, postgrad=postgrad, longterm=longterm, linkedin=linkedin, image=image, id=session["user_id"], plans=plans)
        # delete all the users interest from the table when they select the form to change
        db.execute("DELETE FROM interests WHERE id=:id", id=session["user_id"])

        # get the new interest check box inputs
        sports = request.form.get("Sports")
        health = request.form.get("Health")
        business = request.form.get("Business")
        government = request.form.get("Government")
        law = request.form.get("Law")
        education = request.form.get("Education")
        technology = request.form.get("Technology")
        entrepreneurship = request.form.get("Entrepreneurship")
        finance = request.form.get("Finance")
        media = request.form.get("Media")

        interests_input = set([sports, health, business, government, law, education, technology, entrepreneurship, finance, media])

        # remove any values were not select from that users new set of interests
        interests = [x for x in interests_input if x is not None]

        # insert new interest into the the interest table
        for interest in interests:
            db.execute("INSERT INTO interests (interest, id) VALUES (:interest, :id)", interest=interest, id=session["user_id"])

        # Select the players updated info from the database
        player = db.execute("SELECT name, team, year, concentration, hometown, internship, postgrad, longterm, linkedin, image, plans FROM players WHERE id=:id", id=session["user_id"])

        # pass the user their updated information, interest, and email
        return render_template("settings.html", player=player, email=email[0]["email"], interests=interests)

    else:

        # Get the profile of logged in user
        player = db.execute("SELECT name, team, year, concentration, hometown, internship, postgrad, longterm, linkedin, image, plans FROM players WHERE id=:id", id=session["user_id"])

        # Get email profile of logged in user
        email = db.execute("SELECT email FROM users WHERE id=:id", id=session["user_id"])

        return render_template("change.html", player=player, email=email[0]["email"])


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change Password"""

    if request.method == "POST":

        # check to make sure the user input a value into every registration field
        old_password = request.form.get("old_password")

        # query database for hash password
        password_check = db.execute("SELECT hash FROM users WHERE id=:id", id=session["user_id"])

        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")
        # ensure user entered an old password
        if not old_password:
            return apology("You must input an old password")

        # check old password against hashed password in database
        elif not check_password_hash(password_check[0]["hash"], request.form.get("old_password")):
            return apology("That old password is incorrect")

        # check to see if user inputed a new password
        elif not new_password:
            return apology("You must input a new password")

        # check to see if user inputed a confirmation
        elif not confirmation:
            return apology("You must confirm your new password")

        # check to make sure the new password matches the confirmation
        elif new_password != confirmation:
            return apology("Your new password does not match confirmation password")
        # update user's password with new password once it is hashed
        db.execute("UPDATE users SET hash = :new_password WHERE id=:id",
                   new_password=generate_password_hash(new_password), id=session["user_id"])

        player = db.execute("SELECT name, team, year, concentration, hometown, internship, postgrad, longterm, linkedin, image, plans FROM players WHERE id=:id", id=session["user_id"])

        interests = db.execute("SELECT interest FROM interests WHERE id=:id", id=session["user_id"])

        flash('Password Changed!')

        return render_template("settings.html", player=player, interests=interests)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("password.html")

@app.route("/form", methods =["GET", "POST"] )
@login_required
def form():
    """Change Password"""

    if request.method == "POST":
        # get user email form user database
        email = db.execute("SELECT email FROM users WHERE id=:id", id=session["user_id"])

        # get information from the form
        name = request.form.get("name")
        team = request.form.get("team")
        year = request.form.get("year")
        concentration = request.form.get("concentration")
        hometown = request.form.get("hometown")
        internship = request.form.get("internship")
        postgrad = request.form.get("postgrad")
        longterm = request.form.get("longterm")
        linkedin = request.form.get("linkedin")
        image = request.form.get("image")
        plans = request.form.get("plans")

        # insert information into players table
        db.execute("INSERT INTO players (name, team, email, year, concentration, hometown, internship, postgrad, longterm, linkedin, image, id, plans) VALUES (:name, :team, :email, :year, :concentration, :hometown, :internship, :postgrad, :longterm, :linkedin, :image, :id, :plans)",
                    name=name, team=team, email=email[0]["email"], year=year, concentration=concentration, hometown=hometown, internship=internship, postgrad=postgrad, longterm=longterm, linkedin=linkedin, image=image, id=session["user_id"], plans=plans)

        # get interest from the user
        sports = request.form.get("Sports")
        health = request.form.get("Health")
        business = request.form.get("Business")
        government = request.form.get("Government")
        law = request.form.get("Law")
        education = request.form.get("Education")
        technology = request.form.get("Technology")
        entrepreneurship = request.form.get("Entrepreneurship")
        finance = request.form.get("Finance")
        media = request.form.get("Media")

        # Put input interests into set
        interests_input = set([sports, health, business, government, law, education, technology, entrepreneurship, finance, media])

        # Remove "None" values from the set
        interests = [x for x in interests_input if x is not None]

        # Insert interest into the database
        for interest in interests:
            db.execute("INSERT INTO interests (interest, id) VALUES (:interest, :id)", interest=interest, id=session["user_id"])

        # select player
        player = db.execute("SELECT name, team, year, concentration, hometown, internship, postgrad, longterm, linkedin, image, plans FROM players WHERE id=:id", id=session["user_id"])

        # send player, interest, and email interst to the user
        return render_template("settings.html", player=player, email=email[0]["email"], interests=interests)

    else:

        # render the form
        return render_template("form.html")

def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)

# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
