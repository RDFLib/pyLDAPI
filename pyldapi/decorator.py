from flask import request
from functools import wraps
from pyldapi import PYLDAPI, LdapiParameterError
from .renderer_register_master import RegisterMasterRenderer
from .renderer_register import RegisterRenderer


register_tree = []


def register(rule, renderer=RegisterRenderer, contained_item_class='http://purl.org/linked-data/registry#Register', description=None):
    """
        decorator for registers
        param rule is the route path, param render is a class implemented renderer.py's render() method.
        When render not provided, default RegisterMasterRenderer will be used  if rule == /,
        and RegisterRenderer will be used if rule != /
        If an instance used this decorator, the instance render class must provided, or else, an error will be raised. 
    """
    if rule == '/':
        renderer = RegisterMasterRenderer
        views_formats = renderer.views_formats()
    else:
        views_formats = renderer.views_formats(description)

    register_tree.append({
        'uri': rule,
        'description': views_formats.get('description'),
        'contained_item_class': contained_item_class
    })

    def decorator(func):
        """
            wrap decorated function to make it perform like a view
        """
        @wraps(func)
        def decorated_function(**param):
            """
                ** param will absorb any parameters given to the decorator func
            """
            try:
                view, mime_format = PYLDAPI.get_valid_view_and_format(request, views_formats)
               
                # if alternates model, return this info from file
                # render alternates view 
                if view == 'alternates':
                    return PYLDAPI.render_alternates_view(views_formats, mime_format, request.base_url, 'http://purl.org/linked-data/registry#Register')
                else:
                    # Since all render class instances extend renderer.py, they requires two param to render views:
                    # view and format. The register decorator passes these two parameters from decorated func back
                    args = {}
                    if bool(param):
                        for p in param.keys():
                            args[p] = param[p]
                    args['view'] = view
                    args['format'] = mime_format
                    args['description'] = description
                    return func(**args)
            except LdapiParameterError as e:
                return PYLDAPI.client_error_response(e)
        
        return decorated_function
    return decorator


def instance(rule, renderer, **options):
    """
        decorator for instances
        param rule is the route path, param render is a class implemented renderer.py's render() method.
        When render not provided, default RegisterMasterRenderer will be used  if rule == /,
        and RegisterRenderer will be used if rule != /
        If an instance used this decorator, the instance render class must provided, or else, an error will be raised.
    """
    views_formats = renderer.views_formats()
    instance_class = renderer.INSTANCE_CLASS
    instance_uri_base = renderer.INSTANCE_URI_BASE

    def decorator(func):
        """
            wrap decorated function to make it perform like a view
        """

        @wraps(func)
        def decorated_function(**param):
            """
                ** param will absorb any parameters given to the decoracted func
            """
            try:
                view, mime_format = PYLDAPI.get_valid_view_and_format(request, views_formats)

                # if alternates model, return this info from file
                # render alternates view
                if view == 'alternates':
                    return PYLDAPI.render_alternates_view(views_formats, mime_format, request.base_url, instance_class)
                else:
                    # Since all render class instances extend renderer.py, they requires two param to render views:
                    # view and format. The register decorator passes these two parameters from decorated func back
                    args = {}
                    if bool(param):
                        for p in param.keys():
                            args[p] = param[p]
                    args['view'] = view
                    args['format'] = mime_format
                    return func(**args)
            except LdapiParameterError as e:
                return PYLDAPI.client_error_response(e)

        return decorated_function

    return decorator
