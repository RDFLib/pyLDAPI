from flask import Blueprint, render_template, request, Response
import urllib.parse as uriparse
import requests
import json
from _ldapi.__init__ import LDAPI, LdapiParameterError
from .functions import render_alternates_view, client_error_Response
from controller import classes_functions
import _config as conf

# class register():
def register(func):
    def decorator():
        print('register decorator')
            # lists the views and formats available for a Sample
        views_formats = classes_functions.get_classes_views_formats().get('http://purl.org/linked-data/registry#Register')
        # print(views_formats)
        try:
            view, mime_format = LDAPI.get_valid_view_and_format(
                request.args.get('_view'),
                request.args.get('_format'),
                views_formats
            )

            # if alternates model, return this info from file
            class_uri = conf.URI_SITE_CLASS

            if view == 'alternates':
                print('alternates view')
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
                return func
        except LdapiParameterError as e:
            return client_error_Response(e)
    return decorator
def test():
    pass