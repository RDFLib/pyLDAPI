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
        Constructor

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
        """
        self.label = label
        self.comment = comment
        self.formats = formats
        self.default_format = default_format
        self.languages = languages if languages is not None else ['en']
        self.default_language = default_language
        self.namespace = namespace

