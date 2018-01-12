from flask import Blueprint, render_template, request, Response
import urllib.parse as uriparse
import requests
import json
from _ldapi.__init__ import LDAPI, LdapiParameterError
from model.index_register import IndexRegister
from model.default_register import RegisterRenderer
from model.site_instance_render import Site
import _config as conf

from pyldp import decorator


routes = Blueprint('controller', __name__)
# print(path_routes.deferred_functions)

@routes.route('/')
@decorator.register('/')
def index(**args):
    view = args.get('view')
    format = args.get('format')
    return IndexRegister('page_index.html', decorator.register_tree).render(view, format)

@routes.route('/register')
def register():
    # Test only
    return Response('["http://pid.geoscience.gov.au/def/ont/ga/pdm#Site"]', status=200, mimetype='application/json')

@routes.route('/site/')
@decorator.register('/site/', render=RegisterRenderer)
def sites(**args):
    """
    The Register of Site
    :return: HTTP Response
    """
    view = args.get('view')
    format = args.get('format')
    return RegisterRenderer(request).render(view, format)

@routes.route('/site/<string:site_no>')
@decorator.instance('/site/<string:site_no>', render=Site)
def site(**args):
    """
    A single Site
    :return: HTTP Response
    """
    site_no = args.get('site_no')
    view = args.get('view')
    format = args.get('format')
    return Site(site_no).render(view, format)

