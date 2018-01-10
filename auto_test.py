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
        response = self.client.get('/register')
        json_data = json.loads(response.data)
        self.registers = set(json_data)
        # add root register
        self.registers.add('#')

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
        ca = register.split('#')[1].lower()

        response = self.client.get('/'+ca+'/?_view=reg&_format=text/turtle')
        if response.status_code == 200:
            g = Graph()
            g.parse(data=response.data.decode('utf-8'), format='turtle')
            qres = g.query(
                    """ SELECT ?instance
                        WHERE {
                            ?instance  a <"""+register+""">
                            } limit 1 
                    """)
            js_format = json.loads(qres.serialize(format="json").decode('utf-8'))
            print ('#pick_instance() get an instance: '+js_format.get('results').get('bindings')[0].get('instance').get('value'))
        return js_format.get('results').get('bindings')[0].get('instance').get('value')


    def test_instances(self):
        for register in self.registers:
            if register == '#':
                return None
            long_instance = self.pickup_instance(register)
            instance = '/'+'/'.join(long_instance.split("/")[3:])
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
                        if view != 'default' != 'subreg' != 'renderer':
                            formats = data[view]['mimetypes']
                            for format in formats:
                                with self.subTest(format):
                                    print('----#test_instance() Testing instance '+ instance +': view ' + view + ' with format ' + format)
                                    response = self.client.get(instance+'?_view='+view+'&_format='+format)
                                    self.assertEqual(200, response.status_code)
                                    self.assertIn(format, response.headers.get('Content-Type'))

    def test_register(self):
        for register in self.registers:
            ca = register.split('#')[1].lower()
            print('#test_register() test register : '+ ca)
            with self.subTest(ca):
                # from alternates application/json view get JSON style register views and formats info.
                if ca == '':
                    response = self.client.get('/?_view=alternates&_format=application/json')
                else:
                    response = self.client.get('/'+ca+'/?_view=alternates&_format=application/json')
                
                self.assertEqual(200, response.status_code)
                self.assertIn('application/json', response.headers.get('Content-Type'))

                # From response json data, get this register supported views and formats, and start test
                if response.status_code == 200:
                    data = json.loads(response.data)
                    views = data.keys()
                    for view in views:
                        if view != 'default' != 'subreg' != 'renderer':
                            formats = data[view]['mimetypes']
                            for format in formats:
                                with self.subTest(format):
                                    if ca == '':
                                        response = self.client.get('/?_view='+view+'&_format='+format)
                                    else:
                                        response = self.client.get('/'+ca+'/?_view='+view+'&_format='+format)
                                    print('----#test_register() Testing register '+ ca +': view ' + view + ' with format ' + format)
                                    self.assertEqual(200, response.status_code)
                                    self.assertIn(format, response.headers.get('Content-Type'))


    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main(verbosity=2)