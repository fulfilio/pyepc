from __future__ import unicode_literals


from pyepc import SSCC, decode


def test_sscc():
    sscc = SSCC("0614141", "1", "234567890")
    assert sscc.pure_identity_uri == 'urn:epc:id:sscc:0614141.1234567890'
    assert sscc.get_tag_uri() == 'urn:epc:tag:sscc-96:0.0614141.1234567890'
    assert sscc.sscc == '106141412345678908'
    assert sscc.gs1_element_string == '(00)106141412345678908'

    # Encode to RPC Hex
    assert sscc.encode() == '3114257BF4499602D2000000'
    assert SSCC.decode('3114257BF4499602D2000000') == sscc


def test_epc_from_sscc():
    sscc = SSCC.from_sscc('106141412345678908')
    assert sscc == SSCC("0614141", "1", "234567890")


def test_decode():
    assert decode('3114257BF4499602D2000000') == \
        SSCC("0614141", "1", "234567890")
