from builtins import str
from collections import namedtuple
from enum import Enum
import struct

from . import utils
from .epc import EPC, HeaderHex
from .exceptions import EncodingError, DecodingError


class SGTIN(EPC):
    """
    The Serialised Global Trade Item Number EPC scheme
    is used to assign a unique identity to an instance
    of a trade item, such as a specific instance of a
    product or SKU.

    Encoding
    --------

    # Always import from the root of the package
    >>> from pyepc import SGTIN

    # Build an sgtin object from company prefix, item ref and serial number
    >>> company_prefix = '0614141'
    >>> indicator = '8'
    >>> item_ref = '12345'
    >>> serial = '12345'
    >>> sgtin = SGTIN(company_prefix, indicator, item_ref, serial)

    # Get pure identity URI
    >>> sgtin.pure_identity_uri
    'urn:epc:id:sgtin:0614141.812345.12345'

    # Get GS1 element string
    >>> sgtin.gs1_element_string
    '(01)80614141123458(21)12345'

    # Get the tag URI
    >>> sgtin.get_tag_uri()
    'urn:epc:tag:sgtin-96:1.0614141.812345.12345'

    # The sgtin-96 scheme was automatically selected as the most
    # efficient binary encoding scheme for a numeric serial
    # number.

    # To explicitly use another encoding scheme like 'sgtin-198',
    # specify the encoding scheme
    >>> sgtin.get_tag_uri(SGTIN.BinarySchemes.SGTIN_198)
    'urn:epc:tag:sgtin-198:1.0614141.812345.12345'

    # You can also change the filter value. In this case
    # 1 (for POS item) was used as the default
    >>> sgtin.get_tag_uri(
    ...    SGTIN.BinarySchemes.SGTIN_198,
    ...    SGTIN.FilterValues.UNIT_LOAD,
    ... )
    'urn:epc:tag:sgtin-198:6.0614141.812345.12345'
    # The filter value is now 6

    # If you want to encode the EPC into the EPC bank of an RFID
    # tag, you will need the hex encoded value of the tag uri.
    >>> sgtin.encode()
    '3034257BF7194E4000003039'

    # Similar to the `get_tag_uri` methods, you can enforce which
    # scheme should be used and the filter value
    >>> sgtin.encode(
    ...     SGTIN.BinarySchemes.SGTIN_198,
    ...     SGTIN.FilterValues.UNIT_LOAD,
    ... )
    '36D4257BF7194E58B266D1A800000000000000000000000000'

    Decoding
    --------
    >>> SGTIN.decode('36D4257BF7194E58B266D1A800000000000000000000000000')
    '<urn:epc:id:sgtin:0614141.812345.12345>'

    EPC from GTIN
    -------------
    If all what you have is a GTIN, then you can build an EPC from it

    >>> SGTIN.from_sgtin('80614141123458', '6789AB')
    '<urn:epc:id:sgtin:0614141.812345.6789AB>'

    However, this has to lookup the company prefix length from the GS1
    prefix list and could be expensive the first time. So if you already
    know your company prefix length, then pass that along

    >>> company_prefix_len = len('0614141')
    >>> SGTIN.from_sgtin('80614141123458', '6789AB', company_prefix_len)
    '<urn:epc:id:sgtin:0614141.812345.6789AB>'
    """

    __scheme__ = "sgtin"

    class FilterValues(Enum):
        ALL_OTHERS = "0"
        POS_ITEM = "1"
        CASE = "2"
        RESERVED_3 = "3"
        INNER_PACK = "4"
        RESERVED_2 = "5"
        UNIT_LOAD = "6"
        COMPONENT = "7"

    class BinarySchemes(Enum):
        SGTIN_96 = "sgtin-96"
        SGTIN_198 = "sgtin-198"

    # Implementation of SGTIN Partition table that identifies
    # partition value for different lengths of GS1 company
    # prefix
    # ┌─────────┬──────────────┬────────┐
    # │PARTITION│COMPANY PREFIX│ITEM REF│
    # │    3    │    20-40     │  24-4  │
    # └─────────┴──────────────┴────────┘
    # p - partition value
    # m - Company prefix - bits
    # l - Company prefix - digits
    # n - Item reference bits
    PTR = namedtuple("PTR", "p m l n")
    partition_table = [
        PTR(p=0, m=40, l=12, n=4),
        PTR(p=1, m=37, l=11, n=7),
        PTR(p=2, m=34, l=10, n=10),
        PTR(p=3, m=30, l=9, n=14),
        PTR(p=4, m=27, l=8, n=17),
        PTR(p=5, m=24, l=7, n=20),
        PTR(p=6, m=20, l=6, n=24),
    ]

    def __init__(
        self,
        company_prefix,
        indicator,
        item_ref,
        serial_number="0",
        default_binary_scheme=BinarySchemes.SGTIN_96,
        default_filter_value=FilterValues.POS_ITEM,
    ):
        self.company_prefix = str(company_prefix)
        self.validate_company_prefix()

        self.item_ref = item_ref
        self.indicator = indicator
        # Length of company prefix + indicator + item reference
        # must be 13. So if the item_ref length is
        # smaller, pad with zeros
        self.item_ref_and_indicator = "{}{}".format(indicator, item_ref).zfill(
            13 - len(self.company_prefix)
        )

        self.serial_number = str(serial_number)

        # Store the defaults for creating tag URIs.
        self.default_binary_scheme = default_binary_scheme
        self.default_filter_value = default_filter_value

    def get_uri_body_parts(self):
        return [self.company_prefix, self.item_ref_and_indicator, self.serial_number]

    def guess_binary_scheme(self):
        """
        Change the guessing behavior by looking at the serial
        number. If the serial number is numeric, then one can
        use the sgtin-96 scheme.

        If alpha numeric then default to sgtin-198
        """
        if self.serial_number.isnumeric():
            return self.BinarySchemes.SGTIN_96
        return self.BinarySchemes.SGTIN_198

    def validate_sgtin_96(self):
        """
        The SGTIN-96 encoding allows for numeric-only
        serial numbers, without leading zeros, whose value
        is less than 2^38 (that is, from 0 through
        274,877,906,943, inclusive)
        """
        if len(self.serial_number) > 1 and self.serial_number.startswith("0"):
            raise EncodingError(
                "`sgtin-96` encoding does not allow leading 0s for "
                "serial numbers. Serial: '{}'".format(self.serial_number)
            )
        try:
            serial_number_int = int(self.serial_number)
        except ValueError:
            raise EncodingError(
                "`sgtin-96` encoding requires numeric-only "
                "serial numbers. Serial: '{}'".format(self.serial_number)
            )

        if not 0 <= serial_number_int <= 274877906943:
            raise EncodingError(
                "`sgtin-96` encoded serial numbers must be between 0 and "
                "274,877,906,943. Serial: '{}'".format(self.serial_number)
            )

        return True

    def _encode_gtin(self):
        """
        Encode the GTIN part of the URI. This is common between
        sgtin-96 and sgtin-198
        """
        for ptr in self.partition_table:
            if ptr.l == self.company_prefix_digits:  # noqa
                break
        else:
            raise EncodingError("Length of Company Prefix is invalid")

        return utils.encode_partition_table(
            ptr.p, self.company_prefix, ptr.m, self.item_ref_and_indicator, ptr.n, 47
        )

    @classmethod
    def _decode_gtin(cls, gtin_binary):
        """
        Decode the GTIN part of the epc binary

        ┌──────────────────────────────────────────────────┐
        │                       GTIN                       │
        │                        47                        │
        ├─────────┬──────────────┬─────────────────────────┤
        │PARTITION│COMPANY PREFIX│        ITEM REF         │
        │    3    │    20-40     │          24-4           │
        └─────────┼──────────────┼──────────┬──────────────┤
                  │COMPANY PREFIX│INDICATOR │   ITEM REF   │
                  │    20-40     │    1     │              │
                  └──────────────┴──────────┴──────────────┘

        :return: A tuple of company prefix, indicator and item ref
        """
        assert len(gtin_binary) == 47

        partition = int(utils.decode_integer(gtin_binary[:3]))
        for ptr in cls.partition_table:
            if ptr.p == partition:  # noqa
                break
        else:
            raise DecodingError("Length of Company Prefix is invalid")

        rv = utils.decode_partition_table(
            gtin_binary,
            ptr.m,
            ptr.l,
            ptr.n,
            # Total of 13 chars
            13 - ptr.l,
        )
        return (
            rv[0],  # Company prefix
            rv[1][0],  # Indicator digit
            rv[1][1:],  # Item ref
        )

    def encode_sgtin_96(self, filter_value):
        """
        Encode the tag to binary with sgtin-96 coding scheme

        See 14.5.1.1 on the EPC Tag Data Standard
        """
        # ┌──────────┬──────┬─────────────────────────────────┬──────┐
        # │EPC HEADER│FILTER│              GTIN               │SERIAL│
        # │    8     │  3   │               47                │  38  │
        # ├──────────┼──────┼─────────┬──────────────┬────────┼──────┤
        # │EPC HEADER│FILTER│PARTITION│COMPANY PREFIX│ITEM REF│SERIAL│
        # │    8     │  3   │    3    │    20-40     │  24-4  │  38  │
        # └──────────┴──────┴─────────┴──────────────┴────────┴──────┘

        # EPC Header
        # 8-bits
        #
        # for sgtin-96 is 0x30
        binary = utils.encode_integer(0x30, 8)

        # Filter
        # 3 bits
        binary += utils.encode_integer(int(filter_value.value), 3)

        # GTIN = Partition + Company Prefix + Item Ref
        # 47 bits
        binary += self._encode_gtin()

        # Serial
        binary += utils.encode_integer(int(self.serial_number), 38)

        assert len(binary) == 96

        return utils.bin_2_hex(binary)

    def encode_sgtin_198(self, filter_value):
        """
        Encode the tag to binary with sgtin-198 coding scheme

        See 14.5.1.2 on the EPC Tag Data Standard
        """
        # ┌──────────┬──────┬─────────────────────────────────┬──────┐
        # │EPC HEADER│FILTER│              GTIN               │SERIAL│
        # │    8     │  3   │               47                │ 140  │
        # ├──────────┼──────┼─────────┬──────────────┬────────┼──────┤
        # │EPC HEADER│FILTER│PARTITION│COMPANY PREFIX│ITEM REF│SERIAL│
        # │    8     │  3   │    3    │    20-40     │  24-4  │ 140  │
        # └──────────┴──────┴─────────┴──────────────┴────────┴──────┘

        # EPC Header
        # 8-bits
        #
        # for sgtin-96 is 0x36
        binary = utils.encode_integer(0x36, 8)

        # Filter
        # 3 bits
        binary += utils.encode_integer(int(filter_value.value), 3)

        # GTIN = Partition + Company Prefix + Item Ref
        # 47 bits
        binary += self._encode_gtin()

        # Serial
        binary += utils.encode_string(self.serial_number, 140)

        assert len(binary) == 198

        return utils.bin_2_hex(binary)

    @classmethod
    def decode(cls, epc_hex):
        """
        Decode and return a gtin object from the given EPC.
        """
        header = epc_hex[:2]
        if header == HeaderHex.SGTIN_96.value:
            return cls._decode_sgtin_96(utils.hex_2_bin(epc_hex, 96))
        elif header == HeaderHex.SGTIN_198.value:
            return cls._decode_sgtin_198(utils.hex_2_bin(epc_hex, 198))
        else:
            raise DecodingError("{} is not a valid header for SGTIN".format(header))

    @classmethod
    def _decode_sgtin_96(cls, epc_binary):
        """
        Decode and return a gtin object from the given EPC.
        """
        if len(epc_binary) != 96:
            raise DecodingError(
                "sgtin-96 EPCs should have 96 bits. Found {}".format(len(epc_binary))
            )
        # ┌──────────┬──────┬─────────────────────────────────┬──────┐
        # │EPC HEADER│FILTER│              GTIN               │SERIAL│
        # │    8     │  3   │               47                │ 38   │
        # └──────────┴──────┴─────────────────────────────────┴──────┘
        sgtin_96_struct = struct.Struct("8s 3s 47s 38s")
        header, filter_value, gtin, serial = sgtin_96_struct.unpack(epc_binary)
        company_prefix, indicator, item_ref = cls._decode_gtin(gtin)
        return cls(company_prefix, indicator, item_ref, utils.decode_integer(serial))

    @classmethod
    def _decode_sgtin_198(cls, epc_binary):
        """
        Decode and return a gtin object from the given EPC.
        """
        if len(epc_binary) != 198:
            raise DecodingError(
                "sgtin-198 EPCs should have 198 bits. Found {}".format(len(epc_binary))
            )
        # ┌──────────┬──────┬─────────────────────────────────┬──────┐
        # │EPC HEADER│FILTER│              GTIN               │SERIAL│
        # │    8     │  3   │               47                │ 140  │
        # └──────────┴──────┴─────────────────────────────────┴──────┘

        sgtin_198_struct = struct.Struct("8s 3s 47s 140s")
        header, filter_value, gtin, serial = sgtin_198_struct.unpack(epc_binary)
        company_prefix, indicator, item_ref = cls._decode_gtin(gtin)
        return cls(company_prefix, indicator, item_ref, utils.decode_string(serial))

    @classmethod
    def from_sgtin(cls, gtin, serial_number, company_prefix_len=None):
        """
        Create an EPC by translating GTIN

        When translating from a GTIN to the EPC, it is necessary to
        know the length of the GS1 Company Prefix that was used to
        construct the GTIN.

        This is because the length of the GS1 Company Prefix is
        variable and these digits must be separated from the
        remainder of the key to construct the EPC URI.

        You can either provide a company_prefix_len or the library will
        calculate one using a lookup table. This could be slow the first
        time around as the massive lookup table is downloaded and loaded
        into a map.

        :param gtin: 14 digit GTIN including indicator and check digit
        :param serial_number: Serial number for the GTIN
        :param company_prefix_len: Length of the company prefix
        """
        assert len(gtin) == 14, "GTIN must be 14 digits"

        if company_prefix_len is None:
            # Lookup the company prefix len if not provided.
            # This is expensive the first time
            company_prefix_len = utils.get_gcp_length(gtin)

        return cls(
            # First digit of GTIN
            indicator=gtin[0],
            # Second to the length of company prefix
            company_prefix=gtin[1:][:company_prefix_len],
            # After company prefix, excluding check digit
            item_ref=gtin[(1 + company_prefix_len) : -1],
            serial_number=serial_number,
        )

    @property
    def gtin(self):
        """
        Return the GTIN in "plain" syntax
        """
        gtin_wo_check_digit = "".join(
            [
                self.indicator,
                self.company_prefix,
                self.item_ref.zfill(12 - len(self.company_prefix)),
            ]
        )
        return gtin_wo_check_digit + utils.calculate_check_digit(gtin_wo_check_digit)

    def get_gs1_element_string(self):
        """
        Return a GS1 element string for SGTIN
        """
        return "".join(
            [
                # GS1 Application identifier for GTIN is 01
                "(01)",
                self.gtin,
                # GS1 Application identifier for serial number 21
                "(21)",
                self.serial_number,
            ]
        )
