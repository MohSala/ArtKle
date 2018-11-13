from flask import Flask,request,render_template, flash,redirect,url_for,logging, session
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

#config
app.config ['MYSQL_HOST'] = 'localhost'
app.config ['MYSQL_USER'] = 'root'
app.config ['MYSQL_PASSWORD'] = ''
app.config ['MYSQL_DB'] = 'myflaskapp'
app.config ['MYSQL_CURSORCLASS'] = 'DictCursor'

#init
mysql = MySQL(app) 

Articles = Articles()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    # Create cursor
    cur = mysql.connection.cursor()

    #fetch command
    result = cur.execute('SELECT * FROM articles')
    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html',articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html',msg=msg)

    #close connection
    cur.close()

@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    #execute command
    result = cur.execute('SELECT * FROM articles WHERE id = %s', [id])

    article = cur.fetchone()
    return render_template('article.html',article=article)

    #close connection
    cur.close()



class RegisterForm(Form):
    name = StringField("Name",[validators.Length(min=1, max=50)])
    username = StringField("Username",[validators.Length(min=4, max=25)])
    email = StringField("Email", [validators.Length(min=6, max=50)])
    password = PasswordField("Password ",[
        validators.DataRequired(),
        validators.EqualTo('confirm',message='Passwords do not match')
    ])
    confirm = PasswordField("Confirm Password")
    

@app.route('/register', methods=[ 'GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.hash(str(form.password.data))

        #create cursor
        cur = mysql.connection.cursor()

        #execute commands
        cur.execute("INSERT into users(name,email,username,password) VALUES(%s,%s,%s,%s)",(name,email,username,password))

        #commit to db
        mysql.connection.commit()

        #close db
        cur.close()

        flash('You are now registered and can log in', 'success')

        redirect(url_for('index'))
    return render_template('register.html', form = form)    
    

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #get form values
        username = request.form['username']
        password_candidate = request.form['password']

        #create cursor
        cur = mysql.connection.cursor()

        #execute command
        result = cur.execute('SELECT * FROM USERS WHERE username = %s', [username])

        if result >0:
            #get stored hash
            data = cur.fetchone()
            password = data['password']
            
            #compare passwords
            if sha256_crypt.verify(password_candidate,password):
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'invalid login'
                return render_template('login.html', error=error) 
            #close db connection
            cur.close()  
        else:
           error = 'Username not found'
           return render_template('login.html', error=error)

    return render_template('login.html')



def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please Login', 'warning')
            return redirect(url_for('login'))    
    return wrap

@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    #fetch command
    result = cur.execute('SELECT * FROM articles')
    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html',articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html',msg=msg)

    #close connection
    cur.close()


       

class ArticleForm(Form):
    title = StringField("Title",[validators.Length(min=1, max=50)])
    body = StringField("Body",[validators.Length(min=40)])

@app.route('/add_article',methods=['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate:
        title = form.title.data
        body = form.body.data

        #create cursor
        cur = mysql.connection.cursor()

        #execute command
        cur.execute('INSERT into articles(title,body,author) VALUES(%s,%s,%s)', (title,body, session['username']))

        #connect to db
        mysql.connection.commit()

        #close db
        cur.close()

        flash('Article Successfully Added', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)

@app.route('/edit_article/<string:id>/',methods=['GET','POST'])
@is_logged_in
def edit_article(id):
    #cre`te cursor
    cur = mysql.connection.cursor()

    result = cur.execute('SELECT * from Articles where id = %s', [id])

    article = cur.fetchone()

    #get form
    form = ArticleForm(request.form)

    #prepopulate form
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate:
        title = request.form['title']
        body = request.form['body']

        #create cursor
        cur = mysql.connection.cursor()

        #execute command
        cur.execute('UPDATE articles SET title=%s, body=%s WHERE id=%s', (title,body,[id]))

        #connect to db
        mysql.connection.commit()

        #close db
        cur.close()

        flash('Article Successfully Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

@app.route('/delete_article/<string:id>',methods=['GET','POST'])
@is_logged_in
def delete_article(id):
    cur = mysql.connection.cursor()

    cur.execute('DELETE from articles where id=%s',[id])

    #connect to db
    mysql.connection.commit()

    #close db
    cur.close()

    flash('Article Deleted', 'warning')

    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)