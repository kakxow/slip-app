import argparse
from datetime import datetime, timedelta
import sys
from typing import Tuple

from dotenv import load_dotenv
from loguru import logger

from config import slip_dir
from slip.run_single_table import main_single_table


def get_months() -> Tuple[int, int]:
    """
    Returns current and previous months' numbers.

    Returns
    -------
    Tuple[int, int]
        Tuple of current month number and previous month number.

    """
    now = datetime.now()
    curr_month = now.month
    prev_month = (now - timedelta(now.day + 1)).month
    return (curr_month, prev_month)


def cli():
    arg_parser = argparse.ArgumentParser(description='Run pdf parser')
    arg_parser.add_argument('-t', '--threads', type=int, default=8, nargs='?',
                            help='Specify number of threads to run.')
    arg_parser.add_argument('-d', '--directory', default=slip_dir, nargs='?',
                            help='Specify directory to run here.')
    arg_parser.add_argument('-y', '--years', default=('2020',), nargs='*',
                            help='Specify which years to cover.')
    arg_parser.add_argument('-m', '--months', default=get_months(), nargs='*',
                            type=int, help='Specify which months to cover.')

    args = arg_parser.parse_args()
    logger.info('Start!')
    months = tuple(f'{i:02}' for i in args.months)
    main_single_table(args.directory, args.years, args.threads, months, True)
    logger.info('Finish!')


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
    cli()
