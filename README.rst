Welcome to pyLDAPI
==================

The Python Linked Data API (pyLDAPI) is:

*A very small module to add Linked Data API functionality to a Python Flask installation*.

|PyPI version|

.. |PyPI version| image:: https://badge.fury.io/py/pyldapi.svg
    :target: https://badge.fury.io/py/pyldapi

What is it?
-----------

This module contains only a small Python module which is intended to be added (imported) into a `Python Flask`_ installation in order to add a series of extra functions to endpoints to the ones defined by you as a Flask user (URL routes).

.. _Python Flask: http://flask.pocoo.org/

An API using this module will get:

* an *alternates view* for each *Register* and *Object* that the API delivers
   * if the API declares the appropriate *model views* for each item
* a *Register of Registers*
   * a start-up function that auto-generates a Register of Registers is run when the API is launched.
* a basic, over-writeable template for Registers' HTML & RDF

The main parts of pyLDAPI are as follows:

|blocks|

.. |blocks| image:: images/blocks.png
    :width: 250
    :alt: Block diagram of pyLDAPI's main parts

Web requests arrive at a Web Server, such as *Apache* or *nginx*, which then forwards (some of) them on to *Flask*, a Python web framework. Flask calls Python functions for web requests defined in a request/function mapping and may call pyLDAPI elements. Flask need not call pyLDAPI for all requests, just as Apache/nginx need not forward all web request to flask. pyLDAPI may then draw on any Python data source, such as database APIs, and uses the *rdflib* Python module to formulate RDF responses.


Definitions
-----------

Alternates View
~~~~~~~~~~~~~~~
The *model view* that lists all other views. This API uses the definition of *alternates view* presented at `https://promsns.org/def/alt`_.

.. _https://promsns.org/def/alt: https://promsns.org/def/alt

Linked Data Principles
~~~~~~~~~~~~~~~~~~~~~~
The principles of making things available over the internet in both human and machine-readable forms. Codified by the World Wide Web Consortium. See `https://www.w3.org/standards/semanticweb/data`_.

.. _https://www.w3.org/standards/semanticweb/data: https://www.w3.org/standards/semanticweb/data


Model View
~~~~~~~~~~
A set of properties of a Linked Data object codified according to a standard or profile of a standard.

Object
~~~~~~
Any individual thing delivered according to *Linked Data* principles.

Register
~~~~~~~~
A simple listing of URIs of objects, delivered according to *Linked Data principles*.

Register of Registers
~~~~~~~~~~~~~~~~~~~~~
A *register* that lists all other registers which this API provides.



pyLDAPI in action
-----------------

* Register of Media Types
   * `https://w3id.org/mediatype/`_

.. _https://w3id.org/mediatype/: https://w3id.org/mediatype/

* Linked Data version of the Geocoded National Address File
   * `http://linked.data.gov.au/dataset/gnaf`_

.. _http://linked.data.gov.au/dataset/gnaf: http://linked.data.gov.au/dataset/gnaf

|gnaf|

Parts of the GNAF implementation

.. |gnaf| image:: images/instance-gnaf.png
    :width: 250
    :alt: Block diagram of the GNAF implementation

* Geoscience Australia's Sites, Samples Surveys Linked Data API
   * `http://pid.geoscience.gov.au/sample/`_

.. _http://pid.geoscience.gov.au/sample/: http://pid.geoscience.gov.au/sample/

* Linked Data version of the Australian Statistical Geography Standard product
   * `http://linked.data.gov.au/dataset/asgs`_

.. _http://linked.data.gov.au/dataset/asgs: http://linked.data.gov.au/dataset/asgs

|asgs|

Parts of the ASGS implementation

.. |asgs| image:: images/instance-gnaf.png
    :width: 250
    :alt: Block diagram of the GNAF implementation

Documentation
-------------

Detailed documentation can be found at `https://pyldapi.readthedocs.io/`_

.. _https://pyldapi.readthedocs.io/: https://pyldapi.readthedocs.io/



Licence
-------

This is licensed under GNU General Public License (GPL) v3.0. See the `LICENSE deed`_ for more details.

.. _LICENSE deed: https://raw.githubusercontent.com/RDFLib/pyLDAPI/master/LICENSE



Contact
-------

Dr Nicholas Car (lead)
~~~~~~~~~~~~~~~~~~~~~~
| *Data Systems Architect*
| `SURROUND Australia Pty Ltd`_
| `nicholas.car@surroundaustralia.com`_
| `https://orcid.org/0000-0002-8742-7730`_

.. _SURROUND Australia Pty Ltd: https://surroundaustralia.com
.. _nicholas.car@surroundaustralia.com: nicholas.car@surroundaustralia.com
.. _https://orcid.org/0000-0002-8742-7730: https://orcid.org/0000-0002-8742-7730

Ashley Sommer (senior developer)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
| *Informatics Software Engineer*
| `CSIRO Land and Water`_
| `ashley.sommer@csiro.au`_

.. _ashley.sommer@csiro.au: ashley.sommer@csiro.au

.. _CSIRO Land and Water: https://www.csiro.au/en/Research/LWF


Related work
------------

`pyLDAPI Client`_

* *A Simple helper library for consuming registers, indexes, and instances of classes exposed via a pyLDAPI endpoint.*

.. _pyLDAPI Client: http://pyldapi-client.readthedocs.io/
