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

register_tree = []

# ldapi.route
# path_routes = routes.routes
# path_routes = Blueprint('pyldp', __name__)

def _regist_(rule, descriptions, options):
    is_instance = options.get('is_instance')
    if not is_instance:
        site = {}
        site['uri'] = rule
        site['description'] = descriptions
        register_tree.append(site)

def register(rule, render=None, **options):
    # print('#register decorator')
    # print(rule)
    if rule == '/' and render == None:
        # Home path with default home render
        render = IndexRegister
    if rule != '/' and render == None:
        if bool(param):
            # Instance view, render class must be supported
            # return Response('Instance render class should be provided', status=404, mimetype='text/plain')
            raise Exception('Instance render class should be provided')

        else:
            # None home path with default register render
            render = RegisterRenderer
    views_formats = json.loads(render.view())
    _regist_(rule, views_formats.get('description'), options)
    # @path_routes.route(rule)
    def decorator(func):
        @wraps(func)
        def decorated_function(**param):
            try:
                view, mime_format = LDAPI.get_valid_view_and_format(
                    request.args.get('_view'),
                    request.args.get('_format'),
                    views_formats
                )
                # print(view, mime_format)
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
                        mime_format
                    )
                else:
                    # print('return default customer function')
                    args = {}
                    if bool(param):
                        for p in param.keys():
                            args[p] = param[p]
                    args['view'] = view
                    args['format'] = mime_format

                    return func(**args)
            except LdapiParameterError as e:
                return client_error_Response(e)
        
        return decorated_function
    # path_routes.add_url_rule(rule,view_func=decorator)
    return decorator

instance = register

def instance(rule, render=None, is_instance=True, **options):
    return register(rule, render, is_instance=True) 