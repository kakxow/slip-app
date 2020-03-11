from typing import Dict, List, Union
from urllib.parse import urlencode

from flask_sqlalchemy import Pagination

from datetime import datetime
import datetime as dt

from flask_app import db_slip
from db import try_query, Slip


def get_meta(
    pagination: Pagination,
    args: Dict[str, Union[str, int, List[str], None]],
    data: List[Dict[str, str]]
) -> Dict[str, Union[str, int, None]]:
    """
    Forms meta data for response.

    Parameters
    ----------
    pagination
        flask_sqlalchemy.Pagination object from original query.
    args
        Arguments from request.
    data
        Resulting list of dicts for response.

    Returns
    -------
    Dict[str, Union[str, int, None]]
        Resulting meta data, as described in schema.

    """
    pages = pagination.pages
    page = pagination.page
    total = pagination.total
    form = {k: v for k, v in args.items() if v}
    base_url = '/api/slips?'

    form_next = {**form, 'page': page + 1}
    form_prev = {**form, 'page': page - 1}
    next_url = base_url + urlencode(form_next)
    prev_url = base_url + urlencode(form_prev)
    next_ = next_url if (page != pages and total) else None
    prev_ = prev_url if page != 1 else None

    meta = {
        'page': page,
        'pages': pages,
        'items': len(data),
        'total': pagination.total,
        'next': next_,
        'prev': prev_,
    }
    return meta


def rrn_exists(date: str, ref_num: str) -> Union[Slip, bool]:
    """
    Finds a row in DB filtered by date and ref_num.

    Parameters
    ----------
    date
        Date as a string in format '%Y-%m-%d'.
    ref_num
        Numeric string, unique for every operation.

    Returns
    -------
    Union[Slip, bool]
        Returns a Slip if found one, False otherwise.

    """
    q = Slip.query.filter(Slip.date == date, Slip.ref_num == ref_num).scalar
    return try_query(q)


def format_dates(
    slip: Dict[str, str]
) -> Dict[str, Union[str, dt.date, dt.time]]:
    """
    Converts 'date', 'time' and 'updated' attributes of slip to
    datetime.date/time objects.

    Parameters
    ----------
    slip
        Dict, containing Slip attributes.

    Returns
    -------
    Dict[str, Union[str, date, time]]
        Dict, containing Slip attributes with 'date', 'time' and 'updated' attributes
        turned to datetime.date/time objects.

    """
    return {
        **slip,
        'date': datetime.strptime(slip['date'], '%Y-%m-%d').date(),
        'time': datetime.strptime(slip['time'], '%H:%M').time(),
        'updated': datetime.strptime(slip['updated'], '%Y-%m-%d').date(),
    }


def insert_slips(dicts: List[Dict[str, str]]) -> int:
    """
    Validates and inserts valid slips from dicts to the DB.

    Parameters
    ----------
    slips
        List of dicts, representing Slip attributes.

    Returns
    -------
    int
        Returns ammount of inserted slips from the list.

    """
    counter_add = 0
    unique_dicts = {d['file_link']: d for d in dicts}.values()
    filtered_dicts = [d for d in unique_dicts
                      if not Slip.query.get(d['file_link'])]

    for dct in filtered_dicts:
        slip = Slip(**format_dates(dct))
        db_slip.session.add(slip)
        counter_add += 1
    db_slip.session.commit()

    return counter_add
