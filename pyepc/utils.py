"""
The EPC binary encoding stored on tags is a string of bits and
the first part is an 8 bit header, followed by tag data. The
overall length, structure and function is determined by the
header.
"""
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
        raise EncodingError(
            "Cannot fit integer '{}' into {} bits".format(
                value, bits
            )
        )
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
    rv = ''
    assert len(value) <= bits / 7, "String {} is too long".format(value)
    for char in value.encode('ascii'):
        rv += encode_integer(char, 7)

    # Pad with zero bits as necessary to total bits
    return "{rv:0<{bits}}".format(rv=rv, bits=bits)


def decode_string(value):
    """
    Implements the string decoding method defined in section
    14.4.2 of the EPC Tag Data Standard
    """
    size = 7
    return "".join([
        chr(int(value[i:i + size], 2))
        for i in range(0, len(value), size)
        if int(value[i:i + size], 2) != 0
    ])


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
    return ''.join([
        encode_integer(partition, 3),
        encode_integer(var1, var1_bits),
        encode_integer(var2, var2_bits),
    ])


def decode_partition_table(bin_value, var1_bits, var1_digits,
                           var2_bits, var2_digits):
    """
    Implements partition table decoding defined in 14.4.3

    Returns a tuple of the two parts
    """
    return (
        decode_integer(
            bin_value[3:3 + var1_bits]
        ).zfill(var1_digits),
        decode_integer(
            bin_value[3 + var1_bits:3 + var1_bits + var2_bits]
        ).zfill(var2_digits),
    )


def bin_2_hex(binary):
    """
    Given the binary string, convert it into hex string
    """
    byte = 4
    return "".join([
        "{:X}".format(int(binary[i:i + byte], 2))
        for i in range(0, len(binary), byte)
    ])


def hex_2_bin(hex_val, bits):
    """
    Given the hex string, convert it into binary string
    """
    return "".join([
        "{:04b}".format(int(hex_val, 16)) for hex_val in hex_val
        ])[:bits].encode()


def calculate_check_digit(number):
    """
    Given a number without the check-digit, calculate
    the check digit and return it.

    See: https://www.gs1.org/services/how-calculate-check-digit-manually
    """
    # Step 2: Multiply alternate position by 3 and 1
    # and get the sum
    step_2 = sum(
        [int(n) * 3 for n in number[::-1][::2]]
    ) + sum(
        [int(n) for n in number[::-1][1::2]]
    )

    # Subtract the sum from nearest equal or higher multiple of ten
    return 10 - (step_2 % 10)
