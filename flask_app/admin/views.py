from flask import (
    Blueprint,
    redirect,
    flash,
    url_for,
    render_template,
    request
)

from .utils import admin_required, make_forms, change_user, delete_user
from .forms import UserForm, NewUserForm

admin = Blueprint('admin', __name__, template_folder='templates', url_prefix='/admin')


@admin.route('/', methods=['GET', 'POST'])
@admin_required
def admin():
    """
    View, change, add and delete users from this view!
    """
    user_form = None
    if request.method == 'POST':
        user_is_new = request.form.get('new_user', type=int)
        user_form = NewUserForm() if user_is_new else UserForm()
        if user_form.validate_on_submit():
            change_user(user_form)
            flash(f'Change successful!')
    forms, new_form = make_forms(user_form)
    return render_template('admin.html', forms=forms, new_form=new_form)


@admin.route('/delete', methods=['GET'])
@admin_required
def delete():
    """
    Delete user entirely.
    """
    user_id = request.args.get('id', type=int)
    user = delete_user(user_id)
    if user:
        flash(f'User {user.username} is deleted.')
    else:
        flash(f'User with id {user_id} does not exist.')
    return redirect(url_for('.admin_panel'))
