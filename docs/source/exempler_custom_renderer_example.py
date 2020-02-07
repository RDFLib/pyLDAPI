from flask import Response, render_template
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, URIRef, Namespace, RDF, RDFS, XSD, OWL, Literal
from pyldapi import Renderer, Profile
import _conf as conf


class MediaTypeRenderer(Renderer):
    def __init__(self, request, instance_uri):
        profiles = {
            'mt': Profile(
                'Mediatype View',
                'Basic properties of a Media Type, as recorded by IANA',
                ['text/html'] + Renderer.RDF_MEDIA_TYPES,
                'text/turtle',
                languages=['en', 'pl'],
                uri='http://test.linked.data.gov.au/def/mt#'
            )
        }
        super(MediaTypeRenderer, self).__init__(
            request,
            instance_uri,
            profiles,
            'mt'
        )

    def render(self):
        if hasattr(self, 'vf_error'):
            return Response(self.vf_error, status=406, mimetype='text/plain')
        else:
            if self.profile == 'alternates':
                return self._render_alternates_profile()
            elif self.profile == 'mt':
                if self.format in Renderer.RDF_MEDIA_TYPES:
                    rdf = self._get_instance_rdf()
                    if rdf is None:
                        return Response('No triples contain that URI as subject', status=404, mimetype='text/plain')
                    else:
                        return Response(rdf, mimetype=self.format)
                else:  # only the HTML format left
                    deets = self._get_instance_details()
                    if deets is None:
                        return Response('That URI yielded no data', status=404, mimetype='text/plain')
                    else:
                        mediatype = self.instance_uri.replace('%2B', '+').replace('%2F', '/').split('/mediatype/')[1]
                        if self.language == 'pl':
                            return render_template(
                                'mediatype-pl.html',
                                deets=deets,
                                mediatype=mediatype
                            )
                        else:
                            return render_template(
                                'mediatype-en.html',
                                deets=deets,
                                mediatype=mediatype
                            )

    def _get_instance_details(self):
        sparql = SPARQLWrapper(conf.SPARQL_QUERY_URI, returnFormat=JSON)
        q = '''
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX dct:  <http://purl.org/dc/terms/>
            SELECT *
            WHERE {{
                <{0[uri]}>  rdfs:label ?label .
                OPTIONAL {{ <{0[uri]}> dct:contributor ?contributor . }}
            }}
        '''.format({'uri': self.instance_uri})
        sparql.setQuery(q)
        d = sparql.query().convert()
        d = d.get('results').get('bindings')
        if d is None or len(d) < 1:  # handle no result
            return None

        label = ''
        contributors = []
        for r in d:
            label = str(r.get('label').get('value'))
            contributors.append(str(r.get('contributor').get('value')))

        return {
            'label': label,
            'contributors': contributors
        }

    def _get_instance_rdf(self):
        deets = self._get_instance_details()

        g = Graph()
        DCT = Namespace('http://purl.org/dc/terms/')
        g.bind('dct', DCT)
        me = URIRef(self.instance_uri)
        g.add((me, RDF.type, DCT.FileFormat))
        g.add((
            me,
            OWL.sameAs,
            URIRef(self.instance_uri.replace('https://w3id.org/mediatype/', 'https://www.iana.org/assignments/media-types/'))
        ))
        g.add((me, RDFS.label, Literal(deets.get('label'), datatype=XSD.string)))
        source = 'https://www.iana.org/assignments/media-types/' + self.instance_uri.replace('%2B', '+').replace('%2F', '/').split('/mediatype/')[1]
        g.add((me, DCT.source, URIRef(source)))
        if deets.get('contributors') is not None:
            for contributor in deets.get('contributors'):
                g.add((me, DCT.contributor, URIRef(contributor)))

        if self.format in ['application/rdf+json', 'application/json']:
            return g.serialize(format='json-ld')
        else:
            return g.serialize(format=self.format)
