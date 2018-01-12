from flask import Blueprint, render_template, request
from _ldapi.__init__ import LDAPI, LdapiParameterError
import _config as conf
from pyldp.index_register import DefaultIndexRegister
from pyldp.default_register import DefaultRegisterRenderer
from pyldp import decorator
from model.site_instance_render import Site

routes = Blueprint('controller', __name__)

@routes.route('/')
@decorator.register('/')
def index(**args):
    view = args.get('view')
    format = args.get('format')
    return DefaultIndexRegister('page_index.html', decorator.register_tree).render(view, format)

@routes.route('/site/')
@decorator.register('/site/', render=DefaultRegisterRenderer)
def sites(**args):
    """
    The Register of Site
    """
    view = args.get('view')
    format = args.get('format')
    return DefaultRegisterRenderer(request).render(view, format)

@routes.route('/site/<string:site_no>')
@decorator.instance('/site/<string:site_no>', render=Site)
def site(**args):
    """
    A single Site
    """
    site_no = args.get('site_no')
    view = args.get('view')
    format = args.get('format')
    return Site(site_no).render(view, format)

