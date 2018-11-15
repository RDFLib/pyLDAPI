.. _example-renderer-reference:

Custom Renderer
===============

In this example, we are creating a custom :class:`.Renderer` class by inheritance to cater for a `media type`_ instance. More information about this code can be found at this repository_.

* The interest for :class:`.View` declarations are on lines |view linenos|.

* On line |init linenos|, we pass we call the :code:`__init__()` of the super class, passing in the list of :class:`.View` objects and some other arguments.

* Lines |render linenos| demonstrate how to implement the abstract :func:`pyldapi.Renderer.render` and how it works in tandem with the list of :class:`.View` objects.


.. _repository: https://github.com/nicholascar/mediatypes-dataset
.. _media type: https://www.iana.org/assignments/media-types/media-types.xml

.. note:: The focus here is to demonstrate how to create a custom :class:`.Renderer` class, defining a custom :code:`render()` method and defining a list of :class:`.View` objects.

.. literalinclude:: exempler_custom_renderer_example.py
    :linenos:
    :emphasize-lines: 10-19, 20-25, 27-57

.. shame I can't use the replace directive in directive parameters. :(

.. |view linenos| replace:: 10-19
.. |init linenos| replace:: 20-25
.. |render linenos| replace:: 27-57