
## Decoration define ##
* ```@decorator.register``` provides a decoration based alternates views and register views decorator by providing customed render class, such as  ```@decorator.register('/', render = DefaultIndexRegister)```, or ```@decorator.register('/')``` when ```DefaultIndexRegister``` will be used by default.
* ```@deciratir.instance extends @register```, besides provides alternates views and register views of an instance, it also renders the instance display views. The render class must be provided. Such as ```@deciratir.instance('/site/10', render=Site)```

## Render class ##
* the render classes used in the register decorator and instance decorator must extends the renderer.py class, which asks sub-class must implementing the static view() method and render() method.
* the static view() method tells decorator what views and formats does it support, default view, and the instance description which will be displayed on home page as registers navigation introduction.
* the render() method accepts view and mimetype parameters to render views as specified by view and mimetype.

## Usage ##
* The usge of the pyldp register model is as simple as adding a @decorator.register decorator between @routes.route and the method.  In future, we are going to combine route decorator with the register decorator, when just one ```@decorator.register``` decorator could process both route and render class register operation. 

* Here is an example of usage:
``` python
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
```

## How to walk through the website? ##
* the entry of website if the home page where an site map was provided in defualt text/html view. 
* specifying ```?_view=reg&_format=application/json``` when call the root URI, a json format data will be responsed, which tells terminal users what registers are supported.
```
http://127.0.0.1:5000/?_view=reg&_format=application/json
```
```javascript
[
	{
		"uri": "/",
		"description": "Index register, return all registers with links navigating to them. This index register will be used\
		when there is not register specified in @decorator.register() in routes.py.  People can replace this default 	\
		register by simply adding customized index register in @decorator.register() decorator."
	},
	{
		"uri": "/site/",
		"description": "Default register, return all instances with links in one page.   When register class doesnot specified \ 
		in @decorator.register() in router.py, this default register will be applied."
	}
]

```
* specifying ```?_view=alternates&_format=application/json``` to a specific register, a jons format data will be responsed, which tells views and formats the register supported.
```
http://127.0.0.1:5000/site/?_view=alternates&_format=application/json
```
```javascript
{
	"default": "reg",
	"alternates": {
		"mimetypes": [
			"text/html",
			"text/turtle",
			"application/rdf+xml",
			"application/rdf+json",
			"application/json"
		],
		"default_mimetype": "text/html",
		"namespace": "http://www.w3.org/ns/ldp#Alternates",
		"description": "The view listing all other views of this class of object"
	},
	"reg": {
		"mimetypes": [
			"text/html",
			"text/turtle",
			"application/rdf+xml",
			"application/rdf+json"
		],
		"default_mimetype": "text/html",
		"namespace": "http://purl.org/linked-data/registry#",
		"description": "The Registry Ontology. Core ontology for linked data registry services. Based on ISO19135 but \
		heavily modified to suit Linked Data representations and applications"
	},
	"description": "Default register, return all instances with links in one page.   \
		When register class doesnot specified in @decorator.register() in router.py, this default register will be applied."
}
```
* specifying ```?_view=alternates&_format=application/json``` to a specific instance, a jons format data will be responsed, which tells views and formats the instance supported.
```
http://127.0.0.1:5000/site/10?_view=alternates&_format=application/json
```

```json
{
	"default": "pdm",
	"alternates": {
		"mimetypes": [
			"text/html",
			"text/turtle",
			"application/rdf+xml",
			"application/rdf+json",
			"application/json"
		],
		"default_mimetype": "text/html",
		"namespace": "http://www.w3.org/ns/ldp#Alternates",
		"description": "The view listing all other views of this class of object"
	},
	"pdm": {
		"mimetypes": [
			"text/html",
			"text/turtle",
			"application/rdf+xml",
			"application/rdf+json"
		],
		"default_mimetype": "text/html",
		"namespace": "http://pid.geoscience.gov.au/def/ont/ga/pdm",
		"description": "Geoscience Australia's Public Data Model ontology"
	},
	"nemsr": {
		"mimetypes": [
			"application/vnd.geo+json"
		],
		"default_mimetype": "application/vnd.geo+json",
		"namespace": "http://www.neii.gov.au/nemsr",
		"description": "The National Environmental Monitoring Sites Register"
		},
	"description": "instance render class for register Site"
}
```
	
		
		
