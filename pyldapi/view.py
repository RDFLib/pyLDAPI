# -*- coding: utf-8 -*-
class View:
    """
    A class containing elements for a Linked Data 'model view',
    including MIME type 'formats'
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
        self.label = label
        self.comment = comment
        self.formats = formats
        self.default_format = default_format
        self.languages = languages if languages is not None else ['en']
        self.default_language = default_language
        self.namespace = namespace

