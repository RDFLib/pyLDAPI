from flask import Blueprint, request
from pyldp.register_master import RegisterMasterRenderer
from pyldp.register import RegisterRenderer
from pyldp import decorator
from model.site_instance_renderer import SiteRenderer

routes = Blueprint('controller', __name__)


@routes.route('/')
@decorator.register('/')
def index(**args):
    view = args.get('view')
    format = args.get('format')
    return RegisterMasterRenderer('page_index.html', decorator.register_tree).render(view, format)


@routes.route('/site/')
@decorator.register('/site/', render=RegisterRenderer, contained_item_class='http://pid.geoscience.gov.au/def/ont/pdm#Site')
def sites(**args):
    """
    The Register of Sites
    """
    view = args.get('view')
    format = args.get('format')
    return RegisterRenderer(request).render(view, format)


@routes.route('/site/<string:site_no>')
@decorator.instance('/site/<string:site_no>', render=SiteRenderer)
def site(**args):
    """
    A single Site
    """
    site_no = args.get('site_no')
    view = args.get('view')
    format = args.get('format')
    return SiteRenderer(site_no).render(view, format)

