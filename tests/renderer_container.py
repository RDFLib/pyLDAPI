from pyldapi import ContainerRenderer, Profile
from pyldapi.data import RDF_MEDIATYPES
from fastapi.requests import Request


req = Request({"type": "http", "query_string": None, "headers": {}})

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

cr = ContainerRenderer(
    req,
    "http://example.com",
    "Dummy Label",
    "Dummy Comment",
    None,
    None,
    [
        ("http://example.com/one", "One"),
        ("http://example.com/two", "Two"),
        ("http://example.com/three", "Three"),
        ("http://example.com/four", "Four"),
        ("http://example.com/five", "Five"),
    ],
    60,
    None,
    profiles={"sdo": sdo},
    default_profile_token="sdo",
)

txt = cr._render_mem_profile_html()
print(txt.body.decode())