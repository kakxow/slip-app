import datetime as dt
from functools import wraps
from time import sleep
from typing import List, Callable, Optional, Tuple, Union
from multiprocessing import Process

from flask import flash, redirect, url_for
from flask_login import current_user, login_required

from flask_app.auth.models import User
from flask_app.auth import db
from db import SessionCM
from .forms import UserForm, NewUserForm


def delete_unverified_users() -> None:
    """
    Deletes users, whose e-mail is unverified for more than 5 days.

    Returns
    -------
    None
        Only works with DB.

    """
    today = dt.datetime.now()
    cutoff_date = today - dt.timedelta(days=5)
    with SessionCM as sess:
        # print(sess.get_bind())
        q = sess.query(User). \
            filter_by(is_verified=False). \
            filter(User.date_created < cutoff_date.date())
        # print(q, cutoff_date)
        old_unverified_users = q.all()
        # print(old_unverified_users)
        for user in old_unverified_users:
            sess.delete(user)
        sess.commit()


def worker():
    while True:
        delete_unverified_users()
        sleep(86400)


def run_delete_task() -> None:
    """
    Spawns parallel process to delete unverified users every 24h.
    """
    proc = Process(target=worker, daemon=True)
    proc.start()


def admin_required(func: Callable) -> Callable:
    """
    Add this decorator to ensure current user is admin before calling view.
    """
    @wraps(func)
    @login_required
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin:
            flash('You\'re not allowed here!')
            return redirect(url_for('views.index'))
        return func(*args, **kwargs)
    return decorated_view


def make_forms(changed_form: Union[UserForm, NewUserForm, None]) -> Tuple[List[UserForm], NewUserForm]:
    """
    Generates UserForms and a NewUserForm from all active users.
    Takes in account recently changed data from changed_form, if present.

    Parameters
    ----------
    changed_form
        Form with recently changed data.

    Returns
    -------
    List[FlaskForm]
        List of forms for all users.

    """
    users = User.query.all()
    user_ids = tuple(user.id for user in users)
    next_id = max(user_ids) + 1
    changed_id = changed_form.user_id.data if changed_form else None

    forms = [UserForm(None, obj=user, user_id=user.id) for user in users if user.id != changed_id]
    new_form = NewUserForm(
            None,
            user_id=next_id,
            date_created=dt.datetime.now(),
            is_active=True
        )
    if changed_id in user_ids:
        # new newform or changed userform
        user_form = UserForm(None, data=changed_form.data)  # type: ignore
        forms += [user_form]
    elif changed_id and changed_form.errors:  # type: ignore
        new_form = changed_form  # type: ignore

    forms.sort(key=lambda x: x.data['user_id'])
    return forms, new_form


def change_user(user_form: UserForm) -> None:
    """
    Changes or creates user, based on id from user_form.

    Parameters
    ----------
    user_form
        Form with changed user data.

    Returns
    -------
    None
        Changes or creates a record in DB.

    """
    form = user_form.data
    # next_id = db.session.query(db.func.max(User.id)).scalar() + 1
    # Pop ID and date_created - no plans to change them!
    user_id = form.pop('user_id')
    user = User.query.get(user_id) or User()
    # Pop password - it's managed separately with User.set_password() method.
    passwd = form.pop('password', None)
    user_form.populate_obj(user)
    if passwd:
        user.set_password(passwd)
    print(user.__dict__)
    db.session.add(user)
    db.session.commit()


def delete_user(user_id: int) -> Optional[User]:
    """
    Deletes user from DB.

    Parameters
    ----------
    user_id
        User ID to activate/inactivate.

    Returns
    -------
    Optional[User]
        Returns user if successful or None otherwise.

    """
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return user
