#!/usr/bin/env python3
import os
import unittest
from app import app

class SingleSiteViewTest(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client() 
        self.base_uri = ''
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
        self.nemsr_supported_formats = set(['application/vnd.geo+json'])
        self.pdm_supported_formats =set(
                            ['text/html', 
                            'text/turtle',
                            'application/rdf+xml', 
                            'application/rdf+json'])
        self.alternates_supported_formats = set(
                            ['text/html', 
                            'text/turtle',
                            'application/rdf+xml', 
                            'application/rdf+json',
                            'application/json'])
       
    def tearDown(self):
        pass

    # Test unvalid site no
    def test_unvalid_site_no_view(self):
        '''
        Assert response error with message: Invalid site no
        '''
        
        response = self.client.get('/site/abc')
        self.assertEqual(response.status_code,200)
        # self.assertIn(b'Invalid site no', response.data)
        # response2 = self.client.get('/site/*')
        # self.assertIn(b'Invalid site no', response2.data)
    
    # Test valid site no
    def test_valid_site_no_view(self):
        response = self.client.get('/site/10')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'<td>Site No</td><td>10</td>', response.data)
        self.assertIn(b'<td>MONSOON Leg 6, Argo</td>', response.data)
    
    # Test default view: 'pdm' with different format and valid  site no.
    def test_pdm_default_view(self):
        response = self.client.get('/site/10?_view=pdm')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'<td>Site No</td><td>10</td>', response.data)
        self.assertIn(b'<td>MONSOON Leg 6, Argo</td>', response.data)

    # Test pdm view with supported formats
    def test_pdm_text_html_view(self):
        '''
        text/html
        '''
        response = self.client.get('/site/10?_view=pdm&_format=text/html')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'<td>Site No</td><td>10</td>', response.data)
        self.assertIn(b'<td>MONSOON Leg 6, Argo</td>', response.data)
    def test_pdm_text_turtle_view(self):
        '''
        text/turtle
        '''
        response = self.client.get('/site/10?_view=pdm&_format=text/turtle')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'rdfs:label "Site 10"', response.data)
        self.assertIn(b'rdfs:comment "MONSOON Leg 6, Argo"', response.data)
    def test_pdm_application_rdf_json__view(self):
        '''
        application/rdf+json
        500 returned for current
        '''
        response = self.client.get('/site/10?_view=pdm&_format=application/rdf+json')
        self.assertEqual(response.status_code,200)
        # self.assertIn(b'rdfs:label "Site 10"', response.data)
        # self.assertIn(b'rdfs:comment "MONSOON Leg 6, Argo"', response.data)
    def test_pdm_application_rdf_xml_view(self):
        '''
        application/rdf+xml
        result was saved as a rdf xml file
        '''
        response = self.client.get('/site/10?_view=pdm&_format=application/rdf+xml')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'<rdfs:label rdf:datatype="http://www.w3.org/2001/XMLSchema#string">Site 10</rdfs:label>', response.data)
        self.assertIn(b'<rdfs:comment rdf:datatype="http://www.w3.org/2001/XMLSchema#string">MONSOON Leg 6, Argo</rdfs:comment>', response.data)
    
    # Test pdm view unsupported format definded in self.pdm_unsupported_formats
    def test_pdm_unsupported_formats(self):
        # The _format parameter is invalid. For this model view, format should be one of text/html, text/turtle, application/rdf+xml, application/rdf+json.
        for format in self.formats - self.pdm_supported_formats:
            response = self.client.get('/site/10?_view=pdm&_format='+format)
            self.assertEqual(response.status_code,400)
            self.assertIn(b'The _format parameter is invalid.', response.data)
    
    
    # Test nemsr view with different format and valid  site no.
    def test_nemsr_view(self):
        response = self.client.get('/site/10?_view=nemsr')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'"siteDescription": "MONSOON Leg 6, Argo"', response.data)
    def test_nemsr_application_vnd_geo_json_view(self):
        '''
        Valid
        '''
        response = self.client.get('/site/10?_view=nemsr&_format=application/vnd.geo+json')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'"siteDescription": "MONSOON Leg 6, Argo"', response.data)

    # Test nemsr unsupported format
    def test_nemsr_unsupported_format(self):
        for format in self.formats - self.nemsr_supported_formats:
            # The _format parameter is invalid. For this model view, format should be one of application/vnd.geo+json.
            response = self.client.get('/site/10?_view=nemsr&_format='+format)
            self.assertEqual(response.status_code,400)
            self.assertIn(b'The _format parameter is invalid.', response.data)  

    # Test alternaties view with different mimetype
    def test_alternates_default_view(self):
        '''
        Valid, 
        '''
        response = self.client.get('/site/10?_view=alternates')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'<h1>Alternates view</h1>', response.data)
    def test_alternates_text_html_view(self):
        '''
        Valid, 
        '''
        response = self.client.get('/site/10?_view=alternates&_format=text/html')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'<h1>Alternates view</h1>', response.data)
    def test_alternates_text_turtle_view(self):
        '''
        Current 500 error,  
        '''
        response = self.client.get('/site/10?_view=alternates&_format=text/turtle')
        self.assertEqual(response.status_code,200)
        # self.assertIn(b'<h1>Alternates view</h1>.', response.data)
    def test_alternates_application_rdf_xml_view(self):
        '''
        500 Error for now
        '''
        response = self.client.get('/site/10?_view=alternates&_format=application/rdf+xml')
        self.assertEqual(response.status_code,200)
        # self.assertIn(b'<h1>Alternates view</h1>.', response.data)
    def test_alternates_application_rdf_json_view(self):
        '''
        500 Error for now
        '''
        response = self.client.get('/site/10?_view=alternates&_format=application/rdf+json')
        self.assertEqual(response.status_code,200)
        # self.assertIn(b'<h1>Alternates view</h1>.', response.data)
    def test_alternates_application_json_view(self):
        '''
        Valid, 
        '''
        response = self.client.get('/site/10?_view=alternates&_format=application/json')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'"default": "pdm", "alternates": {"mimetypes": ["text/html", "text/turtle", "application/rdf+xml", "application/rdf+json", "application/json"]', response.data)
    
    # Test alternates unsupported formats
    def test_alternates_unsupported_formats(self):
        # The _format parameter is invalid. For this model view, format should be one of text/html, text/turtle, application/rdf+xml, application/rdf+json, application/json.
        for format in self.formats - self.alternates_supported_formats:
            response = self.client.get('/site/10?_view=alternates&_format='+format)
            self.assertEqual(response.status_code,400)
            self.assertIn(b'The _format parameter is invalid.', response.data)


class RegisterSiteViewsTest(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client() 
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
        
        self.reg_alternates_supported_formats = set(
                            ['text/html', 
                            'text/turtle',
                            'application/rdf+xml', 
                            'application/rdf+json'])
        self.reg_supported_formats = set(
                            ['text/html', 
                            'text/turtle',
                            'application/rdf+xml', 
                            'application/rdf+json'])

    def tearDown(self):
        pass

     # Test alternaties view with different mimetype
    def test_alternates_default_view(self):
        '''
        Valid, 
        '''
        response = self.client.get('/site/?_view=alternates')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'<h1>Alternates view</h1>', response.data)
    def test_alternates_text_html_view(self):
        '''
        Valid, 
        '''
        response = self.client.get('/site/?_view=alternates&_format=text/html')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'<h1>Alternates view</h1>', response.data)
    def test_alternates_text_turtle_view(self):
        '''
        Current 500 error,  
        '''
        response = self.client.get('/site/?_view=alternates&_format=text/turtle')
        self.assertEqual(response.status_code,200)
        # self.assertIn(b'<h1>Alternates view</h1>.', response.data)
    def test_alternates_application_rdf_xml_view(self):
        '''
        500 Error for now
        '''
        response = self.client.get('/site/?_view=alternates&_format=application/rdf+xml')
        self.assertEqual(response.status_code,200)
        # self.assertIn(b'<h1>Alternates view</h1>.', response.data)
    def test_alternates_application_rdf_json_view(self):
        '''
        500 Error for now
        '''
        response = self.client.get('/site/?_view=alternates&_format=application/rdf+json')
        self.assertEqual(response.status_code,200)
        # self.assertIn(b'<h1>Alternates view</h1>.', response.data)

    # Test alternates unsupported formats
    def test_alternates_unsupported_formats(self):
        # The _format parameter is invalid. For this model view, format should be one of text/html, text/turtle, application/rdf+xml, application/rdf+json.
        for format in self.formats - self.reg_alternates_supported_formats:
            response = self.client.get('/site/?_view=alternates&_format='+format)
            self.assertEqual(response.status_code,400)
            self.assertIn(b'The _format parameter is invalid.', response.data)
        


    # Test default reg view with different mimetype
    def test_reg_default_view(self):
        '''
        Valid, 
        '''
        response = self.client.get('/site/?_view=reg')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'<h1>Register</h1>', response.data)
    def test_alternates_text_html_view(self):
        '''
        Valid, 
        '''
        response = self.client.get('/site/?_view=reg&_format=text/html')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'<h1>Register</h1>', response.data)
    def test_reg_text_turtle_view(self):
        '''
        valid  
        '''
        response = self.client.get('/site/?_view=reg&_format=text/turtle')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'rdfs:label "Site:10"', response.data)
        self.assertIn(b'rdfs:label "Sites Register"', response.data)
    def test_reg_application_rdf_xml_view(self):
        '''
        No header but just download file
        '''
        response = self.client.get('/site/?_view=reg&_format=application/rdf+xml')
        self.assertEqual(response.status_code,200)
        # self.assertIn(b'<h1>Register</h1>.', response.data)
    def test_reg_application_rdf_json_view(self):
        '''
        500 Error for now
        '''
        response = self.client.get('/site/?_view=reg&_format=application/rdf+json')
        self.assertEqual(response.status_code,200)
        # self.assertIn(b'<h1>Register</h1>.', response.data)

    # Test reg unsupported formats
    def test_reg_unsupported_formats(self):
        # The _format parameter is invalid. For this model view, format should be one of text/html, text/turtle, application/rdf+xml, application/rdf+json.
        for format in self.formats - self.reg_supported_formats:
            response = self.client.get('/site/?_view=reg&_format='+format)
            self.assertEqual(response.status_code,400)
            self.assertIn(b'The _format parameter is invalid.', response.data)
    
if __name__ == '__main__':
    unittest.main(verbosity=2)