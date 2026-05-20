import io
import re

import flask
import base64, os

import markdown
from markupsafe import Markup

from init import app, db
import models
import views_auth


@app.before_request
def setup_csrf():
    if 'csrf_token' not in flask.session:
        flask.session['csrf_token'] = base64.b64encode(os.urandom(32)).decode('ascii')


@app.before_request
def setup_user():
    if 'auth_user' in flask.session:
        user = models.User.query.get(flask.session['auth_user'])
        if user is None:
            # old bad cookie, no good
            del flask.session['auth_user']
        # save the user in 'flask.g', set of globals for this request
        flask.g.user = user


@app.route('/')
def index():
    count = 0
    if 'auth_user' not in flask.session:
        users = models.User.query.all()
        p = models.Post
        posts = p.query.order_by(p.timestamp.desc()).all()
        for post in posts:
            if post.content is not None:
                msg = Markup(markdown.markdown(msg, output_format='html5'))
                post.content = msg
        return flask.render_template('index.html', posts=posts, users=users, count=count)
    else:
        follows = models.Follow.query.filter_by(follower_id=flask.session['auth_user'])
        idList = []
        for f in follows:
            idList.append(f.followee_id)

        idList.append(flask.session['auth_user'])
        p = models.Post
        posts = p.query.filter(p.creator_id.in_(idList)).order_by(p.timestamp.desc()).all()

        for post in posts:
            if post.content is not None:
                msg = Markup(markdown.markdown(msg, output_format='html5'))
                post.content = msg
        users = models.User.query.all()

    return flask.render_template('index.html', posts=posts, users=users, count=count)


@app.route('/u/<user>')
def user_page(user):
    count = 0
    user = models.User.query.filter_by(username=user).first()
    for post in user.posts:
        if post.content is not None:
            msg = Markup(markdown.markdown(msg, output_format='html5'))
            post.content = msg
    return flask.render_template('user.html', user=user,
                                 posts=user.posts, count=count)

@app.route('/edit_profile/<user>')
def edit_profile(user):
    user = models.User.query.filter_by(username=user).first()
    return flask.render_template('edit_profile.html', user=user)

@app.route('/post/edit_profile', methods=['POST'])
def post_edited_profile():
    location = flask.request.form['location']
    bio = flask.request.form['bio']
    user = models.User.query.filter_by(username=flask.g.user.username).first()
    user.location = location
    user.bio = bio
    db.session.commit()
    return flask.redirect('u/'+flask.g.user.username, code=303)

@app.route('/post/photo-send', methods=['POST'])
def photo_post():
    user_id = int(flask.request.form['user-id'])
    username = flask.request.form['user-name']
    # request.files has uploaded files
    file = flask.request.files['image']

    if not file.mimetype.startswith('image/'):
        flask.abort(400)

    post = models.Post()
    post.photo_type = file.mimetype

    # get photo content. read it into a 'BytesIO'
    photo_data = io.BytesIO()
    file.save(photo_data)

    # now put data into the model object
    post.photo = photo_data.getvalue()

    post.creator_id = user_id
    post.content = flask.request.form['post']

    #save!
    db.session.add(post)
    db.session.commit()
    return flask.redirect(flask.request.form['path'], 303)


@app.route('/post/<int:post_id>/photo')
def post_photo(post_id):
    post = models.Post.query.get_or_404(post_id)

    return flask.send_file(io.BytesIO(post.photo))

