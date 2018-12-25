from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


app=Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'parallels'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'project'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

@app.route('/') #reference to the index page
def index():
    return render_template('home.html')

@app.route('/about')    #reference to the about me page
def about():
    return render_template('about.html')

@app.route('/search')   #reference to the Search Music Page
def search():
    # Create cursor
    cur = mysql.connection.cursor()

    #getting all queries
    result = cur.execute("SELECT * from queries")
    querydata = cur.fetchall()

    cur.close()

    models=['Cosine','WordNet','BM25']

    return render_template('search.html',querydata=querydata[0:25], models=models)

    #return render_template('search.html')


@app.route('/searched',methods=['GET','POST'])  #reference to specific music searched page
def searched():
    a='nothinh'
    b='thingno'
    c=''

    if request.method=='POST':
        a=request.form['query']
        b=request.form['model']

    if b == 'Cosine':
        c=1

        # Create cursor
        cur = mysql.connection.cursor()

        #getting all songs with respect to the searched query id
        result = cur.execute("SELECT * FROM songs WHERE id IN (SELECT songid FROM cosinemodel WHERE queryid = %s)",[a])
        data = cur.fetchall()

        app.logger.info(data)

        if result > 0:
            return render_template('searched.html',query=a,model=b,c=c,data=data)
        else:
            msg='No Song recommeneded'
            return render_template('searched.html',msg=msg,query=a,model=b,c=c)

        cur.close()



    elif b== 'WordNet':
        c='2'
    elif b=='BM25':
        c='3'

    return render_template('searched.html',query=a,model=b,c=c)


# Register Form Class for wtforms
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query for inserting users
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('index'))
    return render_template('register.html', form=form)

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():

    # Create cursor
    cur = mysql.connection.cursor()

    # Get user songs with respect to username
    result = cur.execute("SELECT * FROM songs WHERE id IN (SELECT songid FROM userplaylist WHERE username = %s)",[session['username']])
    data = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html',data=data)
    else:
        msg='No Song in Playlist'
        return render_template('dashboard.html',msg=msg)

    cur.close()

# Delete Song from userplaylist
@app.route('/delete_song/<string:id>', methods=['POST'])
@is_logged_in
def delete_song(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # delete song with respect to username
    cur.execute("DELETE FROM userplaylist WHERE songid = %s and username=%s", ([id],[session['username']]))

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Song Deleted from Playlist', 'success')

    return redirect(url_for('dashboard'))

# Add Song to User Playlist
@app.route('/add_playlist_song/<string:id>', methods=['POST'])
@is_logged_in
def add_playlist_song(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # insert into table playlist
    cur.execute("INSERT INTO userplaylist(username, songid) VALUES(%s, %s)", ([session['username']], id))

    # Commit to DB
    mysql.connection.commit()

    # Close connection
    cur.close()

    flash('Song Added to Playlist', 'success')

    return redirect(url_for('dashboard'))


@app.route('/allsong')    #reference to the All Song Page
def allsong():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get names of all artists
    result = cur.execute("SELECT DISTINCT artist from songs")
    data = cur.fetchall()

    if result > 0:
        return render_template('allsong.html',data=data)
    else:
        msg='No Song Available'
        return render_template('allsong.html',msg=msg)

    cur.close()

# Selecting artist Songs
@app.route('/artist_song_selected/<string:artist>', methods=['POST'])
def artist_song_selected(artist):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get songs by specific artist
    result = cur.execute("SELECT * from songs where artist=%s",[artist])
    data = cur.fetchall()

    if result > 0:
        return render_template('artistsongs.html',data=data,namee=artist)
    else:
        msg='No Song in Playlist'
        return render_template('artistsongs.html',msg=msg,namee=artist)

    cur.close()

    #return redirect(url_for('allsong'),data=data)

if __name__=="__main__":    #main function for the python
    app.secret_key='secretkey1122'
    app.run(debug=True)
