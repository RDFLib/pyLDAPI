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
