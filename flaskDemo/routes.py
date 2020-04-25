import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flaskDemo import app, db, bcrypt
from flaskDemo.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, Reserveform
# from flaskDemo.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, DeptForm,DeptUpdateForm, Assignform
from flaskDemo.models import Reservation, User1, Item, User1_type, Publisher
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime


@app.route("/")
@app.route("/home")
def home():
    # results2 = Faculty.query.join(Qualified,Faculty.facultyID == Qualified.facultyID) \
    #            .add_columns(Faculty.facultyID, Faculty.facultyName, Qualified.Datequalified, Qualified.courseID) \
    #            .join(Course, Course.courseID == Qualified.courseID).add_columns(Course.courseName)
    # results = Faculty.query.join(Qualified,Faculty.facultyID == Qualified.facultyID) \
    #           .add_columns(Faculty.facultyID, Faculty.facultyName, Qualified.Datequalified, Qualified.courseID)
    #results3 = Works_On.query.join(Employee,Works_On.essn == Employee.ssn)\
     #       .add_columns(Employee.ssn, Project.pnumber, Employee.fname, Project.pname)\
      #      .join(Project, Project.pnumber == Works_On.pno)
    
    # print("Hello world....shivang here....", flush=True)

    results4 = Reservation.query.join(User1,Reservation.User_ID == User1.User_Id)\
               .add_columns(Reservation.Reservation_Id,User1.User_Id, Item.Item_Id, User1.Name, Item.Keyword)\
               .join(Item, Item.Item_Id == Reservation.Item_Id)       

               ##### get data by user1.user_id == current user of logged in user   where condition
               
    return render_template('assign_home.html', joined_m_n = results4)
    posts = Post.query.all()
    return render_template('home.html', posts=posts)
    results4 = Reservation.query.join(User1,Reservation.User_ID == User1.User_Id)\
               .add_columns(Reservation.Reservation_Id,User1.User_Id, Item.Item_Id, User1.Name, Item.Keyword)\
               .join(Item, Item.Item_Id == Reservation.Item_Id)
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
        user = User1(Name=form.name.data,DOB=form.dateofbirth.data,Email=form.email.data, Password=hashed_password, User1_type_id=form.user1typeid.data, Address=form.address.data)
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
            print(user.Name, flush=True)
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
@login_required
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
        form.username.data = current_user.Name
        form.email.data = current_user.Email
    image_file = url_for('static', filename='profile_pics/' + current_user.Name)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


@app.route("/dept/new", methods=['GET', 'POST'])
@login_required
def new_dept():
    form = DeptForm()
    if form.validate_on_submit():
        dept = Department(dname=form.dname.data, dnumber=form.dnumber.data,mgr_ssn=form.mgr_ssn.data,mgr_start=form.mgr_start.data)
        db.session.add(dept)
        db.session.commit()
        flash('You have added a new department!', 'success')
        return redirect(url_for('home'))
    return render_template('create_dept.html', title='New Department',
                           form=form, legend='New Department')


#@app.route("/dept/<dnumber>")
#@login_required
#def dept(dnumber):
 #   dept = Department.query.get_or_404(dnumber)
  #  return render_template('dept.html', title=dept.dname, dept=dept, now=datetime.utcnow())


@app.route("/dept/<dnumber>/update", methods=['GET', 'POST'])
@login_required
def update_dept(dnumber):
    dept = Department.query.get_or_404(dnumber)
    currentDept = dept.dname

    form = DeptUpdateForm()
    if form.validate_on_submit():          # notice we are are not passing the dnumber from the form
        if currentDept !=form.dname.data:
            dept.dname=form.dname.data
        dept.mgr_ssn=form.mgr_ssn.data
        dept.mgr_start=form.mgr_start.data
        db.session.commit()
        flash('Your department has been updated!', 'success')
        return redirect(url_for('dept', dnumber=dnumber))
    elif request.method == 'GET':              # notice we are not passing the dnumber to the form

        form.dnumber.data = dept.dnumber
        form.dname.data = dept.dname
        form.mgr_ssn.data = dept.mgr_ssn
        form.mgr_start.data = dept.mgr_start
    return render_template('create_dept.html', title='Update Department',
                           form=form, legend='Update Department')




@app.route("/dept/<dnumber>/delete", methods=['POST'])
@login_required
def delete_dept(dnumber):
    dept = Department.query.get_or_404(dnumber)
    db.session.delete(dept)
    db.session.commit()
    flash('The department has been deleted!', 'success')
    return redirect(url_for('home'))



@app.route("/publish/<Publisher_Id>/<Name>")
@login_required
def publish(Publisher_Id,Name):
    publish = Publisher.query.get_or_404([Publisher_Id,Name])
    return render_template('publish.html', title=publish.Address, publish=publish,now=datetime.utcnow())

@app.route("/reserve", methods=['GET', 'POST'])
@login_required
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
@login_required
def details_reserve(Reservation_Id):
    reserve = Reservation.query.get_or_404([Reservation_Id])
    return render_template('reserve.html', title=str(reserve.Reservation_Id), reserve=reserve, now=datetime.utcnow())


@app.route("/reserve/<Reservation_Id>/delete", methods=['POST'])
@login_required
def delete_reserve(Reservation_Id):
    reserve = Reservation.query.get_or_404([Reservation_Id])
    db.session.delete(reserve)
    db.session.commit()
    flash('The relation has been deleted!', 'success')
    return redirect(url_for('home'))


# @app.route("/reserve/<Reservation_Id>/<newDate>/update", methods=['POST'])
# @login_required
# def update_reserve(Reservation_Id, newDate):
#     # reserve = Reservation.query.get_or_404([Reservation_Id])
#     reserve = Reservation(Reservation_Id = Reservation_Id, Reservation_Date=datetime.today().strftime('%Y-%m-%d-%H:%M:%S'),Due_Date=newDate)
#     db.session.update(reserve)
#     db.session.commit()
#     flash('The relation has been deleted!', 'success')
#     return redirect(url_for('home'))


#@app.route("/assign/<User_ID>/<Item_Id>/delete", methods=['POST'])
#@login_required
#def delete_assign(User_ID,Item_Id):
#    assign = Reservation.query.get_or_404([User_ID,Item_Id])
#    db.session.delete(assign)
#    db.session.commit()
#    flash('The relation has been deleted!', 'success')
#    return redirect(url_for('home'))



@app.route("/assign/new", methods=['GET', 'POST'])
@login_required
def new_assign():
    form = Assignform()
    if form.validate_on_submit():
        assign = assignvalidate(essn=form.essn.data, pno=form.pno.data)
        db.session.add(assign)
        db.session.commit()
        flash('You have added a new relation!', 'success')
        return redirect(url_for('home'))
    return render_template('create_assign.html', title='New Employee-Project Assignment',form=form, legend='New Assignment')



