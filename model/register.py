from .renderer import Renderer
from flask import Response, render_template
from rdflib import Graph, URIRef, RDF, RDFS, XSD, Namespace, Literal
from _ldapi.__init__ import LDAPI
from lxml import etree
import requests
from io import StringIO, BytesIO
import _config as conf


class RegisterRenderer(Renderer):
    """
    Version 1.0
    """
    def __init__(self, request, base_uri, uri, endpoints, page, per_page, prev_page, next_page, last_page):
        Renderer.__init__(self, uri, endpoints)

        self.request = request
        self.base_uri = base_uri
        self.uri = uri
        self.register = []
        self.g = None
        self.per_page = per_page
        self.page = page
        self.prev_page = prev_page
        self.next_page = next_page
        self.last_page = last_page

        self._get_details_from_oracle_api(page, per_page)

    def render(self, view, mimetype, extra_headers=None):
        if view == 'reg':
            # is an RDF format requested?
            if mimetype in LDAPI.get_rdf_mimetypes_list():
                # it is an RDF format so make the graph for serialization
                self._make_reg_graph(view)
                rdflib_format = LDAPI.get_rdf_parser_for_mimetype(mimetype)
                return Response(
                    self.g.serialize(format=rdflib_format),
                    status=200,
                    mimetype=mimetype,
                    headers=extra_headers
                )
            elif mimetype == 'text/html':
                return Response(
                    render_template(
                        'class_register.html',
                        base_uri=self.base_uri,
                        class_name=self.uri,
                        register=self.register,
                        page=self.page,
                        per_page=self.per_page,
                        prev_page=self.prev_page,
                        next_page=self.next_page,
                        last_page=self.last_page
                    ),
                    mimetype='text/html',
                    headers=extra_headers
                )
        else:
            return Response('The requested model model is not valid for this class', status=400, mimetype='text/plain')

    def _get_details_from_file(self, file_path=None, xml_content=None):
        """
        Populates this instance with data from an XML file.

        :param xml: XML according to GA's Oracle XML API from the Sites DB
        :return: None
        """
        if file_path is not None:
            xml = open(file_path, 'rb')
        elif xml_content is not None:
            xml = BytesIO(xml_content)
        else:
            raise ValueError('You must specify either a file path or file XML contents')

        for event, elem in etree.iterparse(xml):
            if elem.tag == "ENO":
                self.register.append(elem.text)

    def validate_xml(self, xml):
        parser = etree.XMLParser(dtd_validation=False)

        try:
            etree.fromstring(xml, parser)
            return True
        except Exception:
            print('not valid xml')
            return False

    def _get_details_from_oracle_api(self, page, per_page):
        """
        Populates this instance with data from the Oracle Sites table API

        :param page: the page number of the total resultset from the Sites Set API
        :return: None
        """
        #os.environ['NO_PROXY'] = 'ga.gov.au'
        r = requests.get(conf.XML_API_URL_SITESET.format(page, per_page), timeout=3)
        xml = r.content

        if self.validate_xml(xml):
            self._get_details_from_file(xml_content=xml)
            return True
        else:
            return False

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
            for item in self.register:
                item_uri = URIRef(self.request.base_url + item)
                self.g.add((item_uri, RDF.type, URIRef(self.uri)))
                self.g.add((item_uri, RDFS.label, Literal('Site:' + item, datatype=XSD.string)))
                self.g.add((item_uri, REG.register, page_uri))
