import csv
import io
import json
import operator
import pickle
import re
from typing import List, Dict, Any, Optional, Callable

from flask import abort
from flask_sqlalchemy import Pagination
from flask_login import current_user
from werkzeug import Response

from db import Slip
from flask_app.auth import db
import config


def page_error_handler(pagination: Pagination) -> Response:
    """Error handler for out of range page_id's."""
    abort(404, f'Page {pagination.page} is out of range.')


def get_data(
    pagination: Pagination,
    page_id: int = 0,
    per_page: int = None,
    error_handler: Callable = None
) -> List[Slip]:
    """
    Extracts data from pagination - one page if page_id or all data if
    page_id == 0.

    Parameters
    ----------
    pagination
        Complete pagination object.
    page_id
        Number of the page to be extracted.  If page_id == 0 - all data will be
        returned.
    per_page
        Items per page
    error_handler
        Callable to use if page_id > total pages.

    Returns
    -------
    List[Slip]
        Returns list of Slip objects.

    """
    # pagination = get_from_db_paginate(form, page_id or 1, per_page)
    if page_id > pagination.pages and pagination.total:
        if error_handler:
            error_handler(pagination)
        else:
            raise IndexError('page_id out of range')
    # Page ID is set and it's within the bounds.
    creiterion = page_id and page_id <= pagination.pages
    data = pagination.items if creiterion else pagination.query.all()
    return data


def prettify_result(input_: List[Slip]) -> List[Dict[str, str]]:
    """
    Prettify list of Slips from input to list of Dict[str, str]
    with leading _id, starting from 1

    Parameters
    ----------
    input_
        List of Slips - the output from database query.

    Returns
    -------
    List[Dict[str, str]]
        List of enumerated dictionaries, where both keys and values are strings.

    """
    exclude_list = ['something', 'updated']
    result = [exclude_keys(el.to_json(), exclude_list)
              for el in input_]
    result = [{**el, '_id': str(i)} for i, el in enumerate(result, start=1)]
    return result


def save_form_to_current_user(form: Dict[str, str]) -> None:
    """
    Fills last_query fild of User with jsonified form.
    Used to effectively paginate.

    Parameters
    ----------
    form
        Any dictionary with json serializable keys.

    Returns
    -------
    None
        Only works with DB, nothign is returned.

    """
    user = current_user
    user.last_query = json.dumps(form)
    db.session.add(user)
    db.session.commit()


def get_form_for_current_user() -> Dict[str, str]:
    """
    Returns form, saved in user DB for current user.

    Returns
    -------
    Dict[str, str]
        Dictionary with form from previous successful query.

    """
    last_query = current_user.last_query or '{}'
    return json.loads(last_query)


def format_summ(s: Optional[str]) -> Optional[str]:
    """
    Formats s to make sure it matches pattern \\d+[.]\\d{2}

    Parameters
    ----------
    s
        :obj:`str` to format.

    Returns
    -------
    Optional[str]
        Correctly formatted :obj:`str` or None, if s is not :obj:`str`.

    """
    pttrn_replace = r'[,\-_=]'
    try:
        s = s.replace(' ', '')
        return f'{float(re.sub(pttrn_replace, ".", s)):.2f}'
    except (TypeError, ValueError, AttributeError):
        return None


def format_pos_id(s: Optional[str]) -> Optional[str]:
    """
    Formats s to make sure it matches pattern \\d{8}.

    Parameters
    ----------
    s
        :obj:`str` to format.

    Returns
    -------
    Optional[str]
        Correctly formatted :obj:`str` or None, if s is not :obj:`str` or :obj:`int`.

    """
    try:
        return f'{int(s):08d}'
    except (TypeError, ValueError):
        return None


def save_file(page_id: int) -> io.BytesIO:
    """
    Gets data from DB for current user (all or one page) and saves it
    in bytes as .csv file.

    Parameters
    ----------
    page_id
        Page number to extract.  Use None if you want all data.

    Returns
    -------
    io.BytesIO
        Bytes buffer to be sent as file.

    """
    form = get_form_for_current_user()
    pagination = get_from_db_paginate(form, page_id)
    data = get_data(pagination, error_handler=page_error_handler)
    result = prettify_result(data)

    temp = io.BytesIO()
    with io.StringIO() as f:
        w = csv.DictWriter(f, fieldnames=result[0], delimiter=';')
        w.writeheader()
        w.writerows(result)

        temp.write(f.getvalue().encode('cp1251'))
        temp.seek(0)

    return temp


def get_from_db_paginate(
    form: Dict[str, str],
    page_id: int,
    per_page: int = None
) -> Pagination:
    """
    Queries DB with filters given in a form and returns a Pagination object.

    Parameters
    ----------
    form
        WTForms form.data or any other dict to filter with.
    page_id
        Page number.
    per_page
        Items per page

    Returns
    -------
    Pagination
        Flask-SQLAlchemy Pagination object.

    """
    per_page = per_page or config.PAGE_SIZE
    fixture = {
        'start_date': (
            'date',
            operator.methodcaller(
                'between',
                form.get('start_date'),
                form.get('end_date'),
            )
        ),
        'merchant_name': (
            'merchant_name',
            operator.methodcaller(
                'contains',
                form.get('merchant_name')
            )
        ),
        'object_code': (
            'object_code',
            operator.methodcaller(
                '__eq__',
                (form.get('object_code', '') or '').upper()
            )
        ),
        'card_number': (
            'card_number',
            operator.methodcaller(
                'endswith',
                form.get('card_number')
            )
        ),
        'pos_id': (
            'pos_id',
            operator.methodcaller(
                '__eq__',
                format_pos_id(form.get('pos_id'))
            )
        ),
        'ref_num': (
            'ref_num',
            operator.methodcaller(
                '__eq__',
                form.get('ref_num')
            )
        ),
        'auth_code': (
            'auth_code',
            operator.methodcaller(
                '__eq__',
                form.get('auth_code')
            )
        ),
        'start_summ': (
            'summ',
            operator.methodcaller(
                '__ge__',
                format_summ(form.get('start_summ'))
            )
        ),
        'end_summ': (
            'summ',
            operator.methodcaller(
                '__le__',
                format_summ(form.get('end_summ'))
            )
        ),
    }
    q = Slip.query
    for key, value in form.items():
        if value and key in fixture:
            filter_attr, filter_func = fixture[key]
            q = q.filter(filter_func(getattr(Slip, filter_attr)))
    pagination = q.paginate(page=page_id, per_page=per_page, error_out=False)
    return pagination


def exclude_keys(
    dct: Dict[Any, Any],
    exclude: List[Any]
) -> Dict[Any, Any]:
    """
    Excludes multiple keys from dct.  Doesn't raise errors if key is not found.
    Parameters
    ----------
    dct
        Dictionary to process.
    exclude
        List of keys to exclude from dct.

    Returns
    -------
    Dict[Any, Any]
        Dictionary without keys from exclude.

    """
    result = dct
    for key in exclude:
        result.pop(key, None)
    return result
