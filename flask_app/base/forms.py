from flask_wtf import FlaskForm
from wtforms import StringField, DateField
from wtforms.validators import Length, regexp, Optional, ValidationError
from wtforms.validators import DataRequired
from loguru import logger


summ_pattern = r'([\d]+[.,-][\d]{1,2})|([\d]+)'
date_pattern = r'\d{4}-\d{2}-\d{2}'
object_pattern = r'([A-Za-z][\d]{3})|([A-Za-z]{2}[\d]{2})'


class SlipSearch(FlaskForm):
    """
    Form for search criterias on index page.
    """
    merchant_name = StringField(
        'Merchant name',
        [
            Length(min=1, max=100),
            regexp(r'[\w\s]+'),
            Optional(),
        ]
    )
    object_code = StringField(
        'Object code',
        [
            Length(min=4, max=8),
            regexp(object_pattern),
            Optional(),
        ]
    )
    pos_id = StringField(
        'POS ID',
        [
            Length(min=4, max=8),
            regexp(r'[\d]{4,8}'),
            Optional(),
        ]
    )
    start_date = DateField('Date from', [DataRequired()])
    end_date = DateField('Date to', [DataRequired()])
    card_number = StringField(
        'Card number',
        [
            Length(min=4, max=4),
            regexp(r'[\d]{4}'),
            Optional()
        ]
    )
    start_summ = StringField(
        'Summ from',
        [
            Optional(),
            Length(min=1, max=12),
            regexp(summ_pattern)
        ]
    )
    end_summ = StringField(
        'Summ to',
        [
            Optional(),
            Length(min=1, max=12),
            regexp(summ_pattern)
        ]
    )
    ref_num = StringField(
        'RRN',
        [
            Length(min=12, max=12),
            regexp(r'[\d]{12}'),
            Optional()
        ]
    )
    auth_code = StringField(
        'Authorization code',
        [
            Length(min=6, max=6),
            regexp(r'[\w]{6}'),
            Optional()
        ]
    )

    def validate_date(form, field):
        if not ('2018-01-01' < str(form.start_date.data) < '2021-12-31' and
                '2018-01-01' < str(form.end_date.data) < '2021-12-31'):
            msg = f'{form.start_date.data} and {form.end_date.data} should be ' \
                  f'between 2018 and 2021'
            logger.warning(msg)
            raise ValidationError(msg)
        if form.start_date.data > form.end_date.data:
            msg = f'{form.start_date.data} should be < than {form.end_date.data}'
            logger.warning(msg)
            raise ValidationError(msg)

    def validate_summ(form, field):
        if form.start_summ.data and form.end_summ.data and \
           form.start_summ.data > form.end_summ.data:
            msg = f'Start summ {form.start_summ.data }must be lower than ' \
                  f'end summ {form.end_summ.data}'
            logger.warning(msg)
            raise ValidationError(msg)
