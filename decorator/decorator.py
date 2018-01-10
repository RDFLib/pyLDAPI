
from flask import Blueprint, render_template, request, Response
from functools import wraps
import urllib.parse as uriparse
import requests
import json


from _ldapi.__init__ import LDAPI, LdapiParameterError
from .functions import render_alternates_view, client_error_Response
import _config as conf

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


def register(render='root'):
    print('#register decorator')
   
    def decorator(func):
        @wraps(func)
        def decorated_function( **param):
            if render != 'root':
                __global_view_format__[request.path] = render.view()
            views_formats = json.loads(__global_view_format__.get(request.path))
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
                    del views_formats['renderer']
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
                    
                    if render != 'root':
                        print(len(param))
                        if bool(param) :
                            return render(param.get('site_no')).render(view, mime_format)
                        return render(request).render(view, mime_format)
                    return func()
            except LdapiParameterError as e:
                return client_error_Response(e)
        return decorated_function
    return decorator

def instance(func):
    def decorator():
        pass