import pytest


from pyepc import SGTIN
from pyepc.exceptions import EncodingError


def test_sgtin_no_serial():
    sgtin = SGTIN("0614141", "8", "12345")
    assert sgtin.pure_identity_uri == 'urn:epc:id:sgtin:0614141.812345.0'
    assert sgtin.get_tag_uri() == 'urn:epc:tag:sgtin-96:1.0614141.812345.0'


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

    assert SGTIN.decode('3034257BF7194E4000001A85') == sgtin


def test_sgtin_198():
    sgtin = SGTIN("0614141", "8", "12345", "6789")
    assert sgtin.pure_identity_uri == 'urn:epc:id:sgtin:0614141.812345.6789'
    assert sgtin.get_tag_uri(binary_scheme=SGTIN.BinarySchemes.SGTIN_198) == \
        'urn:epc:tag:sgtin-198:1.0614141.812345.6789'
    assert sgtin.encode(binary_scheme=SGTIN.BinarySchemes.SGTIN_198) == \
        '3634257BF7194E5B3770E40000000000000000000000000000'
    assert SGTIN.decode(
        '3634257BF7194E5B3770E40000000000000000000000000000') == sgtin


def test_sgtin_198_alpha_num_serial():
    sgtin = SGTIN("0614141", "8", "12345", "6789AB")
    assert sgtin.pure_identity_uri == 'urn:epc:id:sgtin:0614141.812345.6789AB'
    assert sgtin.get_tag_uri(binary_scheme=SGTIN.BinarySchemes.SGTIN_198) == \
        'urn:epc:tag:sgtin-198:1.0614141.812345.6789AB'
    assert sgtin.encode(binary_scheme=SGTIN.BinarySchemes.SGTIN_198) == \
        '3634257BF7194E5B3770E60C20000000000000000000000000'
    assert SGTIN.decode(
        '3634257BF7194E5B3770E60C20000000000000000000000000') == sgtin
