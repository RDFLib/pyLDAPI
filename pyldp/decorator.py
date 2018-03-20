from flask import request
from functools import wraps
import urllib.parse as uriparse

from _ldapi.__init__ import LDAPI, LdapiParameterError
from .functions import render_alternates_view, client_error_response
from .register_master import RegisterMasterRenderer
from .register import RegisterRenderer


register_tree = []


def _regist_(rule, description, options):
    """
        store decorated rule and render class information to home page navigation
    """
    # add all registers to register_tree
    if not options.get('is_instance'):
        site = {
            'uri': rule,
            'description': description
        }
        register_tree.append(site)


def register(rule, render=None, contained_item_class='http://purl.org/linked-data/registry#Register', **options):
    """
        decorator for registers
        param rule is the route path, param render is a class implemented renderer.py's render() method.
        When render not provided, default RegisterMasterRenderer will be used  if rule == /,
        and RegisterRenderer will be used if rule != /
        If an instance used this decorator, the instance render class must provided, or else, an error will be raised. 
    """
    if render is None:
        if rule == '/':
            render = RegisterMasterRenderer
        if rule != '/':
            if bool(options) and options.get('is_instance'):
                # Instance view, render class must be supported
                raise Exception('Instance render class should be provided')
            else:
                # None home path with default register render
                render = RegisterRenderer

    views_formats = render.views_formats()
    _regist_(rule, views_formats.get('description'), options)

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
                    return render_alternates_view(
                        contained_item_class,
                        uriparse.quote_plus(contained_item_class),
                        None,
                        None,
                        views_formats,
                        mime_format
                    )
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


instance = register


def instance(rule, render=None, is_instance=True, **options):
    """
        instance decorator wraps register, and provides it with a new param: is_instance with default value True
    """
    return register(rule, render, is_instance=is_instance)