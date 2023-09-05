from __future__ import unicode_literals

import pytest

from pyepc.exceptions import EncodingError
from pyepc.utils import (
    encode_integer,
    encode_hex,
    encode_string,
    decode_string,
    calculate_check_digit,
    get_gcp_length,
)


def test_encode_integer():
    assert encode_integer(3, 3) == "011"
    assert encode_integer(7, 3) == "111"
    assert encode_integer(7, 8) == "00000111"
    with pytest.raises(EncodingError):
        encode_integer(8, 3)


def test_encode_hex():
    assert encode_hex("3", 3) == "011"
    assert encode_hex("0x7", 3) == "111"
    assert encode_hex("7", 8) == "00000111"

    # Different representations
    assert encode_hex("A", 8) == "00001010"
    assert encode_hex("0xA", 8) == "00001010"

    with pytest.raises(EncodingError):
        encode_hex("0x8", 3)


def test_encode_string():
    assert encode_string("0", 7) == "0110000"
    # Small letter a = 0x61
    assert encode_string("a", 7) == "1100001"
    assert encode_string("a", 14) == "11000010000000"
    assert encode_string("ab", 14) == "11000011100010"

    assert decode_string("11000011100010") == "ab"


def test_check_digits():
    assert calculate_check_digit("629104150021") == "3"


def test_get_gcp_length():
    assert get_gcp_length("80614141123458") == 7
