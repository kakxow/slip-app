import sys
from datetime import datetime, timedelta

from loguru import logger
from dotenv import load_dotenv

from slip.run_single_table import main_single_table
from config import slip_dir


if __name__ == '__main__':
    load_dotenv()
    logger.remove()
    logger.add(
        'logs/log_{time}.log',
        rotation='1 day',
        retention='15 days',
        level='DEBUG'
    )
    logger.add(
        sys.stdout,
        level='INFO'
    )
    now = datetime.now()
    curr_month = f'{now.month:02}'
    prev_month = f'{(now - timedelta(now.day + 1)).month:02}'
    months = (curr_month, prev_month)

    try:
        threads = int(sys.argv[1])
    except (ValueError, IndexError):
        print('Restart with valid number of threads as 1st argument.')
    else:
        logger.info('Start!')
        main_single_table(slip_dir, ('2020',), threads, months, True)
        logger.info('Finish!')
