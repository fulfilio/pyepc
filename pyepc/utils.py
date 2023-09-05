# -*- coding: utf-8 -*-
"""
The EPC binary encoding stored on tags is a string of bits and
the first part is an 8 bit header, followed by tag data. The
overall length, structure and function is determined by the
header.
"""
from __future__ import unicode_literals
from builtins import str

import requests

from .exceptions import EncodingError


def encode_integer(value, bits):
    """
    Implements the Integer encoding method defined in section
    14.3.1 of the EPC Tag Data Standard

    b-bit integer (padded to the left with zero bits as necessary)
    """
    fmt_str = "0{bits}b".format(bits=bits)
    rv = format(int(value), fmt_str)
    if len(rv) > bits:
        raise EncodingError("Cannot fit integer '{}' into {} bits".format(value, bits))
    return rv


def decode_integer(value):
    """
    Decode from binary and return the integer value
    as a string
    """
    return str(int(value, 2))


def encode_hex(value, bits):
    assert isinstance(value, str)
    return encode_integer(int(value, 16), bits)


def encode_string(value, bits):
    """
    Implements the string encoding method defined in section
    14.3.1 of the EPC Tag Data Standard

    The String encoding method is used for a segment that appears
    as an alphanumeric string in the URI

    Pad with zero bits as necessary to total bits
    """
    rv = ""
    assert len(value) <= bits / 7, "String {} is too long".format(value)
    for char in str(value).encode("ascii"):
        rv += encode_integer(char, 7)

    # Pad with zero bits as necessary to total bits
    return "{rv:0<{bits}}".format(rv=rv, bits=bits)


def decode_string(value):
    """
    Implements the string decoding method defined in section
    14.4.2 of the EPC Tag Data Standard
    """
    size = 7
    return "".join(
        [
            chr(int(value[i : i + size], 2))
            for i in range(0, len(value), size)
            if int(value[i : i + size], 2) != 0
        ]
    )


def encode_partition_table(partition, var1, var1_bits, var2, var2_bits, bits):
    """
    Implements the partition table encoding method defined in
    section 14.3.3 of the EPC Tag Data Standard.

    The Partition Table encoding method is used for a segment that
    appears in the URI as a pair of variable-length numeric fields
    separated by a dot (“.”) character

    The number of characters in the two URI fields always totals to
    a constant number of characters and the number of bits in the
    binary encoding likewise totals to a constant number of bits.
    """
    return "".join(
        [
            encode_integer(partition, 3),
            encode_integer(var1, var1_bits),
            encode_integer(var2, var2_bits),
        ]
    )


def decode_partition_table(bin_value, var1_bits, var1_digits, var2_bits, var2_digits):
    """
    Implements partition table decoding defined in 14.4.3

    Returns a tuple of the two parts
    """
    return (
        decode_integer(bin_value[3 : 3 + var1_bits]).zfill(var1_digits),
        decode_integer(bin_value[3 + var1_bits : 3 + var1_bits + var2_bits]).zfill(
            var2_digits
        ),
    )


def bin_2_hex(binary):
    """
    Given the binary string, convert it into hex string
    """
    byte = 4
    return "".join(
        [
            "{:X}".format(int(binary[i : i + byte], 2))
            for i in range(0, len(binary), byte)
        ]
    )


def hex_2_bin(hex_val, bits):
    """
    Given the hex string, convert it into binary string
    """
    return "".join(["{:04b}".format(int(hex_char, 16)) for hex_char in hex_val])[
        :bits
    ].encode()


def calculate_check_digit(number):
    """
    Given a number without the check-digit, calculate
    the check digit and return it.

    See: https://www.gs1.org/services/how-calculate-check-digit-manually
    """
    # Step 2: Multiply alternate position by 3 and 1
    # and get the sum
    step_2 = sum([int(n) * 3 for n in number[::-1][::2]]) + sum(
        [int(n) for n in number[::-1][1::2]]
    )
    if step_2 % 10 == 0:
        return "0"

    # Subtract the sum from nearest equal or higher multiple of ten
    return str(10 - (step_2 % 10))


# A data store to retreive and store the company prefixes and
# corresponding lengths. This is required to determine the length
# of the company prefix and it is variable.
GCP_LENGTHS = {}


def get_gcp_length(gs1_identification_key):
    """
    Return the length of the GS1 Company Prefix (GCP)
    by using the lookup table.

    This is an implementation of the procedure outlines in
    section 5.6.3 of the GS1 RFID/Barcode Interoperability Guideline
    """
    # If the table has not been loaded yet, load it
    if not GCP_LENGTHS:
        response = requests.get(
            "https://www.gs1.org/sites/default/files/docs/gcp_length/gcpprefixformatlist.json"  # noqa
        ).json()
        for entry in response["GCPPrefixFormatList"]["entry"]:
            GCP_LENGTHS[entry["prefix"]] = entry["gcpLength"]

    # Step 1: Start with the first six digits of the GS1 identification
    # key (skipping the Indicator Digit of a GTIN, the Extension Digit
    # of an SSCC or the zero padding digit of a GRAI).
    # Call this the “candidate prefix”.
    candidate_prefix = gs1_identification_key[1:]

    for candidate_length in range(11, 2, -1):
        # Take the first part (starting with first 6 digits)
        # and lookup if an entry exists. If there is one, return the
        # value.
        length = GCP_LENGTHS.get(candidate_prefix[:candidate_length])
        if length is not None:
            return length

        # If not increase the digit and then check until all
        # all the way down to 3 digits
