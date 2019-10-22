# -*- coding: utf-8 -*-
from abc import ABCMeta
import json
from flask import Response, render_template
from rdflib import Graph, Namespace, URIRef, BNode, Literal, RDF, RDFS, XSD
from rdflib.namespace import DCTERMS
from pyldapi.view import View
from pyldapi.exceptions import ViewsFormatsException
import connegp


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

    def __init__(self,
                 request,
                 instance_uri,
                 views,
                 default_view_token,
                 alternates_template=None,
                 **kwargs
                 ):
        """
        Constructor

        :param request: Flask request object that triggered this class object's creation.
        :type request: :class:`flask.request`
        :param instance_uri: The URI that triggered this API endpoint (can be via redirects but the main URI is needed).
        :type instance_uri: str
        :param views: A dictionary of views available for this resource.
        :type views: dict (of :class:`.View` class objects)
        :param default_view_token: The ID of the default view (key of a view in the dictionary of :class:`.View`
        objects)
        :type default_view_token: str (a key in views)
        :param alternates_template: The Jinja2 template to use for rendering the HTML *alternates view*. If None, then
        it will default to try and use a template called :code:`alternates.html`.
        :type alternates_template: str

        .. seealso:: See the :class:`.View` class on how to create a dictionary of views.

        """
        self.vf_error = None
        self.request = request
        self.instance_uri = instance_uri

        # ensure alternates token isn't hogged by user
        for k, v in views.items():
            if k == 'alternates':
                self.vf_error = 'You must not manually add a view with token \'alternates\' as this is auto-created.'

        self.views = views
        self.view = None

        # ensure that the default view is actually a given view
        if default_view_token == "alternates":
            self.vf_error = 'You cannot specify \'alternates\' as the default view.'

        # ensure the default view is in the list of views
        if default_view_token not in self.views.keys():
            self.vf_error = 'The view token you specified for the default view is not in the list of views you supplied'

        self.default_view_token = default_view_token

        # TODO: supply an alternates.html template
        self.alternates_template = alternates_template

        # auto-add in an Alternates view
        self.views['alternates'] = View(
            'Alternates',
            'The view that lists all other views',
            ['text/html', 'application/json', '_internal'] + self.RDF_MIMETYPES,
            'text/html',
            languages=['en'],  # default 'en' only for now
            profile_uri='https://w3id.org/profile/alt'  # the registered URI for the Alternates View Profile
        )

        self.views['all'] = View(
            'Alternate Representations',
            'The representation of the resource that lists all other representations (profiles and Media Types)',
            ['text/html', 'application/json'] + self.RDF_MIMETYPES,
            'text/html',
            languages=['en'],  # default 'en' only for now
            profile_uri='http://www.w3.org/ns/dx/conneg/altr'  # the ConnegP URI for RRD Functional Profile
        )

        # get view & format for this request, flag any errors but do not except out
        self.view = self._get_profile()
        self.format = self._get_mediatype()
        self.language = self._get_language()

        # make headers only if there's no error
        if self.vf_error is None:
            self.headers = dict()
            self.headers['Content-Profile'] = '<' + self.views[self.view].namespace + '>'
            self.headers['Content-Type'] = self.format
            self.headers['Content-Language'] = self.language

            self.headers['Link'] = self._make_header_link_tokens()
            self.headers['Link'] = self.headers['Link'] + ', ' + self._make_header_link_list_profiles()

    #
    # getting request's preferences
    #

    # TODO: wrap all the input parsing functions in try/except block pushing errors to vf_error
    def _get_profiles_from_qsa(self):
        """
        Reads either _profile or _view Query String Argument and returns a list of Profile tokens
        in ascending preference order

        Ref: https://www.w3.org/TR/dx-prof-conneg/#qsa-getresourcebyprofile

        :return: List of URIs of accept profiles in descending request order
        :rtype: list
        """
        # try QSAa and, if we have any, return them only
        profiles_string = self.request.values.get('_view', self.request.values.get('_profile'))
        if profiles_string is not None:
            pqsa = connegp.ProfileQsaParser(profiles_string)
            if pqsa.valid:
                profiles = []
                for profile in pqsa.profiles:
                    if profile['profile'].startswith('<'):
                        # convert this valid URI/URN to a token
                        for token, view in self.views.items():
                            if view.namespace == profile['profile'].strip('<>'):
                                profiles.append(token)
                    else:
                        # it's already a token so just add it
                        profiles.append(profile['profile'])
                if len(profiles) > 0:
                    return profiles

        return None

    def _get_profiles_from_http(self):
        """
        Reads an Accept-Profile HTTP header and returns a list of Profile tokens in descending weighted order

        Ref: https://www.w3.org/TR/dx-prof-conneg/#http-getresourcebyprofile

        :return: List of URIs of accept profiles in descending request order
        :rtype: list
        """
        if self.request.headers.get('Accept-Profile') is not None:
            try:
                ap = connegp.AcceptProfileHeaderParser(self.request.headers.get('Accept-Profile'))
                if ap.valid:
                    profiles = []
                    for profile in ap.profiles:
                        # convert this valid URI/URN to a token
                        for token, view in self.views.items():
                            if view.namespace == profile['profile']:
                                profiles.append(token)
                    if len(profiles) == 0:
                        return None
                    else:
                        return profiles
                else:
                    return None
            except Exception as e:
                msg = 'You have requested a profile using an Accept-Profile header that is incorrectly formatted.'
                raise ViewsFormatsException(msg)
        else:
            return None

    def _get_available_profiles(self):
        uris = {}
        for token, view in self.views.items():
            uris[view.namespace] = token

        return uris

    def _get_profile(self):
        # if we get a profile from QSA, use that
        profiles_requested = self._get_profiles_from_qsa()

        # if not, try HTTP
        if profiles_requested is None:
            profiles_requested = self._get_profiles_from_http()

        # if still no profile, return None
        if profiles_requested is None:
            return self.default_view_token

        # if we have a result from QSA or HTTP, got through each in order and see if there's an available
        # view for that token, return first one
        profiles_available = self._get_available_profiles()
        for profile in profiles_requested:
            for k, v in profiles_available.items():
                if profile == v:
                    return v  # return the profile token

        # if no match found, should never o
        return self.default_view_token

    def _get_mediatypes_from_qsa(self):
        """Returns a list of Media Types from QSA

        :return: list
        """
        qsa_mediatypes = self.request.values.get('_format', self.request.values.get('_mediatype', None))
        if qsa_mediatypes is not None:
            qsa_mediatypes = str(qsa_mediatypes).replace(' ', '+').split(',')
            # if the internal format is requested, return the default
            if qsa_mediatypes[0] == "_internal":
                return [self.views[self.view].default_format]
            else:
                return qsa_mediatypes
        else:
            return None

    def _get_mediatypes_from_http(self):
        """Returns a list of Media Type tokens from an Accept HTTP header in descending weighted order

        :return: List of URIs of accept profiles in descending request order
        :rtype: list
        """
        if hasattr(self.request, 'headers'):
            if self.request.headers.get('Accept') is not None:
                try:
                    # split the header into individual URIs, with weights still attached
                    mediatypes = self.request.headers['Accept'].split(',')
                    # remove \s
                    mediatypes = [x.strip() for x in mediatypes]

                    # split off any weights and sort by them with default weight = 1
                    mediatypes = [
                        (float(x.split(';')[1].replace('q=', '')) if ";q=" in x else 1, x.split(';')[0]) for x in mediatypes
                    ]

                    # sort profiles by weight, heaviest first
                    mediatypes.sort(reverse=True)

                    # return only the orderd list of mediatypes, not weights
                    return[x[1] for x in mediatypes]
                except Exception as e:
                    raise ViewsFormatsException(
                        'You have requested a Media Type using an Accept header that is incorrectly formatted.')

        return None

    def _get_available_mediatypes(self):
        return self.views[self.view].formats

    def _get_mediatype(self):
        mediatypes_requested = self._get_mediatypes_from_qsa()
        if mediatypes_requested is None:
            mediatypes_requested = self._get_mediatypes_from_http()

        # no Media Types requested so return default
        if mediatypes_requested is None:
            return self.views[self.view].default_format

        # iterate through requested Media Types until a valid one is found
        mediatypes_available = self._get_available_mediatypes()
        for mediatype in mediatypes_requested:
            if mediatype in mediatypes_available:
                return mediatype

        # no valid Media Type is found so return default
        return self.views[self.view].default_format

    def _get_languages_from_qsa(self):
        """Returns a list of Languages from QSA

        :return: list
        """
        languages = self.request.values.get('_lang')
        if languages is not None:
            languages = str(languages).replace(' ', '_').replace('+', '_').split(',')
            # if the internal format is requested, return the default
            if languages == "_internal":
                return self.views[self.view].default_language
            else:
                return languages

        return None

    def _get_languages_from_http(self):
        """
        Reads an Accept HTTP header and returns an array of Media Type string in descending weighted order

        :return: List of URIs of accept profiles in descending request order
        :rtype: list
        """
        if hasattr(self.request, 'headers'):
            if self.request.headers.get('Accept-Language') is not None:
                try:
                    # split the header into individual URIs, with weights still attached
                    languages = self.request.headers['Accept-Language'].split(',')
                    # remove \s
                    languages = [x.strip() for x in languages]

                    # split off any weights and sort by them with default weight = 1
                    languages = [
                        (float(x.split(';')[1].replace('q=', ''))
                         if len(x.split(';')) == 2 else 1, x.split(';')[0]) for x in languages
                    ]

                    # sort profiles by weight, heaviest first
                    languages.sort(reverse=True)

                    # return only the orderd list of languages, not weights
                    return[x[1] for x in languages]
                except Exception as e:
                    raise ViewsFormatsException(
                        'You have requested a language using an Accept-Language header that is incorrectly formatted.')

        return None

    def _get_available_languages(self):
        return self.views[self.view].languages

    def _get_language(self):
        languages_requested = self._get_languages_from_qsa()
        if languages_requested is None:
            languages_requested = self._get_languages_from_http()

        # no Media Types requested so return default
        if languages_requested is None:
            return self.views[self.view].default_language

        # iterate through requested Media Types until a valid one is found
        languages_available = self._get_available_mediatypes()
        for language in languages_requested:
            if language in languages_available:
                return language

        # no valid Media Type is found so return default
        return self.views[self.view].default_language

    # end getting request's preferences

    #
    # making response headers
    #

    def _make_header_link_tokens(self):
        individual_links = []
        link_header_template = '<http://www.w3.org/ns/dx/prof/Profile>; rel="type"; token="{}"; anchor=<{}>, '

        for token, view in self.views.items():
            individual_links.append(link_header_template.format(token, view.namespace))

        return ''.join(individual_links).rstrip(', ')

    def _make_header_link_list_profiles(self):
        individual_links = []
        for token, view in self.views.items():
            # create an individual Link statement per Media Type
            for format_ in view.formats:
                # set the rel="self" just for this view & format
                if format_ != '_internal':
                    if token == self.view and format_ == self.format:
                        rel = 'self'
                    else:
                        rel = 'alternate'

                    individual_links.append(
                        '<{}?_view={}&_format={}>; rel="{}"; type="{}"; profile="{}", '.format(
                            self.instance_uri,
                            token,
                            format_,
                            rel,
                            format_,
                            view.namespace)
                    )

        # append to, or create, Link header
        return ''.join(individual_links).rstrip(', ')

    # end making response headers

    #
    # making response content
    #

    def _render_alternates_view(self):
        """
        Return a Flask Response object depending on the value assigned to :code:`self.format`.

        :return: A Flask Response object
        :rtype: :class:`flask.Response`
        """
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
            'uri': self.instance_uri,
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
        ALT = Namespace('http://w3id.org/profile/alt#')
        g.bind('alt', ALT)

        g.bind('dct', DCTERMS)

        PROF = Namespace('http://www.w3.org/ns/prof/')
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
                g.add((v_node, URIRef(DCTERMS + 'format'), URIRef('http://w3id.org/mediatype/' + f)))
            g.add((v_node, ALT.hasDefaultFormat, Literal(v.default_format, datatype=XSD.string)))
            if v.namespace is not None:
                g.add((v_node, DCTERMS.conformsTo, URIRef(v.namespace)))
            g.add((URIRef(self.instance_uri), ALT.view, v_node))

            if self.default_view_token == token:
                g.add((URIRef(self.instance_uri), ALT.hasDefaultView, v_node))
        return g

    def _make_rdf_response(self, graph, mimetype=None, headers=None, delete_graph=True):
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
                'uri': self.instance_uri,
                'views': list(self.views.keys()),
                'default_view': self.default_view_token
            }),
            mimetype='application/json',
            headers=self.headers
        )

    def _render_rdd_view_html(self, template_context=None):
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
            'uri': self.instance_uri,
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

    # TODO: languages not included
    def _render_rdd_view_rdf(self):
        g = Graph()
        ALTR = Namespace('http://www.w3.org/ns/dx/conneg/altr#')
        g.bind('altr', ALTR)

        g.bind('dct', DCTERMS)

        PROF = Namespace('http://www.w3.org/ns/prof/')
        g.bind('prof', PROF)

        res = URIRef(self.instance_uri)
        g.add((res, RDF.type, RDFS.Resource))

        for token, v in self.views.items():
            for f in v.formats:
                if str(f).startswith('_'):  # ignore formats like `_internal`
                    continue
                v_node = BNode()
                g.add((v_node, RDF.type, ALTR.Representation))
                g.add((v_node, PROF.token, Literal(token, datatype=XSD.token)))
                g.add((v_node, RDFS.label, Literal(v.label, datatype=XSD.string)))
                g.add((v_node, RDFS.comment, Literal(v.comment, datatype=XSD.string)))

                g.add((v_node, DCTERMS.conformsTo, URIRef(v.namespace)))

                if self.default_view_token == token:
                    g.add((URIRef(self.instance_uri), ALTR.hasDefaultRepresentation, v_node))
                else:
                    g.add((URIRef(self.instance_uri), ALTR.hasRepresentation, v_node))

                g.add((v_node, URIRef(DCTERMS + 'format'), URIRef('http://w3id.org/mediatype/' + f)))
                if f == v.default_format:
                    g.add((v_node, ALTR.isProfilesDefault, Literal(True, datatype=XSD.boolean)))

        return self._make_rdf_response(g)

    def _render_rdd_view(self):
        if self.format == '_internal':
            return self
        if self.format == 'text/html':
            return self._render_rdd_view_html()
        else:  # self.format in Renderer.RDF_MIMETYPES:
            return self._render_rdd_view_rdf()

    def render(self):
        """
        Use the received view and format to create a response back to the client.

        TODO: Ashley, are you able to update this description with your new changes please?
        What is the method for rendering other views now? - Edmond

        This is an abstract method.

        .. note:: The :class:`pyldapi.Renderer.render` requires you to implement your own business logic to render
        custom responses back to the client using :func:`flask.render_template` or :class:`flask.Response` object.
        """

        # if there's been an error with the request, return that
        if self.vf_error is not None:
            print(self.vf_error)
            return Response(self.vf_error, status_code=400, mimtype='text/plain')
        elif self.view == 'alternates':
            return self._render_alternates_view()
        elif self.view == 'all':
            return self._render_rdd_view()
        return None

    # end making response content
