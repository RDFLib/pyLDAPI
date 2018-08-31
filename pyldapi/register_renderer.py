# -*- coding: utf-8 -*-
from flask import Response, render_template
from flask_paginate import Pagination
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, XSD
from pyldapi.renderer import Renderer
from pyldapi.view import View
from pyldapi.exceptions import ViewsFormatsException


class RegisterRenderer(Renderer):
    """
    Specific implementation of the abstract Renderer for displaying Register information
    """
    def __init__(
            self,
            request,
            uri,
            label,
            comment,
            register_items,
            contained_item_classes,
            register_total_count,
            views=None,
            default_view_token=None,
            super_register=None,
            page_size_max=1000
    ):
        """
        Init function for class
        :param request: the Flask request triggering this class object creation
        :type request: Flask request
        :param uri: the URI requested
        :type uri: string
        :param label: the label of the Register
        :type label: string
        :param comment: a description of the Register
        :type comment: string
        :param register_items: items within this register
        :type register_items: list (of URIs (strings) or tuples like (URI, label) of (string, string)
        :param contained_item_classes: list of URIs of each distinct class of item contained in this register
        :type contained_item_classes: list (of strings)
        :param register_total_count: total number of items in this Register (not of a page but the register as a whole)
        :type register_total_count: int
        :param views: a list of views available for this Register, apart from 'reg' which is auto-created
        :type views: list (of Views)
        :param default_view_token: the ID of the default view (key of a view in the list of Views)
        :type default_view_token: string (key in views)
        :param super_register: a super-register URI for this register. Can be within this API or external
        :type super_register: string
        """
        if views is None:
            self.views = self._add_standard_reg_view()
        if default_view_token is None:
            self.default_view_token = 'reg'
        super().__init__(request, uri, self.views, self.default_view_token)
        self.label = label
        self.comment = comment
        if register_items is not None:
            self.register_items = register_items
        else:
            self.register_items = []
        self.contained_item_classes = contained_item_classes
        self.register_total_count = register_total_count
        self.per_page = request.args.get('per_page', type=int, default=20)
        self.page = request.args.get('page', type=int, default=1)
        self.super_register = super_register
        self.page_size_max = page_size_max

        self.paging_error = self._paging()

        try:
            self.format = self._get_requested_format()
        except ViewsFormatsException as e:
            self.vf_error = str(e)

    def _paging(self):
        # calculate last page
        self.last_page = int(round(self.register_total_count / self.per_page, 0)) + 1  # same as math.ceil()

        # if we've gotten the last page value successfully, we can choke if someone enters a larger value
        if self.page > self.last_page:
            return 'You must enter either no value for page or an integer <= {} which is the last page number.'\
                .format(self.last_page)

        if self.per_page > self.page_size_max:
            return 'You must choose a page size >= {}'.format(self.page_size_max)

        # set up Link headers
        links = list()
        # signalling this is an LDP Resource
        links.append('<http://www.w3.org/ns/ldp#Resource>; rel="type"')
        # signalling that this is, in fact, a Resource described in pages
        links.append('<http://www.w3.org/ns/ldp#Page>; rel="type"')

        # always add a link to first
        self.first_page = 1
        links.append('<{}?per_page={}&page={}>; rel="first"'
                     .format(self.uri, self.per_page, self.first_page))

        # if this isn't the first page, add a link to "prev"
        if self.page > 1:
            self.prev_page = self.page - 1
            links.append('<{}?per_page={}&page={}>; rel="prev"'.format(
                self.uri,
                self.per_page,
                self.prev_page
            ))
        else:
            self.prev_page = None

        # if this isn't the last page, add a link to next
        if self.page < self.last_page:
            self.next_page = self.page + 1
            links.append('<{}?per_page={}&page={}>; rel="next"'.format(
                self.uri,
                self.per_page,
                self.next_page
            ))
        else:
            self.next_page = None

        # always add a link to last
        links.append('<{}?per_page={}&page={}>; rel="last"'
                     .format(self.uri, self.per_page, self.last_page))

        self.headers = {
            'Link': ', '.join(links)
        }

        return None

    def render(self):
        if self.view == 'alternates':
            return self._render_alternates_view()
        elif self.view == 'reg':
            if self.paging_error is None:
                self.headers['Profile'] = 'http://purl.org/linked-data/registry#'
                return self._render_reg_view()
            else:  # there is a paging error (e.g. page > last_page)
                return Response(self.paging_error, status=400, mimetype='text/plain')

    def _render_reg_view(self):
        # add link headers for all formats of reg view
        if self.format == 'text/html':
            return self._render_reg_view_html()
        elif self.format in Renderer.RDF_MIMETYPES:
            return self._render_reg_view_rdf()

    def _render_reg_view_html(self):
        pagination = Pagination(page=self.page, per_page=self.per_page, total=self.register_total_count)

        return Response(
            render_template(
                'register.html',
                uri=self.uri,
                label=self.label,
                contained_item_classes=self.contained_item_classes,
                register_items=self.register_items,
                page=self.page,
                per_page=self.per_page,
                first_page=self.first_page,
                prev_page=self.prev_page,
                next_page=self.next_page,
                last_page=self.last_page,
                super_register=self.super_register,
                pagination=pagination
            ),
            headers=self.headers
        )

    def _render_reg_view_rdf(self):
        g = Graph()

        REG = Namespace('http://purl.org/linked-data/registry#')
        g.bind('reg', REG)

        LDP = Namespace('http://www.w3.org/ns/ldp#')
        g.bind('ldp', LDP)

        XHV = Namespace('https://www.w3.org/1999/xhtml/vocab#')
        g.bind('xhv', XHV)

        EREG = Namespace('https://promsns.org/def/eregistry#')
        g.bind('ereg', EREG)

        register_uri = URIRef(self.uri)
        g.add((register_uri, RDF.type, REG.Register))
        g.add((register_uri, RDFS.label, Literal(self.label, datatype=XSD.string)))
        g.add((register_uri, RDFS.comment, Literal(self.comment, datatype=XSD.string)))
        for cic in self.contained_item_classes:
            g.add((register_uri, REG.containedItemClass, URIRef(cic)))
        if self.super_register is not None:
            g.add((register_uri, EREG.superregister, URIRef(self.super_register)))

        page_uri_str = self.uri + '?per_page=' + str(self.per_page) + '&page=' + str(self.page)
        page_uri_str_nonum = self.uri + '?per_page=' + str(self.per_page) + '&page='
        page_uri = URIRef(page_uri_str)

        # pagination
        # this page
        g.add((page_uri, RDF.type, LDP.Page))
        g.add((page_uri, LDP.pageOf, register_uri))

        # links to other pages
        g.add((page_uri, XHV.first, URIRef(page_uri_str_nonum + '1')))
        g.add((page_uri, XHV.last, URIRef(page_uri_str_nonum + str(self.last_page))))

        if self.page != 1:
            g.add((page_uri, XHV.prev, URIRef(page_uri_str_nonum + str(self.page - 1))))

        if self.page != self.last_page:
            g.add((page_uri, XHV.next, URIRef(page_uri_str_nonum + str(self.page + 1))))

        # add all the items
        for item in self.register_items:
            if isinstance(item, tuple):  # if it's a tuple, add in the label
                item_uri = URIRef(item[0])
                g.add((item_uri, RDF.type, URIRef(self.uri)))
                g.add((item_uri, RDFS.label, Literal(item[1], datatype=XSD.string)))
                g.add((item_uri, REG.register, register_uri))
            else:  # just URIs
                item_uri = URIRef(item)
                g.add((item_uri, RDF.type, URIRef(self.uri)))
                g.add((item_uri, REG.register, register_uri))

        # because the rdflib JSON-LD serializer needs the string 'json-ld', not a MIME type
        if self.format in ['application/rdf+json', 'application/json']:
            return Response(g.serialize(format='json-ld'), mimetype=self.format, headers=self.headers)
        else:
            return Response(g.serialize(format=self.format), mimetype=self.format, headers=self.headers)

    def _add_standard_reg_view(self):
        return {
            'reg': View(
                'Registry Ontology',
                'A simple list-of-items view taken from the Registry Ontology',
                ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json'],
                'text/html',
                'http://purl.org/linked-data/registry#'
            )
        }


class RegisterOfRegistersRenderer(RegisterRenderer):
    """
    Specialised implementation of the RegisterRenderer for displaying Register of Register information

    This subclass just auto-fills many of the RegisterRenderer options
    """
    def __init__(
            self,
            request,
            uri,
            label,
            comment,
            rofr_file_path,
            super_register=None,
    ):
        """
        Init function for class
        :param request: the Flask request triggering this class object creation
        :type request: Flask request
        :param uri: the URI requested
        :type uri: string
        :param label: the label of the Register
        :type label: string
        :param comment: a description of the Register
        :type comment: string
        :param rofr_file_path: the path to the Register of Register RDF file (used in API setup)
        :type rofr_file_path: path (string)
        :param super_register: a super-register URI for this register. Can be within this API or external
        :type super_register: string
        """
        super(RegisterOfRegistersRenderer, self).__init__(
            request,
            uri,
            label,
            comment,
            None,
            ['http://purl.org/linked-data/registry#Register'],
            0,
            super_register
        )

        # find subregisters from rofr.ttl
        g = Graph().parse(rofr_file_path, format='turtle')
        q = '''
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX reg: <http://purl.org/linked-data/registry#>
            SELECT ?uri ?label
            WHERE {
                ?rofr reg:subregister ?uri .
                ?uri rdfs:label ?label .
            }
            '''
        for r in g.query(q):
            self.register_items.append((r['uri'], r['label']))
