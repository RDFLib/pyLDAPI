from flask import request
from functools import wraps

from _ldapi.__init__ import LDAPI, LdapiParameterError
from .functions import render_alternates_view, client_error_response
from .renderer_register_master import RegisterMasterRenderer
from .renderer_register import RegisterRenderer


register_tree = []


def _add_to_register_tree(rule, description, contained_item_class):
    """
        store decorated rule and render class information to home page navigation
    """
    register = {
        'uri': rule,
        'description': description,
        'contained_item_class': contained_item_class
    }
    register_tree.append(register)


def register(rule, renderer, contained_item_class='http://purl.org/linked-data/registry#Register', description=None):
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
        renderer = RegisterRenderer
        views_formats = renderer.views_formats(description)

    _add_to_register_tree(rule, views_formats.get('description'), contained_item_class)

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
                view, mime_format = LDAPI.get_valid_view_and_format(request, views_formats)
               
                # if alternates model, return this info from file
                # render alternates view 
                if view == 'alternates':
                    return render_alternates_view(views_formats, mime_format, contained_item_class, None)
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
                return client_error_response(e)
        
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
                view, mime_format = LDAPI.get_valid_view_and_format(request, views_formats)

                # if alternates model, return this info from file
                # render alternates view
                if view == 'alternates':
                    return render_alternates_view(views_formats, mime_format, instance_class, param['instance_id'])
                else:
                    # Since all render class instances extend renderer.py, they requires two param to render views:
                    # view and format. The register decorator passes these two parameters from decoracted func back
                    args = {}
                    if bool(param):
                        for p in param.keys():
                            args[p] = param[p]
                    args['view'] = view
                    args['format'] = mime_format
                    return func(**args)
            except LdapiParameterError as e:
                return client_error_response(e)

        return decorated_function

    return decorator
