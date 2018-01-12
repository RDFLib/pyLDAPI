from flask import  render_template, request
from functools import wraps
import urllib.parse as uriparse
import json

from _ldapi.__init__ import LDAPI, LdapiParameterError
from .functions import render_alternates_view, client_error_Response
import _config as conf
from .default_register import DefaultRegisterRenderer
from .index_register import DefaultIndexRegister


register_tree = []


def _regist_(rule, descriptions, options):
    ''' 
        store decorated rule and render class information to home page naviation
    '''
    is_instance = options.get('is_instance')
    if not is_instance:
        site = {}
        site['uri'] = rule
        site['description'] = descriptions
        register_tree.append(site)

def register(rule, render=None, **options):
    '''
        decorator for registers
        param rule is the route path, param render is a class implemented rederer.py's render() method.
        When render not provided, default DefaultIndexRegister will be used  if rule == /,  
        and DefaultRegisterRenderer will be used if rule != /
        If an instance used this decorator, the instance render class must provided, or else, an error will be raised. 
    '''
    if rule == '/' and render == None:
        # default render will be allocated if render is not provided and rule is / 
        render = DefaultIndexRegister
    if rule != '/' and render == None:
        if bool(param) and param.get('is_instance')==True:
            # Instance view, render class must be supported
            raise Exception('Instance render class should be provided')
        else:
            # None home path with default register render
            render = DeafultRegisterRenderer
    views_formats = json.loads(render.view())
    _regist_(rule, views_formats.get('description'), options)

    def decorator(func):
        '''
            wrap decorated function to make it perform like a view
        '''
        @wraps(func)
        def decorated_function(**param):
            '''
                ** param will absorb any parameters given to the decoracted func
            '''
            try:
                view, mime_format = LDAPI.get_valid_view_and_format(
                    request.args.get('_view'),
                    request.args.get('_format'),
                    views_formats
                )
               
                # if alternates model, return this info from file
                class_uri = conf.URI_SITE_CLASS
                # render alternates view 
                if view == 'alternates':
                    return render_alternates_view(
                        class_uri,
                        uriparse.quote_plus(class_uri),
                        None,
                        None,
                        views_formats,
                        mime_format
                    )
                else:
                    # Since all render class extends from renderer.py, it requires two param to render views: view and format
                    # register decorator pass these two parameters and  parameters came from decoracted func back
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
    return decorator

instance = register

def instance(rule, render=None, is_instance=True, **options):
    '''
        instance decoractor wraps register, and provides it with a new param: is_instance with default value True
    '''
    return register(rule, render, is_instance=True) 