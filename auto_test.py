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
        # cvf = json.load(open(join(dirname(__file__), 'controller/views_formats.json')))
        # Get root register information from 'localhost/minimal/register'. 
        # collect all categories 
        response = self.client.get('/register')
        json_data = json.loads(response.data)
        self.registers = set(json_data)
        # add root register
        self.registers.add('#')

        self.instances =  self.pickup_instances()

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

    # def get_instance(self, cls):
    #     # rdf query like %s a cls limit 1
    #     response = self.client.get('/register')
    # def test_register():
    #     response = self.client.get('/register')

    def pickup_instances(self):
        for register in self.registers:
            if register == '':
                return None
            ca = register.split('#')[1].lower()

            response = self.client.get('/'+ca+'/?_view=reg&_format=text/turtle')
            print(response.data)
            # self.assertEqual(200, response.status_code)
            # self.assertIn('text/turtle', response.headers.get('Content-Type'))
            if response.status_code == 200:
                g = Graph()
                print(response.headers)
                g.parse(str(response.data), format='turtle')
                print(len(g))


    # def test_register(self):
    #     for register in self.registers:
    #         ca = register.split('#')[1].lower()
    #         print('_________'+ca+'___________')
    #         with self.subTest(ca):
    #             # from alternates application/json view get JSON style register views and formats info.
    #             if ca == '':
    #                 response = self.client.get('/?_view=alternates&_format=application/json')
    #             else:
    #                 response = self.client.get('/'+ca+'/?_view=alternates&_format=application/json')
                
    #             self.assertEqual(200, response.status_code)
    #             self.assertIn('application/json', response.headers.get('Content-Type'))

    #             # From response json data, get this register supported views and formats, and start test
    #             # print(response.data)
    #             if response.status_code == '200':
    #                 data = json.loads(response.data)
    #                 views = data.keys()
    #                 for view in views:
    #                     with self.subTest(view):
    #                         if view != 'default' != 'subreg' != 'renderer':
    #                             formats = data[view]['mimetypes']
                                
    #                             for format in formats:
    #                                 with self.subTest(format):
    #                                     if ca == '':
    #                                         response = self.client.get('/?_view='+view+'&_format='+format)
    #                                     else:
    #                                         response = self.client.get('/'+ca+'/?_view='+view+'&_format='+format)
    #                                     print('Testing register '+ ca +': view ' + view + 'with format ' + format)
    #                                     self.assertEqual(200, response.status_code)
    #                                     self.assertIn(format, response.headers.get('Content-Type'))


    # def test_instance(self):
    #     for register in self.registers:
    #         if register == '':
    #             return None
    #         ca = register.split('#')[1].lower()
    #         with self.subTest(ca):
    #             # from alternates application/json view get JSON style register views and formats info.
    #             response = self.client.get('/'+ca+'/?_view=pdm&_format=text/turtle')
                
    #             self.assertEqual(200, response.status_code)
    #             self.assertIn('text/turtle', response.headers.get('Content-Type'))
    #             # pick up one instances for following test

    #             # From response json data, get this register supported views and formats, and start test
    #             if response.status_code == '200':
    #                 data = json.loads(response.data)
    #                 views = data.keys()
    #                 for view in views:
    #                     with self.subTest(view):
    #                         if view != 'default' != 'subreg' != 'renderer':
    #                             formats = data[view]['mimetypes']
                                
    #                             for format in formats:
    #                                 with self.subTest(format):
    #                                     if ca == '':
    #                                         response = self.client.get('/?_view='+view+'&_format='+format)
    #                                     else:
    #                                         response = self.client.get('/'+ca+'/?_view='+view+'&_format='+format)
    #                                     print('Testing register '+ ca +': view ' + view + 'with format ' + format)
    #                                     self.assertEqual(200, response.status_code)
    #                                     self.assertIn(format, response.headers.get('Content-Type'))



    # def class_test(self, cls, random_instance):
    #     for key in reg.keys:
    #         if key != 'renderer' != 'default':
    #             # Process views
    #             view = key
    #             mimetypes = reg.get(key).get('mimetypes')
    #             for format in mimetypes:
    #                 response = self.client.get()
    #     pass
    def tearDown(self):
        pass

    def test_nothing(self):
        pass
    # Test unvalid site no
    # def test_unvalid_site_no_view(self):

if __name__ == '__main__':
    unittest.main(verbosity=2)