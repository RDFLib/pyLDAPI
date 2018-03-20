"""
A list of functions for use anywhere but particularly in routes.py
"""
from flask import Response, render_template
from _ldapi.__init__ import LDAPI
from rdflib import Graph, Namespace, Literal, URIRef, RDF, XSD, BNode, plugin
import json
import urllib.parse as uparse


def client_error_response(error_message):
    return Response(
        str(error_message),
        status=400,
        mimetype='text/plain'
    )


def render_alternates_view(class_uri, class_uri_encoded, instance_uri, instance_uri_encoded, views_formats, mimetype):
    """Renders an HTML table, a JSON object string or a serialised RDF representation of the alternate views of an
    object"""
    if mimetype == 'application/json':
        return Response(json.dumps(views_formats), status=200, mimetype='application/json')
    elif mimetype in LDAPI.get_rdf_mimetypes_list():
        g = Graph()
        LDAPI_O = Namespace('http://promsns.org/def/_ldapi#')
        g.bind('_ldapi', LDAPI_O)
        DCT = Namespace('http://purl.org/dc/terms/')
        g.bind('dct', DCT)

        class_uri_ref = URIRef(uparse.unquote_plus(class_uri))

        if instance_uri:
            instance_uri_ref = URIRef(instance_uri)
            g.add((instance_uri_ref, RDF.type, class_uri_ref))
        else:
            g.add((class_uri_ref, RDF.type, LDAPI_O.ApiResource))

        # alternates model
        alternates_view = BNode()
        g.add((alternates_view, RDF.type, LDAPI_O.View))
        g.add((alternates_view, DCT.title, Literal('alternates', datatype=XSD.string)))
        g.add((class_uri_ref, LDAPI_O.view, alternates_view))

        # default model
        default_view = BNode()
        g.add((default_view, DCT.title, Literal('default', datatype=XSD.string)))
        g.add((class_uri_ref, LDAPI_O.defaultView, default_view))
        default_title = views_formats['default']

        # the ApiResource is incorrectly assigned to the class URI
        for view_name in views_formats.keys():
            formats = views_formats.get(view_name)
            if view_name == 'alternates':
                for f in formats:
                    g.add((alternates_view, URIRef('http://purl.org/dc/terms/format'), Literal(f, datatype=XSD.string)))
            elif view_name == 'default':
                pass
            elif view_name == 'renderer':
                pass
            else:
                x = BNode()
                if view_name == default_title:
                    g.add((default_view, RDF.type, x))
                g.add((class_uri_ref, LDAPI_O.view, x))
                g.add((x, DCT.title, Literal(view_name, datatype=XSD.string)))
                for f in formats:
                    g.add((x, URIRef('http://purl.org/dc/terms/format'), Literal(f, datatype=XSD.string)))

        # make the static part of the graph
        # REG = Namespace('http://purl.org/linked-data/registry#')
        # self.g.bind('reg', REG)
        #
        # self.g.add((URIRef(self.request.url), RDF.type, REG.Register))
        #
        # # add all the items
        # for item in self.register:
        #     self.g.add((URIRef(item['uri']), RDF.type, URIRef(self.uri)))
        #     self.g.add((URIRef(item['uri']), RDFS.label, Literal(item['label'], datatype=XSD.string)))
        #     self.g.add((URIRef(item['uri']), REG.register, URIRef(self.request.url)))
        rdflib_format = [item[1] for item in LDAPI.MIMETYPES_PARSERS if item[0] == mimetype][0]
        return Response(g.serialize(format=rdflib_format), status=200, mimetype=mimetype)
    else:  # HTML
        return render_template(
            'alternates.html',
            class_uri=class_uri,
            class_uri_encoded=class_uri_encoded,
            instance_uri=instance_uri,
            instance_uri_encoded=instance_uri_encoded,
            views_formats=views_formats
        )
