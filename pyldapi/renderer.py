# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import json
from flask import Response, render_template
from rdflib import Graph, Namespace, URIRef, BNode, Literal, RDF, RDFS, XSD
from pyldapi.view import View
from pyldapi.exceptions import ViewsFormatsException


class Renderer(object, metaclass=ABCMeta):
    """
    Abstract class as a parent for classes that validate the views & formats for an API-delivered resource (typically
    either registers or objects) and also creates an 'alternates view' for them, based on all available views & formats.
    """

    RDF_MIMETYPES = ['text/turtle', 'application/rdf+xml', 'application/ld+json', 'text/n3', 'application/n-triples']
    RDF_SERIALIZER_MAP = {
        "text/turtle": "turtle",
        "text/n3": "n3",
        "application/n-triples": "nt",
        "application/ld+json": "json-ld",
        "application/rdf+xml": "xml",
        # Some common but incorrect mimetypes
        "application/rdf": "xml",
        "application/rdf xml": "xml",
        "application/json": "json-ld",
        "application/ld json": "json-ld",
        "text/ttl": "turtle",
        "text/ntriples": "nt",
        "text/n-triples": "nt",
        "text/plain": "nt",  # text/plain is the old/deprecated mimetype for n-triples
    }

    def __init__(self, request, uri, views, default_view_token, alternates_template=None):
        """
        Init function for class
        :param request: the Flask request object that triggered this class object creation
        :type request: Flask request object
        :param uri: the URI called that triggered this API endpoint (can be via redirects but the main URI is needed)
        :type uri: string
        :param views: a list of views available for this resource
        :type views: list (of View class objects)
        :param default_view_token: the ID of the default view (key of a view in the list of Views)
        :type default_view_token: string (key in views)
        :param alternates_template: the jinja template to use for rendering the HTML alternates view
        :type alternates_template: string | None
        """
        self.request = request
        self.uri = uri

        # ensure alternates isn't hogged by user
        for k, v in views.items():
            if k == 'alternates':
                raise ViewsFormatsException(
                    'You must not manually add a view with token \'alternates\' as this is auto-created'
                )
        self.views = views

        # ensure that the default view is actually a given view
        if default_view_token not in self.views.keys():
            raise ViewsFormatsException(
                'The view token you specified for the default view is not in the list of views you supplied'
            )
        self.default_view_token = default_view_token
        self.alternates_template = alternates_template
        # auto-add in an Alternates view
        self.views['alternates'] = View(
            'Alternates',
            'The view that lists all other views',
            ['text/html', 'application/json', '_internal'] + self.RDF_MIMETYPES,
            'text/html',
            languages=['en'],  # default 'en' only for now
            namespace='https://promsns.org/def/alt'
        )

        # get view & format for this request, flag any errors but do not except out
        try:
            self.view = self._get_requested_view()
            try:
                self.format = self._get_requested_format()
                if self.format is None:
                    self.format = self.views[self.view].default_format

                self.language = self._get_requested_language()
                if self.language is None:
                    self.language = self.views[self.view].default_language
            except ViewsFormatsException as e:
                print(e)
                self.vf_error = str(e)
        except ViewsFormatsException as e:
            print(e)
            self.vf_error = str(e)

        self.headers = dict()

    def _get_accept_profiles_in_order(self):
        """
        Reads an Accept-Profile HTTP header and returns an array of Profile URIs in descending weighted order

        :return: List of URIs of accept profiles in descending request order
        :rtype: list
        """
        try:
            # split the header into individual URIs, with weights still attached
            profiles = self.request.headers['Accept-Profile'].split(',')
            # remove <, >, and \s
            profiles = [x.replace('<', '').replace('>', '').replace(' ', '').strip() for x in profiles]

            # split off any weights and sort by them with default weight = 1
            profiles = [(float(x.split(';')[1].replace('q=', '')) if len(x.split(';')) == 2 else 1, x.split(';')[0]) for x in profiles]

            # sort profiles by weight, heaviest first
            profiles.sort(reverse=True)

            return [x[1] for x in profiles]
        except Exception as e:
            raise ViewsFormatsException(
                'You have requested a profile using an Accept-Profile header that is incorrectly formatted.')

    def _get_available_profile_uris(self):
        uris = {}
        for k, view in self.views.items():
            uris[view.namespace] = k

        return uris

    def _get_best_accept_profile(self):
        profiles_requested = self._get_accept_profiles_in_order()
        profiles_available = self._get_available_profile_uris()

        for profile in profiles_requested:
            if profiles_available.get(profile):
                return profiles_available.get(profile)  # return the profile token

        return None  # if no match found

    def _get_accept_mediatypes_in_order(self):
        """
        Reads an Accept HTTP header and returns an array of Media Type string in descending weighted order

        :return: List of URIs of accept profiles in descending request order
        :rtype: list
        """
        try:
            # split the header into individual URIs, with weights still attached
            profiles = self.request.headers['Accept'].split(',')
            # remove \s
            profiles = [x.replace(' ', '').strip() for x in profiles]

            # split off any weights and sort by them with default weight = 1
            profiles = [(float(x.split(';')[1].replace('q=', '')) if len(x.split(';')) == 2 else 1, x.split(';')[0]) for x in profiles]

            # sort profiles by weight, heaviest first
            profiles.sort(reverse=True)

            return[x[1] for x in profiles]
        except Exception as e:
            raise ViewsFormatsException(
                'You have requested a Media Type using an Accept header that is incorrectly formatted.')

    def _get_available_mediatypes(self):
        return self.views[self.view].formats

    def _get_best_accept_mediatype(self):
        mediatypes_requested = self._get_accept_mediatypes_in_order()
        mediatypes_available = self._get_available_mediatypes()

        for mediatype in mediatypes_requested:
            if mediatype in mediatypes_available:
                return mediatype

        return None  # if no match found

    def _get_accept_languages_in_order(self):
        """
        Reads an Accept HTTP header and returns an array of Media Type string in descending weighted order

        :return: List of URIs of accept profiles in descending request order
        :rtype: list
        """
        try:
            # split the header into individual URIs, with weights still attached
            profiles = self.request.headers['Accept-Language'].split(',')
            # remove \s
            profiles = [x.replace(' ', '').strip() for x in profiles]

            # split off any weights and sort by them with default weight = 1
            profiles = [(float(x.split(';')[1].replace('q=', '')) if len(x.split(';')) == 2 else 1, x.split(';')[0]) for x in profiles]

            # sort profiles by weight, heaviest first
            profiles.sort(reverse=True)

            return[x[1] for x in profiles]
        except Exception as e:
            raise ViewsFormatsException(
                'You have requested a language using an Accept-Language header that is incorrectly formatted.')

    def _get_available_languages(self):
        return self.views[self.view].languages

    def _get_best_accept_language(self):
        languages_requested = self._get_accept_languages_in_order()
        languages_available = self._get_available_languages()

        for languages in languages_requested:
            if languages in languages_available:
                return languages

        return None  # if no match found

    def _get_requested_view(self):
        # if a particular _view is requested, if it's available, return it
        # the _view selector, coming first (before profile neg) will override profile neg, if both are set
        # if nothing is set, return default view (not HTTP 406)
        if self.request.values.get('_view') is not None:
            if self.views.get(self.request.values.get('_view')) is not None:
                return self.request.values.get('_view')
            else:
                raise ViewsFormatsException(
                    'The requested view is not available for the resource for which it was requested')
        elif hasattr(self.request, 'headers'):
            if self.request.headers.get('Accept-Profile') is not None:
                h = self._get_best_accept_profile()
                return h if h is not None else self.default_view_token

        return self.default_view_token

    def _get_requested_format(self):
        # try Query String Argument
        if self.request.values.get('_format') is not None:
            requested_format = self.request.values.get('_format').replace(' ', '+')
            if requested_format in self.views[self.view].formats:
                return requested_format
            # silently return default format
            # else:
            #     raise ViewsFormatsException(
            #         'The requested format for the {} view is not available for the resource for which '
            #         'it was requested'.format(self.view))

        # try HTTP headers
        elif hasattr(self.request, 'headers'):
            if self.request.headers.get('Accept') is not None:
                h = self._get_best_accept_mediatype()
                return h if h is not None else self.views[self.view].default_format

        return self.views[self.view].default_format

    def _get_requested_language(self):
        if self.request.values.get('_lang') is not None:
            requested_lang = self.request.values.get('_lang')
            if requested_lang in self.views[self.view].languages:
                return requested_lang
            # silently return default lang
            # else:
            #     raise ViewsFormatsException(
            #         'The requested language for the {} view is not available for the resource for which '
            #         'it was requested'.format(self.view))

        # try HTTP headers
        elif hasattr(self.request, 'headers'):
            if self.request.headers.get('Accept-Language') is not None:
                h = self._get_best_accept_language()
                return h if h is not None else self.views[self.view].default_language

        return self.views[self.view].default_language

    def _make_alternates_view_headers(self):
        self.headers['Profile'] = 'https://promsns.org/def/alt'  # the profile of the Alternates View
        self.headers['Content-Type'] = self.format  # the format of the Alternates View

        # TODO: add in the list of all other available Profiles (views) here

    def _render_alternates_view(self):
        # TODO: Pass self.uri to here. WHY?
        # https://github.com/RDFLib/pyLDAPI/issues/3
        self._make_alternates_view_headers()
        if self.format == '_internal':
            return self
        if self.format == 'text/html':
            return self._render_alternates_view_html()
        elif self.format in Renderer.RDF_MIMETYPES:
            return self._render_alternates_view_rdf()
        else:  # application/json
            return self._render_alternates_view_json()

    def _render_alternates_view_html(self):
        return Response(
            render_template(
                self.alternates_template or 'alternates.html',
                uri=self.uri,
                default_view_token=self.default_view_token,
                views=self.views
            ),
            headers=self.headers
        )

    def _generate_alternates_view_rdf(self):
        g = Graph()
        ALT = Namespace('http://promsns.org/def/alt#')
        g.bind('alt', ALT)

        DCT = Namespace('http://purl.org/dc/terms/')
        g.bind('dct', DCT)

        PROF = Namespace('https://w3c.github.io/dxwg/profiledesc#')
        g.bind('prof', PROF)

        for token, v in self.views.items():
            v_node = BNode()
            g.add((v_node, RDF.type, ALT.View))
            g.add((v_node, PROF.token, Literal(token, datatype=XSD.token)))
            g.add((v_node, RDFS.label, Literal(v.label, datatype=XSD.string)))
            g.add((v_node, RDFS.comment, Literal(v.comment, datatype=XSD.string)))
            for f in v.formats:
                if str(f).startswith('_'):  # ignore formats like `_internal`
                    continue
                g.add((v_node, URIRef(DCT + 'format'), URIRef('http://w3id.org/mediatype/' + f)))
            g.add((v_node, ALT.hasDefaultFormat, Literal(v.default_format, datatype=XSD.string)))
            if v.namespace is not None:
                g.add((v_node, DCT.conformsTo, URIRef(v.namespace)))
            g.add((URIRef(self.uri), ALT.view, v_node))

            if self.default_view_token == token:
                g.add((URIRef(self.uri), ALT.hasDefaultView, v_node))

        return g

    def _make_rdf_response(self, graph, mimetype=None, headers=None):
        if headers is None:
            headers = self.headers
        serial_format = self.RDF_SERIALIZER_MAP.get(self.format, None)
        if serial_format is None:
            serial_format = "turtle"
            response_mimetype = "text/turtle"
        else:
            response_mimetype = self.format
        if mimetype is not None:
            # override mimetype?
            response_mimetype = mimetype
        return Response(graph.serialize(format=serial_format), mimetype=response_mimetype, headers=headers)

    def _render_alternates_view_rdf(self):
        g = self._generate_alternates_view_rdf()
        return self._make_rdf_response(g)

    def _render_alternates_view_json(self):
        return Response(
            json.dumps({
                'uri': self.uri,
                'views': list(self.views.keys()),
                'default_view': self.default_view_token
            }),
            mimetype='application/json',
            headers=self.headers
        )

    @abstractmethod
    def render(self):
        # use the now gotten view & format to create a response
        pass
