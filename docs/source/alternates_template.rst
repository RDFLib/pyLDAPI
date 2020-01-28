Alternates template
===================

Example of a generic alternates template:

.. code-block:: HTML

    {% extends "layout.html" %}
    {% block content %}
        <h1>{{ register_name }} Linked Data API</h1>
        {% if class_uri %}
            <h3>Alternates view of a <a href="{{ class_uri }}">{{ class_uri }}</a></h3>
        {% else %}
            <h3>Alternates view</h3>
        {% endif %}
        {% if instance_uri %}
            <h3>Instance <a href="{{ instance_uri }}">{{ instance_uri }}</a></h3>
        {% endif %}
        <p>Default profile: <a href="{{ request.base_url }}?_profile={{ default_profile_token }}">{{ default_profile_token }}</a></p>
        <table class="pretty">
        <tr><th>View</th><th>Formats</th><th>View Desc.</th><th>View Namespace</th></tr>
        {% for v, vals in profiles.items() %}
                <tr>
                    <td><a href="{{ request.base_url }}?_profile={{ v }}">{{ v }}</a></td>
                    <td>
                    {% for f in vals['formats'] %}
                        <a href="{{ request.base_url }}?_profile={{ v }}&_format={{ f }}">{{ f }}</a>
                        {% if loop.index != vals['formats']|length %}<br />{% endif %}
                    {% endfor %}
                    </td>
                    <td>{{ vals['namespace'] }}</td>
                    <td>{{ vals['comment'] }}</td>
                </tr>
        {% endfor %}
        </table>
    {% endblock %}

The alternates profile template is shared for both a Register's alternates profile as well as a class instance item's alternates profile. In any case, since a :class:`.RegisterRenderer` class and a :ref:`example-renderer-reference` class both inherit from the base class :class:`.Renderer`, then they can both easily render the alternates profile by calling the base class' :func:`pyldapi.Renderer.render_alternates_profile` method. One distinct difference is that pyLDAPI will handle the alternates profile automatically for a :class:`.RegisterRenderer` whereas a :ref:`example-renderer-reference` will have to explicitly call the :func:`pyldapi.Renderer.render_alternates_profile`.

Example usage for a :ref:`example-renderer-reference`:

.. code-block:: python
    :linenos:
    :emphasize-lines: 7

    # context: inside a 'custom' Renderer class which inherits from pyldapi.Renderer

    # this is an implementation of the abstract render() of the base class Renderer
    def render(self):
        # ...
        if self.profile == 'alternates':
            return self.render_alternates_profile() # render the alternates profile for this class instance
        # ...
