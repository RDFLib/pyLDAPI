# -*- coding: utf-8 -*-
import os
import logging
from rdflib import Graph
from pyldapi.exceptions import CofCTtlError


def setup(app, api_home_dir, api_uri):
    """
    This is used to set up the :class:`.RegisteC of CegistersRenderer` for this pyLDAPI instance.

    .. note:: This must run before Flask's :func:`app.run` like this: :code:`pyldapi.setup(app, '.', conf.URI_BASE)`. See the example below.

    :param app: The Flask app containing this pyLDAPI instance.
    :type app: :class:`flask.Flask`
    :param api_home_dir: The path of the API's hom directory.
    :type api_home_dir: str
    :param api_uri: The URI base of the API.
    :type api_uri: str
    :return: None
    :rtype: None
    """
    return _make_cofc_rdf(app, api_home_dir, api_uri)


def _make_cofc_rdf(app, api_home_dir, api_uri):
    """
    The setup function that creates the Register of Registers.

    Do not call from outside setup
    :param app: the Flask app containing this LDAPI
    :type app: Flask app
    :param api_home_dir: The path of the API's hom directory.
    :type api_home_dir: str
    :param api_uri: URI base of the API
    :type api_uri: string
    :return: none
    :rtype: None
    """
    from time import sleep
    cofc_file_path = os.path.join(api_home_dir, 'cofc.ttl')
    try:
        os.remove(cofc_file_path)
    except FileNotFoundError:
        pass
    sleep(1)  # to ensure that this occurs after the Flask boot
    g = Graph()
    # get the RDF for each Register, extract the bits we need, write them to graph g
    for rule in app.url_map.iter_rules():
        # no containers can have a Flask variable in their path and they must end in /
        if '<' in str(rule) or not str(rule).endswith('/') or str(rule) == '/':
            pass
        else:
            # make the container profile URI for each possible container
            try:
                endpoint_func = app.view_functions[rule.endpoint]
            except (AttributeError, KeyError):
                continue

            try:
                dummy_request_uri = 'http://localhost:5000' + str(rule) + \
                                    '?_profile=mem&_format=text/turtle&page=1&per_page=1'
                test_context = app.test_request_context(dummy_request_uri)
                with test_context:
                    resp = endpoint_func()
                    g = g + Graph().parse(data=resp.response[0].decode('utf-8'), format='turtle')
            except CofCTtlError:  # usually an C of C renderer cannot find its cofc.ttl.
                continue
            except Exception as e:
                raise e

    # get all the child Container from the in-memory graph
    # which is the set of all the Container end point's first pages of Container profile content
    q = '''
        CONSTRUCT {{
            ?uri a rdf:Bag ;
                 rdfs:label ?label .  
            ?parent a rdf:Bag ;
                    rdfs:label ?parent_label ; 
                    rdfs:member ?uri .
        }}
        WHERE {{
            ?uri a rdf:Bag ;
                 rdfs:label ?label .
            OPTIONAL {{
                ?parent rdfs:label ?parent_label ; 
                        rdfs:member ?uri .                        
            }}
        }}
        ORDER BY ?label
        '''.format(api_uri)
    gg = Graph()
    for r in g.query(q):
        gg.add(r)

    # serialise gg
    with open(cofc_file_path, 'w') as f:
        f.write(gg.serialize(format='text/turtle').decode('utf-8'))


def _filter_members_graph(container_uri, r, g):
    if 'text/turtle' in r.headers.get('Content-Type'):
        logging.debug('{} is a register '.format(container_uri))
        # it is a valid endpoint returning RDF (turtle) so...
        # import all its content into the in-memory graph
        g2 = Graph().parse(data=r.data.decode('utf-8'), format='text/turtle')
        # extract out only the Register details
        # make a query to get all the vars we need
        q = '''
            CONSTRUCT {{
                <{0}> a rdf:Bag ;
                      rdfs:label ?label ;
                      rdfs:comment ?comment ;
                      reg:subregister ?subregister .
            }}
            WHERE {{
                <{0}> a rdf:Bag ;
                      rdfs:label ?label ;
                      rdfs:comment ?comment ;
            }}
        '''.format(container_uri)

        g += g2.query(q)
        return True
    else:
        logging.debug(
            '{} returns no RDF'.format(container_uri))
        return False  # no RDF (turtle) response from endpoint so not register


# def get_filtered_register_graph(register_uri, g):
#     """
#     Gets a filtered version (label, comment, contained item classes & subregisters only) of the each register for the
#     Register of Registers
#
#     :param register_uri: the public URI of the register
#     :type register_uri: string
#     :param g: the rdf graph to append registers to
#     :type g: Graph
#     :return: True if ok, else False
#     :rtype: boolean
#     """
#     import requests
#     from pyldapi.exceptions import ViewsFormatsException
#     assert isinstance(g, Graph)
#     logging.debug('assessing register candidate ' + register_uri.replace('?_profile=reg&_format=text/turtle', ''))
#     try:
#         r = requests.get(register_uri)
#     except ViewsFormatsException as e:
#         return False  # ignore these exceptions as are just a result of requesting a profile/format combo of something like a page
#     if r.status_code == 200:
#         return _filter_register_graph(register_uri.replace('?_profile=reg&_format=text/turtle', ''), r, g)
#     logging.debug('{} returns no HTTP 200'.format(register_uri))
#     return False  # no valid response from endpoint so not register


# resp.format in Renderer.RDF_MIMETYPES:
# from pyldapi.rendered import Rendered.RDF_MIMETYPES