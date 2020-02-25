from flask import (Blueprint, redirect, flash, url_for, render_template,
                   request)
from flask_login import login_required, current_user

from flask_app.auth.models import User
from flask_app.auth import db
from .utils import fix_form

admin = Blueprint('admin', __name__, template_folder='templates')


@admin.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_view():
    if not current_user.admin_rights:
        flash('You\'re not allowed here!')
        return redirect(url_for('views.index'))
    users = User.query.all()
    if request.method == 'POST':
        form = fix_form(request.form)
        print(form)
        user = User.query.get(form['id'])
        for key, value in form.items():
            setattr(user, key, value)
        db.session.add(user)
        db.session.commit()
        flash(f'Change successful!')
    return render_template('admin.html', users=users)
