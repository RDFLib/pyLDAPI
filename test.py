#!/usr/bin/env python
import os
import unittest
import json
# import rdflib
from os.path import join, dirname
from rdflib.graph import Graph
from app import app
import requests

def test():
    for register in ['http://pid.geoscience.gov.au/def/ont/ga/pdm#Site']:
        if register == '#':
            return None
        ca = register.split('#')[1].lower()

        response = requests.get('http://localhost:5000/'+ca+'/?_view=reg&_format=text/turtle')
        # print(response.data)
       
        if response.status_code == 200:
            g = Graph()
            g.parse((response.text), format='turtle')
            qres = g.query(
                    """ SELECT ?instance
                    WHERE {
                    ?instance  a <"""+register+""">
                    } limit 1 """)
            print (qres.serialize(format="json"))

if __name__=="__main__":
    test()