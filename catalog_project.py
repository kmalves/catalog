from flask import (Flask, render_template, url_for, request,
                   redirect, flash, jsonify)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from catalog_database import Base, ActivityCategory, ActivityItem, User

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Activities Catalog"

engine = create_engine('sqlite:///activitiescatalogwithuser.db')
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


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session.get('username'), email=login_session.get(
                   'email'), picture=login_session.get('picture'))
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
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


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    print "result %s " % result
    data = json.loads(result)
    token = 'access_token=' + data['access_token']

    url = 'https://graph.facebook.com/v2.8/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data.get('name')
    login_session['email'] = data.get('email')
    login_session['facebook_id'] = data.get('id')

    # Strip out the information before the equals
    # sign in the token to store in the login_session
    stored_token = token.split("=")[1]
    print stored_token
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    print data
    login_session['picture'] = data['data']['url']

    # Add new user to the database if this user doesn't already exist
    if getUserID(login_session.get('email')) is None:
        new_user = createUser(login_session)
        login_session['user_id'] = new_user
    else:
        user_id = getUserID(login_session.get('email'))
        login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += """ " style = "width: 300px;
                    height: 300px;
                    border-radius: 150px;
                    -webkit-border-radius: 150px;
                    -moz-border-radius: 150px;"> """

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "You have been logged out"


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
                                 'Current user is already connected'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # Add new user to the database if this user doesn't already exist
    if getUserID(login_session.get('email')) is None:
        new_user = createUser(login_session)
        login_session['user_id'] = new_user
    else:
        user_id = getUserID(login_session.get('email'))
        login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += """ " style = "width: 300px;
                    height: 300px;
                    border-radius: 150px;
                    -webkit-border-radius: 150px;
                    -moz-border-radius: 150px;"> """
    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    print login_session['user_id']
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session.get('username')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
                   'Failed to revoke token for given user', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/main/JSON')
def MainPageJSON():
    categories = session.query(ActivityCategory).all()
    return jsonify(categories=[c.serialize for c in categories])

symbols = {'Family': '&#128106;',
           'Date Night': '&#128525;',
           'Weekend and Day Trips': '&#128665;',
           'Spa and Wellness': '&#128524;',
           'Outdoors': '&#128690;',
           'Everything Else': '&#128526;'}


@app.route('/')
@app.route('/main')
def MainPage():
    categories = session.query(ActivityCategory).all()
    return render_template('main.html', categories=categories, symbols=symbols)


@app.route('/main/<int:category_id>/JSON')
def CategoryItemsJSON(category_id):
    category = session.query(ActivityCategory).filter_by(id=category_id).one()
    items = session.query(ActivityItem).filter_by(category_id=category.id)
    return jsonify(activities=[i.serialize for i in items])


@app.route('/main/<int:category_id>/')
def CategoryItems(category_id):
    user_name = login_session.get('username')
    user_id = login_session.get('user_id')
    category = session.query(ActivityCategory).filter_by(id=category_id).one()
    items = session.query(ActivityItem).filter_by(category_id=category.id). \
        join(ActivityItem.user).all()
    return render_template('items.html', items=items,
                           category=category,
                           user_name=user_name,
                           user_id=user_id,
                           symbols=symbols)


@app.route('/main/<int:category_id>/new', methods=['GET', 'POST'])
def NewCategoryItem(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(ActivityCategory).filter_by(id=category_id).one()
    if request.method == 'POST':
        newItem = ActivityItem(name=request.form['name'],
                               description=request.form['description'],
                               website=request.form['website'],
                               category_id=category_id,
                               user_id=login_session.get('user_id'))
        session.add(newItem)
        session.commit()
        print newItem.user_id
        flash('New activity %s was successfully created!' % (newItem.name))
        return redirect(url_for('CategoryItems', category_id=category_id))
    else:
        return render_template('new_activity_item.html',
                               category_id=category_id)


@app.route('/main/<int:category_id>/edit/<int:item_id>',
           methods=['GET', 'POST'])
def EditCategoryItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(ActivityCategory).filter_by(id=category_id).one()
    editedItem = session.query(ActivityItem).filter_by(id=item_id).one()
    if login_session.get('user_id') != editedItem.user_id:
        flash('You did not create activity %s!' % (editedItem.name))
        return redirect(url_for('CategoryItems', category_id=category_id))
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['website']:
            editedItem.website = request.form['website']
        session.add(editedItem)
        session.commit()
        flash('Your activity %s was successfully updated!' % (editedItem.name))
        return redirect(url_for('CategoryItems', category_id=category_id))
    else:
        return render_template('edit_activity_item.html',
                               category_id=category_id,
                               item_id=item_id,
                               item=editedItem)


@app.route('/main/<int:category_id>/delete/<int:item_id>',
           methods=['GET', 'POST'])
def DeleteCategoryItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(ActivityCategory).filter_by(id=category_id).one()
    deleteItem = session.query(ActivityItem).filter_by(id=item_id).one()
    if login_session.get('user_id') != deleteItem.user_id:
        flash('You did not create activity %s!' % (deleteItem.name))
        return redirect(url_for('CategoryItems', category_id=category_id))
    if request.method == 'POST':
        session.delete(deleteItem)
        session.commit()
        flash('Your activity was successfully deleted!')
        return redirect(url_for('CategoryItems', category_id=category_id))
    else:
        return render_template('delete_activity_item.html',
                               category_id=category_id,
                               item_id=item_id,
                               item=deleteItem)


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out")
        return redirect(url_for('MainPage'))
    else:
        flash("You were not logged in")
        return redirect(url_for('MainPage'))


if __name__ == '__main__':
    app.secret_key = "akbara"
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
