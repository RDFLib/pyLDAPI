from abc import ABCMeta, abstractmethod


class Renderer:
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, uri, endpoints):
        """Every thing to be rendered must at least have a graph (its data) and a URI (its ID)"""
        self.uri = uri
        self.endpoints = endpoints

    @abstractmethod
    def render(self, view, mimetype):
        """This method must be implemented by all classes that inherit from Renderer

        :param view: a model view available for this class instance
        :param mimetype: a mimetype string, e.g. text/html
        :return: a Flask Response object
        """
        pass

    @staticmethod
    @abstractmethod
    def views_formats():
        """
        return supported views, default views, description, and mimetypes for supported views.
        Example:
        '
        {
            "default": "reg",
            "alternates": {
                "mimetypes":
                    ["text/html", "text/turtle", "application/rdf+xml", "application/rdf+json", "application/json"],
                "default_mimetype": "text/html",
                "namespace": "http://www.w3.org/ns/ldp#Alternates",
                "description": "The view listing all other views of this class of object"
            },
            "reg": {
                "mimetypes": ["text/html", "text/turtle", "application/rdf+xml", "application/rdf+json"],
                "default_mimetype": "text/html",
                "namespace": "http://purl.org/linked-data/registry#",
                "description":
                    "The Registry Ontology. Core ontology for linked data registry services. Based on ISO19135 but
                    heavily modified to suit Linked Data representations and applications",
                "containedItemClass": ["http://pid.geoscience.gov.au/def/ont/ga/pdm#Site"]
            }, 
            "description":
                "Some description for this render, this infomation will be displayed on the home register page"
        }
        '
        """
        pass
