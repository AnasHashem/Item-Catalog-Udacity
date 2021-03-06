from database_setup import Category, Item, User, Base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, desc
from flask import Flask, render_template, request, redirect, url_for, jsonify
# Auth imports ..
from flask import session as login_session
import random
import string
# Gconnect imports
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

engine = create_engine(
        'sqlite:///itemcatalogwithusers.db?check_same_thread=False')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)
CLIENT_ID = json.loads(
    open('/var/www/catalog/catalog/client_secrets.json', 'r').read())['web']['client_id']


def create_user(login_session):
    new_user = User(name=login_session['username'], email=login_session[
        'email'])
    session.add(new_user)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def get_user_info(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def get_user_id(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception:
        return None


@app.route('/')
def home():
    categories = session.query(Category).all()
    items = session.query(Item).order_by(desc('item.id')).all()[:9]

    if 'username' not in login_session:
        return render_template('publichome.html',
                               categories=categories, items=items)
    else:
        return render_template('home.html', categories=categories, items=items)


@app.route('/catalog/<string:name>/items')
def items(name):
    categories = session.query(Category).all()
    the_category = session.query(Category).filter_by(name=name).one()
    items = session.query(Item).filter_by(category=the_category).all()
    return render_template('items.html', categories=categories, items=items)


@app.route('/catalog/<string:ctg>/<string:item_name>')
def single_item(ctg, item_name):
    the_category = session.query(Category).filter_by(
                name=ctg).one()
    item = session.query(Item).filter_by(category=the_category,
                                         name=item_name).one()
    creator = get_user_info(item.user_id)

    if ('username' not in login_session or
            creator.id != login_session.get('user_id', '')):
        return render_template("publicsingleitem.html", item=item)
    else:
        return render_template("singleitem.html", item=item)


@app.route('/catalog/add_item/', methods=['GET', 'POST'])
def add_item():
    if 'username' not in login_session:
        return redirect(url_for('showlogin'))

    categories = session.query(Category).all()
    if 'username' not in login_session:
        return redirect(url_for('showlogin'))
    if request.method == 'GET':
        return render_template('additem.html', categories=categories)
    else:
        item_name = request.form['name']
        item_description = request.form['description']
        category = request.form['category']
        item_category = session.query(Category).filter_by(name=category).one()
        owner = get_user_info(login_session['user_id'])
        new_item = Item(name=item_name, description=item_description,
                        category=item_category, user=owner)
        session.add(new_item)
        session.commit()
        return redirect(url_for('home'))


@app.route('/catalog/<string:item>/edit/', methods=['GET', 'POST'])
def edit_item(item):
    if 'username' not in login_session:
        return redirect(url_for('showlogin'))

    the_item = session.query(Item).filter_by(name=item).one()
    if the_item.user_id != login_session.get('user_id', ''):
        return '''\
            <script>
            alert("You should'nt be here!");
            </script>
        '''

    categories = session.query(Category).all()
    if request.method == 'GET':
        return render_template('edititem.html',
                               categories=categories, item=item)
    else:
        the_ctg = session.query(Category).filter_by(
                        name=request.form['category']).one()
        the_item.name = request.form['name']
        the_item.description = request.form['description']
        the_item.category = the_ctg
        session.add(the_item)
        session.commit()
        return redirect(url_for('single_item',
                                ctg=the_ctg.name, item_name=the_item.name))


@app.route('/catalog/<string:item>/delete', methods=['GET', 'POST'])
def delete_item(item):
    if 'username' not in login_session:
        return redirect(url_for('showlogin'))

    the_item = session.query(Item).filter_by(name=item).one()
    if the_item.user_id != login_session.get('user_id', ''):
        return '''\
            <script>
            alert("You should'nt be here!");
            </script>
        '''

    if request.method == 'GET':
        return render_template('deleteitem.html', item=item)
    else:
        session.delete(the_item)
        session.commit()
        return redirect(url_for('home'))


@app.route('/catalog.json')
def json_format():
    categories = session.query(Category).all()
    final_json = {}
    id = 1
    for c in categories:
        final_json[c.name] = c.json  # To add a key-value pair
        items = session.query(Item).filter_by(category_id=id).all()
        temp_items = []
        for i in items:
            temp_items.append(i.json)
        final_json[c.name]['item'] = temp_items
        id += 1
    return jsonify(Catalog=[v for v in final_json.values()])


@app.route('/login')
def showlogin():
    # create anti-forgery state token
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Validate state token"""
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain Authorization code
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('/var/www/catalog/catalog/client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
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
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check if the user is already logged in.
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')

    if (stored_access_token is not None and
            gplus_id == stored_gplus_id):
        response = make_response(json.dumps('User is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session['username'] = data['name']
    login_session['email'] = data['email']

    user_id = get_user_id(login_session['email'])
    if not user_id:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('User not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = '''https://accounts.google.com/o/
             oauth2/revoke?token=%s''' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print result['status']
    print 'access_token'
    print login_session['access_token']

    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    else:
        response = make_response(
                json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


if __name__ == '__main__':
    app.secret_key = 'super'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
