#!/usr/bin/env python
import os
import unittest
import json
# import rdflib
from os.path import join, dirname
from rdflib.graph import Graph
from app import app

class SingleSiteViewTest(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client() 
        # collect all categories 
        response = self.client.get('/?_view=reg&_format=application/json')
        json_data = json.loads(response.data)

        self.registers = set(ele.get('uri') for ele in json_data)

        self.formats = set(['text/html', 
                            'text/turtle', 
                            'text/ntriples', 
                            'text/nt', 
                            'text/n3', 
                            'application/rdf+xml', 
                            'application/xml',
                            'application/rdf+json', 
                            'application/json', 
                            'abcdef'])


    def pickup_instance(self, register):
        response = self.client.get(register+'?_view=reg&_format=text/turtle')
        if response.status_code == 200:
            g = Graph()
            g.parse(data=response.data.decode('utf-8'), format='turtle')
            # This query shoud be changed later to allow it query instances for different site
            qres = g.query(
                    """ SELECT ?instance
                        WHERE {
                            ?instance  a <http://pid.geoscience.gov.au/def/ont/ga/pdm#Site>
                            } limit 1 
                    """)
            js_format = json.loads(qres.serialize(format="json").decode('utf-8'))
            # print(js_format)
            print ('#pickup_instance() get an instance: '+js_format.get('results').get('bindings')[0].get('instance').get('value'))
        else:
            raise Exception("call view=reg&_format=text/turtle error for register: " + register)
        return js_format.get('results').get('bindings')[0].get('instance').get('value')


    def test_instance(self):
        for register in self.registers:
            if register != '/':
                raw_instance = self.pickup_instance(register)

                instance = register+raw_instance.split('/')[-1]
                print('#test_instance() test instance: '+instance)

                with self.subTest(instance):
                    # from alternates application/json view get JSON style register views and formats info.
                    response = self.client.get(instance+'?_view=alternates&_format=application/json')

                    self.assertEqual(200, response.status_code)
                    self.assertIn('application/json', response.headers.get('Content-Type'))

                    # From response json data, get this register supported views and formats, and start test
                    if response.status_code == 200:
                        data = json.loads(response.data)
                        views = data.keys()
                        for view in views:
                            if view != 'default' and view != 'description' and view != 'alternates':
                                # print(view)
                                formats = data[view].get('mimetypes')
                                for format in formats:
                                    with self.subTest(format):
                                        # view [non-alternaties and default ] and mimetypes test for instance
                                        print('----#test_instance() Testing instance '+ instance +': view ' + view + ' with format ' + format)
                                        response = self.client.get(instance+'?_view='+view+'&_format='+format)
                                        self.assertEqual(200, response.status_code)
                                        self.assertIn(format, response.headers.get('Content-Type'))

    def test_register(self):
        for ca in self.registers:
            print('#test_register() test register : '+ ca)
            with self.subTest(ca):
                # from alternates application/json view get JSON style register views and formats info.
                response = self.client.get(ca+'?_view=alternates&_format=application/json')
                
                self.assertEqual(200, response.status_code)
                self.assertIn('application/json', response.headers.get('Content-Type'))

                # From response json data, get this register supported views and formats, and start test
                if response.status_code == 200:
                    data = json.loads(response.data)
                    views = data.keys()
                    for view in views:
                        if view != 'default' and view != 'description':
                            formats = data[view].get('mimetypes')
                            for format in formats:
                                with self.subTest(format):
                                    # View [alternates, and reg] and mimetypes test
                                    response = self.client.get(ca+'?_view='+view+'&_format='+format)
                                    print('----#test_register() Testing register '+ ca +': view ' + view + ' with format ' + format)
                                    self.assertEqual(200, response.status_code)
                                    self.assertIn(format, response.headers.get('Content-Type'))


    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main(verbosity=2)