.. _`demo-jinja-templates`:

Download Jinja Templates
========================

This page contains a few general templates that are likely to be used in a pyLDAPI instance. They are provided to ease the initial development efforts with pyLDAPI.

All Jinja2 templates should use the Jinja2 :code:`extends` keyword to extend the generic :code:`page.html` to reduce duplicated HTML code.

Page
----

This template contains the persistent HTML code like the product's logo, the navigation bar and the footer. All other persistent things should go in this template.

:download:`page.html <download_templates/page.html>`


Index
-----

The home page of the pyLDAPI instance. Add whatever you like to this page.

:download:`index.html <download_templates/index.html>`


Register
--------

The register template lists all the items in a register.

:download:`register.html <download_templates/register.html>`


Instance
--------

The instance template presents the basic metadata of an instance item.

:download:`instance.html <download_templates/instance.html>`


Alternates
----------

The alternates template renders a list of alternate views and formats for a register or instance item.

:download:`alternates.html <download_templates/alternates.html>`