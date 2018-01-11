from flask import Blueprint, render_template, request, Response, Flask
from functools import wraps
import urllib.parse as uriparse
import requests
import json


from _ldapi.__init__ import LDAPI, LdapiParameterError
from .functions import render_alternates_view, client_error_Response
import _config as conf
from model.default_register import RegisterRenderer
from model.index_register import IndexRegister
# from controller import routes


__global_view_format__ = {"/": json.dumps({
		"renderer": "RegisterRenderer",
		"default": "reg",
		"alternates": {
			"mimetypes": ["text/html", "text/turtle", "application/rdf+xml", "application/rdf+json", "application/json"],
			"default_mimetype": "text/html",
			"namespace": "http://www.w3.org/ns/ldp#Alternates",
			"description": "The view listing all other views of this class of object"
		},
		"reg": {
			"mimetypes": ["text/html", "text/turtle", "application/rdf+xml", "application/rdf+json"],
			"default_mimetype": "text/html",
			"namespace": "http://purl.org/linked-data/registry#",
			"description": "The Registry Ontology. Core ontology for linked data registry services. Based on ISO19135 but heavily modified to suit Linked Data representations and applications",
			"containedItemClass": ["http://pid.geoscience.gov.au/def/ont/ga/pdm#Site"]
		}
	})}
# ldapi.route
# path_routes = routes.routes
# path_routes = Blueprint('pyldp', __name__)

def register(rule, render=None):
    print('#register decorator')
    print(rule)
   
    # @path_routes.route(rule)
    def decorator(func):
        @wraps(func)
        def decorated_function(**param):
            if rule == '/' and render == None:
                # Home path with default home render
                render = IndexRegister
            if rule != '/' and render == None:
                if bool(param):
                    # Instance view, render class must be supported
                    return Response('Instance render class should be provided', status=404, mimetype='text/plain')
                else:
                    # None home path with default register render
                    render = RegisterRenderer
            
            views_formats = json.loads(render.view())
            try:
                view, mime_format = LDAPI.get_valid_view_and_format(
                    request.args.get('_view'),
                    request.args.get('_format'),
                    views_formats
                )

                # if alternates model, return this info from file
                class_uri = conf.URI_SITE_CLASS

                if view == 'alternates':
                    # print('alternates view')
                    return render_alternates_view(
                        class_uri,
                        uriparse.quote_plus(class_uri),
                        None,
                        None,
                        views_formats,
                        request.args.get('_format')
                    )
                else:
                    print('return default customer function')
                    args = {}
                    if bool(param):
                        for p in param.keys():
                            print(p)
                            args[p] = param[p]
                    args['view'] = view
                    args['format'] = mime_format

                    return func(**args)
            except LdapiParameterError as e:
                return client_error_Response(e)
        
        return decorated_function
    # path_routes.add_url_rule(rule,view_func=decorator)
    return decorator

