from abc import ABCMeta, abstractmethod
from flask import render_template, Response
import json
from .renderer import Renderer

class IndexRegister(Renderer):
    __metaclass__ = ABCMeta


    def __init__(self, template, register_tree):
        """Every thing to be rendered must at least have a graph (its data) and a URI (its ID)"""
        self.register_tree = register_tree
        self.template = template


    def render(self, view, mimetype):
        """This method must be implemented by all classes that inherit from Renderer

        :param view: a model view available for this class instance
        :param mimetype: a mimetype string, e.g. text/html
        :return: a Flask Response object
        """
        if view=='reg' and mimetype=='application/json':
            return Response(json.dumps(self.register_tree), status=200, mimetype='application/json')
        return render_template(self.template, register_tree = self.register_tree)

    @staticmethod
    def view():
        """
        return this register supported views and mimetypes for each view
        """
        return  json.dumps({
            "default": "reg",
            "alternates": {
                "mimetypes": ["text/html", "text/turtle", "application/rdf+xml", "application/rdf+json", "application/json"],
                "default_mimetype": "text/html",
                "namespace": "http://www.w3.org/ns/ldp#Alternates",
                "description": "The view listing all other views of this class of object"
            },
            "reg": {
                "mimetypes": ["text/html", "application/json"],
                "default_mimetype": "text/html",
                "namespace": "http://purl.org/linked-data/registry#",
                "description": "The Registry Ontology. Core ontology for linked data registry services. Based on ISO19135 but heavily modified to suit Linked Data representations and applications",
                "containedItemClass": ["http://pid.geoscience.gov.au/def/ont/ga/pdm#Site"]
            },
            "description": "Index register, return all registers with links navigating to them. This index register will be used when there is not register specified in @decorator.register() in routes.py.  People can replace this default register by simply adding customized index register in @decorator.register() decorator."
        })
        
        