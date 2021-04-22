from flask import Flask, render_template, redirect, request, session, abort
from flask_session import Session

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

import random
import string

import os
from werkzeug.utils import secure_filename
from os.path import join, dirname, realpath


app = Flask(__name__)

##### SESSION COOKIES #####
###########################
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


##### IMAGES LOCATION #####
###########################
UPLOADS_PATH = join(dirname(realpath(__file__)), 'static/images')
app.config['UPLOAD_FOLDER'] = UPLOADS_PATH

##### DATABASE #####
####################
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

##### MODELS #####
##################

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable = False)
    email = db.Column(db.String(80), unique=True, nullable = False)
    password = db.Column(db.String(30), nullable = False)
    blog_id = db.Column(db.Integer)

    def __repr__(self):
        return '<User %r>' % id

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    num_likes = db.Column(db.Integer, default = 0)
    num_followers = db.Column(db.Integer, default = 0)
    title = db.Column(db.String(60))
    profile_pic_location = db.Column(db.String(100))
    description = db.Column(db.String(200))

    def __repr__(self):
        return '<Blog %r>' % id

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer)
    title = db.Column(db.String(60))
    content = db.Column(db.String(300))
    date = db.Column(db.DateTime, default = datetime.utcnow)
    num_likes = db.Column(db.Integer, default = 0)

    def __repr__(self):
        return '<Post %r>' % id

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    content = db.Column(db.String(300))
    date = db.Column(db.DateTime, default = datetime.utcnow)
    post_id = db.Column(db.Integer)
    num_likes = db.Column(db.Integer, default = 0)

    def __repr__(self):
        return '<Comment %r>' % id

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    post_id = db.Column(db.Integer)
    comm_id = db.Column(db.Integer)
    
    def __repr__(self):
        return '<Like %r>' % id

class Follower(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    blog_id = db.Column(db.Integer)

    def __repr__(self):
        return '<Follower %r>' % id


# Pt a crea baza de date:
# db.create_all()

##### ROUTES #####
##################

@app.errorhandler(404)
def error404(e):
    return render_template('404.html')

# INDEX
@app.route('/', methods = ['POST', 'GET'])
def index():
    # Test if logged in
    if 'login-data' not in session:
        logged_in = False
        user = None
    else:
        logged_in = True
        try:
            user = User.query.filter_by(id=session['login-data']).first()
        except:
            print('err')
            user = None

    # Search for a blog
    if request.method == 'POST':
        search_term = request.form['search-bar']
        return redirect('results/' + str(search_term))

    # Latest posts:
    latest_posts = Post.query.filter_by().order_by(Post.date.desc()).all()
    # The blog where the post was found:
    posts_blog = dict()
    for p in latest_posts:
        posts_blog[p.blog_id] = Blog.query.filter_by(id = p.blog_id).first().title

    # Get comments:
    comments = Comment.query.filter_by().order_by(Comment.date.desc()).all()
    comments = comments[:5]
    if logged_in:
        # Get fav blogs:
        favourite_blogs = list()
        follows = Follower.query.filter_by(user_id = user.id).all()
        for f in follows:
            favourite_blogs.append(Blog.query.filter_by(id = f.blog_id).first())
        favourite_blogs = favourite_blogs[:5]
        fresh_blogs = None

        # Get new comments:
        #TODO
    else:
        # Get fresh blogs:
        favourite_blogs = None
        fresh_blogs = Blog.query.filter_by().order_by(Blog.id.desc()).all()
        fresh_blogs = fresh_blogs[:5]
    
        # Get hot comments:
        #TODO
    return render_template('index.html', logged_in = logged_in, user = user, latest_posts = latest_posts, favourite_blogs = favourite_blogs, fresh_blogs = fresh_blogs, new_comments = comments, hot_comments = comments, posts_blog = posts_blog)


# LOGIN
@app.route('/login', methods = ['POST', 'GET'])
def login():
    # If user's already logged in redirect to index
    if 'login-data' in session:
        return redirect('/')    
    if request.method == 'POST':
        # Get data from form
        username = request.form['uname']
        password = request.form['pswd']
        try:
            # Verify if user exists
            user = User.query.filter_by(username=username).first()
            if user is None:                
                print('Wrong name')
                return redirect('/login')
            # Check passowrd
            if user.password == password:
                #Session cookie
                session['login-data'] = user.id
                print('login successful')
                return redirect('/')   
            else:
                return redirect('/login')             
        except:
            print('err DB')
    else:
        return render_template('login.html')


# SIGN UP
@app.route('/sign-up', methods = ['POST', 'GET'])
def sign_up():    
    if request.method == 'POST':
        # Get data from form
        username = request.form['uname']
        email = request.form['email']
        password = request.form['pswd']
        try:
            # Test if username or email are already used 
            if User.query.filter_by(username=username).first() is not None:  
                print('username already used')
                return redirect('/sign-up')
            if User.query.filter_by(email=email).first() is not None:
                print('email already used')
                return redirect('/sign-up')
            # Create new user
            user = User(username=username, email=email, password=password)
            # Add user to DB
            db.session.add(user)
            db.session.commit()

            #Create login session
            session['login-data'] = user.id     
            print('sign-up succesful')

            #Create a blog for a new account
            blog = Blog(user_id = user.id)
            user.blog_id = blog.id
            #Add blog to DB
            try:
                db.session.add(blog)
                db.session.commit()
                blog = Blog.query.filter_by(user_id = user.id).first()
                user.blog_id = blog.id
                db.session.commit()
            except:
                print('err')

            #Redirect to blog edit
            return redirect('/edit-blog')
        except:
            print('err DB')
            return redirect('/sign-up')
    else:
        print('test2')
        return render_template('sign-up.html')


# USER RELATED
@app.route('/my-account', methods = ['POST', 'GET'])
def my_account():
    # Test if logged in
    if 'login-data' not in session:
            logged_in = False
            user = None
    else:
        logged_in = True
        try:
            user = User.query.filter_by(id=session['login-data']).first()
        except:
            print('err')
            user = None

    if request.method == 'POST':
        # Get data from form
        email = request.form['email']
        password = request.form['pswd']
        try:
            # Test if email is already used
            if User.query.filter_by(email=email).first() is not None:
                print('email already used')
                return redirect('/my-account')       
            # Update db    
            user.email = email
            user.password = password
            db.session.commit()
        except:
            print('err DB')
        return redirect('/my-account')
    else:
        return render_template('my-account.html', logged_in = logged_in, user = user)
 

#BLOG RELATED
@app.route('/blog/<id>', methods = ['GET', 'POST'])
def blog(id):    
    # Test if logged in
    if 'login-data' not in session:
        logged_in = False
        user = None
    else:
        logged_in = True
        try:
            user = User.query.filter_by(id=session['login-data']).first()
        except:
            print('err-user')
            user = None    
    try:
        # Get Blog
        blog = Blog.query.filter_by(id=id).first()
        blog_owner = User.query.filter_by(id=blog.user_id).first()
        # Get blog's  owner's name
        blog_owner_name = blog_owner.username

        # Get Blog Posts
        posts = Post.query.filter_by(blog_id=blog.id).order_by(Post.date.desc()).all()

        # Get Comments for each post
        comments = dict() 
        comments_user = dict()              
        for post in posts:
            comments[post.id] = Comment.query.filter_by(post_id = post.id).order_by(Comment.date.desc()).all()
            # Get comment's owner name       
            for i in comments[post.id]:
                comments_user[i.id] = User.query.filter_by(id = i.user_id).first().username
        
        # Test if user is the blog's owner
        if logged_in and blog.user_id == user.id:
            owner = True
        else:
            owner = False
        if logged_in:
            # Test if user is following this blog
            follower = Follower.query.filter_by(user_id = user.id, blog_id = blog.id).first()
            if follower is not None:
                followed = True
            else:
                followed = False

            # POST METHOD
            if request.method == 'POST':                                
                # Create New POST
                if 'post-title' in request.form and 'post-content' in request.form:
                    post_title = request.form['post-title']
                    post_content = request.form['post-content']
                    post = Post(blog_id = blog.id, title = post_title, content = post_content)
                    db.session.add(post)
                    db.session.commit()

                # Create New COMMENT
                for post in posts:
                    name = 'comment' + str(post.id)
                    if name in request.form:                       
                        comment_content = request.form[name]
                        post_id = int(name.strip('comment'))
                        comment = Comment(user_id = user.id, content = comment_content, post_id = post_id)
                        db.session.add(comment)
                        db.session.commit()
                # FOLLOW BUTTON
                # If user unfollows set followed = False and delete DB entry
                if 'f-btn' in request.form:
                    if request.form['f-btn'] == 'unfollow':
                        # Update number of followers
                        blog.num_followers = blog.num_followers - 1                 
                        followed = False
                        # Update DB
                        db.session.delete(follower)
                        db.session.commit()
                    # If user follows set followed = True and add entry to DB
                    elif request.form['f-btn'] == 'follow':
                        # Update number of followers
                        blog.num_followers = blog.num_followers + 1

                        followed = True
                        follower = Follower(user_id = user.id, blog_id = blog.id)
                        # Update DB                    
                        db.session.add(follower)
                        db.session.commit()
        else:
            followed = False        
        
    except:
        print('err-blog')
        blog = None
        owner = False
        abort(404)
    
    return render_template('blog.html', logged_in = logged_in, blog = blog, owner = owner, blog_owner_name = blog_owner_name, followed = followed, posts = posts, comments = comments, comments_user = comments_user)

@app.route('/my-blog')
def my_blog():
    # Test if logged in, if not go to 404
    if 'login-data' not in session:        
        logged_in = False
        user = None
        abort(404)
    else:
        logged_in = True
        try:
            # Try to get user's blog
            user = User.query.filter_by(id=session['login-data']).first()
            print(user.id)
            blog = Blog.query.filter_by(id=user.blog_id).first()
            print(blog.id)
            return redirect('/blog/' + ''.join(str(blog.id)))        
        except:
            print('err-user')
            user = None    
            abort(404)
        

@app.route('/edit-blog', methods = ['POST', 'GET'])
def edit_blog():    
    # Test if logged in
    if 'login-data' not in session:
        logged_in = False
        user = None
    else:
        logged_in = True
        try:
            # Get the pair of user and blog
            user = User.query.filter_by(id=session['login-data']).first()
            blog = Blog.query.filter_by(user_id = user.id).first()
            # POST METHOD
            if request.method == 'POST':
                # Get data from form and update DB
                blog.title = request.form['blog-title']
                blog.description = request.form['description-txt']      
                # Get profile image                       
                if 'file' in request.files:
                    file = request.files['file']
                    filename = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6)) + secure_filename(file.filename)
                    print('Nume fisier ' + filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    if blog.profile_pic_location is not None:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], blog.profile_pic_location))
                    blog.profile_pic_location = filename
                else:
                    print('fwawga')
                db.session.commit()  
                
                # Redirect
                return redirect('/')
              
        except:
            print('err-250')
            user = None
            blog = None
         
        # GET METHOD
        return render_template('edit-blog.html', logged_in = logged_in)

@app.route('/results/<search_term>', methods = ['POST', 'GET'])
def results(search_term):    
    # Test if logged in
    if 'login-data' not in session:
        logged_in = False
        user = None
    else:
        logged_in = True
        try:
            user = User.query.filter_by(id=session['login-data']).first()
        except:
            print('err')
            user = None

    blog_owner_names = dict()
    # Get blogs
    blogs = Blog.query.filter(Blog.title.like(search_term))
    # Get blog owners
    for b in blogs:
        blog_owner_names[b.user_id] = User.query.filter_by(id = b.user_id).first().username
    # Search for other blogs
    if request.method == 'POST':
        search_term = request.form['search-bar']
        return redirect('/results/' + str(search_term))
    # Render results
    return render_template('results.html', search_term = search_term, logged_in = logged_in, blogs = blogs, blog_owner_names = blog_owner_names)

@app.route('/log-out')
def log_out():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    app.run(debug = True, port = 9566)