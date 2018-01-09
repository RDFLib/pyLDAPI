from flask import Response
import json
from os.path import join, dirname
from werkzeug.contrib.cache import SimpleCache


class LDAPI:
    """
    A class containing static functions to assist with building a Linked Data API

    This class is issued as a Python file, rather than a Git submodule so check the version number before use!

    Version 2.1
    """

    # maps HTTP MIMETYPES to rdflib's RDF parsing formats
    MIMETYPES_PARSERS = [
        ('text/turtle', 'turtle'),
        ('application/rdf+xml', 'xml'),
        ('application/rdf xml', 'xml'),
        ('application/rdf+json', 'json-ld'),
        ('application/rdf json', 'json-ld'),
        ('application/json', 'json-ld'),
        ('text/ntriples', 'nt'),
        ('text/nt', 'nt'),
        ('text/n3', 'nt')
    ]

    def __init__(self):
        pass

    @staticmethod
    def get_rdf_mimetypes_list():
        return [item[0] for item in LDAPI.MIMETYPES_PARSERS]

    @staticmethod
    def get_rdf_parser_for_mimetype(mimetype):
        return [item[1] for item in LDAPI.MIMETYPES_PARSERS if item[0] == mimetype][0]

    @staticmethod
    def get_mimetype_for_rdf_parser(rdf_parser):
        return [item[0] for item in LDAPI.MIMETYPES_PARSERS if item[1] == rdf_parser][0]

    @staticmethod
    def get_file_extension(mimetype):
        """
        Matches the file extension to MIME types

        :param mimetype: an HTTP mime type
        :return: a string
        """
        file_extension = {
            'text/turtle': '.ttl',
            'application/rdf+xml': '.rdf',
            'application/rdf+json': '.json',
            'application/xml': '.xml',
            'text/xml': '.xml',
            'text/nt': '.nt',
            'text/n3': '.n3',
        }

        return file_extension[mimetype]

    @staticmethod
    def an_int(s):
        """
        Safely (no Error throw) tests to see whether a string can be itnerpreted as an int

        :param s: string
        :return: boolean
        """
        if s is not None:
            try:
                int(s)
                return True
            except ValueError:
                return False
        else:
            return False

    @staticmethod
    def valid_view(view, views_formats):
        """
        Determines whether a requested model model is valid and, if it is, it returns it

        :return: model name (string) or False
        """
        if view is not None:
            if view in views_formats.keys():
                return view
            else:
                raise LdapiParameterError(
                    'The _view parameter is invalid. For this object, it must be one of {0}.'
                    .format(', '.join(views_formats.keys()))
                )
        else:
            # views_formats will give us the default model
            return views_formats['default']

    @staticmethod
    def valid_format(format, view, views_formats):
        """
        Determines whether a requested format for a particular model model is valid and, if it is, it returns it

        :return: model name (string) or False
        """
        if format is not None:
            if format.replace(' ', '+') in views_formats.get(view)['mimetypes']:
                return format.replace(' ', '+')
            else:
                raise LdapiParameterError(
                    'The _format parameter is invalid. For this model view, format should be one of {0}.'
                        .format(', '.join(views_formats.get(view)['mimetypes']))
                )
        else:
            # HTML is default
            return 'text/html'

    @staticmethod
    def get_valid_view_and_format(view, format, views_formats):
        """
        If both the model and the format are valid, return them

        If a view is given but no format, return the default format for that view
        :param view: the model model parameter
        :param format: the MIMETYPE format parameter
        :param views_formats: the allowed model and their formats in this instance
        :return: valid model and format
        """
        view = LDAPI.valid_view(view, views_formats)
        if format is not None:
            format = LDAPI.valid_format(format, view, views_formats)
        else:
            format = views_formats[view]['default_mimetype']

        if view and format:
            # return valid model and format
            return view, format

    @staticmethod
    def client_error_Response(error_message):
        return Response(
            error_message,
            status=400,
            mimetype='text/plain'
        )

    @staticmethod
    def is_a_uri(uri_candidate):
        """
        Validates a string as a URI

        :param uri_candidate: string
        :return: True or False
        """
        import re
        # https://gist.github.com/dperini/729294
        URL_REGEX = re.compile(
            u"^"
            # protocol identifier
            u"(?:(?:https?|ftp)://)"
            # user:pass authentication
            u"(?:\S+(?::\S*)?@)?"
            u"(?:"
            # IP address exclusion
            # private & local networks
            u"(?!(?:10|127)(?:\.\d{1,3}){3})"
            u"(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})"
            u"(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})"
            # IP address dotted notation octets
            # excludes loopback network 0.0.0.0
            # excludes reserved space >= 224.0.0.0
            # excludes network & broadcast addresses
            # (first & last IP address of each class)
            u"(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])"
            u"(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}"
            u"(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))"
            u"|"
            # host name
            u"(?:(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9]+)"
            # domain name
            u"(?:\.(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9]+)*"
            # TLD identifier
            u"(?:\.(?:[a-z\u00a1-\uffff]{2,}))"
            u")"
            # port number
            u"(?::\d{2,5})?"
            # resource path
            u"(?:/\S*)?"
            u"$"
            , re.UNICODE
        )
        return re.match(URL_REGEX, uri_candidate)

    @staticmethod
    def get_classes_views_formats():
        """
        Caches the graph_classes JSON file in memory
        :return: a Python object parsed from the views_formats.json file
        """
        cache = SimpleCache()
        cvf = cache.get('classes_views_formats')
        if cvf is None:
            cvf = json.load(open(join(dirname(dirname(__file__)), 'controller', 'views_formats.json')))
            # times out never (i.e. on app startup/shutdown)
            cache.set('classes_views_formats', cvf)
        return cvf


class LdapiParameterError(ValueError):
    pass


if __name__ == '__main__':
    vfs = LDAPI.get_classes_views_formats().get('http://reference.data.gov.au/def/dataset#Dataset')
    print(LDAPI.get_valid_view_and_format('dataset', 'text/turtle', vfs))
