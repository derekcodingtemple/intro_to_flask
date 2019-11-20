from app import db
from flask import current_app, render_template, redirect, url_for, flash, request
from app.forms import ProfileForm, BlogForm, ContactForm
from app.models import User, Post
from flask_login import login_user, logout_user, current_user, login_required
from app.email import send_email
import requests, json

# Made a small change somewhere

# FLASK_LOGIN
# .is_authenticated
# .is_active
# .is_anonymous
# .get_id()

# CRUD APPLICATION
# C - CREATE: POST
# R - READ: GET
# U - UPDATE: PUT
# D - DELETE: DELETE

@current_app.context_processor
def getGlobal():
  return dict(
    g_username=""
  )

@current_app.route('/', methods=['GET', 'POST'])
@login_required
def index():
  form = BlogForm()
  context = {
    'form': form,
    'posts': current_user.followed_posts()
  }
  if form.validate_on_submit():
    p = Post(body=form.body.data, user_id=current_user.id)
    db.session.add(p)
    db.session.commit()
    flash("Post added successfully", 'success')
    return redirect(url_for('index'))
  return render_template('index.html', **context)

@current_app.route('/contact', methods=['GET', 'POST'])
def contact():
  form = ContactForm()
  context = {
    'form': form
  }
  if form.validate_on_submit():
    send_email()
    flash("Your form submission was successful", "info")
    return redirect(url_for('contact'))
  return render_template('contact.html', **context)

@current_app.route('/about', methods=['GET', 'POST'])
@login_required
def about():
  form = ProfileForm()
  context = {
    'form': form
  }
  if request.method == 'GET':
    form.name.data = current_user.name
    form.email.data = current_user.email
  if form.validate_on_submit():
    current_user.name = form.name.data
    current_user.email = form.email.data
    current_user.password = form.password.data
    current_user.generate_password(current_user.password)
    db.session.commit()
    flash('Profile information updated successfully', 'success')
    return redirect(url_for('about'))
  return render_template('about.html', **context)

# /profile/
@current_app.route('/profile/<name>', methods=['GET', 'POST'])
@login_required
def profile(name):
  form = BlogForm()
  if form.validate_on_submit():
    p = Post(body=form.body.data, user_id=current_user.id)
    db.session.add(p)
    db.session.commit()
    flash("Post added successfully", 'success')
    return redirect(url_for('profile'))
  context = {
    'form': form,
    'posts': Post.query.filter_by(user_id=current_user.id).order_by(Post.timestamp.desc()).all()
  }
  return render_template('profile.html', **context)

@current_app.route('/post/delete/<int:id>')
@login_required
def post_delete(id):
  p = Post.query.get(id)
  db.session.delete(p)
  db.session.commit()
  flash("Post deleted successfully", "info")
  return redirect(url_for('profile', id=current_user.id))

@current_app.route('/users')
def users():
  context = {
    'users': [i for i in User.query.all() if i.id != current_user.id],
  }
  return render_template('users.html', **context)

@current_app.route('/users/add/<user>')
@login_required
def users_add(user):
  user = User.query.filter_by(name=user).first()
  if user not in current_user.followed:
    current_user.follow(user)
    flash("User added successfully", "success")
    return redirect(url_for('users'))
  flash(f"You are already following {user.name}", "warning")
  return redirect(url_for('users'))

@current_app.route('/users/remove/<user>')
@login_required
def users_remove(user):
  user = User.query.filter_by(name=user).first()
  if user in current_user.followed:
    current_user.unfollow(user)
    flash("User removed successfully", "info")
    return redirect(url_for('users'))
  flash("You cannot unfollow someone you're not following. Make it make sense, sis...", "danger")
  return redirect(url_for('users'))

@current_app.route('/users/delete/<user>')
@login_required
def users_delete(user):
  user = current_user
  db.session.delete(user)
  db.session.commit()
  flash("Your account was deleted successfully. Sorry to see you go.", "info")
  return redirect(url_for('index'))

@current_app.route('/racers')
def racers():
  response = requests.get('https://ergast.com/api/f1/2019/20/driverStandings.json')
  data = response.json()['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
  return render_template('racers.html', data=data)