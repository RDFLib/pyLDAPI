# -*- coding: utf-8 -*-
import os
import logging

from jinja2 import TemplateNotFound
from rdflib import Graph

from pyldapi.exceptions import RegOfRegTtlError


def setup(app, api_home_dir, api_uri):
    """
    This is used to set up the :class:`.RegisterOfRegistersRenderer` for this pyLDAPI instance.

    .. note:: This must run before Flask's :func:`app.run` like this: :code:`pyldapi.setup(app, '.', conf.URI_BASE)`. See the example below.

    :param app: The Flask app containing this pyLDAPI instance.
    :type app: :class:`flask.request`
    :param api_uri: The URI base of the API.
    :type api_uri: str
    :return: None
    :rtype: None
    """
    return _make_rofr_rdf(app, api_home_dir, api_uri)


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
    from pyldapi import RegisterRenderer, RegisterOfRegistersRenderer
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
            try:
                endpoint_func = app.view_functions[rule.endpoint]
            except (AttributeError, KeyError):
                continue
            candidate_register_uri = api_uri + str(rule)
            try:
                dummy_request_uri = "http://localhost:5000" + str(
                    rule) + '?_view=reg&_format=_internal'
                test_context = app.test_request_context(dummy_request_uri)
                with test_context:
                    resp = endpoint_func()
            except RegOfRegTtlError:  # usually an RofR renderer cannot find its rofr.ttl.
                continue
            except Exception as e:
                raise e
            if isinstance(resp, RegisterOfRegistersRenderer):
                continue  # forbid adding a register of registers to a register of registers.
            if isinstance(resp, RegisterRenderer):
                with test_context:
                    try:
                        resp.format = 'text/html'
                        html_resp = resp._render_reg_view_html()
                    except TemplateNotFound:  # missing html template
                        pass  # TODO: Fail on this error
                    resp.format = 'application/json'
                    json_resp = resp._render_reg_view_json()
                    resp.format = 'text/turtle'
                    rdf_resp = resp._render_reg_view_rdf()

                _filter_register_graph(candidate_register_uri, rdf_resp, g)

    # serialise g
    with open(os.path.join(api_home_dir, 'rofr.ttl'), 'w') as f:
        f.write(g.serialize(format='text/turtle').decode('utf-8'))

    print('finished making RofR')


def _filter_register_graph(register_uri, r, g):
    if 'text/turtle' in r.headers.get('Content-Type'):
        logging.debug('{} is a register '.format(register_uri))
        # it is a valid endpoint returning RDF (turtle) so...
        # import all its content into the in-memory graph
        g2 = Graph().parse(data=r.data.decode('utf-8'), format='text/turtle')
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
        '''.format(register_uri)

        g += g2.query(q)
        return True
    else:
        logging.debug(
            '{} returns no RDF'.format(register_uri))
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
#     logging.debug('assessing register candidate ' + register_uri.replace('?_view=reg&_format=text/turtle', ''))
#     try:
#         r = requests.get(register_uri)
#         print('getting ' + register_uri)
#     except ViewsFormatsException as e:
#         return False  # ignore these exceptions as are just a result of requesting a view/format combo of something like a page
#     if r.status_code == 200:
#         return _filter_register_graph(register_uri.replace('?_view=reg&_format=text/turtle', ''), r, g)
#     logging.debug('{} returns no HTTP 200'.format(register_uri))
#     return False  # no valid response from endpoint so not register

