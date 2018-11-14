from flask import Response, render_template
from pyldapi import Renderer, View
from datetime import datetime
from io import StringIO
import requests
from lxml import etree
from lxml import objectify
from rdflib import Graph, URIRef, RDF, RDFS, XSD, OWL, Namespace, Literal, BNode
import _config as conf
from controller.oai_datestamp import *
from .lookups import TERM_LOOKUP


class SampleRenderer(Renderer):
    """
                This class represents a Sample and methods in this class allow a sample to be loaded from GA's internal Oracle
                Samples database and to be exported in a number of formats including RDF, according to the 'IGSN Ontology' and an
                expression of the Dublin Core ontology, HTML, XML in the form given by the GA Oracle DB's API and also XML according
                to CSIRO's IGSN schema (v2).
                """

    """
    Associates terms in the database with terms in the IGSN codelist vocabulary:
    http://pid.geoscience.gov.au/def/voc/igsn-codelists

    One of:
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/accessType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/all-concepts
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/collectionType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/contributorType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/featureType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/geometryType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/identifierType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/materialType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/methodType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/relationType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/resourceType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/sampleType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/sridType
    """

    URI_MISSSING = 'http://www.opengis.net/def/nil/OGC/0/missing'
    URI_GA = 'http://pid.geoscience.gov.au/org/ga/geoscienceaustralia'

    def __init__(self, request, uri, igsn, xml=None):
        views = {
            # 'igsn-o': View(
            #     'IGSN Ontology View',
            #     'The view listing all other views of this class of object',
            #     ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json'],
            #     'text/html',
            #     namespace='http://www.w3.org/ns/ldp#Alternates'
            # ),

            'csirov3': View(
                'CSIRO IGSN View',
                'An XML-only metadata schema for descriptive elements of IGSNs',
                ['text/xml'],
                'text/xml',
                namespace='https://confluence.csiro.au/display/AusIGSN/CSIRO+IGSN+IMPLEMENTATION'
            ),

            'dct': View(
                'DC Terms View',
                'Dublin Core Terms from the Dublin Core Metadata Initiative',
                [
                    "text/html",
                    "text/turtle",
                    "application/rdf+xml",
                    "application/rdf+json",
                    "application/xml",
                    "text/xml"
                ],
                'text/turtle',
                namespace='http://purl.org/dc/terms/'
            ),

            'igsn': View(
                'IGSN View',
                'The official IGSN XML schema',
                ['text/xml'],
                'text/xml',
                namespace='http://schema.igsn.org/description/'
            ),

            'igsn-r1': View(
                'IGSN v1. View',
                'Version 1 of the official IGSN XML schema',
                ['text/xml'],
                'text/xml',
                namespace='http://schema.igsn.org/description/1.0'
            ),

            'igsn-o': View(
                'IGSN Ontology View',
                "An OWL ontology of Samples based on CSIRO's XML-based IGSN schema",
                ["text/html", "text/turtle", "application/rdf+xml", "application/rdf+json"],
                'text/html',
                namespace='http://pid.geoscience.gov.au/def/ont/ga/igsn'
            ),

            'prov': View(
                'PROV View',
                "The W3C's provenance data model, PROV",
                ["text/html", "text/turtle", "application/rdf+xml", "application/rdf+json"],
                "text/turtle",
                namespace="http://www.w3.org/ns/prov/"
            ),

            'sosa': View(
                'SOSA View',
                "The W3C's Sensor, Observation, Sample, and Actuator ontology within the Semantic Sensor Networks ontology",
                ["text/turtle", "application/rdf+xml", "application/rdf+json"],
                "text/turtle",
                namespace="http://www.w3.org/ns/sosa/"
            ),
        }

        super(SampleRenderer, self).__init__(request, uri, views, 'igsn-o')

        self.igsn = igsn
        self.sample_id = None
        self.access_rights = None
        self.sample_type = None
        self.method_type = None
        self.material_type = None
        self.long_min = None
        self.long_max = None
        self.lat_min = None
        self.lat_max = None
        self.gtype = None
        self.srid = None
        self.x = None
        self.y = None
        self.z = None
        self.elem_info = None
        self.ordinates = None
        self.state = None
        self.country = None
        self.depth_top = None
        self.depth_base = None
        self.strath = None
        self.age = None
        self.remark = None
        self.lith = None
        self.date_acquired = None
        self.entity_uri = None
        self.entity_name = None
        self.entity_type = None
        self.hole_long_min = None
        self.hole_long_max = None
        self.hole_lat_min = None
        self.hole_lat_max = None
        self.date_modified = None
        self.sample_no = None
        self.custodian_uri = self.URI_GA  # default
        self.custodian_label = 'Geoscience Australia'  # default
        self.collector = None

        if xml is not None:  # even if there are values for Oracle API URI and IGSN, load from XML file if present
            self._populate_from_xml_file(xml)
        else:
            self._populate_from_oracle_api()

    def validate_xml(self, xml):
        parser = etree.XMLParser(dtd_validation=False)

        try:
            etree.fromstring(xml, parser)
            return True
        except Exception:
            print('not valid xml')
            return False

    def _populate_from_oracle_api(self):
        """
        Populates this instance with data from the Oracle Samples table API

        :param oracle_api_samples_url: the Oracle XML API URL string for a single sample
        :param igsn: the IGSN of the sample desired
        :return: None
        """
        # internal URI
        # os.environ['NO_PROXY'] = 'ga.gov.au'
        # call API
        r = requests.get(conf.XML_API_URL_SAMPLE.format(self.igsn))
        if "No data" in r.content.decode('utf-8'):
            raise ParameterError('No Data')

        if self.validate_xml(r.content):
            self._populate_from_xml_file(r.content)
            return True
        else:
            return False

    def _populate_from_xml_file(self, xml):
        """
        Populates this instance with data from an XML file.

        :param xml: XML according to GA's Oracle XML API from the Samples DB
        :return: None
        """
        try:
            root = objectify.fromstring(xml)

            self.igsn = str(root.ROW.IGSN)
            if hasattr(root.ROW, 'SAMPLEID'):
                self.sample_id = root.ROW.SAMPLEID
            self.sample_no = root.ROW.SAMPLENO if hasattr(root.ROW, 'SAMPLENO') else None
            self.access_rights = self._make_vocab_uri('public',
                                                      'access_rights')  # statically 'public' for all samples
            if hasattr(root.ROW, 'REMARK'):
                self.remark = str(root.ROW.REMARK).strip() if len(str(root.ROW.REMARK)) > 5 else None
            if hasattr(root.ROW, 'SAMPLE_TYPE_NEW'):
                self.sample_type = self._make_vocab_uri(root.ROW.SAMPLE_TYPE_NEW, 'sample_type')
            if hasattr(root.ROW, 'SAMPLING_METHOD'):
                self.method_type = self._make_vocab_uri(root.ROW.SAMPLING_METHOD, 'method_type')
                self.method_type_non_uri = root.ROW.SAMPLING_METHOD
            if hasattr(root.ROW, 'MATERIAL_CLASS'):
                self.material_type = self._make_vocab_uri(root.ROW.MATERIAL_CLASS, 'material_type')
            # self.long_min = root.ROW.SAMPLE_MIN_LONGITUDE
            # self.long_max = root.ROW.SAMPLE_MAX_LONGITUDE
            # self.lat_min = root.ROW.SAMPLE_MIN_LATITUDE
            # self.lat_max = root.ROW.SAMPLE_MAX_LATITUDE
            if hasattr(root.ROW, 'SDO_GTYPE'):
                self.gtype = root.ROW.GEOM.SDO_GTYPE

            self.srid = 'GDA94'  # if root.ROW.GEOM.SDO_SRID == '8311' else root.ROW.GEOM.SDO_SRID

            if hasattr(root.ROW, 'GEOM'):
                if hasattr(root.ROW.GEOM, 'SDO_POINT'):
                    if hasattr(root.ROW.GEOM.SDO_POINT, 'X'):
                        self.x = root.ROW.GEOM.SDO_POINT.X
                    if hasattr(root.ROW.GEOM.SDO_POINT, 'Y'):
                        self.y = root.ROW.GEOM.SDO_POINT.Y
                    if hasattr(root.ROW.GEOM.SDO_POINT, 'Z'):
                        self.z = root.ROW.GEOM.SDO_POINT.Z
                if hasattr(root.ROW.GEOM, 'SDO_ELEM_INFO'):
                    self.elem_info = root.ROW.GEOM.SDO_ELEM_INFO
                if hasattr(root.ROW.GEOM, 'SDO_ORDINATES'):
                    self.ordinates = root.ROW.GEOM.SDO_ORDINATES.getchildren()
                    # calculate centroid values to centre a map
                    self.centroid_lat = round(sum(self.ordinates[1:-2:2]) / len(self.ordinates[:-2:2]), 2)
                    self.centroid_lon = round(sum(self.ordinates[:-2:2]) / len(self.ordinates[1:-2:2]), 2)
                    # self.ordinates = zip(*[iter(raw_ordinates)]*2)
            if hasattr(root.ROW, 'STATEID'):
                self.state = root.ROW.STATEID  # self._make_vocab_uri(root.ROW.STATEID, 'state')
            if hasattr(root.ROW, 'COUNTRY'):
                self.country = root.ROW.COUNTRY
            if hasattr(root.ROW, 'TOP_DEPTH'):
                self.depth_top = root.ROW.TOP_DEPTH
            if hasattr(root.ROW, 'BASE_DEPTH'):
                self.depth_base = root.ROW.BASE_DEPTH
            if hasattr(root.ROW, 'STRATNAME'):
                self.strath = root.ROW.STRATNAME
            if hasattr(root.ROW, 'AGE'):
                self.age = root.ROW.AGE
            if hasattr(root.ROW, 'LITHNAME'):
                self.lith = self._make_vocab_uri(root.ROW.LITHNAME, 'lithology')
            if hasattr(root.ROW, 'ACQUIREDATE'):
                self.date_acquired = str2datetime(root.ROW.ACQUIREDATE).date()
            if hasattr(root.ROW, 'MODIFIED_DATE'):
                self.date_modified = str2datetime(root.ROW.MODIFIED_DATE)
            if hasattr(root.ROW, 'ENO'):
                self.entity_uri = 'http://pid.geoscience.gov.au/site/' + str(root.ROW.ENO)
            if hasattr(root.ROW, 'ENTITYID'):
                self.entity_name = root.ROW.ENTITYID
            if hasattr(root.ROW, 'ENTITYID'):
                self.entity_type = self._make_vocab_uri(root.ROW.ENTITY_TYPE, 'entity_type')
            if hasattr(root.ROW, 'HOLE_MIN_LONGITUDE'):
                self.hole_long_min = root.ROW.HOLE_MIN_LONGITUDE
            if hasattr(root.ROW, 'HOLE_MAX_LONGITUDE'):
                self.hole_long_max = root.ROW.HOLE_MAX_LONGITUDE
            if hasattr(root.ROW, 'HOLE_MIN_LATITUDE'):
                self.hole_lat_min = root.ROW.HOLE_MIN_LATITUDE
            if hasattr(root.ROW, 'HOLE_MAX_LATITUDE'):
                self.hole_lat_max = root.ROW.HOLE_MAX_LATITUDE
            if hasattr(root.ROW, 'ORIGINATOR'):
                if str(root.ROW.ORIGINATOR) == 'GSSA':
                    self.custodian_label = 'Geological Survey of South Australia'
                    self.custodian_uri = 'http://www.minerals.statedevelopment.sa.gov.au/about_us#gssa'
                elif str(root.ROW.ORIGINATOR) == 'GSV':
                    self.custodian_label = 'Geological Survey of Victoria'
                    self.custodian_uri = 'http://earthresources.vic.gov.au/earth-resources/geology-of-victoria/' \
                                         'geological-survey-of-victoria'
                else:
                    # custodian_uri & custodian_label set to GA by default
                    self.collector = str(root.ROW.ORIGINATOR)
        except Exception as e:
            print(e)

        return True

    def _make_vocab_uri(self, xml_value, vocab_type):
        if TERM_LOOKUP[vocab_type].get(xml_value) is not None:
            return TERM_LOOKUP[vocab_type].get(xml_value)
        else:
            return TERM_LOOKUP[vocab_type].get('unknown')

    def _make_vocab_alink(self, vocab_uri):
        if vocab_uri is not None:
            if vocab_uri.endswith('/'):
                return '<a href="{}">{}</a>'.format(vocab_uri, vocab_uri.split('/')[-2])
            else:
                return '<a href="{}">{}</a>'.format(vocab_uri, vocab_uri.split('/')[-1])

    def render(self):
        # if self.sample_no is None:
        #     return Response('Sample with IGSN {} not found.'.format(self.igsn), status=404, mimetype='text/plain')

        if self.view == 'alternates':
            return self._render_alternates_view()
        elif self.view == 'igsn-o':
            if self.format == 'text/html':
                return self.export_html(model_view=self.view)
            else:
                return Response(self.export_rdf(self.view, self.format), mimetype=self.format)
        elif self.view == 'dct':
            if self.format == 'text/html':
                return self.export_html(model_view=self.view)
            elif self.format == 'text/xml':
                return Response(self.export_dct_xml(), mimetype=self.format)
            else:
                return Response(self.export_rdf(self.view, self.format), mimetype=self.format)
        elif self.view == 'igsn':  # only XML for this view
            return Response(
                '<?xml version="1.0" encoding="utf-8"?>\n' + self.export_igsn_xml(),
                mimetype='text/xml'
            )
        elif self.view == 'igsn-r1':  # only XML for this view
            return Response(
                '<?xml version="1.0" encoding="utf-8"?>\n' + self.export_igsn_r1_xml(),
                mimetype='text/xml'
            )
        elif self.view == 'csirov3':  # only XML for this view
            return Response(
                '<?xml version="1.0" encoding="utf-8"?>\n' + self.export_csirov3_xml(),
                mimetype='text/xml'
            )
        elif self.view == 'prov':
            if self.format == 'text/html':
                return self.export_html(model_view=self.view)
            else:
                return Response(self.export_rdf(self.view, self.format), mimetype=self.format)
        elif self.view == 'sosa':  # RDF only for this view
            return Response(self.export_rdf(self.view, self.format), mimetype=self.format)

    def _render_alternates_view_html(self):
        return Response(
            render_template(
                self.alternates_template or 'alternates.html',
                register_name='Sample Register',
                class_uri=self.uri,
                instance_uri=conf.URI_SAMPLE_INSTANCE_BASE + self.igsn,
                default_view_token=self.default_view_token,
                views=self.views
            ),
            headers=self.headers
        )

    def _generate_sample_wkt(self):
        if self.z is not None:
            return '<http://www.opengis.net/def/crs/EPSG/0/4283> POINTZ({} {} {})'.format(self.x, self.y,
                                                                                          self.z)
        elif self.srid is not None and self.x is not None and self.y is not None:
            return '<http://www.opengis.net/def/crs/EPSG/0/4283> POINT({} {})'.format(self.x, self.y)
        elif self.ordinates is not None:
            s = []
            for x, y in zip(*[iter(self.ordinates)] * 2):
                s.append(str(x) + ' ' + str(y))
            return '<http://www.opengis.net/def/crs/EPSG/0/4283> POLYGON(({}))'.format(
                ', '.join(s)
            )
        else:
            return ''

    def _generate_sample_gmap_bbox(self):
        if self.ordinates is not None:
            s = []
            for x, y in zip(*[iter(self.ordinates)] * 2):
                s.append('{lat: ' + str(y) + ', lng: ' + str(x) + '}')
            return ',\n                '.join(s)
        else:
            return None

    def _generate_sample_gml(self):
        if self.z is not None:
            gml = '<gml:Point srsDimension="3" srsName="https://epsg.io/{}">' \
                  '<gml:pos>{} {} {}</gml:pos>' \
                  '</gml:Point>'.format(self.srid, self.x, self.y, self.z)
        else:
            if self.srid is not None and self.x is not None and self.y is not None:
                gml = '<gml:Point srsDimension="2" srsName="https://epsg.io/{}">' \
                      '<gml:pos>{} {}</gml:pos>' \
                      '</gml:Point>'.format(self.srid, self.x, self.y)
            else:
                gml = ''

        return gml

    def _generate_parent_wkt(self):
        if self.hole_long_min is not None and self.hole_long_max is not None:
            coordinates = {
                'long_min': self.hole_long_min,
                'long_max': self.hole_long_max,
                'lat_min': self.hole_lat_min,
                'lat_max': self.hole_lat_max
            }
            wkt = '<http://www.opengis.net/def/crs/EPSG/0/4283> POLYGON(({long_min} {lat_max}, {long_max} {lat_max}, ' \
                  '{long_max} {lat_min}, {long_max} {lat_min}, {long_min} {lat_max}))'.format(**coordinates)
        elif self.hole_long_min is not None:
            coordinates = {
                'long_min': self.hole_long_min,
                'lat_min': self.hole_lat_min
            }
            wkt = '<http://www.opengis.net/def/crs/EPSG/0/4283> POINT({long_min} {lat_min})'.format(
                **coordinates)
        else:
            wkt = ''

        return wkt

    def _generate_parent_gml(self):
        if self.hole_long_min is not None and self.hole_long_max is not None:
            coordinates = {
                'srid': self.srid,
                'long_min': self.hole_long_min,
                'long_max': self.hole_long_max,
                'lat_min': self.hole_lat_min,
                'lat_max': self.hole_lat_max
            }
            gml = '<ogc:BBOX>' \
                  '<ogc:PropertyName>ows:BoundingBox</ogc:PropertyName>' \
                  '<gml:Envelope srsName="https://epsg.io/{srid}">' \
                  '<gml:upperCorner>{long_min} {lat_max}</gml:upperCorner>' \
                  '<gml:lowerCorner>{long_max} {lat_min}</gml:lowerCorner>' \
                  '</gml:Envelope>' \
                  '</ogc:BBOX>'.format(**coordinates)
        elif self.hole_long_min is not None:
            coordinates = {
                'srid': self.srid,
                'long_min': self.hole_long_min,
                'lat_min': self.hole_lat_min
            }
            gml = '<gml:Point srsDimension="2" srsName="https://epsg.io/{srid}">' \
                  '<gml:pos>{long_min} {lat_min}</gml:pos>' \
                  '</gml:Point>'.format(**coordinates)
        else:
            gml = ''

        return gml

    def _generate_google_maps_coords(self):
        return '{},{}'.format(self.y, self.x)

    def __graph_preconstruct(self, g):
        u = '''
            PREFIX prov: <http://www.w3.org/ns/prov#>
            DELETE {
                ?a prov:generated ?e .
            }
            INSERT {
                ?e prov:wasGeneratedBy ?a .
            }
            WHERE {
                ?a prov:generated ?e .
            }
        '''
        g.update(u)

        # simplifying qualified relationships
        u = '''
            PREFIX prov: <http://www.w3.org/ns/prov#>
            PREFIX foaf: <http://xmlns.com/foaf/0.1/>
            INSERT {
                ?e prov:wasAttributedTo ?a .
                ?a rdfs:label ?n .
            }
            WHERE {
                ?e prov:qualifiedAttribution/prov:agent ?a .
                ?a foaf:name ?n .
            }
        '''
        g.update(u)

        # up classing all prov:Person & org:Org as prov:Agent
        u = '''
            PREFIX prov: <http://www.w3.org/ns/prov#>
            PREFIX foaf: <http://xmlns.com/foaf/0.1/>
            INSERT {
                ?a a prov:Agent
            }
            WHERE {
                {?a a foaf:Organization}
                UNION
                {?a a prov:Person}
            }
        '''
        g.update(u)

        return g

    def __gen_visjs_nodes(self, g):
        nodes = ''

        q = '''
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX prov: <http://www.w3.org/ns/prov#>
            SELECT *
            WHERE {
                ?s a ?o .
                {?s a prov:Entity .}
                UNION
                {?s a prov:Activity .}
                UNION
                {?s a prov:Agent .}
                OPTIONAL {?s rdfs:label ?label .}
            }
            '''
        for row in g.query(q):
            if str(row['o']) == 'http://www.w3.org/ns/prov#Entity':
                if row['label'] is not None:
                    label = row['label']
                else:
                    label = 'Entity'
                nodes += '\t\t\t\t{id: "%(node_id)s", label: "%(label)s", shape: "ellipse", color:{background:"#FFFC87", border:"#808080"}},\n' % {
                    'node_id': row['s'],
                    'label': label
                }
            elif str(row['o']) == 'http://www.w3.org/ns/prov#Activity':
                if row['label'] is not None:
                    label = row['label']
                else:
                    label = 'Activity'
                nodes += '\t\t\t\t{id: "%(node_id)s", label: "%(label)s", shape: "box", color:{background:"#9FB1FC", border:"blue"}},\n' % {
                    'node_id': row['s'],
                    'label': label
                }
            elif str(row['o']) == 'http://www.w3.org/ns/prov#Agent':
                if row['label'] is not None:
                    label = row['label']
                else:
                    label = 'Agent'
                nodes += '\t\t\t\t{id: "%(node_id)s", label: "%(label)s", image: "/static/img/ga/agent.png", shape: "image"},\n' % {
                    'node_id': row['s'],
                    'label': label
                }

        return nodes

    def __gen_visjs_edges(self, g):
        edges = ''

        q = '''
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX prov: <http://www.w3.org/ns/prov#>
            SELECT *
            WHERE {
                ?s ?p ?o .
                ?s prov:wasAttributedTo|prov:wasGeneratedBy|prov:used|prov:wasDerivedFrom|prov:wasInformedBy ?o .
            }
            '''
        for row in g.query(q):
            edges += '\t\t\t\t{from: "%(from)s", to: "%(to)s", arrows:"to", font: {align: "bottom"}, color:{color:"black"}, label: "%(relationship)s"},\n' % {
                'from': row['s'],
                'to': row['o'],
                'relationship': str(row['p']).split('#')[1]
            }

        return edges

    def _make_citation(self):
        return '{} {}"Sample {}". A digital catalogue record of ' \
               'a physical sample managed by {}. Accessed {}. <a href="{}">igsn:{}</a>' \
            .format(
            self.collector if self.collector is not None else self.custodian_label,
            '({}) '.format(
                datetime.datetime.strftime(self.date_acquired, '%Y')) if self.date_acquired is not None else '',
            self.igsn,
            self.custodian_label,
            datetime.datetime.now().strftime('%d %B %Y'),
            conf.URI_SAMPLE_INSTANCE_BASE + self.igsn,
            self.igsn
        )

    def _make_vsjs(self, g):
        g = self.__graph_preconstruct(g)

        nodes = 'var nodes = new vis.DataSet([\n'
        nodes += self.__gen_visjs_nodes(g)
        nodes = nodes.rstrip().rstrip(',') + '\n\t\t\t]);\n'

        edges = 'var edges = new vis.DataSet([\n'
        edges += self.__gen_visjs_edges(g)
        edges = edges.rstrip().rstrip(',') + '\n\t\t\t]);\n'

        visjs = '''
        %(nodes)s

        %(edges)s

        var container = document.getElementById('network');

        var data = {
            nodes: nodes,
            edges: edges,
        };

        var options = {};
        var network = new vis.Network(container, data, options);
        ''' % {'nodes': nodes, 'edges': edges}

        return visjs

    def export_rdf(self, model_view='igsn-o', rdf_mime='text/turtle'):
        """
        Exports this instance in RDF, according to a given model from the list of supported models,
        in a given rdflib RDF format

        :param model_view: string of one of the model view names available for Sample objects ['igsn', 'dct', '',
            'default']
        :param rdf_mime: string of one of the rdflib serlialization format ['n3', 'nquads', 'nt', 'pretty-xml', 'trig',
            'trix', 'turtle', 'xml'], from http://rdflib3.readthedocs.io/en/latest/plugin_serializers.html
        :return: RDF string
        """

        # things that are applicable to all model views; the graph and some namespaces
        g = Graph()

        # URI for this sample
        this_sample = URIRef(conf.REGISTER_BASE_URI + self.igsn)
        g.add((this_sample, RDFS.label, Literal('Sample igsn:' + self.igsn, datatype=XSD.string)))

        # define GA
        ga = URIRef(self.URI_GA)

        # pingback endpoint
        PROV = Namespace('http://www.w3.org/ns/prov#')
        g.bind('prov', PROV)
        g.add((this_sample, PROV.pingback, URIRef(conf.REGISTER_BASE_URI + self.igsn + '/pingback')))
        SKOS = Namespace('http://www.w3.org/2004/02/skos/core#')
        g.bind('skos', SKOS)
        ADMS = Namespace('http://www.w3.org/ns/adms#')
        g.bind('adms', ADMS)
        DCT = Namespace('http://purl.org/dc/terms/')
        g.bind('dct', DCT)
        SAMFL = Namespace('http://def.seegrid.csiro.au/ontology/om/sam-lite#')
        g.bind('samfl', SAMFL)
        GEOSP = Namespace('http://www.opengis.net/ont/geosparql#')
        g.bind('geosp', GEOSP)
        AUROLE = Namespace('http://communications.data.gov.au/def/role/')
        g.bind('aurole', AUROLE)
        FOAF = Namespace('http://xmlns.com/foaf/0.1/')
        g.bind('foaf', FOAF)
        ORG = Namespace('http://www.w3.org/ns/org#')
        g.bind('org', ORG)

        # sample location in GML & WKT, formulation from GeoSPARQL
        wkt = Literal(self._generate_sample_wkt(), datatype=GEOSP.wktLiteral)
        gml = Literal(self._generate_sample_gml(), datatype=GEOSP.gmlLiteral)

        # select model view
        if model_view == 'igsn-o':
            # default model is the IGSN model
            # IGSN model required namespaces
            IGSN = Namespace('http://pid.geoscience.gov.au/def/ont/igsn#')
            g.bind('igsn', IGSN)

            # classing the sample
            g.add((this_sample, RDF.type, SAMFL.Specimen))

            # AlternateIdentifier
            alternate_identifier = BNode()
            g.add((alternate_identifier, RDF.type, ADMS.Identifier))
            g.add((alternate_identifier, SKOS.notation, Literal(self.igsn, datatype=XSD.string)))
            g.add((alternate_identifier, ADMS.schemeAgency, URIRef('http://igsn.org')))
            # TODO: add in a schema identifier, as per ADMS documentation
            g.add((this_sample, DCT.identifier, alternate_identifier))

            # Geometry
            geometry = BNode()
            g.add((this_sample, SAMFL.samplingLocation, geometry))
            g.add((geometry, RDF.type, SAMFL.Point))
            g.add((geometry, GEOSP.asGML, gml))
            g.add((geometry, GEOSP.asWKT, wkt))

            # Elevation
            elevation = BNode()
            g.add((this_sample, SAMFL.samplingElevation, elevation))
            g.add((elevation, RDF.type, SAMFL.Elevation))
            if self.z is None:
                z = 'NaN'
            else:
                z = self.z
            g.add((elevation, SAMFL.elevation, Literal(z, datatype=XSD.float)))
            g.add((elevation, SAMFL.verticalDatum, URIRef('http://spatialreference.org/ref/epsg/4283/')))

            # properties
            g.add((this_sample, SAMFL.currentLocation, Literal('GA Services building', datatype=XSD.string)))

            if self.material_type is not None:
                g.add((this_sample, SAMFL.materialClass, URIRef(self.material_type)))
            if self.method_type != 'http://www.opengis.net/def/nil/OGC/0/missing':
                g.add((this_sample, SAMFL.samplingMethod, URIRef(self.method_type)))
            if self.date_acquired is not None:
                g.add((this_sample, SAMFL.samplingTime,
                       Literal(self.date_acquired.isoformat(), datatype=XSD.datetime)))

            g.add((this_sample, DCT.accessRights, URIRef(TERM_LOOKUP['access_rights']['public'])))
            # TODO: make a register of Entities
            if self.entity_uri is not None:
                site = URIRef(self.entity_uri)

                g.add((this_sample, SAMFL.relatedSamplingFeature, site))  # could be OM.featureOfInterest

                # parent
                if self.entity_type is not None:
                    g.add((site, RDF.type, URIRef(self.entity_type)))
                else:
                    g.add((
                        site,
                        RDF.type,
                        URIRef('http://pid.geoscience.gov.au/def/voc/featureofinteresttype/borehole')
                    ))

                site_geometry = BNode()
                g.add((site, GEOSP.hasGeometry, site_geometry))
                g.add((site_geometry, RDF.type, SAMFL.Point))  # TODO: extend this for other geometry types
                g.add((site_geometry, GEOSP.asWKT,
                       Literal(self._generate_parent_wkt(), datatype=GEOSP.wktLiteral)))
                g.add((site_geometry, GEOSP.asGML,
                       Literal(self._generate_parent_gml(), datatype=GEOSP.wktLiteral)))

                site_elevation = BNode()
                g.add((site, SAMFL.samplingElevation, site_elevation))
                g.add((site_elevation, RDF.type, SAMFL.Elevation))
                if self.z is None:
                    z = 'NaN'
                else:
                    z = self.z
                g.add((site_elevation, SAMFL.elevation, Literal(z, datatype=XSD.float)))
                g.add(
                    (site_elevation, SAMFL.verticalDatum, URIRef('http://spatialreference.org/ref/epsg/4283/')))
                g.add((site, SAMFL.sampledFeature, this_sample))

            # Agents
            # define custodian as an PROV Org with an ISO19115 role of custodian
            custodian_uri = URIRef(self.custodian_uri)
            g.add((custodian_uri, RDF.type, ORG.Organization))
            g.add((custodian_uri, FOAF.name, Literal(self.custodian_label, datatype=XSD.string)))
            qualified_attribution = BNode()
            g.add((qualified_attribution, RDF.type, PROV.Attribution))
            g.add((qualified_attribution, PROV.agent, custodian_uri))
            g.add((qualified_attribution, PROV.hadRole, AUROLE.custodian))
            g.add((this_sample, PROV.qualifiedAttribution, qualified_attribution))

            # if a collector is known, term then a principalInvestigator
            if self.collector is not None:
                collector = BNode()
                g.add((collector, RDF.type, PROV.Person))
                g.add((collector, FOAF.name, Literal(self.collector, datatype=XSD.string)))
                qualified_attribution2 = BNode()
                g.add((qualified_attribution2, RDF.type, PROV.Attribution))
                g.add((qualified_attribution2, PROV.agent, collector))
                g.add((qualified_attribution2, PROV.hadRole, AUROLE.principalInvestigator))
                g.add((this_sample, PROV.qualifiedAttribution, qualified_attribution2))
        elif model_view == 'dct':
            # this is the cut-down IGSN --> Dublin core mapping describe at http://igsn.github.io/oai/
            g.add((this_sample, RDF.type, DCT.PhysicalResource))
            g.add((this_sample, DCT.coverage, wkt))
            # g.add((this_sample, DCT.creator, Literal('Unknown', datatype=XSD.string)))
            if self.date_acquired is not None:
                g.add((this_sample, DCT.date, Literal(self.date_acquired.isoformat(), datatype=XSD.date)))
            if self.remark is not None:
                g.add((this_sample, DCT.description, Literal(self.remark, datatype=XSD.string)))
            if self.material_type is not None:
                g.add((this_sample, URIRef('http://purl.org/dc/terms/format'), URIRef(self.material_type)))
            g.add((this_sample, DCT.identifier, Literal(self.igsn, datatype=XSD.string)))
            # define GA as a dct:Agent
            g.add((ga, RDF.type, DCT.Agent))
            g.add((this_sample, DCT.publisher, ga))
            # g.add((this_sample, DCT.relation, ga)) -- no value yet in GA DB
            # g.add((this_sample, DCT.subject, ga)) -- how is this different to type?
            # g.add((this_sample, DCT.title, ga)) -- no value at GA
            if self.sample_type is not None:
                g.add((this_sample, DCT.type, URIRef(self.sample_type)))
        elif model_view == 'prov':
            g.add((this_sample, RDF.type, PROV.Entity))
            # Agents
            # define custodian as an PROV Org with an ISO19115 role of custodian
            custodian_uri = URIRef(self.custodian_uri)
            g.add((custodian_uri, RDF.type, FOAF.Organization))
            g.add((custodian_uri, FOAF.name, Literal(self.custodian_label, datatype=XSD.string)))
            qualified_attribution = BNode()
            g.add((qualified_attribution, RDF.type, PROV.Attribution))
            g.add((qualified_attribution, PROV.agent, custodian_uri))
            g.add((qualified_attribution, PROV.hadRole, AUROLE.custodian))
            g.add((this_sample, PROV.qualifiedAttribution, qualified_attribution))

            # if a collector is known, term then a principalInvestigator
            if self.collector is not None:
                collector = BNode()
                g.add((collector, RDF.type, PROV.Person))
                g.add((collector, FOAF.name, Literal(self.collector, datatype=XSD.string)))
                qualified_attribution2 = BNode()
                g.add((qualified_attribution2, RDF.type, PROV.Attribution))
                g.add((qualified_attribution2, PROV.agent, collector))
                g.add((qualified_attribution2, PROV.hadRole, AUROLE.principalInvestigator))
                g.add((this_sample, PROV.qualifiedAttribution, qualified_attribution2))
        elif model_view == 'sosa':
            SOSA = Namespace('http://www.w3.org/ns/sosa/')
            g.bind('sosa', SOSA)
            # Sample
            g.add((this_sample, RDF.type, SOSA.Sample))

            #
            #   Sampling
            #
            # Sampling declaration
            sampling = BNode()
            g.add((sampling, RDF.type, SOSA.Sampling))
            if self.date_acquired is not None:
                g.add((sampling, SOSA.resultTime, Literal(self.date_acquired.isoformat(), datatype=XSD.date)))
            g.add((this_sample, SOSA.isResultOf, sampling))  # associate

            #
            #   Sampler
            #
            # Sampler declaration
            sampler = BNode()
            g.add((sampler, RDF.type, SOSA.Sampler))
            g.add((sampler, RDF.type, URIRef(self.method_type)))
            g.add((sampling, SOSA.madeBySampler, sampler))  # associate Sampler (with Sampling)

            # #
            # #   Procedure
            # #
            # # Procedure declaration
            # procedure = BNode()
            # g.add((procedure, RDF.type, SOSA.Procedure))
            # # g.add((this_sample, RDF.type, SOSA.Procedure))
            #  TODO: domsthing about missing if any method info is not known
            # # associate Procedure
            # g.add((this_sample, SOSA.usedProcedure, procedure))

            SAMP = Namespace('http://www.w3.org/ns/sosa/sampling/')
            g.bind('sampling', SAMP)

            # SampleRelationship to Site
            if self.entity_uri is not None:
                site = URIRef(self.entity_uri)
                sr = BNode()
                g.add((sr, RDF.type, SAMP.SampleRelationship))
                g.add((sr, SAMP.relatedSample, site))
                # TODO: replace with a real Concept URI
                g.add((sr, SAMP.natureOfRelationship,
                       URIRef('http://example.org/sampling/relationship/subsample')))
                g.add((this_sample, SAMP.hasSampleRelationship, sr))  # associate

                # Site details
                g.add((site, RDF.type, OWL.NamedIndividual))
                # specific type of Site
                if self.entity_type is not None:
                    site_type = URIRef(self.entity_type)
                else:
                    site_type = URIRef('http://pid.geoscience.gov.au/def/voc/featureofinteresttype/borehole')
                g.add((site, RDF.type, site_type))
                g.add((site_type, RDFS.subClassOf, SOSA.Sample))

                # FOI geometry
                site_geometry = BNode()
                g.add((site, GEOSP.hasGeometry, site_geometry))
                g.add((site_geometry, RDF.type, GEOSP.Geometry))
                g.add((site_geometry, GEOSP.asWKT,
                       Literal(self._generate_parent_wkt(), datatype=GEOSP.wktLiteral)))
                # g.add((site_geometry, GEOSP.asGML, Literal(self._generate_parent_gml(), datatype=GEOSP.wktLiteral)))
                # FOI elevation
                site_elevation = BNode()
                g.add((site, SAMFL.samplingElevation, site_elevation))
                g.add((site_elevation, RDF.type, SAMFL.Elevation))
                if self.z is None:
                    z = 'NaN'
                else:
                    z = self.z
                g.add((site_elevation, SAMFL.elevation, Literal(z, datatype=XSD.float)))
                g.add((site_elevation, SAMFL.verticalDatum,
                       Literal("http://spatialreference.org/ref/epsg/4283/", datatype=XSD.anyUri)))

            #
            #   Feature of Interest
            #
            # domain feature, same for all Samples
            domain_feature = URIRef(
                'http://registry.it.csiro.au/sandbox/csiro/oznome/feature/earth-realm/lithosphere')
            g.add((domain_feature, RDF.type, SOSA.FeatureOfInterest))
            g.add((domain_feature, SKOS.exactMatch,
                   URIRef('http://sweet.jpl.nasa.gov/2.3/realmGeol.owl#Lithosphere')))
            g.add((this_sample, SOSA.isSampleOf, domain_feature))  # associate

            g.add((this_sample, RDF.type, PROV.Entity))

            # Provenance Agents
            # define custodian as an PROV Org with an ISO19115 role of custodian
            custodian_uri = URIRef(self.custodian_uri)
            g.add((custodian_uri, RDF.type, FOAF.Organization))
            g.add((custodian_uri, FOAF.name, Literal(self.custodian_label, datatype=XSD.string)))
            qualified_attribution = BNode()
            g.add((qualified_attribution, RDF.type, PROV.Attribution))
            g.add((qualified_attribution, PROV.agent, custodian_uri))
            g.add((qualified_attribution, PROV.hadRole, AUROLE.custodian))
            g.add((this_sample, PROV.qualifiedAttribution, qualified_attribution))

            # if a collector is known, term then a principalInvestigator
            if self.collector is not None:
                collector = BNode()
                g.add((collector, RDF.type, PROV.Person))
                g.add((collector, FOAF.name, Literal(self.collector, datatype=XSD.string)))
                qualified_attribution2 = BNode()
                g.add((qualified_attribution2, RDF.type, PROV.Attribution))
                g.add((qualified_attribution2, PROV.agent, collector))
                g.add((qualified_attribution2, PROV.hadRole, AUROLE.principalInvestigator))
                g.add((this_sample, PROV.qualifiedAttribution, qualified_attribution2))

        return g.serialize(format=self._get_rdf_mimetype(rdf_mime))

    def _get_rdf_mimetype(self, rdf_mime):
        return self.RDF_SERIALIZER_MAP[rdf_mime]


    def _is_xml_export_valid(self, xml_string):
        """
        Validate and export of this Sample instance in XML using the XSD files from the dev branch
        of the IGSN repo: https://github.com/IGSN/metadata/tree/dev/description. The actual XSD
        files used are in the xml-validation dir, commit be2f0f8d7ef78407c386d3c8a0aba7c31397aa29

        :param xml_string:
        :return: boolean
        """
        # online validator: https://www.corefiling.com/opensource/schemaValidate.html
        # load the schema
        xsd_doc = etree.parse('../xml-validation/igsn-csiro-v2.0-all.xsd')
        xsd = etree.XMLSchema(xsd_doc)

        # load the XML doc
        xml = etree.parse(StringIO(xml_string))

        return xsd.validate(xml)

    def export_dct_xml(self):
        """
        Exports this Sample instance in XML that validates against the IGSN XML Schema

        :return: XML string
        """

        if self.date_acquired is None:
            d = ''
        else:
            d = self.date_acquired
        template = render_template(
            'class_sample_dct.xml',
            identifier=self.igsn,
            description=self.remark,
            date=d,
            type=self.sample_type,
            format=self.material_type,
            wkt=self._generate_sample_wkt(),
            creator=self.collector,
            publisher_uri=self.custodian_uri,
            publisher_label=self.custodian_label
        )

        return template

    def export_igsn_xml(self):
        """
        Exports this Sample instance in XML that validates against the IGSN XML Schema

        :return: XML string
        """

        # acquired date fudge
        if self.date_acquired is not None:
            collection_time = datetime_to_datestamp(self.date_acquired)
        else:
            collection_time = '1900-01-01T00:00:00Z'

        template = render_template(
            'class_sample_igsn.xml',
            igsn=self.igsn,
            sample_id=self.sample_id,
            description=self.remark,
            wkt=self._generate_sample_wkt(),
            sample_type=self.sample_type,
            material_type=self.material_type,
            collection_method=self.method_type,
            collection_time=collection_time,
            collector=self.collector,
            publisher_uri=self.custodian_uri,
            publisher_label=self.custodian_label
        )

        return template

    def export_igsn_r1_xml(self):
        """
        Exports this Sample instance in XML that validates against the IGSN XML Schema

        :return: XML string
        """
        template = render_template(
            'class_sample_igsn_r1.xml',
            igsn=self.igsn,
            sample_id=self.sample_id,
            description=self.remark,
            wkt=self._generate_sample_wkt(),
            sample_type=self.sample_type,
            material_type=self.material_type,
            collection_method=self.method_type_non_uri,
            collection_time=self.date_acquired,
            collector=self.collector,
            custodian_uri=self.custodian_uri,
            custodian_label=self.custodian_label
        )

        return template

    def export_csirov3_xml(self):
        """
        Exports this Sample instance in XML that validates against the CSIRO v3 Schema

        :return: XML string
        """
        # sample location in GML & WKT, formulation from GeoSPARQL
        template = render_template(
            'class_sample_csirov3.xml',
            igsn=self.igsn,
            sample_type=self.sample_type,
            material_type=self.material_type,
            method_type=self.method_type,
            wkt=self._generate_sample_wkt(),
            sample_id=self.sample_id,
            collection_time=self.date_acquired,
            collector=self.collector,
            publisher_uri=self.custodian_uri,
            publisher_label=self.custodian_label
        )

        return template

    def export_html(self, model_view='default'):
        """
        Exports this instance in HTML, according to a given model from the list of supported models.

        :param model_view: string of one of the model view names available for Sample objects ['igsn', 'dct', '',
            'default']
        :return: HTML string
        """
        if model_view == 'igsn-o':
            view_title = 'IGSN Ontology view'
            sample_table_html = render_template(
                'class_sample_igsn-o.html',
                igsn=self.igsn,
                sample_id=self.sample_id,
                description=self.remark,
                access_rights_alink=self._make_vocab_alink(self.access_rights),
                date_acquired=self.date_acquired if self.date_acquired is not None else '<a href="{}">{}</a>'.format(
                    self.URI_MISSSING, self.URI_MISSSING.split('/')[-1]),
                wkt=self._generate_sample_wkt(),
                state=self.state,
                sample_type_alink=self._make_vocab_alink(self.sample_type),
                method_type_alink=self.method_type,
                method_type_text=self.method_type_non_uri,
                material_type_alink=self._make_vocab_alink(self.material_type),
                lithology_alink=self._make_vocab_alink(self.lith),
                entity_type_alink=self._make_vocab_alink(self.entity_type),
                custodian_uri=self.custodian_uri,
                custodian_label=self.custodian_label,
                collector=self.collector
            )
        elif model_view == 'prov':
            view_title = 'PROV Ontology view'
            prov_turtle = self.export_rdf('prov', 'text/turtle')
            g = Graph().parse(data=prov_turtle, format='turtle')

            sample_table_html = render_template(
                'class_sample_prov.html',
                visjs=self._make_vsjs(g),
                prov_turtle=prov_turtle.decode('utf-8'),
            )
        else:  # elif model_view == 'dct':
            view_title = 'Dublin Core view'

            sample_table_html = render_template(
                'class_sample_dct.html',
                identifier=self.igsn,
                description=self.remark if self.remark != '' else '-',
                date=self.date_acquired if self.date_acquired is not None else '<a href="{}">{}</a>'.format(
                    self.URI_MISSSING, self.URI_MISSSING.split('/')[-1]),
                type=self.sample_type,
                format=self.material_type,
                wkt=self._generate_sample_wkt(),
                custodian_uri=self.custodian_uri,
                custodian_label=self.custodian_label,
                collector=self.collector
            )

        if self.date_acquired is not None:
            year_acquired = '({})'.format(datetime.datetime.strftime(self.date_acquired, '%Y'))
        else:
            year_acquired = ''

        # add in the Pingback header links as they are valid for all HTML views
        pingback_uri = conf.URI_SAMPLE_INSTANCE_BASE + self.igsn + "/pingback"
        headers = {
            'Link': '<{}>;rel = "http://www.w3.org/ns/prov#pingback"'.format(pingback_uri)
        }

        return Response(
            render_template(
                'page_sample.html',
                organisation_branding=TERM_LOOKUP['custodian'].get(self.custodian_uri) if TERM_LOOKUP[
                                                                                              'custodian'].get(
                    self.custodian_uri) is not None else 'ga',
                view=model_view,
                igsn=self.igsn,
                year_acquired=year_acquired,
                view_title=view_title,
                sample_table_html=sample_table_html,
                gm_key=conf.GOOGLE_MAPS_API_KEY,
                lat=self.y if self.y is not None else self.centroid_lat,
                lon=self.x if self.x is not None else self.centroid_lon,
                gmap_bbox=self._generate_sample_gmap_bbox(),
                citation=self._make_citation()
            ),
            headers=headers
        )

class ParameterError(ValueError):
    pass

if __name__ == '__main__':
    # s = Sample(None, xml='c:/work/samples-api/test/static_data/AU239.xml')
    #
    # from model.lookups import TERM_LOOKUP
    #
    # print(TERM_LOOKUP['sample_type']['unknown'])
    #
    # print(TERM_LOOKUP['method_type']['Unknown'])
    #
    # print(TERM_LOOKUP['material_type']['unknown'])
    pass
