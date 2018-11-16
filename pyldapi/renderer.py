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
        Constructor

        :param request: Flask request object that triggered this class object's creation.
        :type request: :class:`flask.request`
        :param uri: The URI that triggered this API endpoint (can be via redirects but the main URI is needed).
        :type uri: str
        :param views: A dictionary of views available for this resource.
        :type views: dict (of :class:`.View` class objects)
        :param default_view_token: The ID of the default view (key of a view in the dictionary of :class:`.View` objects)
        :type default_view_token: str (a key in views)
        :param alternates_template: The Jinja2 template to use for rendering the HTML *alternates view*. If None, then it will default to try and use a template called :code:`alternates.html`.
        :type alternates_template: str

        .. seealso:: See the :class:`.View` class on how to create a dictionary of views.

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
        query_view = self.request.values.get('_view', None)
        if query_view is not None:
            requested_view = str(query_view).replace(' ', '+')
            if requested_view == "_internal":
                return requested_view
            if self.views.get(requested_view, None) is not None:
                return requested_view
            else:
                # TODO: determine whether or not to
                # silently return default view
                raise ViewsFormatsException(
                    'The requested view is not available for the resource for which it was requested')
        elif hasattr(self.request, 'headers'):
            if self.request.headers.get('Accept-Profile') is not None:
                h = self._get_best_accept_profile()
                return h if h is not None else self.default_view_token

        return self.default_view_token

    def _get_requested_format(self):
        # try Query String Argument
        query_format = self.request.values.get('_format', None)
        if query_format is not None:
            requested_format = str(query_format).replace(' ', '+')
            if requested_format == "_internal":
                return requested_format
            if requested_format in self.views[self.view].formats:
                return requested_format

            # TODO: determine whether or not to
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
        query_lang = self.request.values.get('_lang', None)
        if query_lang is not None:
            # turn "en AU" into "en_AU" and turn "en+AU" into "en_AU"
            requested_lang = str(query_lang).replace(' ', '_').replace('+', '_')
            if requested_lang == "_internal":
                return requested_lang
            if requested_lang in self.views[self.view].languages:
                return requested_lang
            # TODO: determine whether or not to
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
        """
        Return a Flask Response object depending on the value assigned to :code:`self.format`.

        :return: A Flask Response object
        :rtype: :class:`flask.Response`
        """
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

    def _render_alternates_view_html(self, template_context=None):
        views = {}
        for token, v in self.views.items():
            view = {'label': str(v.label), 'comment': str(v.comment),
                    'formats': tuple(f for f in v.formats if not f.startswith('_')),
                    'default_format': str(v.default_format),
                    'languages': v.languages if v.languages is not None else ['en'],
                    'default_language': str(v.default_language),
                    'namespace': str(v.namespace)}
            views[token] = view
        _template_context = {
            'uri': self.uri,
            'default_view_token': self.default_view_token,
            'views': views
        }
        if template_context is not None and isinstance(template_context, dict):
            _template_context.update(template_context)
        return Response(
            render_template(
                self.alternates_template or 'alternates.html',
                **_template_context
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

    def _make_rdf_response(self, graph, mimetype=None, headers=None,
                           delete_graph=True):
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
        response_text = graph.serialize(format=serial_format)
        if delete_graph:
            # destroy the triples in the triplestore, then delete the triplestore
            # this helps to prevent a memory leak in rdflib
            graph.store.remove((None, None, None))
            graph.destroy({})
            del graph
        return Response(response_text,
                        mimetype=response_mimetype, headers=headers)

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

    def render(self):
        """
        Use the received view and format to create a response back to the client.

        This is an abstract method.

        .. note:: The :class:`pyldapi.Renderer.render` requires you to implement your own business logic to render custom responses back to the client using :func:`flask.render_template` or :class:`flask.Response` object.
        """
        if self.view == 'alternates':
            return self._render_alternates_view()
        return None
