import os
import secrets
import mysql.connector
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, request, abort, session
from flaskDemo import app, db, bcrypt
from flaskDemo.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, Reserveform, ItemSearchForm, AddItemform, ReserveUpdateForm
from flaskDemo.models import Reservation, User1, Item, User1_type, Publisher, Author, Language, Post, Results, Location, Item_type
from flask_login import login_user, current_user, logout_user, login_required, LoginManager
from datetime import datetime

from functools import wraps

#Below 2 imports are for creating db_session, which is used for access to the whole database -Ted
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine('mysql://root:NummerEins#1@localhost/university library', convert_unicode=True) #IMPORTANT!!!! CHANGE THE URL WITH YOUR DB!!! -Ted
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind = engine))

#This part is a redefiner for the login_reqired decorater, to make it simple just testing with 3-library_stuff for accessing add and delete  -Ted
login_manager = LoginManager()

@app.route("/test", methods=['GET','POST'])
def test():
    searchdb = mysql.connector.connect(host="localhost",        #Change to your URL
                                       database='university library',
                                       user='root',                   #Change to your User
                                       password='NummerEins#1')              #Change to your Password
    if searchdb.is_connected():
        cursor = searchdb.cursor()
        
        sql = "SELECT \
            item.Title AS Title, \
            author.Author_Id AS Author \
            FROM item \
            INNER JOIN author ON item.Author_Id = author.Author_Id"
        cursor.execute(sql)
        results = cursor.fetchall()
    return render_template('result.html', results=results)

def login_required(role='ANY'):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            
            if not current_user.is_authenticated:
                return app.login_manager.unauthorized()
            if ((current_user.User1_type_id != role) and (role != 'ANY')):
                return app.login_manager.unauthorized()
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper
#End of new stuff -Ted


@app.route("/")

#This is the search part in construction -Ted
@app.route("/search", methods=['GET','POST'])
@login_required(role = 'ANY')
def search():
    search = ItemSearchForm(request.form)
    if request.method == 'POST':
        return search_results(search)
    return render_template('search.html', form=search)
        

@app.route("/results")
@login_required(role = 'ANY')
def search_results(search):
    search_string = search.data['search']

    if search_string:
        if search.data['select'] == 'Author':
#            qry = Item.query.join(Author, Item.Author_Id == Author.Author_Id) \
#                  .add_columns(Item.Title, Item.Item_Id, Author.LastName) \
#                  .join(Publisher, Item.Publisher_Id == Publisher.Publisher_Id) \
#                  .add_columns(Publisher.Name) \
#                  .filter(Author.LastName.contains(search_string))
            qry = db_session.query(Item, Author).filter(
                    Author.Author_Id==Item.Author_Id).filter(
                            Author.LastName.contains(search_string))
            results = [item[0] for item in qry.all()]
        elif search.data['select'] == 'Title':
#            qry = Item.query.join(Author,Item.Author_Id == Author.Author_Id) \
#                  .add_columns(Item.Title,Item.Item_Id,Author.LastName) \
#                  .join(Publisher, Item.Publisher_Id == Publisher.Publisher_Id) \
#                  .add_columns(Publisher.Name) \
#                  .filter(Item.Title.contains(search_string))
            qry = db_session.query(Item).filter(
                    Item.Title.contains(search_string))
            results = qry.all()
        elif search.data['select'] == 'Publisher':
            qry = db_session.query(Item, Publisher).filter(
                    Publisher.Publisher_Id==Item.Publisher_Id).filter(
                            Publisher.Publisher_Id.contains(search_string))
            results = [item[0] for item in qry.all()]
        elif search.data['select'] == 'Keyword':
            qry = db_session.query(Item).filter(
                    Item.Keyword.contains(search_string))
            results = qry.all()
        else:
            qry = db_session.query(Item)
            results = qry.all()
    else:
        qry = db_session.query(Item)
        results = qry.all()
    
    if not results:
        flash('No results found!')
        return redirect(url_for('search'))
    else:
        table = Results(results)
        table.border = True
        return render_template('results.html', table=table)
#End of the search part -Ted
        
    
    
    
@app.route("/home")
def home():

    
    # print("Hello world....shivang here....", flush=True)

    results4 = Reservation.query.join(User1,Reservation.User_ID == User1.User_Id)\
               .add_columns(Reservation.Reservation_Id,User1.FName, User1.LName)\
               .join(Item, Item.Item_Id == Reservation.Item_Id) \
               .add_columns(Item.Title)

               ##### get data by user1.user_id == current user of logged in user   where condition
               
    return render_template('assign_home.html', joined_m_n = results4)
    posts = Post.query.all()
    return render_template('search.html', posts=posts)
#
    return render_template('join.html', title='Join',joined_m_n = results4)

   

@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User1(UName=form.uname.data,FName=form.firstname.data,LName=form.lastname.data, DOB=form.dateofbirth.data,Email=form.email.data, Password=hashed_password, User1_type_id=form.user1typeid.data, Address=form.address.data)
        # user = User1(username=form.username.data, Email=form.email.data, Password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        print("user is already authenticated", flush=True)
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User1.query.filter_by(Email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.Password, form.password.data):
            print(user.UName, flush=True)
            user.authenticated = True
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required(role = 'ANY')
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.Email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.UName
        form.email.data = current_user.Email
    image_file = url_for('static', filename='profile_pics/' + current_user.UName)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)
    

@app.route("/publish/<Publisher_Id>/<Name>")
@login_required(role = 'ANY')
def publish(Publisher_Id,Name):
    publish = Publisher.query.get_or_404([Publisher_Id,Name])
    return render_template('publish.html', title=publish.Address, publish=publish,now=datetime.utcnow())

@app.route("/reserve", methods=['GET', 'POST'])
@login_required(role = 'ANY')
def reserve():
    form = Reserveform()
    if form.validate_on_submit():
        reserve = Reservation(Item_Id = form.Item_Id.data, User_ID=form.User_ID.data,Reservation_Date=datetime.today().strftime('%Y-%m-%d-%H:%M:%S'),Due_Date=form.Due_Date.data)
        db.session.add(reserve)
        db.session.commit()
        flash('The Item has been reserved to you till date' + datetime.today().strftime('%Y-%m-%d-%H:%M:%S'), 'success')
        return redirect(url_for('home'))
    return render_template('create_reserve.html', title='New Reservation',form=form, legend='New Reservation')


@app.route("/reserve/<Reservation_Id>")
@login_required(role = 'ANY')
def details_reserve(Reservation_Id):
    reserve = Reservation.query.get_or_404([Reservation_Id])
    return render_template('reserve.html', title=str(reserve.Reservation_Id), reserve=reserve, now=datetime.utcnow())


@app.route("/reserve/<Reservation_Id>/delete", methods=['POST'])
@login_required(role = 'ANY')
def delete_reserve(Reservation_Id):
    reserve = Reservation.query.get_or_404([Reservation_Id])
    db.session.delete(reserve)
    db.session.commit()
    flash('The relation has been deleted!', 'success')
    return redirect(url_for('home'))

#Structure is written by Yanji, modified by Ted. Also several html files modified by Yanji, include a new "update_reserve.html" file
@app.route("/reserve/<Reservation_Id>/update", methods=['GET', 'POST'])
@login_required(role = 'ANY')
def update_reserve(Reservation_Id):
    reserve = Reservation.query.get_or_404([Reservation_Id])
    
    form = ReserveUpdateForm()
    if form.validate_on_submit():
        reserve.Item_Id = form.Item_Id.data
        reserve.User_ID = form.User_ID.data
        reserve.Reservation_Date = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
        db.session.commit()
        flash('The relation has been updated!', 'success')
        return redirect(url_for('home'))
    elif request.method == 'GET':
        form.Item_Id.data = reserve.Item_Id
        form.User_ID.data = reserve.User_ID
    return render_template('update_reserve.html', title = 'Update Reservation', form=form, legend='Update Reservation')
#Yanji's codes end



#Emmanuels Add and Delete Item begins
@app.route("/add", methods=['GET', 'POST'])
@login_required(role = 3)
def add():
    form = AddItemform()
    items = Item.query.all()
    #
    if request.method == 'POST':

        addItem = Item(Keyword=form.keyword.data, \
                       Rack_Id=form.location.data, \
                       Item_type_id=form.type.data, \
                       Publisher_Id=form.publisher.data,\
                       Author_Id=form.author.data,\
                       Language_Id=form.language.data,\
                       Publication_Date=form.publication_date.data,\
                       Item_Id=0,\
                       Title=form.title.data)

        db.session.add(addItem)
        db.session.commit()
        items = Item.query.all()
        flash('The Item has been added', 'success')
        return render_template('add_item.html', title='New Item', form=form, legend='New Item', items=items)
    return render_template('add_item.html', title='New Item', form=form, legend='New Item', items=items)


@app.route("/item/delete", methods=['POST'])
@login_required(role=3)
def delete_item():
    item_id = int(request.form.get('itemId'));
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('The Item has been deleted!', 'success')
    return redirect(url_for('add'))

# Emmanuel's Add and Delete Item Ends


# Subquery -- prints in terminal -- Emmanuel
with engine.connect() as con:

    rs = con.execute('SELECT * FROM item WHERE keyword = "fiction"')

    for row in rs:
        print(row)
# Aggregation --prints in terminal --Emmanuel
with engine.connect() as con:

    rs = con.execute('SELECT * FROM author GROUP BY author_id')

    for row in rs:
        print(row)
# Compound condition -- prints in terminal --Emmanuel
with engine.connect() as con:

    rs = con.execute("SELECT * FROM author WHERE author_id BETWEEN 300 and 301")

    for row in rs:
        print(row)

