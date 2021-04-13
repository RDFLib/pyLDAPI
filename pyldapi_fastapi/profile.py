# -*- coding: utf-8 -*-
class Profile:
    """
    A class containing elements for a Linked Data 'model view',
    including MIME type 'mediatypes'.

    The syntax for mediatypes can be found at iana org: https://www.iana.org/assignments/media-types/media-types.xhtml

    Example of common mediatypes and languages as a list:

    .. code-block:: python

        mediatypes = ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json']
        languages = ['en', 'pl'] # 'en' for English and 'pl' for Polish.

    """
    def __init__(
            self,
            uri,
            label,
            comment,
            mediatypes,
            default_mediatype,
            languages=None,
            default_language='en',
    ):
        """
        Constructor

        :param label: The view label.
        :type label: str
        :param comment: The comment describing the view.
        :type comment: str
        :param mediatypes: The list of mediatypes according to iana org.
        :type mediatypes: list
        :param default_mediatype: The default mediatype according to iana org.
        :type default_mediatype: str
        :param languages: A list of languages as strings.
        :type languages: list
        :param default_language: The default language, by default it is 'en' English.
        :type default_language: str
        :param uri: The namespace URI for the *profile* view.
        :type uri: str
        """
        self.label = label
        self.comment = comment
        self.mediatypes = mediatypes
        self.default_mediatype = default_mediatype
        self.languages = languages if languages is not None else ['en']
        self.default_language = default_language
        self.uri = uri
