from pyldapi import Renderer, Profile


# Mock class
class Request:
    pass


class MockRenderer(Renderer):
    def render(self):
        # use the now gotten view & format to create a response
        pass


def setup():
    # profiles for testing
    global profiles
    profiles = {
        'agor': Profile(
            'http://linked.data.gov.au/def/agor',
            'AGOR Profile',
            'A profile of organisations according to the Australian Government Organisations Register',
            ['text/html'] + Renderer.RDF_MEDIA_TYPES,
            'text/turtle'
        ),
        'fake': Profile(
            'http://fake.com',
            'Fake Profile',
            'A fake Profile for testing',
            ['text/xml'],
            'text/xml'
        ),
        'other': Profile(
            'http://other.com',
            'Another Testing Profile',
            'Another profile for testing',
            ['text/html', 'text/xml'],
            'text/html'
        )
        # 'alt'  # included by default
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

    # this tests QSA selection of 'alt' profile
    mr2 = Request()
    mr2.url = 'http://whocares.com'
    mr2.values = {'_profile': 'alt'}
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


def test_get_profiles_from_http():
    expected = ['fake', 'agor']
    actual = r._get_profiles_from_http()
    assert actual == expected, \
        'r failed _get_profiles_from_http() test 1. Got {}, expected {}'.format(actual, expected)

    expected = None
    actual = r2._get_profiles_from_http()
    assert actual == expected, \
        'r2 failed _get_profiles_from_http() test 2. Got {}, expected {}'.format(actual, expected)


def test_get_profiles_from_qsa():
    expected = None
    actual = r._get_profiles_from_qsa()
    assert actual == expected, \
        'r failed _get_profiles_from_qsa() test 1. Got {}, expected {}'.format(actual, expected)

    expected = ['alt']
    actual = r2._get_profiles_from_qsa()
    assert actual == expected, \
        'r2 failed _get_profiles_from_qsa() test 2. Got {}, expected {}'.format(actual, expected)


def test_get_available_profiles():
    expected = {'agor', 'alt', 'fake', 'other'}
    actual = set(r._get_available_profiles().values())
    assert actual == expected, \
        'r failed test_get_available_profiles() test 1. Got {}, expected {}'.format(actual, expected)


def test_get_profile():
    expected = 'fake'
    actual = r._get_profile()
    assert actual == expected, \
        'r failed test_get_profile() test 1. Got {}, expected {}'.format(actual, expected)

    expected = 'alt'
    actual = r2._get_profile()
    assert actual == expected, \
        'r2 failed test_get_profile() test 2. Got {}, expected {}'.format(actual, expected)

    # testing the return of default ('agor') when no existing profiles are quested for
    mr3 = Request()
    mr3.url = 'http://whocares.com'
    mr3.values = {}
    mr3.headers = {
        'Accept-Profile': '<http://junk.com>; q=0.9, '
                          '<http://otherjunk.com>; q=0.1',
        'Accept': 'text/turtle'
    }

    global profiles
    r3 = MockRenderer(
        mr3,
        'http://whocares.com',
        profiles,
        'agor'
    )

    expected = 'agor'  # default, since requests gets no legit profile
    actual = r3._get_profile()
    assert actual == expected, \
        'r failed test_get_profile() test 3. Got {}, expected {}'.format(actual, expected)


def test_get_mediatype():
    mr4 = Request()
    mr4.url = 'http://whocares.com'
    mr4.values = {'_mediatype': 'text/turtle;q=0.5,application/rdf+xml,application/json+ld;q=0.6'}
    mr4.headers = {}

    r4 = MockRenderer(
        mr4,
        'http://whocares.com',
        profiles,
        'agor'  # default view
    )
    expected = 'application/rdf+xml'
    actual = r4._get_mediatype()
    assert actual == expected, \
        'r4 failed test_get_mediatype() test 1. Got {}, expected {}'.format(actual, expected)


if __name__ == '__main__':
    setup()
    test_get_profiles_from_http()
    test_get_profiles_from_qsa()
    test_get_available_profiles()
    test_get_profile()
    test_get_mediatype()

    print('Passed all tests')
