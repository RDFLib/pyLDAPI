from pyldapi import Renderer, Profile


# Mock class
class Request:
    pass


class MockRenderer(Renderer):
    def render(self):
        # use the now gotten profile & format to create a response
        pass


def setup():
    # profiles for testing
    global profiles
    profiles = {
        'agor': Profile(
            'AGOR Profile',
            'A profile of organisations according to the Australian Government Organisations Register',
            ['text/html'] + Renderer.RDF_MIMETYPES,
            'text/turtle',
            profile_uri='http://linked.data.gov.au/def/agor'
        ),
        'fake': Profile(
            'Fake Profile',
            'A fake Profile for testing',
            ['text/xml'],
            'text/xml',
            profile_uri='http://fake.com'
        ),
        'other': Profile(
            'Another Testing Profile',
            'Another profile for testing',
            ['text/html', 'text/xml'],
            'text/html',
            profile_uri='http://other.com'
        )
        # 'alternates'  # included by default
        # 'all'         # included by default
    }

    # this tests Accept-Profile selection of 'fake' profile
    mr = Request()
    mr.url = 'http://whocares.com'
    mr.values = {}
    mr.headers = {
        'Accept-Profile': 'http://nothing.com ,'  # ignored - broken, no <>
                          'http://nothing-else.com,'  # ignored - broken, no <>
                          '<http://notavailable.com>; q=0.9, '  # not available
                          '<http://linked.data.gov.au/def/agor>; q=0.1, '  # available but lower weight
                          '<http://fake.com>; q=0.2',  # should be this
        'Accept': 'text/turtle'
    }

    # this tests QSA selection of 'alternates' profile
    mr2 = Request()
    mr2.url = 'http://whocares.com'
    mr2.values = {'_profile': 'alternates'}
    mr2.headers = {}

    global r
    r = MockRenderer(
        mr,
        'http://whocares.com',
        profiles,
        'agor'
    )

    global r2
    r2 = MockRenderer(
        mr2,
        'http://whocares.com',
        profiles,
        'agor'
    )


def test_content_profile():
    expected = '<http://fake.com>'
    actual = r.headers.get('Content-Profile')
    assert actual == expected, \
        'test_list_profiles() test 1: Content-Profile expected to be {}, was {}'.format(
            expected,
            actual
        )


def test_list_profiles():
    expected = \
        '<http://www.w3.org/ns/dx/prof/Profile>; rel="type"; token="agor"; anchor=<http://linked.data.gov.au/def/agor>, ' \
        '<http://www.w3.org/ns/dx/prof/Profile>; rel="type"; token="fake"; anchor=<http://fake.com>, ' \
        '<http://www.w3.org/ns/dx/prof/Profile>; rel="type"; token="other"; anchor=<http://other.com>, ' \
        '<http://www.w3.org/ns/dx/prof/Profile>; rel="type"; token="alt"; anchor=<http://www.w3.org/ns/dx/conneg/altr>, ' \
        \
        '<http://whocares.com?_profile=agor&_mediatype=text/html>; rel="alternate"; type="text/html"; profile="http://linked.data.gov.au/def/agor", ' \
        '<http://whocares.com?_profile=agor&_mediatype=text/turtle>; rel="alternate"; type="text/turtle"; profile="http://linked.data.gov.au/def/agor", ' \
        '<http://whocares.com?_profile=agor&_mediatype=application/rdf+xml>; rel="alternate"; type="application/rdf+xml"; profile="http://linked.data.gov.au/def/agor", ' \
        '<http://whocares.com?_profile=agor&_mediatype=application/ld+json>; rel="alternate"; type="application/ld+json"; profile="http://linked.data.gov.au/def/agor", ' \
        '<http://whocares.com?_profile=agor&_mediatype=text/n3>; rel="alternate"; type="text/n3"; profile="http://linked.data.gov.au/def/agor", ' \
        '<http://whocares.com?_profile=agor&_mediatype=application/n-triples>; rel="alternate"; type="application/n-triples"; profile="http://linked.data.gov.au/def/agor", ' \
        '<http://whocares.com?_profile=fake&_mediatype=text/xml>; rel="alternate"; type="text/xml"; profile="http://fake.com", ' \
        '<http://whocares.com?_profile=other&_mediatype=text/html>; rel="alternate"; type="text/html"; profile="http://other.com", ' \
        '<http://whocares.com?_profile=other&_mediatype=text/xml>; rel="alternate"; type="text/xml"; profile="http://other.com", ' \
        '<http://whocares.com?_profile=alt&_mediatype=text/html>; rel="alternate"; type="text/html"; profile="http://www.w3.org/ns/dx/conneg/altr", ' \
        '<http://whocares.com?_profile=alt&_mediatype=application/json>; rel="alternate"; type="application/json"; profile="http://www.w3.org/ns/dx/conneg/altr", ' \
        '<http://whocares.com?_profile=alt&_mediatype=text/turtle>; rel="alternate"; type="text/turtle"; profile="http://www.w3.org/ns/dx/conneg/altr", ' \
        '<http://whocares.com?_profile=alt&_mediatype=application/rdf+xml>; rel="alternate"; type="application/rdf+xml"; profile="http://www.w3.org/ns/dx/conneg/altr", ' \
        '<http://whocares.com?_profile=alt&_mediatype=application/ld+json>; rel="alternate"; type="application/ld+json"; profile="http://www.w3.org/ns/dx/conneg/altr", ' \
        '<http://whocares.com?_profile=alt&_mediatype=text/n3>; rel="alternate"; type="text/n3"; profile="http://www.w3.org/ns/dx/conneg/altr", ' \
        '<http://whocares.com?_profile=alt&_mediatype=application/n-triples>; rel="alternate"; type="application/n-triples"; profile="http://www.w3.org/ns/dx/conneg/altr"'
    actual = r.headers.get('Link')
    assert actual == expected, \
        'test_list_profiles() test 1:\nContent-Profile expected to be\n{},\nwas\n{}'.format(
            expected,
            actual
        )


if __name__ == '__main__':
    setup()
    # test_content_profile()
    test_list_profiles()

    print('Passed all tests')
