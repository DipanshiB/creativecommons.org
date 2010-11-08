import email
import StringIO

from nose.tools import assert_raises
from lxml import etree

import cc.license
from cc.engine import util


util._activate_testing()


class FakeAcceptLanguage(object):
    def __init__(self, best_matches):
        self._best_matches = best_matches

    def best_matches(self):
        return self._best_matches


class FakeRequest(object):
    def __init__(self, best_matches):
        self.accept_language = FakeAcceptLanguage(best_matches)


def test_get_xpath_attribute():
    tree = etree.parse(
        StringIO.StringIO('<foo><bar><baz basil="herb" /></bar></foo>'))
    assert util._get_xpath_attribute(tree, '/foo/bar/baz', 'basil') == 'herb'


def test_get_locale_identity_data():
    identity_data = util.get_locale_identity_data('en-US_POSIX')

    assert identity_data['language'] == 'en'
    assert identity_data['territory'] == 'US'
    assert identity_data['variant'] == 'POSIX'
    assert identity_data['script'] == None


def test_get_locale_text_orientation():
    # Make sure rtl languates are accepted as rtl
    assert util.get_locale_text_orientation('he-il') == u'rtl'

    # Make sure ltr languates are accepted as ltr
    assert util.get_locale_text_orientation('en') == u'ltr'

    # If only an unknown/imaginary language is given, default to ltr
    assert util.get_locale_text_orientation('foo-bar') == u'ltr'


def test_get_license_conditions():
    # TODO: we should test for all license possibilities here in
    #   several languages..

    expected = [
        {'char_title': 'Attribution',
         'char_brief': (
                "You must attribute the work in the manner specified "
                "by the author or licensor (but not in any way that suggests "
                "that they endorse you or your use of the work)."),
         'icon_name': 'by',
         'char_code': 'by',
         'predicate': 'cc:requires',
         'object': 'http://creativecommons.org/ns#Attribution'}]
    result = util.get_license_conditions(
        cc.license.by_code('by'))
    assert result == expected


def test_active_languages():
    {'code': 'en', 'name': u'English'} in util.active_languages()


def test_locale_to_cclicense_style():
    assert util.locale_to_cclicense_style('en-US') == 'en_US'
    assert util.locale_to_cclicense_style('en') == 'en'
    assert util.locale_to_cclicense_style('EN-us') == 'en_US'


def test_safer_resource_filename():
    assert util.safer_resource_filename(
        'cc.engine', 'templates/test/bunnies.pt').endswith(
        'templates/test/bunnies.pt')
    assert_raises(
        util.UnsafeResource,
        util.safer_resource_filename,
        'cc.engine', '../../templates/test/bunnies.pt')


def test_send_email():
    util._clear_test_inboxes()

    # send the email
    util.send_email(
        "sender@creativecommons.org",
        ["amanda@example.org", "akila@example.org"],
        "Testing is so much fun!",
        """HAYYY GUYS!

I hope you like unit tests JUST AS MUCH AS I DO!""")

    # check the main inbox
    assert len(util.EMAIL_TEST_INBOX) == 1
    message = util.EMAIL_TEST_INBOX.pop()
    assert message['From'] == "sender@creativecommons.org"
    assert message['To'] == "amanda@example.org, akila@example.org"
    assert message['Subject'] == "Testing is so much fun!"
    assert message.get_payload() == """HAYYY GUYS!

I hope you like unit tests JUST AS MUCH AS I DO!"""

    # Check everything that the FakeMhost.sendmail() method got is correct
    assert len(util.EMAIL_TEST_MBOX_INBOX) == 1
    mbox_dict = util.EMAIL_TEST_MBOX_INBOX.pop()
    assert mbox_dict['from'] == "sender@creativecommons.org"
    assert mbox_dict['to'] == ["amanda@example.org", "akila@example.org"]
    mbox_message = email.message_from_string(mbox_dict['message'])
    assert mbox_message['From'] == "sender@creativecommons.org"
    assert mbox_message['To'] == "amanda@example.org, akila@example.org"
    assert mbox_message['Subject'] == "Testing is so much fun!"
    assert mbox_message.get_payload() == """HAYYY GUYS!

I hope you like unit tests JUST AS MUCH AS I DO!"""


SILLY_LICENSE_HTML = """This work available under a
<a href="http://example.org/goes/nowhere">very silly license</a>."""

def test_send_license_info_email():
    util._clear_test_inboxes()

    util.send_license_info_email(
        'Creative Commons Very-Silly License 5.8',
        SILLY_LICENSE_HTML,
        'ilovesillylicenses@example.org', 'en')

    assert len(util.EMAIL_TEST_INBOX) == 1
    message = util.EMAIL_TEST_INBOX.pop()
    assert message['From'] == "info@creativecommons.org"
    assert message['To'] == "ilovesillylicenses@example.org"
    assert message['Subject'] == "Your Creative Commons License Information"
    assert message.get_payload() == """Thank you for using a Creative Commons legal tool for your work.

You have selected Creative Commons Very-Silly License 5.8.
You should include a reference to this on the web page that includes
the work in question.

Here is the suggested HTML:

This work available under a
<a href="http://example.org/goes/nowhere">very silly license</a>.

Tips for marking your work can be found at
http://wiki.creativecommons.org/Marking.  Information on the supplied HTML and
metadata can be found at http://wiki.creativecommons.org/CC_REL.

Thank you!
Creative Commons Support
info@creativecommons.org"""


def test_subset_dict():
    expected = {
        'keeper1': 'keepme1',
        'keeper2': 'keepme2'}

    result = util.subset_dict(
        {'keeper1': 'keepme1',
         'loser1': 'loseme1',
         'keeper2': 'keepme2',
         'loser2': 'loseme2'},
        ['keeper1', 'keeper2', 'keeper3'])

    assert result == expected


def test_publicdomain_partner_get_params():
    result = util.publicdomain_partner_get_params({'lang': 'en'})
    assert result == 'lang=en'

    # ignore garbage parameters
    result = util.publicdomain_partner_get_params({'lang': 'en', 'floobie': 'blech'})
    assert result == 'lang=en'

    result = util.publicdomain_partner_get_params(
        {'lang': 'en',
         'partner': 'http://nethack.org/',
         'exit_url': 'http://nethack.org/return_from_cc?license_url=[license_url]&license_name=[license_name]',
         'stylesheet': 'http://nethack.org/yendor.css',
         'extraneous_argument': 'large mimic'})

    result_pieces = result.split('&')
    assert len(result_pieces) == 4

    assert 'lang=en' in result_pieces
    assert 'partner=http%3A%2F%2Fnethack.org%2F' in result_pieces
    assert 'exit_url=http%3A%2F%2Fnethack.org%2Freturn_from_cc%3Flicense_url%3D%5Blicense_url%5D%26license_name%3D%5Blicense_name%5D' in result_pieces
    assert 'stylesheet=http%3A%2F%2Fnethack.org%2Fyendor.css' in result_pieces
