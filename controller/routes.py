from flask import Blueprint, render_template, request, Response
import urllib.parse as uriparse
import requests
import json
from _ldapi.__init__ import LDAPI, LdapiParameterError
from model.site_register_render import RegisterRenderer
from model.site_instance_render import Site
import _config as conf

from decorator import decorator


routes = Blueprint('controller', __name__)


@routes.route('/')
@decorator.register()
def index():
    return render_template('page_index.html')

@routes.route('/register')
def register():
    # Test only
    return Response('["http://pid.geoscience.gov.au/def/ont/ga/pdm#Site"]', status=200, mimetype='application/json')

@routes.route('/site/')
@decorator.register(render=RegisterRenderer)
def sites():
    """
    The Register of Site
    :return: HTTP Response
    """
    pass


@routes.route('/site/<string:site_no>')
@decorator.register(render=Site)
def site(site_no):
    """
    A single Site
    :return: HTTP Response
    """
    pass

