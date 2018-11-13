# -*- coding: utf-8 -*-
class View:
    """
    A class containing elements for a Linked Data 'model view',
    including MIME type 'formats'.

    The syntax for these formats can be found at iana org: https://www.iana.org/assignments/media-types/media-types.xhtml

    Example of common media formats and languages as a list:

    .. code-block:: python

        formats = ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json']
        languages = ['en', 'pl'] # 'en' for English and 'pl' for Polish.

    """
    def __init__(
            self,
            label,
            comment,
            formats,
            default_format,
            languages=None,
            default_language='en',
            namespace=None
    ):
        """

        :param label: The view label.
        :type label: str
        :param comment: The comment describing the view.
        :type comment: str
        :param formats: The list of formats according to iana org.
        :type formats: list
        :param default_format: The default format according to iana org.
        :type default_format: str
        :param languages: A list of languages as strings.
        :type languages: list
        :param default_language: The default language, by default it is 'en' English.
        :type default_language: str
        :param namespace: The namespace URI for the *profile* view.
        :type namespace: str

        Example:

        A dictionary of views:

        .. code-block:: python

            views = {
                'csirov3': View(
                    'CSIRO IGSN View',
                    'An XML-only metadata schema for descriptive elements of IGSNs',
                    ['text/xml'],
                    'text/xml',
                    namespace='https://confluence.csiro.au/display/AusIGSN/CSIRO+IGSN+IMPLEMENTATION'
                ),

                'prov': View(
                    'PROV View',
                    "The W3C's provenance data model, PROV",
                    ["text/html", "text/turtle", "application/rdf+xml", "application/rdf+json"],
                    "text/turtle",
                    namespace="http://www.w3.org/ns/prov/"
                ),
            }

        A dictionary of views are generally intialised in the constructor of a specialised *ClassRenderer*.
        This ClassRenderer inherits from :class:`.Renderer` and must be implemented in the business logic.

        """
        self.label = label
        self.comment = comment
        self.formats = formats
        self.default_format = default_format
        self.languages = languages if languages is not None else ['en']
        self.default_language = default_language
        self.namespace = namespace

