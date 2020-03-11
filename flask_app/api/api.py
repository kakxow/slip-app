import hashlib
import hmac
from typing import Dict, List, Tuple

from flask import jsonify, abort, request

from config import Config
from flask_app.base.functions import get_from_db_paginate, get_data, page_error_handler
from flask_app import db_slip
from db import Slip
from .utils import insert_slips, rrn_exists, format_dates, get_meta


__all__ = ['list_slips', 'add_slips', 'get_one_slip', 'update_one_slip', 'delete_one_slip']


def basic_auth(username: str, password: str, required_scopes=None):
    user_ok = hmac.compare_digest(username, Config.API_USER)
    hashed_password: str = hashlib.sha512(
        password.encode('utf-8') + Config.SECRET_KEY.encode('utf-8')
    ).hexdigest()
    pass_ok = hmac.compare_digest(
        hashed_password,
        Config.API_PASSWORD
    )
    if not (user_ok and pass_ok):
        abort(401)
    return {'username': username, 'password': password}


def list_slips(
    date: List[str],
    page_id: int,
    per_page: int = None,
    object_code: str = '',
    pos_id: str = ''
) -> List[Dict[str, str]]:
    """
    Return all slips for request, filtering with date, object_code and pos_id.

    Parameters
    ----------
    date
        List of dates (1 or 2) to filter with.
    page_id
        Page number.
    per_page
        Number of items on one page.
    object_code
        SAP object code to filter with, optional.
    pos_id
        POS-terminal ID to filter with, optional.

    Returns
    -------
    List[Dict[str, str]]
        Returns JSONified list of dicts, representing found slips.

    """
    args = locals()
    if len(date) == 1:
        start_date = end_date = date[0]
    else:
        start_date = min(date)
        end_date = max(date)
    form = {
        'object_code': object_code,
        'pos_id': pos_id,
        'start_date': start_date,
        'end_date': end_date
    }
    pagination = get_from_db_paginate(form, page_id, per_page)
    slips = get_data(pagination, page_id, per_page, error_handler=page_error_handler)
    data = [slip.to_json() for slip in slips]
    meta = get_meta(pagination, args, data)
    result = {'data': data, 'meta': meta}
    return jsonify(result)


def add_slips() -> Tuple[str, int]:
    """
    Adds slips from JSON to DB, if JSON contents is valid.

    Returns
    -------
    Tuple[str, int]
        Message and HTTP return code.

    """
    slips: List[Dict[str, str]] = request.json
    slips_added_count = insert_slips(slips)
    if slips_added_count == 0:
        abort(409, 'All slips provided are already in db.')
    else:
        return f'Added {slips_added_count} slips out of {len(slips)}', 201


def get_one_slip(date: str, ref_num: str) -> Dict[str, str]:
    """
    Returns one specific slip from DB with Slip.ref_num == ref_num and
    Slip.date == date.

    Parameters
    ----------
    date
        Date as a string in format '%Y-%m-%d'.
    ref_num
        Numeric string, unique for every operation.

    Returns
    -------
    Dict[str, str]
        Returns JSONified dicts, representing found slip.

    """
    slip = rrn_exists(date, ref_num)
    if not slip:
        abort(404, f'No operation found with RRN {ref_num} and {date}.')
    result = slip.to_json()
    return jsonify(result)


def update_one_slip(
    date: str,
    ref_num: str
) -> Tuple[str, int]:
    """
    Updates particular slip in DB, defined by date and ref_num.

    Parameters
    ----------
    date
        Date as a string in format '%Y-%m-%d'.
    ref_num
        Numeric string, unique for every operation.

    Returns
    -------
    Tuple[str, int]
        Message and HTTP return code.

    """
    new_slip = Slip(**format_dates(request.json)).to_dict()
    old_slip = rrn_exists(date, ref_num)
    new_link = new_slip['file_link']
    # Old_slip can not exist by definition of UPDATE method.
    old_link = getattr(old_slip, 'file_link', None)

    if old_link != new_link and Slip.query.get(new_link):
        abort(409, f'Record with unique file_link {new_link} already exists.')

    Slip.query.filter(Slip.date == date, Slip.ref_num == ref_num).\
        update(new_slip, synchronize_session=False)
    return 'Successfully updated', 201


def delete_one_slip(
    date: str,
    ref_num: str
) -> Tuple[str, int]:
    """
    Deletes slip, defined by date and ref_num.

    Parameters
    ----------
    date
        Date as a string in format '%Y-%m-%d'.
    ref_num
        Numeric string, unique for every operation.

    Returns
    -------
    Tuple[str, int]
        Message and HTTP return code.

    """
    slip = rrn_exists(date, ref_num)
    if not slip:
        abort(404, f'No operation found with RRN {ref_num} and {date}.')
    db_slip.session.delete(slip)
    db_slip.session.commit()
    return 'Deleted successfully', 204
