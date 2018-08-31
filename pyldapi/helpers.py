# -*- coding: utf-8 -*-
import os
import logging
from rdflib import Graph


def setup(app, api_home_dir, api_uri):
    """
    Used to set up the Register of Registers for this LDAPI

    Must be run before app.run like this: thread = pyldapi.setup(app, conf.URI_BASE)
    :param app: the Flask app containing this LDAPI
    :type app: Flask app
    :param api_uri: URI base of the API
    :type api_uri: string
    :return: the thread executing this task
    :rtype: Thread
    """
    from threading import Thread
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
    from time import sleep
    try:
        os.remove(os.path.join(api_home_dir, 'rofr.ttl'))
    except FileNotFoundError:
        pass
    sleep(1)  # to ensure that this occurs after the Flask boot
    print('making RofR')
    g = Graph()
    # get the RDF for each Register, extract the bits we need, write them to graph g
    for rule in app.url_map.iter_rules():
        if '<' not in str(rule):  # no registers can have a Flask variable in their path
            # make the register view URI for each possible register
            candidate_register_uri = api_uri + str(rule) + '?_view=reg&_format=text/turtle'
            get_filtered_register_graph(candidate_register_uri, g)

    # serialise g
    with open(os.path.join(api_home_dir, 'rofr.ttl'), 'w') as f:
        f.write(g.serialize(format='text/turtle').decode('utf-8'))

    print('finished making RofR')


def get_filtered_register_graph(register_uri, g):
    """
    Gets a filtered version (label, comment, contained item classes & subregisters only) of the each register for the
    Register of Registers

    :param register_uri: the public URI of the register
    :type register_uri: string
    :param g: the rdf graph to append registers to
    :type g: Graph
    :return: True if ok, else False
    :rtype: boolean
    """
    import requests
    from pyldapi.exceptions import ViewsFormatsException
    assert isinstance(g, Graph)
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
                    <{0}> a reg:Register ;
                          rdfs:label ?label ;
                          rdfs:comment ?comment ;
                          reg:containedItemClass ?cic ;
                          ereg:superregister ?superregister ;
                          reg:subregister ?subregister .
                    ?superregister reg:subregister <{0}> .
                }}
                WHERE {{
                    <{0}> a reg:Register ;
                          rdfs:label ?label ;
                          rdfs:comment ?comment ;
                          reg:containedItemClass ?cic .
                    OPTIONAL {{ <{0}> ereg:superregister ?superregister . }}
                    OPTIONAL {{ <{0}> reg:subregister ?subregister . }}
                }}
            '''.format(register_uri.replace('?_view=reg&_format=text/turtle', ''))

            g += g2.query(q)
            return True
        else:
            logging.debug(
                '{} returns no RDF'.format(register_uri.replace('?_view=reg&_format=text/turtle', '')))
            return False  # no RDF (turtle) response from endpoint so not register
    logging.debug('{} returns no HTTP 200'.format(register_uri.replace('?_view=reg&_format=text/turtle', '')))
    return False  # no valid response from endpoint so not register

