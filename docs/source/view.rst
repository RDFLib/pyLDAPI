View
====

.. autoclass:: pyldapi.View
    :members: __init__

Example Usage
-------------

A dictionary of views:

.. code-block:: python

    views = {
        'csirov3': View(
            'CSIRO IGSN View',
            'An XML-only metadata schema for descriptive elements of IGSNs',
            ['text/xml'],
            'text/xml',
            namespace='https://confluence.csiro.au/display/AusIGSN/CSIRO+IGSN+IMPLEMENTATION'
        ),

        'prov': View(
            'PROV View',
            "The W3C's provenance data model, PROV",
            ["text/html", "text/turtle", "application/rdf+xml", "application/rdf+json"],
            "text/turtle",
            namespace="http://www.w3.org/ns/prov/"
        ),
    }

A dictionary of views are generally intialised in the constructor of a specialised *ClassRenderer*.
This ClassRenderer inherits from :class:`.Renderer`

.. seealso:: See :ref:`example-renderer-reference` for more information.