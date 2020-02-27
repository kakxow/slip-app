import datetime as dt

from flask import (Blueprint, redirect, flash, url_for, render_template,
                   request)
from flask_login import login_required

from flask_app.auth.models import User
from flask_app.auth import db
from .utils import fix_form, admin_required
from .forms import UserForm, NewUserForm

admin = Blueprint('admin', __name__, template_folder='templates', url_prefix='/admin')


@admin.route('/', methods=['GET', 'POST'])
@admin_required
@login_required
def admin_panel():
    """
    View, change, add and delete users from this view!
    """
    user_id = None
    forms = []
    if request.method == 'POST':
        user_form = UserForm()
        user_id = user_form.data['id']
        forms.append(user_form)
        if user_form.validate_on_submit():
            form = fix_form(user_form.data)
            passwd = form.pop('password', None)
            user = User.query.get(user_id) or User()
            for key, value in form.items():
                setattr(user, key, value)
            if passwd:
                user.set_password(passwd)
            db.session.add(user)
            db.session.commit()
            flash(f'Change successful!')
    users = User.query.all()
    forms += [UserForm(None, obj=user) for user in users if user.id != user_id]
    empty_form = NewUserForm(
        None,
        id=max(user.id for user in users)+1,
        date_created=dt.datetime.now()
    )
    print(empty_form.data)
    forms += [empty_form]
    forms.sort(key=lambda x: x.data['id'])
    return render_template('admin_panel.html', forms=forms)


@admin.route('/delete_user', methods=['GET'])
@admin_required
@login_required
def delete_user():
    """
    Deletes user with id from query string.
    """
    user_id = request.args.get('id', type=int)
    user = User.query.get(user_id)
    username = user.username
    if user:
        db.session.delete(user)
        db.session.commit()
        flash(f'User {username} deleted successfuly')
    else:
        flash(f'User with id {user_id} do not exist')
    return redirect(url_for('.admin_panel'))
