from abc import ABCMeta
from flask import render_template, Response
import json
from .renderer import Renderer


class RegisterMasterRenderer(Renderer):
    __metaclass__ = ABCMeta

    def __init__(self, template, register_tree):
        """Everything to be rendered must at least have a graph (its data) and a URI (its ID)"""
        self.register_tree = register_tree
        self.template = template

    def render(self, view, mimetype):
        """This method must be implemented by all classes that inherit from Renderer

        :param view: a model view available for this class instance
        :param mimetype: a mimetype string, e.g. text/html
        :return: a Flask Response object
        """
        if view == 'reg':
            if mimetype == 'application/json':
                return Response(json.dumps(self.register_tree), status=200, mimetype='application/json')
        else:  # any views other than reg and alternates (which is handled by LDAPI)
            return render_template(self.template, register_tree=self.register_tree)

    @staticmethod
    def views_formats():
        """
        return this register's supported views and mimetypes for each view
        """
        return {
            'default': 'reg',
            'alternates': {
                'mimetypes': [
                    'text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json', 'application/json'],
                'default_mimetype': 'text/html',
                'namespace': 'http://www.w3.org/ns/ldp#Alternates',
                'description': 'The view listing all other views of this class of object'
            },
            'reg': {
                'mimetypes': ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json'],
                'default_mimetype': 'text/html',
                'namespace': 'http://purl.org/linked-data/registry#',
                'description':
                    'The Registry Ontology. Core ontology for linked data registry services. Based on ISO19135 but '
                    'heavily modified to suit Linked Data representations and applications',
                'containedItemClass': ['http://purl.org/linked-data/registry#Register']
            },
            'description':
                'This Master Register contains all the registers within this Linked Data API. This register will be '
                'used when another is not specified in @decorator.register() decorator in routes.py. This default can '
                'be replaced by simply adding a customized register in @decorator.register() the decorator.'
        }
