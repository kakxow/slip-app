import platform

from flask import redirect, url_for, flash, render_template, request
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user

from .forms import LoginForm, RegistrationForm, PasswordResetRequestForm
from .forms import PasswordResetForm
from . import db, models, auth
from .email import send_password_reset_email, send_mail_verification_email


@auth.record
def record_params(setup_state):
    """
    Copies app.config to auth blueprint.
    """
    app = setup_state.app
    auth.config = {**app.config}


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Logins user and redirects them to next page (if specified in args) or index.
    """
    if current_user.is_authenticated:
        flash('You\'re already logged in!')
        return redirect(url_for('views.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = models.User.query.filter_by(username=form.username.data).first()
        if not user or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('.login'))
        elif not user.verified:
            flash('Email not verified, check your mailbox.')
            return redirect(url_for('.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('views.index')
        return redirect(next_page)
    return render_template('login.html', form=form)


@auth.route('/logout')
def logout():
    """
    Logouts current user and redirects them to index.
    """
    logout_user()
    return redirect(url_for('views.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registers user, sends verification e-mail and redirects them to login page.
    Doesn't send an email when MAIL environment variables not set.
    """
    mail_flag = auth.config.get('MAIL_FLAG')
    if current_user.is_authenticated:
        flash('You\'re already registered!')
        return redirect(url_for('views.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = models.User(
            username=form.username.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        if not mail_flag:
            user.verified = True
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!'
              'Verify your email and you can log in.')
        if mail_flag:
            send_mail_verification_email(user)
        return redirect(url_for('.login'))
    return render_template('register.html', form=form)


@auth.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    """
    Sends password reset link to the specified e-mail (if it exists in login_db)
    and redirects user to login page.
    """
    mail_flag = auth.config.get('MAIL_FLAG')
    if not mail_flag:
        flash('Not yet implemented.')
        return redirect(url_for('views.index'))
    if current_user.is_authenticated:
        flash('You\'re already logged in!')
        return redirect(url_for('views.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = models.User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(f'Check your email {form.email.data} for the instructions'
              'to reset your password')
        return redirect(url_for('.login'))
    return render_template('reset_password_request.html', form=form)


@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token: str):
    """
    Changes user's password with new and redirects user to login page.
    """
    if current_user.is_authenticated:
        flash('You\'re already logged in!')
        return redirect(url_for('views.index'))
    user = models.User.verify_reset_password_token(token)
    if not user:
        flash('Bad reset password token.')
        return redirect(url_for('views.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('.login'))
    return render_template('reset_password.html', form=form)


@auth.route('/verify_mail/<token>', methods=['GET'])
def verify_mail(token: str):
    """
    Verifies user's e-mail and redirects user to login page.
    """
    if current_user.is_authenticated:
        flash('You\'re already logged in!')
        return redirect(url_for('views.index'))
    user = models.User.verify_mail_verification_token(token)
    if not user:
        flash('Email verification token is tampered.')
        return redirect(url_for('views.index'))
    user.verified = True
    db.session.commit()
    flash('Your email is verified, you can login.')
    return redirect(url_for('.login'))
