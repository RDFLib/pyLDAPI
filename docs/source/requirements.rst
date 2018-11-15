.. _requirements-reference:

Requirements
============

.. note:: To use the pyLDAPI module, a set of requirements must be met for the tool to work correctly.


Jinja2 Templates
----------------

Register
~~~~~~~~

A :code:`register.html` template is required to deliver a register of items.

Example register template:

.. code-block:: HTML

    {% extends "layout.html" %}
    {% block content %}
        <h1>{{ label }}</h1>
        <h2>Register View</h2>
        {% for class in contained_item_classes %}
            <span><h3>Of <a href="{{ class }}">{{ class }}</a> class items</h3></span>
        {% endfor %}
        <table>
            <tr>
                <td style="vertical-align:top; width:500px;">
                    <h3>Items in this Register</h3>
                    <ul>
                    {%- for item in register_items -%}
                        {%- if item is not string %}
                        <li class="no-line-height"><a href="{{ item[0] }}">{{ item[1] }}</a></li>
                        {%- else %}
                        <li class="no-line-height"><a href="{{ item }}">{{ item.split('#')[-1].split('/')[-1] }}</a></li>
                        {%- endif %}
                    {%- endfor -%}
                    </ul>
                    {%  if pagination.links %}
                    <h5>Paging</h5>
                    {%  endif %}
                    {{ pagination.links }}
                </td>
                <td style="vertical-align:top;">
                    <h3>Alternate views</h3>
                    <p>Different views of this register are listed at its <a href="{{ request.base_url }}?_view=alternates">Alternate views</a> page.</p>
                    <h3>Automated Pagination</h3>
                    <p>To page through these items, use the query string arguments 'page' for the page number and 'per_page' for the number of items per page. HTTP <code>Link</code> headers of <code>first</code>, <code>prev</code>, <code>next</code> &amp; <code>last</code> indicate URIs to the first, a previous, a next and the last page.</p>
                    <p>Example:</p>
                    <pre>
                        {{ request.base_url }}?page=7&amp;per_page=50
                    </pre>
                    <p>Assuming 500 items, this request would result in a response with the following Link header:</p>
                    <pre>
                        Link:   &lt;{{ request.base_url }}?per_page=50&gt; rel="first",
                            &lt;{{ request.base_url }}?per_page=50&page=6&gt; rel="prev",
                            &lt;{{ request.base_url }}?per_page=50&page=8&gt; rel="next",
                            &lt;{{ request.base_url }}?per_page=50&page=10&gt; rel="last"
                    </pre>
                    <p>If you want to page the whole collection, you should start at <code>first</code> and follow the link headers until you reach <code>last</code> or until there is no <code>last</code> link given. You shouldn't try to calculate each <code>page</code> query string argument yourself.</p>
                </td>
            </tr>
        </table>
    {% endblock %}

Alternates
~~~~~~~~~~

An :code:`alternates.html` template is required to deliver an *alternates view* of a register or instance of a class. Alternatively, you can specify a different template for the alternates view by passing an optional argument to the :func:`pyldapi.Renderer.__init__` as :code:`alternates_template=`.

Example alternates template:

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
        <p>Default view: <a href="{{ request.base_url }}?_view={{ default_view_token }}">{{ default_view_token }}</a></p>
        <table class="pretty">
        <tr><th>View</th><th>Formats</th><th>View Desc.</th><th>View Namespace</th></tr>
        {% for v, vals in views.items() %}
                <tr>
                    <td><a href="{{ request.base_url }}?_view={{ v }}">{{ v }}</a></td>
                    <td>
                    {% for f in vals['formats'] %}
                        <a href="{{ request.base_url }}?_view={{ v }}&_format={{ f }}">{{ f }}</a>
                        {% if loop.index != vals['formats']|length %}<br />{% endif %}
                    {% endfor %}
                    </td>
                    <td>{{ vals['namespace'] }}</td>
                    <td>{{ vals['comment'] }}</td>
                </tr>
        {% endfor %}
        </table>
    {% endblock %}

Class
~~~~~

A template for each class item in the dataset.

Example: The online LD API for the Geofabric at `geofabricld.net`_ is exposing three class types, *Catchment*, *River Region* and *Drainage Division*. You can see below in the image of the templates used for this API.

.. _geofabricld.net: http://geofabricld.net

.. image:: _static/geofabric_templates.PNG

.. note:: These are of course not the only Jinja2 templates that you will have. Other ones may include something like the API's home page, about page, etc.

.. seealso:: See also the template information under the API section of the documentation for more information in regards to what variables are required to pass in to the required templates.