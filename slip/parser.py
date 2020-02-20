import subprocess
import io
from typing import Dict, Optional
from datetime import datetime
import re

from config import POPPLER_PATH


r"""
Current problems:

headless:
    only 6:
    S934    \\Msk-vm-slip\SLIP\S934\2019\01\S93491E001820190114151311.pdf
    only 2:
    UE75    \\Msk-vm-slip\SLIP\UE75\2019\11\UE759BW009520191129180556.pdf
    all transactions (closed):
    N365    \\Msk-vm-slip\SLIP\N365\2019\01\N365914002020190104134555.pdf
    unknown
    S527    \\Msk-vm-slip\SLIP\S527\2019\01\S527912002920190102133908.pdf
    S458    \\Msk-vm-slip\SLIP\S458\2019\01\S458916005220190106153507.pdf

semi-headless:
    all transactions:
    X092    \\Msk-vm-slip\SLIP\X092\2019\01\X092918011420190108165602.pdf

no summ:
    old:
        only february:
        W356    \\Msk-vm-slip\SLIP\W356\2019\02\W35692E016420190214205028.pdf
        only may:
        KG14    \\Msk-vm-slip\SLIP\KG14\2019\05\KG1495E010320190514170619.pdf
    all transactions:
    N479    \\Msk-vm-slip\SLIP\N479\2019\01\N479913001220190103115054.pdf


RARE:
digits in fin_service (PRO100):
    only one
    GE51    \\Msk-vm-slip\SLIP\GE51\2019\12\GE519C2007120191202150104.pdf

double card-info:
    only one
    L067    \\Msk-vm-slip\SLIP\L067\2019\11\L0679BM025620191121122430.pdf
    YO87    \\Msk-vm-slip\SLIP\YO87\2019\05\YO8795B003920190511171406.pdf

encoding error:
    only one
    GM94    \\Msk-vm-slip\SLIP\GM94\2019\11\GM949BU004720191127115341.pdf
"""


head_p_new = \
    r'^\n*(?P<merchant_name>.*)\n+' \
    r'(?P<city>.*?)(,|\n)' \
    r'(?P<address>(?s:.+?))' \
    r'\n?(т. )?(?P<phone_num>[\d(][-\d)( ]{6,})?\n+' \
    r'(?P<date>\d{1,2}[-.,\\/ ]\d{2}[-.,\\/ ]\d{2,4})\s*' \
    r'(?P<time>\d{1,2}[-:.,\\/ ]\d{2})'

op1_p = \
    r'ЧЕК\s(?P<operation_num>\d+)\n(?P<operation_type>.*)'
op2_p = \
    r'ЧЕК\n(?P<operation_type>.*)(\n.*)*' \
    r'(?<=Номер операции:)\n(?P<operation_num>\d+)'
pos_id_p = \
    r'(?<=Терминал:)\s' \
    r'(?P<pos_id>\d+)\s'
merchant_num_p = \
    r'((?<=Мерчант:)|(?<=Пункт обслуживания:))(\n|\s)(?P<merchant_num>\d+)\n' \
    r'(?P<fin_service>[^\n\d]+)\s(?P<something>A\d+)?'

auth_foot_p = \
    r'(?<=Сумма \(Руб\):)\n(?P<summ>\d+.\d+)(?:\nКомиссия за операцию.*)*'\
    r'(\n(?P<result>.*)' \
    r'(?:\nКод авторизации:)\n' \
    r'(?P<auth_code>.*))?'

ref_num_p = \
    r'(?:Номер ссылки:)\n{1,2}' \
    r'(?P<ref_num>\d+)\n' \
    r'(?P<payment_type>.*)\n'

card1_p = \
    r'(?<=Карта:).*\n?[*]+(?P<card_number>\d{4})\n.*' \
    r'(?<=Клиент:)\n*(?P<card_holder>[\w\s]+/([\S]+)?)?'
card2_p = \
    r'(?<=Карта:...\nКлиент:)(\n.*){2}' \
    r'([*]+)?(?P<card_number>\d{4})\n(?P<card_holder>[\w\s]+/([\S]+)?)?'


def parse_slip(
    file_path: str,
    verbose: bool = False,
) -> Dict[str, str]:
    """
    Main parser.  Takes file_path, opens and converts pdf to txt and executes
    regexp.  Returns a dictionary of group_name: result to be passed to model
    class constructor.  Poppler utils bin musthave in PATH!

    Parameters
    ----------
    file_path
        Path to file of interest.
    verbose
        bool for testing - if True function prints file's text.

    Returns
    -------
    Dict[str, str]
        Returns dictionary of group/model attribute name: value.

    """

    res = {'file_link': file_path}

    # Get text from .pdf file using pdftotext from Poppler utils,
    txt = convert_pdf(file_path)

    if verbose:
        print(txt)
    # Check for errors in txt and add error.
    error = check_text_for_errors(txt)
    if error:
        res['error'] = error
        return res

    res.update({**regexp_result(txt)})
    # Check for errors in dicts.
    if not res.get('pos_id'):
        res['error'] = 'Regexp error.'
        return res

    res.update({
        'date': datetime.strptime(fixed_date(res), '%d.%m.%y').date(),
        'time': datetime.strptime(res['time'], '%H:%M').time(),
        'updated': datetime.now().date(),
        'object_code': file_path[32:36],
    })
    return res


def regexp_result(txt: str) -> Dict[str, str]:
    """
    Execute regexp patterns on given text.

    Parameters
    ----------
    txt
        Text to parse with regexp.

    Returns
    -------
    Dict[str, str]
        Returns dictionary of group_name: result, all as :obj:`str`.

    """

    # Executing RE using global patterns.
    head_m = re.search(head_p_new, txt, re.I)
    operation_m = re.search(op1_p, txt, re.I) or re.search(op2_p, txt, re.I)
    pos_id_m = re.search(pos_id_p, txt, re.I)
    merchant_num_m = re.search(merchant_num_p, txt, re.I)
    auth_foot_m = re.search(auth_foot_p, txt, re.I)
    card_m = re.search(card1_p, txt, re.I) or re.search(card2_p, txt, re.I)
    ref_num_m = re.search(ref_num_p, txt, re.I)

    try:
        # Merge all match.groupdicts to one.
        res = {
            **head_m.groupdict(),
            **operation_m.groupdict(),
            **pos_id_m.groupdict(),
            **merchant_num_m.groupdict(),
            **auth_foot_m.groupdict(),
            **card_m.groupdict(),
            **(ref_num_m.groupdict() if ref_num_m
               else {'ref_num': None, 'payment_type': None}),
        }
    except AttributeError:
        # If any match fails, return empty dict.
        res = {}

    return res


def convert_pdf(file_path: str) -> str:
    """
    Opens a file at file_path (should be .pdf) and returns it's text.
    Poppler utils bin musthave in PATH!

    Parameters
    ----------
    file_path
        Path to file of interest.

    Returns
    -------
    str
        Text contents from file.

    """
    cmd = f'{POPPLER_PATH} {file_path} -'
    pdf_process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    with io.TextIOWrapper(pdf_process.stdout, encoding="utf-8") as f:
        txt = f.read()
    pdf_process.terminate()
    return txt


def check_text_for_errors(txt: str) -> Optional[str]:
    """
    Checks txt for key phrases and returns dict with appropriate status.

    Parameters
    ----------
    txt
        Text to check.

    Returns
    -------
    Optional[str]
        Returns error if anything is wrong with text, or None otherwise.

    """
    h = {
        'I/O Error': 'I/O Error',
        'Сообщение системы мониторинга:': 'Skip',
        'Карта не читается': 'Card error',
        'карта не обслуживается': 'Card out of service',
        'Введите пароль на телефоне': 'Password on phone',
        'чип': 'Use chip',
        'отменена клиентом': 'Cancelled by client',
    }

    if not txt or len(txt) < 10:
        return 'Empty file or convertion error'
    else:
        for key_phrase, error_text in h.items():
            if key_phrase in txt:
                return error_text


def fixed_date(dct: Dict[str, str]) -> str:
    """
    Fix date: take day and month from slip and add year from file_link.

    Parameters
    ----------
    dct
        Dictionary with regexp results.

    Returns
    -------
    str
        date in format dd.mm.yy

    """
    day_month = dct.get('date', [])[:-2]
    year = dct['file_link'][26:28]
    return day_month + year
