from flask import Blueprint, request
from pyldapi.renderer_register_master import RegisterMasterRenderer
from pyldapi.renderer_register import RegisterRenderer
from pyldapi import decorator
from model.renderer_site import SiteRenderer

routes = Blueprint('controller', __name__)


@routes.route('/')
@decorator.register('/', RegisterMasterRenderer)
def index(**args):
    view = args.get('view')
    format = args.get('format')
    return RegisterMasterRenderer(request, 'page_index.html', decorator.register_tree).render(view, format)


@routes.route('/site/')
@decorator.register(
    '/site/',
    RegisterRenderer,
    contained_item_class='http://pid.geoscience.gov.au/def/ont/pdm#Site',
    description='This register contains instances of Geoscience Australia\'s monitoring sites.'
)
def sites(**args):
    """
    The Register of Sites
    """
    view = args.get('view')
    format = args.get('format')
    description = args.get('description')
    return RegisterRenderer(request, description=description).render(view, format)


@routes.route('/site/<string:instance_id>')
@decorator.instance('/site/<string:instance_id>', SiteRenderer)
def site(**args):
    """
    A single Instance
    """
    instance_id = args.get('instance_id')
    view = args.get('view')
    format = args.get('format')
    return SiteRenderer(instance_id).render(view, format)
