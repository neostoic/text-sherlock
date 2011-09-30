# -*- coding: utf-8 -*-
import os
from server import app
from flask import render_template, request, url_for, session
from core.sherlock import indexer, searcher, transformer
from core import settings as core_settings
from core.utils import debug


@app.route('/static/*')
def static_files():
    """Handles static files requests
    """
    endswith = request.path.endswith
    if endswith('main.css'):
        return url_for('static', filename='css/main.css')
    return ''
    

@app.route('/')
def index():
    """Handles index requests
    """
    response = {
        "title" : u"Welcome"
    }
    return render_template('index.html', **response)
    

@app.route('/search', methods=['POST', 'GET'])
def search():
    """Handles search requests
    """
    # get form vars
    if request.method == 'POST':
        form = request.form
    else:
        form = request.args
    search_text = form.get('text')
    idxr = indexer.get_indexer()
    # find something in the file
    results = idxr.get_index().search(search_text)
    # transform the results
    trns = transformer.Transformer()
    items = trns.transform_results(results, type=None)
    # build response
    response = {
        'title' : 'Search',
        'text' : search_text,
        'results' : items
    }
    return render_template('index.html', **response)