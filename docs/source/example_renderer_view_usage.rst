.. _example-renderer-reference:

Example of a Custom Renderer
=============================

In this example, we are creating a custom :class:`.Renderer` class by inheritance to cater for `Geoscience Australia's (GA) Sample instance`_. More information about this code can be found at this repository_.

* The interest for :class:`.View` declarations are on lines 55-117.

* On line 119, we pass we call the :code:`__init__()` of the super class, passing in the list of :class:`.View` objects and some other arguments.

* Lines 307-346 demonstrate how to implement the abstract :func:`pyldapi.Renderer.render` and how it works in tandem with the list of :class:`.View` objects.


.. _repository: https://github.com/CSIRO-enviro-informatics/sss-api
.. _Geoscience Australia's (GA) Sample instance: http://pid.geoscience.gov.au/sample/

.. note:: The focus here is to demonstrate how to create a custom :class:`.Renderer` class, defining a custom :code:`render()` method and defining a list of :class:`.View` objects.
    There is no need to make sense of the rest of the business logic code since your implementation will presumably be vastly different to GA's Sample Renderer implementation.

.. literalinclude:: exempler_custom_renderer_example.py
    :linenos:
    :emphasize-lines: 55-117, 119, 307-346