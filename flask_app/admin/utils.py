import datetime as dt
from time import sleep
from typing import List, Dict, Any
from multiprocessing import Process

from werkzeug.datastructures import ImmutableMultiDict

from flask_app.auth.models import User
from flask_app.auth import db


def fix_form(form: ImmutableMultiDict) -> Dict[str, Any]:
    """
    Changes checkboxes in form from 'on'/missing to bool types,
    converts 'None' in last_query to None.

    Parameters
    ----------
    form
        Web page form as ImmutableMultiDict.

    Returns
    -------
    Dict[str, Any]
        Returns regular dictionary with str keys and Union(bool, None, str)
        values.

    """
    last_query = form['last_query'] if form['last_query'] != 'None' else None
    verified = bool(form.get('verified'))
    admin_approved = bool(form.get('admin_approved'))
    admin_rights = bool(form.get('admin_rights'))
    new_form = {
        **form,
        'last_query': last_query,
        'verified': verified,
        'admin_approved': admin_approved,
        'admin_rights': admin_rights,
    }
    return new_form


def delete_unverified_users() -> None:
    """
    Deletes users, whose e-mail is unverified for more than 5 days.

    Returns
    -------
    None
        Only works with DB.

    """
    unverified_users: List[User] = User.query.filter_by(verified=False).all()
    today = dt.datetime.now()
    for user in unverified_users:
        if (today - user.date_created).days >= 5:
            db.session.delete(user)
    db.session.commit()


def run_delete_task() -> None:
    """
    Spawns parallel process to delete unverified users every 24h.
    """
    def worker():
        delete_unverified_users()
        sleep(86400)

    proc = Process(target=worker)
