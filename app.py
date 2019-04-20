from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from validate_email import validate_email
from flask_share import Share



app=Flask(__name__)

#initializing the extenstion
share = Share(app)


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

    models=['All','Cosine','WordNet','BM25']

    return render_template('search.html',querydata=querydata, models=models)

    #return render_template('search.html')


@app.route('/searched',methods=['GET','POST'])  #reference to specific music searched page
def searched():

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

        #app.logger.info(data)

        if result > 0:
            return render_template('searched.html',query=a,model=b,c=c,data=data)
        else:
            msg='No Song recommeneded'
            return render_template('searched.html',msg=msg,query=a,model=b,c=c)

        cur.close()

    elif b== 'WordNet':
        c=2

        # Create cursor
        cur = mysql.connection.cursor()

        #getting all songs with respect to the searched query id
        result = cur.execute("SELECT * FROM songs WHERE id IN (SELECT songid FROM wordnetmodel WHERE queryid = %s)",[a])
        data = cur.fetchall()

        #app.logger.info(data)

        if result > 0:
            return render_template('searched.html',query=a,model=b,c=c,data=data)
        else:
            msg='No Song recommeneded'
            return render_template('searched.html',msg=msg,query=a,model=b,c=c)

        cur.close()


    elif b=='BM25':
        c=3

        # Create cursor
        cur = mysql.connection.cursor()

        #getting all songs with respect to the searched query id
        result = cur.execute("SELECT * FROM songs WHERE id IN (SELECT songid FROM bm25model WHERE queryid = %s)",[a])
        data = cur.fetchall()

        #app.logger.info(data)

        if result > 0:
            return render_template('searched.html',query=a,model=b,c=c,data=data)
        else:
            msg='No Song recommeneded'
            return render_template('searched.html',msg=msg,query=a,model=b,c=c)

        cur.close()


    elif b=='All':
        c=4

        # Create cursor
        cur = mysql.connection.cursor()

        #getting all songs of cosine to the searched query id
        cosineresult = cur.execute("SELECT * FROM songs WHERE id IN (SELECT songid FROM cosinemodel WHERE queryid = %s)",[a])
        cosinedata = cur.fetchall()

        #getting all songs of wordnet to the searched query id
        wordnetresult = cur.execute("SELECT * FROM songs WHERE id IN (SELECT songid FROM wordnetmodel WHERE queryid = %s)",[a])
        wordnetdata = cur.fetchall()

        #getting all songs of wordnet to the searched query id
        bm25result = cur.execute("SELECT * FROM songs WHERE id IN (SELECT songid FROM bm25model WHERE queryid = %s)",[a])
        bm25data = cur.fetchall()

        app.logger.info(cosinedata)

        if cosineresult > 0 or wordnetresult > 0 or bm25result > 0:
            return render_template('searched.html',query=a,model=b,c=c,cosinedata=cosinedata,wordnetdata=wordnetdata,bm25data=bm25data,checker=1)
        else:
            msg='No Song recommeneded'
            return render_template('searched.html',msg=msg,query=a,model=b,c=c,checker=1)

        cur.close()



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

    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        email = request.form['email']
        cpassword = request.form['cpassword']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s OR email = %s", ([username],[email]))

        if result > 0:
            flash('User already registered', 'danger')
            return render_template('register.html')
        else:
            if password==cpassword:
                password = sha256_crypt.encrypt(password)
                # Execute query for inserting users
                cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", ([name], [email], [username], [password]))
                # Commit to DB
                mysql.connection.commit()

                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now registered and logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Password Does Not Match', 'danger')
                return render_template('register.html')

        cur.close()

        return redirect(url_for('index'))
    return render_template('register.html')

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

#   Selecting single song!
@app.route('/singlesong/<string:id>', methods=['POST'])
def singlesong(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get songs by specific artist
    result = cur.execute("SELECT * from songs where id=%s",[id])
    data = cur.fetchall()

    link=data[0]['song'].replace(" ", "+")

    if result > 0:
        return render_template('singlesong.html',data=data,link=link)
    else:
        msg='No Song'
        return render_template('singlesong.html',msg=msg,namee=artist)

    cur.close()


if __name__=="__main__":    #main function for the python
    app.secret_key='secretkey1122'
    app.run(debug=True)
