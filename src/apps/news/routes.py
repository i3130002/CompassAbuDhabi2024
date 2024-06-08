# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from flask import render_template, request
from flask_login import login_required
from jinja2 import TemplateNotFound

from apps.config import API_GENERATOR

@blueprint.route('/news')
def news():
    return render_template('news/news.html')
