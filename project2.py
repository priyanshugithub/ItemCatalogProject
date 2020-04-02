from flask import Flask, render_template, request, redirect
from flask import url_for, jsonify, flash, make_response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Genre, Movie, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests

app = Flask(__name__)


CLIENT_ID = json.loads(
            open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///moviebaseusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():

    # Validate state token

    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps
                                 ('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code

    code = request.data

    try:

        # Upgrade the authorization code into a credentials object

        oauth_flow = flow_from_clientsecrets('client_secrets.json',
                                             scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps(
                                  'Failed to upgrade the authorization code.'
                                     ), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.

    access_token = credentials.access_token
    url = \
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' \
        % access_token
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.

    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.

    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
            response = make_response(json.dumps(
                "Token's user ID doesn't match given user ID."
                                 ), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

    # Verify that the access token is valid for this app.

    if result['issued_to'] != CLIENT_ID:
        response = \
            make_response(json.dumps("Token's client ID does not match app's"),
                          401)

        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = \
            make_response(json.dumps('Current user is already connected.'),
                          200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.

    login_session['provider'] = 'google'
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info

    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = json.loads(answer.text)

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += \
        ' " style = "width: 300px; height: 300px;border-radius: \
        150px;-webkit-border-radius: 150px;-moz-border-radius: \
         150px;"> '
    flash('you are now logged in as %s' % login_session['username'])
    print 'done!'
    return output


@app.route('/gdisconnect')
def gdisconnect():

        # Only disconnect a connected user.

    credentials = login_session.get('credentials')
    if credentials is None:
        response = \
            make_response(json.dumps('Current user not connected.'),
                          401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # A Bug in google logout code, instead of assigning like this:
    # access_token = credentials.access_token
    # it should be like below

    access_token = credentials
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
        % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':

        # Reset the user's sesson.

        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:

        # For whatever reason, the given token was invalid.

        response = \
            make_response(json.dumps('Failed to revoke token for given user.',
                          400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print 'access token received %s ' % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r'
                             ).read())['web']['app_id']
    app_secret = json.loads(open('fb_client_secrets.json', 'r'
                                 ).read())['web']['app_secret']
    url = \
        'https://graph.facebook.com/oauth/access_token \
        ?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' \
        % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API

    userinfo_url = 'https://graph.facebook.com/v2.4/me'

    # strip expire tag from access token

    token = result.split('&')[0]

    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' \
        % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result

    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['facebook_id'] = data['id']

    # The token must be stored in the login_session in order to
    # properly logout, let's strip out the
    # information before the equals sign in our token

    stored_token = token.split('=')[1]
    login_session['access_token'] = stored_token

    # Get user picture

    url = \
        'https://graph.facebook.com/v2.4/me/picture? \
        %s&redirect=0&height=200&width=200' \
        % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += \
        ' " style = "width: 300px; height: 300px;border-radius: \
         150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash('Now logged in as %s' % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']

    # The access token must me included to successfully logout

    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' \
        % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['user_id']
    del login_session['facebook_id']
    return 'you have been logged out'

# Disconnect based on provider


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']

        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have been successfully logged out.")
        return redirect(url_for('showGenres'))
    else:
        flash("You were not logged in to begin with!!")
        redirect(url_for('showGenres'))


@app.route('/logout')
def logout():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash('You have successfully been logged out.')
        return redirect(url_for('showGenres'))
    else:
        flash('You were not logged in')
        return redirect(url_for('showGenres'))

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email'
                                                             ]).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/genre/<int:genre_id>/movie/JSON')
def genreMovieJSON(genre_id):
    genre = session.query(Genre).filter_by(id=genre_id).one()
    movies = session.query(Movie).filter_by(
        genre_id=genre_id).all()
    return jsonify(Movies=[i.serialize for i in movies])


# ADD JSON ENDPOINT HERE
@app.route('/genre/<int:genre_id>/movie/<int:movie_id>/JSON')
def movieJSON(genre_id, movie_id):
    moviee = session.query(Movie).filter_by(id=movie_id).one()
    return jsonify(moviee=moviee.serialize)


@app.route('/genre/JSON')
def genresJSON():
    genres = session.query(Genre).all()
    return jsonify(genres=[r.serialize for r in genres])


# Show all genres
@app.route('/')
@app.route('/genre/')
def showGenres():
    genres = session.query(Genre).order_by(Genre.name)
    # return "This page will show all my genres"
    if 'username' not in login_session:
        return render_template('genres.html', genres=genres)
    else:
        return render_template('mygenres.html', genres=genres)

############################################################
# Create a new Genre


@app.route('/genre/new/', methods=['GET', 'POST'])
def newGenre():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newGenre = Genre(name=request.form['name'],
                         user_id=login_session['user_id'])
        session.add(newGenre)
        flash('New Genre %s Successfully Created' % newGenre.name)
        session.commit()
        return redirect(url_for('showGenres'))
    else:
        return render_template('newGenre.html')
    # return "This page will be for making a new restaurant"

# Edit a Genre


@app.route('/genre/<int:genre_id>/edit/', methods=['GET', 'POST'])
def editGenre(genre_id):
    editedGenre = session.query(
        Genre).filter_by(id=genre_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedGenre.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized \
        to edit this genre. Please create your own genre in order to edit. \
        ');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedGenre.name = request.form['name']
            flash('Genre Successfully Edited %s' % editedGenre.name)
            return redirect(url_for('showGenres'))
    else:
        return render_template(
            'editGenre.html', genre=editedGenre)

    # return 'This page will be for editing genre %s' % restaurant_id

# Delete a Genre


@app.route('/genre/<int:genre_id>/delete/', methods=['GET', 'POST'])
def deleteGenre(genre_id):
    genreDelete = session.query(
        Genre).filter_by(id=genre_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if genreDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized \
       to delete this genre. Please create your own genre in order to delete. \
       ');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(genreDelete)
        flash('%s Successfully Deleted' % genreDelete.name)
        session.commit()
        return redirect(
            url_for('showGenres', genre_id=genre_id))
    else:
        return render_template(
            'deleteGenre.html', genre=genreDelete)
    # return 'This page will be for deleting genre %s' % genre_id
###################################################################

# Show all genre movies


@app.route('/genre/<int:genre_id>/')
@app.route('/genre/<int:genre_id>/movie/')
def showMovie(genre_id):
    genre = session.query(Genre).filter_by(id=genre_id).one()
    creator = getUserInfo(genre.user_id)
    movies = session.query(Movie).filter_by(
        genre_id=genre_id).all()
    if 'username' not in login_session or \
            creator.id != login_session['user_id']:
        return render_template('publicmenu.html',
                               movies=movies, genre=genre, creator=creator)
    else:
        return render_template('menu.html', movies=movies, genre=genre,
                               creator=creator)


# Create a new Movie
@app.route('/genres/<int:genre_id>/new', methods=['GET', 'POST'])
def newMovie(genre_id):
    if 'username' not in login_session:
        return redirect('/login')
    genre = session.query(Genre).filter_by(id=genre_id).one()
    if login_session['user_id'] != genre.user_id:
        return "<script>function myFunction() {alert('You are not authorized \
        to add movies to this genre. Please create your own genre in order to \
        add movies.');}</script><body onload='myFunction()''>"

    if request.method == 'POST':
        newMovie = Movie(name=request.form['name'], description=request.form[
                        'description'], region=request.form[
                        'region'], genre_id=genre_id)
        session.add(newMovie)
        session.commit()
        return redirect(url_for('genreMovie', genre_id=genre_id))
    else:
        return render_template('newmovie.html', genre_id=genre_id)

# Edit a movie


@app.route('/genre/<int:genre_id>/menu/<int:movie_id>/ \
            edit', methods=['GET', 'POST'])
def editMovie(genre_id, movie_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedMovie = session.query(Movie).filter_by(id=movie_id).one()
    genre = session.query(Genre).filter_by(id=genre_id).one()
    if login_session['user_id'] != genre.user_id:
        return "<script>function myFunction() {alert('You are not \
        authorized to edit movies to this genre. Please create your \
        own new genre in order to edit movies.');}</script> \
        <body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedMovie.name = request.form['name']
        if request.form['description']:
            editedMovie.description = request.form['description']
        if request.form['region']:
            editedMovie.region = request.form['region']
        session.add(editedMovie)
        session.commit()
        return redirect(url_for('genreMovie', genre_id=genre_id))
    else:
        return render_template('editmovie.html', genre_id=genre_id,
                               movie_id=movie_id, movie=editedMovie)


# Delete a movie
@app.route('/genre/<int:genre_id>/movie/<int:movie_id> \
           /delete', methods=['GET', 'POST'])
def deleteMovie(genre_id, movie_id):
    if 'username' not in login_session:
        return redirect('/login')
    genre = session.query(Genre).filter_by(id=genre_id).one()
    movieDelete = session.query(Movie).filter_by(id=movie_id).one()
    if login_session['user_id'] != genre.user_id:
        return "<script>function myFunction() {alert('You are not \
        authorized to delete movies to this genre. Please create \
        your own genre in order to delete movies.');}</script> \
        <body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(movieDelete)
        session.commit()
        flash('Movie Successfully Deleted')
        return redirect(url_for('showMovie', genre_id=genre_id))
    else:
        return render_template('deletemovie.html', movie=movieDelete)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
