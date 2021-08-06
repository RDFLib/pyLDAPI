from pyldapi import Renderer, Profile
from pyldapi.data import RDF_MEDIATYPES
from fastapi.requests import Request


# Mock FastAPI / Starlette Request object
req = Request({"type": "http", "query_string": None, "headers": {}})

# dummy profile to use
sdo = Profile(
    uri="https://schema.org",
    label="schema.org",
    comment="Schema.org is a collaborative, community activity with a mission to create, maintain, and promote schemas "
            "for structured data on the Internet, on web pages, in email messages, and beyond.",
    mediatypes=RDF_MEDIATYPES,
    default_mediatype="text/turtle",
    languages=["en"],
    default_language="en",
)

r = Renderer(req, "http://example.com", {"sdo": sdo}, "alt")
txt = r._render_alt_profile_html(
        alt_template="alt.html",
        additional_alt_template_context={"stuff": ["one", "two"], "title": "Dummy Title"}
    )
print(txt.body.decode())
