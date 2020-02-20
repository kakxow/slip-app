from datetime import datetime, timedelta
from time import sleep
import re
import sys
import os

from sqlalchemy.exc import OperationalError

os.environ['SQLALCHEMY_DATABASE_URI'] = \
        r'sqlite:///C:\Max\slip_db\slipDB.db'

import slip.models as models
from slip.db_stuff import SessionCM


def main(pos_id: str) -> str:
    """select object_code from slips where pos_id = {pos_id} limit 1;"""
    pos_id_ = '{pos_id:08}'
    today_month = datetime.now().strftime('%Y-%m')
    today_model = models.mapping[today_month]
    with SessionCM as sess:
        q = sess.query(today_model.object_code).\
            filter(today_model.pos_id == pos_id_).first
        result = try_query(q)
        if not result:
            last_month = (datetime.now() - timedelta(days=15)).strftime('%Y-%m')
            older_model = models.mapping[last_month]
            q = sess.query(older_model.object_code).\
                filter(today_model.pos_id == pos_id_).first
            result = try_query(q)
    if result:
        result = result[0]
    return f'{pos_id} - {result or "уточняю"}'


def try_query(query: callable, logger: callable = None, tries: int = 60):
    """
    """
    err_counter = 0
    while True:
        try:
            result = query()
        except OperationalError as e:
            if logger is not None:
                logger(e)
            err_counter += 1
            if err_counter > tries:
                raise
            sleep(1)
        else:
            break
    return result


if __name__ == '__main__':
    subj = ' '.join(sys.argv[1:])
    # subj = '21813186 21814860 1234 '
    print(*list(map(main, re.findall(r'\d+', subj))), sep='\n')
