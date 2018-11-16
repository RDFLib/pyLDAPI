Class template
==============

Example of a class item template customised for the `mediatypes dataset`_:

.. _mediatypes dataset: https://github.com/nicholascar/mediatypes-dataset

.. code-block:: HTML

    {% extends "layout.html" %}

        {% block content %}
        <h1>{{ mediatype }}</h1>
        <h3><a href="{{ request.values.get('uri') }}">{{ request.values.get('uri') }}</a></h3>
        <h4>Source:</h4>
        <ul>
            <li><a href="https://www.iana.org/assignments/media-types/{{ mediatype }}">https://www.iana.org/assignments/media-types/{{ mediatype }}</a></li>
        </ul>
        {% if deets['contributors'] is not none %}
        <h4>Contributors:</h4>
        <ul>
        {% for contributor in deets['contributors'] %}
            <li><a href="{{ contributor }}">{{ contributor }}</a></li>
        {% endfor %}
        </ul>
        {% endif %}
        <h3>Other profiles, formats and languages:</h3>
        <ul><li><a href="{{ request.base_url }}?uri={{ request.values.get('uri') }}&_view=alternates">Alternate Views</a></li></ul>
    {% endblock %}

Variables used by the class instance template:

This will be called within a custom Renderer class' :func:`render`. See :ref:`example-renderer-reference`.

.. code-block:: python

    return render_template(
        'mediatype-en.html',    # the class item template
        deets=deets,            # a python dict containing keys *label* and *contributors* to its respective values.
        mediatype=mediatype     # the mediatype class instance item name
    )