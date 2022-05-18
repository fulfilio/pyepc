from __future__ import unicode_literals

import pytest


from pyepc import SGTIN
from pyepc.exceptions import EncodingError


def test_sgtin_no_serial():
    sgtin = SGTIN("0614141", "8", "12345")
    assert sgtin.pure_identity_uri == 'urn:epc:id:sgtin:0614141.812345.0'
    assert sgtin.get_tag_uri() == 'urn:epc:tag:sgtin-96:1.0614141.812345.0'
    assert sgtin.gtin == '80614141123458'
    assert sgtin.gs1_element_string == '(01)80614141123458(21)0'


def test_sgtin_96_invalid_serial():
    sgtin = SGTIN("0614141", "8", "12345", "001")

    # Pure identity has no issue because the encoding determined the
    # validty of this
    assert sgtin.pure_identity_uri == 'urn:epc:id:sgtin:0614141.812345.001'

    with pytest.raises(EncodingError):
        sgtin.get_tag_uri(binary_scheme=SGTIN.BinarySchemes.SGTIN_96)

    assert sgtin.get_tag_uri(binary_scheme=SGTIN.BinarySchemes.SGTIN_198) == \
        'urn:epc:tag:sgtin-198:1.0614141.812345.001'


def test_sgtin_96():
    sgtin = SGTIN("0614141", "8", "12345", "6789")
    assert sgtin.pure_identity_uri == 'urn:epc:id:sgtin:0614141.812345.6789'
    assert sgtin.get_tag_uri() == 'urn:epc:tag:sgtin-96:1.0614141.812345.6789'
    assert sgtin.encode() == '3034257BF7194E4000001A85'
    assert sgtin.gtin == '80614141123458'
    assert sgtin.gs1_element_string == '(01)80614141123458(21)6789'

    assert SGTIN.decode('3034257BF7194E4000001A85') == sgtin


def test_sgtin_198():
    sgtin = SGTIN("0614141", "8", "12345", "6789")
    assert sgtin.pure_identity_uri == 'urn:epc:id:sgtin:0614141.812345.6789'
    assert sgtin.gtin == '80614141123458'
    assert sgtin.get_tag_uri(binary_scheme=SGTIN.BinarySchemes.SGTIN_198) == \
        'urn:epc:tag:sgtin-198:1.0614141.812345.6789'
    assert sgtin.encode(binary_scheme=SGTIN.BinarySchemes.SGTIN_198) == \
        '3634257BF7194E5B3770E40000000000000000000000000000'
    assert SGTIN.decode(
        '3634257BF7194E5B3770E40000000000000000000000000000') == sgtin


def test_sgtin_198_alpha_num_serial():
    sgtin = SGTIN("0614141", "8", "12345", "6789AB")
    assert sgtin.gtin == '80614141123458'
    assert sgtin.gs1_element_string == '(01)80614141123458(21)6789AB'
    assert sgtin.pure_identity_uri == 'urn:epc:id:sgtin:0614141.812345.6789AB'
    assert sgtin.get_tag_uri(binary_scheme=SGTIN.BinarySchemes.SGTIN_198) == \
        'urn:epc:tag:sgtin-198:1.0614141.812345.6789AB'
    assert sgtin.encode(binary_scheme=SGTIN.BinarySchemes.SGTIN_198) == \
        '3634257BF7194E5B3770E60C20000000000000000000000000'
    assert SGTIN.decode(
        '3634257BF7194E5B3770E60C20000000000000000000000000') == sgtin


def test_epc_from_gtin():
    sgtin = SGTIN.from_sgtin('80614141123458', '6789AB')
    assert sgtin == SGTIN("0614141", "8", "12345", "6789AB")


def test_gtin_from_epc():
    decoded = SGTIN.decode('3036142C8C008F8000053244')
    assert decoded.gtin == '08719139005740', "Decoded GTIN is wrong"
