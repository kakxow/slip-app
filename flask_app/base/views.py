from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask import Response, session, abort, stream_with_context
from flask_login import login_required
from loguru import logger
from werkzeug.datastructures import MultiDict

from .forms import SlipSearch
from . import functions


views = Blueprint('views', __name__, template_folder='templates')


@views.route('/', methods=['GET'])
@views.route('/index', methods=['GET'])
@login_required
def index():
    """
    Returns index page.
    """
    form = SlipSearch()
    form_data = session.get('form_data', None)
    if form_data:
        form_data = {k: str(v) for k, v in form_data.items()}
        form = SlipSearch(MultiDict(form_data))
        form.validate()
        session.pop('form_data')
    return render_template('slip_page.html', form=form)


@views.route('/output', methods=['GET', 'POST'])
@login_required
def output_fn():
    """
    Returns page with search results table, or redirects to index if nothing found.
    """
    page_id = request.args.get('page', type=int)
    if not page_id or page_id < 1:
        abort(404, f'Specify correct page number.')
    form = SlipSearch()
    search_criteria = form.data

    if form.validate_on_submit():
        search_form = {k: str(v) for k, v in search_criteria.items()}
        search_form.pop('csrf_token', None)
    elif request.method == 'POST':
        # Validation failed.
        form_dict = {k: v for k, v in search_criteria.items() if v != ''}
        session['form_data'] = form_dict
        return redirect(url_for('.index'))
    else:
        # Request == GET
        search_form = functions.get_form_for_current_user()

    logger.debug(f'Searching with:\n{search_form}')
    pagination = functions.get_from_db_paginate(search_form, page_id)
    data = functions.get_data(pagination, page_id, error_handler=functions.page_error_handler)

    if not data:
        # No result.
        form_dict = {k: v for k, v in search_form.items() if v != ''}
        flash(f'Nothing found for {form_dict}')
        session['form_data'] = form_dict
        return redirect(url_for('.index'))

    functions.save_form_to_current_user(search_form)
    result = functions.prettify_result(data)
    return render_template(
        'output_page.html',
        ls=result,
        pagination=pagination
    )


@views.route('/download', methods=['GET'])
@login_required
def download_file():
    """
    Streams csv vile for page_id or all pages if page_id is 0.
    """
    page_id = request.args.get('page', 0, int)
    if page_id < 0:
        abort(404, f'Specify correct page number.')
    file_name = f'query_result_{("page_" + str(page_id)) if page_id else "all"}.csv'

    return Response(
        stream_with_context(functions.stream_csv(page_id)),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={file_name}'}
    )
