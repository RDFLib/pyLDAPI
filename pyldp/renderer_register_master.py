from abc import ABCMeta
from flask import render_template, Response
from .renderer import Renderer
from rdflib import Graph, URIRef, RDF, RDFS, XSD, Namespace, Literal
from _ldapi.__init__ import LDAPI
import _config as conf


class RegisterMasterRenderer(Renderer):
    __metaclass__ = ABCMeta

    def __init__(self, request, template, register_tree):
        """Everything to be rendered must at least have a graph (its data) and a URI (its ID)"""
        self.request = request
        self.template = template
        self.register_tree = register_tree
        self.paging_params(self.request)

    def render(self, view, mimetype):
        """This method must be implemented by all classes that inherit from Renderer

        :param view: a model view available for this class instance
        :param mimetype: a mimetype string, e.g. text/html
        :return: a Flask Response object
        """
        # alternates view is handled by the pyldapi
        if mimetype == 'text/html':
            return render_template(self.template, register_tree=self.register_tree)
        else:
            self._make_reg_graph(view)
            rdflib_format = LDAPI.get_rdf_parser_for_mimetype(mimetype)
            return Response(
                self.g.serialize(format=rdflib_format),
                status=200,
                mimetype=mimetype,
                headers=self.headers
            )
            
    @staticmethod
    def views_formats():
        """
        return this register's supported views and mimetypes for each view
        """
        return {
            'default': 'reg',
            'alternates': {
                'mimetypes': [
                    'text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json', 'application/json'],
                'default_mimetype': 'text/html',
                'namespace': 'http://www.w3.org/ns/ldp#Alternates',
                'description': 'The view listing all other views of this class of object'
            },
            'reg': {
                'mimetypes': ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json'],
                'default_mimetype': 'text/html',
                'namespace': 'http://purl.org/linked-data/registry#',
                'description':
                    'The Registry Ontology. Core ontology for linked data registry services. Based on ISO19135 but '
                    'heavily modified to suit Linked Data representations and applications',
                'containedItemClass': ['http://purl.org/linked-data/registry#Register']
            },
            'description':
                'This is the Master Register containing all the registers within this Linked Data API.'
        }

    def paging_params(self, request):
        # pagination
        self.page = int(request.args.get('page')) if request.args.get('page') is not None else 1
        self.per_page = int(request.args.get('per_page')) if request.args.get('per_page') is not None \
            else conf.PAGE_SIZE_DEFAULT

        if self.per_page > conf.PAGE_SIZE_MAX:
            return Response(
                'You must enter either no value for per_page or an integer <= {}.'.format(conf.PAGE_SIZE_MAX),
                status=400,
                mimetype='text/plain'
            )

        links = list()
        links.append('<http://www.w3.org/ns/ldp#Resource>; rel="type"')
        # signalling that this is, in fact, a resource described in pages
        links.append('<http://www.w3.org/ns/ldp#Page>; rel="type"')
        links.append('<{}?per_page={}>; rel="first"'.format(conf.URI_SITE_INSTANCE_BASE, self.per_page))

        # if this isn't the first page, add a link to "prev"
        if self.page != 1:
            links.append('<{}?per_page={}&page={}>; rel="prev"'.format(
                conf.URI_SITE_INSTANCE_BASE,
                self.per_page,
                (self.page - 1)
            ))

        # if this isn't the first page, add a link to "prev"
        if self.page != 1:
            self.prev_page = self.page - 1
            links.append('<{}?per_page={}&page={}>; rel="prev"'.format(
                conf.URI_SITE_INSTANCE_BASE,
                self.per_page,
                self.prev_page
            ))
        else:
            self.prev_page = None

        # add a link to "next" and "last"
        try:
            no_of_items = len(self.register_tree)
            print(no_of_items)
            self.last_page = int(round(no_of_items / self.per_page, 0)) + 1  # same as math.ceil()

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
                             .format(conf.URI_SITE_INSTANCE_BASE, self.per_page, (self.page + 1)))
            else:
                self.next_page = None

            # add a link to "last"
            links.append('<{}?per_page={}&page={}>; rel="last"'
                         .format(conf.URI_SITE_INSTANCE_BASE, self.per_page, self.last_page))
        except:
            # if there's some error in getting the no of samples, add the "next" link but not the "last" link
            self.next_page = self.page + 1
            links.append('<{}?per_page={}&page={}>; rel="next"'
                         .format(conf.URI_SITE_INSTANCE_BASE, self.per_page, (self.page + 1)))
            self.last_page = None

        self.headers = {
            'Link': ', '.join(links)
        }

    def _make_reg_graph(self, model_view):
        self.g = Graph()

        if model_view == 'reg':  # reg is default
            # make the static part of the graph
            REG = Namespace('http://purl.org/linked-data/registry#')
            self.g.bind('reg', REG)

            LDP = Namespace('http://www.w3.org/ns/ldp#')
            self.g.bind('ldp', LDP)

            XHV = Namespace('https://www.w3.org/1999/xhtml/vocab#')
            self.g.bind('xhv', XHV)

            register_uri = URIRef(self.request.base_url)
            self.g.add((register_uri, RDF.type, REG.Register))
            self.g.add((register_uri, RDFS.label, Literal('Sites Register', datatype=XSD.string)))

            page_uri_str = self.request.base_url
            if self.per_page is not None:
                page_uri_str += '?per_page=' + str(self.per_page)
            else:
                page_uri_str += '?per_page=100'
            page_uri_str_no_page_no = page_uri_str + '&page='
            if self.page is not None:
                page_uri_str += '&page=' + str(self.page)
            else:
                page_uri_str += '&page=1'
            page_uri = URIRef(page_uri_str)

            # pagination
            # this page
            self.g.add((page_uri, RDF.type, LDP.Page))
            self.g.add((page_uri, LDP.pageOf, register_uri))

            # links to other pages
            self.g.add((page_uri, XHV.first, URIRef(page_uri_str_no_page_no + '1')))
            self.g.add((page_uri, XHV.last, URIRef(page_uri_str_no_page_no + str(self.last_page))))

            if self.page != 1:
                self.g.add((page_uri, XHV.prev, URIRef(page_uri_str_no_page_no + str(self.page - 1))))

            if self.page != self.last_page:
                self.g.add((page_uri, XHV.next, URIRef(page_uri_str_no_page_no + str(self.page + 1))))

            # add all the items
            for register in self.register_tree:
                if '#' in register.get('contained_item_class'):
                    label = register.get('contained_item_class').split('#')[1]
                else:
                    label = register.get('contained_item_class').split('/')[-1]

                item_uri = URIRef(self.request.base_url + register.get('uri')[1:])
                self.g.add((item_uri, RDF.type, URIRef('http://purl.org/linked-data/registry#Register')))
                self.g.add((item_uri, RDFS.label, Literal('Register of ' + label + 's', datatype=XSD.string)))
                self.g.add((item_uri, RDFS.comment, Literal(register.get('description'), datatype=XSD.string)))
                self.g.add((item_uri, REG.register, page_uri))
                self.g.add((item_uri, REG.containedItemClass, URIRef(register.get('contained_item_class'))))
