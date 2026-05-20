import flask
import bcrypt
from init import app, db
import models
import re
from sqlalchemy import text


@app.route('/login')
def login():
    # GET request to /login - send login form
    return flask.render_template('login.html')


@app.route('/login', methods=['POST'])
def handle_login():
    username = flask.request.form['username']
    password = flask.request.form['password']

    user = models.User.query.filter(text(f"username = '{username}'")).first()
    if user is not None:
        pw_hash = bcrypt.hashpw(password.encode('utf8'), user.pw_hash)

        # check password
        if pw_hash == user.pw_hash:
            # its good!
            flask.session['auth_user'] = user.id
            return flask.redirect(flask.request.form['url'], 303)

    return flask.render_template('login.html', error='Invalid username or password')


@app.route('/create_user')
def create_user_form():
    return flask.render_template('signup.html')


@app.route('/create_user', methods=['POST'])
def create_user():
    email = flask.request.form['email']
    username = flask.request.form['username']
    password = flask.request.form['password']

    error = None

    # do passwords match?
    if password != flask.request.form['confirm']:
        error = "Passwords don't match"

    if not re.search("^[A-Za-z0-9_-]*$", username):
        error = "Username can only contain letters, numbers, underscore, and hyphen."

    existing = models.User.query.filter_by(username=username).first()
    if existing is not None:
        error = "Username already exists"

    if error:
        return flask.render_template('signup.html', error=error)

    # create user
    user = models.User()
    user.email = email
    user.username = username
    user.pw_hash = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt(15))

    # save user
    db.session.add(user)
    db.session.commit()

    flask.session['auth_user'] = user.id

    # all good!
    return flask.redirect(flask.url_for('index'), 303)



@app.route('/logout')
def handle_logout():
    del flask.session['auth_user']
    return flask.redirect(flask.request.args.get('url', '/'))
