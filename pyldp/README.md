
## decoration ##
* @register -- provide alternates view and register view, because these two views are required by any category and instances, even root path, it should be extended by all of them.
* @instance (extends @register, belongs @category(site) or @sub-category(sub-site))


## Usage ##
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


## How to go crossing the website? ##
1. @register decoration adds alternates and regester views to all routes, 
2. @category, @sub-categories extends @register
3. using URL/_view=alternates&_format=application/json can acquire current register views and alternates view, 
4. at the same time, using register.__subclasses__() to get all categories as a tree and return them as the categories the system support. 
5. In the testing, I can access these categories using alternates view in application/json format, and go cross categories and pick up an instance each of them.
5. since at any category, sub-category and instance, I could easily access any information or data as I wish.
 

	

## What each url returned ##
URL/
	| return categories of this system, such as category1, category2, and category/sub-category etc.
	| site introduction, register view and alternates view info can also been put here
	| by default text/html returned -> display available categories of the system
	| Using _view=alternates to display alternative views and formats  of this URL
	| Using URL/_view=alternates&_format=application/json can read current register information -- Testing can follow this clue to go crossing the website


URL/category1/
		| return all available instances of this category
		| category1 introduction, register view and alternates view info can also been put here
		| by default text/html returned -> display available instances of the category
		| Using _view=alternates to display alternative views and formats  of this category
		| Using URL/category1/_view=alternates&_format=application/json can read current category register information


URL/category1/id/
		| return an instance quired by id
		| by default text/html returned -> display the instance information and alternates view info link
		| Using _view=alternates to display alternative views and formats  of this category
		| Using URL/category1/_view=alternates&_format=application/json can read current instance register information

URL/category/
		| return sub-category belonging to this category, such as sub-category1, sub-category2, ...
		| category category introduction and alternates view info can been put here
		| by default text/html returned 
		| Using _view=alternates to display alternative views and formats  of this URL
		| Using URL/_view=alternates&_format=application/json can read current category register information

ULR/category/sub-category1
		| similar to ULR/category1

ULR/category/sub-category/id
		| similar to ULR/category1/id
		
		