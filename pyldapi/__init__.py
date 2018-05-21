import os
import logging
from flask import Response, render_template
from threading import Thread
from time import sleep
import requests
from rdflib import Graph, Namespace, URIRef, BNode, Literal, RDF, RDFS, XSD
from abc import ABCMeta, abstractmethod


g = Graph()


def setup(app, api_home_dir, api_uri):
    """
    Used to set up the Register of Registers for this LDAPI

    Must be fun before app.run like this: thread = pyldapi.setup(app, conf.URI_BASE)
    :param app: the Flask app containing this LDAPI
    :type app: Flask app
    :param api_uri: URI base of the API
    :type api_uri: string
    :return: the thread executing this task
    :rtype: thread
    """
    t = Thread(target=_make_rofr_rdf, args=(app, api_home_dir, api_uri))
    t.start()

    return t


def _make_rofr_rdf(app, api_home_dir, api_uri):
    """
    The setup function that creates the Register of Registers.

    Do not call from outside setup
    :param app: the Flask app containing this LDAPI
    :type app: Flask app
    :param api_uri: URI base of the API
    :type api_uri: string
    :return: none
    :rtype: None
    """
    sleep(1)  # to ensure that this occurs after the Flask boot
    print('making RofR')

    # get the RDF for each Register, extract the bits we need, write them to graph g
    for rule in app.url_map.iter_rules():
        if '<' not in str(rule):  # no registers can have a Flask variable in their path
            # make the register view URI for each possible register
            candidate_register_uri = api_uri + str(rule) + '?_view=reg&_format=text/turtle'
            get_filtered_register_graph(candidate_register_uri)

    # serialise g
    with open(os.path.join(api_home_dir, 'rofr.ttl'), 'w') as f:
        f.write(g.serialize(format='text/turtle').decode('utf-8'))

    print('finished making RofR')


def get_filtered_register_graph(register_uri):
    """
    Gets a filtered version (label, comment, contained item classes & subregisters only) of the each register for the
    Register of Registers

    :param register_uri: the public URI of the register
    :type register_uri: string
    :return: True if ok, else False
    :rtype: boolean
    """
    logging.debug('assessing register candidate ' + register_uri.replace('?_view=reg&_format=text/turtle', ''))
    try:
        r = requests.get(register_uri)
        print('getting ' + register_uri)
    except ViewsFormatsException as e:
        pass  # ignore these exceptions as are just a result of requesting a view/format combo of something like a page

    if r.status_code == 200:
        if 'text/turtle' in r.headers.get('Content-Type'):
            logging.debug('{} is a register '.format(register_uri.replace('?_view=reg&_format=text/turtle', '')))
            # it is a valid endpoint returning RDF (turtle) so...
            # import all its content into the in-memory graph
            g2 = Graph().parse(data=r.content.decode('utf-8'), format='text/turtle')
            # extract out only the Register details
            # make a query to get all the vars we need
            q = '''
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX reg: <http://purl.org/linked-data/registry#>
                PREFIX ereg: <https://promsns.org/def/eregistry#>
                CONSTRUCT {{
                    <{0}> a reg:Register .
                    ?r rdfs:label ?label .
                    ?r rdfs:comment ?comment .
                    ?r reg:containedItemClass ?cic .
                    ?superregister reg:subregister ?r .
                }}
                WHERE {{
                    <{0}> a reg:Register .
                    ?r rdfs:label ?label .
                    ?r rdfs:comment ?comment .
                    ?r reg:containedItemClass ?cic .
                    OPTIONAL {{ ?r ereg:superregister ?superregister . }}
                    OPTIONAL {{ ?r reg:subregister ?subregister . }}
                }}
            '''.format(register_uri.replace('?_view=reg&_format=text/turtle', ''))

            global g
            g += g2.query(q)

            return True
        else:
            logging.debug(
                '{} returns no RDF'.format(register_uri.replace('?_view=reg&_format=text/turtle', '')))
            return False  # no RDF (turtle) response from endpoint so not register
    logging.debug('{} returns no HTTP 200'.format(register_uri.replace('?_view=reg&_format=text/turtle', '')))
    return False  # no valid response from endpoint so not register


class View:
    """
    A class containing elements for a Linked Data 'movel view', including MIME type 'formats'
    """
    def __init__(
            self,
            label,
            comment,
            formats,
            default_format,
            namespace=None
    ):
        self.label = label
        self.comment = comment
        self.formats = formats
        self.default_format = default_format
        self.namespace = namespace


class ViewsFormatsException(ValueError):
    pass


class Renderer:
    """
    Abstract class as a parent for classes that validate the views & formats for an API-delivered resource (typically
    either registers or objects) and also creates an 'alternates view' for them, based on all available views & formats.
    """
    __metaclass__ = ABCMeta

    RDF_MIMETYPES = ['text/turtle', 'application/rdf+xml', 'application/rdf+json', 'text/n3', 'application/json']

    def __init__(self, request, uri, views, default_view_token):
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

        # auto-add in an alternates view
        self.views['alternates'] = View(
            'Alternates',
            'The view that lists all other views',
            ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json', 'application/json'],
            'text/html'
        )

        # get view & format for this request, flag any errors but do not except out
        try:
            self.view = self._get_requested_view()
            try:
                self.format = self._get_requested_format()
            except ViewsFormatsException as e:
                self.vf_error = str(e)
        except ViewsFormatsException as e:
            self.vf_error = str(e)

    def _get_requested_view(self):
        # if a particular _view is requested, if it's available, return it
        if self.request.values.get('_view') is not None:
            if self.views.get(self.request.values.get('_view')) is not None:
                return self.request.values.get('_view')
            else:
                raise ViewsFormatsException(
                    'The requested view is not available for the resource for which it was requested')
        # if no _view is requested, return default view
        else:
            return self.default_view_token

    def _get_requested_format(self):
        # if a particular _format is requested, see if it's valid for the requested view
        if self.request.values.get('_format') is not None:
            requested_format = self.request.values.get('_format').replace(' ', '+')
            if requested_format in self.views[self.view].formats:
                return requested_format
            else:
                raise ViewsFormatsException(
                    'The requested format for the {} view is not available for the resource for which '
                    'it was requested'.format(self.view))
        elif len(self.request.accept_mimetypes) > 1:  # if a particular format is requested by conneg, see if it's valid
            return self.request.accept_mimetypes.best_match(self.views[self.view].formats)
        else:
            return self.views[self.view].default_format

    def _render_alternates_view(self):
        if self.format == 'text/html':
            return self._render_alternates_view_html()
        elif self.format in Renderer.RDF_MIMETYPES:
            return self._render_alternates_view_rdf()
        else:  # application/json
            return self._render_alternates_view_json()

    def _render_alternates_view_html(self):
        return render_template(
            'alternates.html',
            default_view_token=self.default_view_token,
            views=self.views
        )

    def _render_alternates_view_rdf(self):
        g = Graph()
        EREG = Namespace('http://promsns.org/def/eregistry#')
        g.bind('ereg', EREG)

        for token, v in self.views.items():
            v_node = BNode()
            g.add((v_node, RDF.type, EREG.View))
            g.add((v_node, EREG.token, Literal(token, datatype=XSD.string)))
            g.add((v_node, RDFS.label, Literal(v.label, datatype=XSD.string)))
            g.add((v_node, RDFS.comment, Literal(v.comment, datatype=XSD.string)))
            for f in v.formats:
                g.add((v_node, EREG.mimetype, Literal(f, datatype=XSD.string)))
            g.add((v_node, EREG.hasDefaultFormat, Literal(v.default_format, datatype=XSD.string)))
            if v.namespace is not None:
                g.add((v_node, EREG.namespace, Literal(v.comment, datatype=XSD.string)))
            g.add((URIRef(self.uri), EREG.view, v_node))

            if self.default_view_token == token:
                g.add((URIRef(self.uri), EREG.hasDefaultView, v_node))

        if self.format in ['application/rdf+json', 'application/json']:
            self.format = 'json-ld'
        return g.serialize(format=self.format)

    # TODO: consider adding a 'plain' JSON (i.e. not JSON-LD) version
    # def _render_alternates_view_json(self):
    #    return json.dumps({'views': self.views, 'default_view': self.default_view_token})

    @abstractmethod
    def render(self):
        # use the now gotten view & format to create a response
        pass


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
            super_register=None
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
            self.views = self.add_standard_reg_view()
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

        self._paging()

    def _paging(self):
        links = list()
        links.append('<http://www.w3.org/ns/ldp#Resource>; rel="type"')
        # signalling that this is, in fact, a resource described in pages
        links.append('<http://www.w3.org/ns/ldp#Page>; rel="type"')
        links.append('<{}?per_page={}>; rel="first"'.format(self.uri, self.per_page))

        # if this isn't the first page, add a link to "prev"
        if self.page != 1:
            links.append('<{}?per_page={}&page={}>; rel="prev"'.format(
                self.uri,
                self.per_page,
                (self.page - 1)
            ))

        # if this isn't the first page, add a link to "prev"
        if self.page != 1:
            self.prev_page = self.page - 1
            links.append('<{}?per_page={}&page={}>; rel="prev"'.format(
                self.uri,
                self.per_page,
                self.prev_page
            ))
        else:
            self.prev_page = None

        # add a link to "next" and "last"
        try:
            self.last_page = int(round(self.register_total_count / self.per_page, 0)) + 1  # same as math.ceil()

            # if we've gotten the last page value successfully, we can choke if someone enters a larger value
            if self.page > self.last_page:
                return Response(
                    'You must enter either no value for page or an integer <= {} which is the last page number.'
                    .format(self.last_page),
                    status=400,
                    mimetype='text/plain'
                )

            # add a link to "next"
            if self.page != self.last_page:
                self.next_page = self.page + 1
                links.append('<{}?per_page={}&page={}>; rel="next"'
                             .format(self.uri, self.per_page, (self.page + 1)))
            else:
                self.next_page = None

            # add a link to "last"
            links.append('<{}?per_page={}&page={}>; rel="last"'
                         .format(self.uri, self.per_page, self.last_page))
        except:
            # if there's some error in getting the no of samples, add the "next" link but not the "last" link
            self.next_page = self.page + 1
            links.append('<{}?per_page={}&page={}>; rel="next"'
                         .format(self.uri, self.per_page, (self.page + 1)))
            self.last_page = None

        self.headers = {
            'Link': ', '.join(links)
        }

    def render(self):
        if self.view == 'alternates':
            return Response(self._render_alternates_view(), mimetype=self.format)
        elif self.view == 'reg':
            return Response(self._render_reg_view(), mimetype=self.format, headers=self.headers)

    def _render_reg_view(self):
        # add link headers for all formats of reg view
        if self.format == 'text/html':
            return self._render_reg_view_html()
        elif self.format in Renderer.RDF_MIMETYPES:
            return self._render_reg_view_rdf()

    def _render_reg_view_html(self):
        return render_template(
            'register.html',
            uri=self.uri,
            label=self.label,
            contained_item_classes=self.contained_item_classes,
            register_items=self.register_items,
            page=self.page,
            per_page=self.per_page,
            prev_page=self.prev_page,
            next_page=self.next_page,
            last_page=self.last_page,
            super_register=self.super_register
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
                g.add((item_uri, REG.register, page_uri))
            else:  # just URIs
                item_uri = URIRef(item)
                g.add((item_uri, RDF.type, URIRef(self.uri)))
                g.add((item_uri, REG.register, page_uri))

        # serialize the RDF in whichever format was selected by the user, after converting from mimetype
        if self.format in ['application/rdf+json', 'application/json']:
            self.format = 'json-ld'
        return g.serialize(format=self.format)

    def add_standard_reg_view(self):
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
            ['http://purl.org/linked-data/registry#register'],
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
