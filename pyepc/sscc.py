from builtins import str
from collections import namedtuple
from enum import Enum
import struct

from . import utils
from .epc import EPC
from .exceptions import EncodingError, DecodingError


class SSCC(EPC):
    """
    The Serial Shipping Container Code (SSCC) is the GS1
    Identification Key used to identify a logistic unit.

    Encoding
    --------

    # Always import from the root of the package
    >>> from pyepc import SSCC

    # Build an SSCC object from the company prefix, extension digit
    # and a serial reference for the logistics unit
    >>> company_prefix = '0614141'
    >>> extension_digit = '1'
    >>> serial_ref = '234567890'
    >>> sscc = SSCC(company_prefix, extension_digit, serial_ref)

    # Get pure identity URI
    >>> sscc.pure_identity_uri
    'urn:epc:id:sscc:0614141.1234567890'

    # Get GS1 element string
    >>> sscc.gs1_element_string
    '(00)106141412345678908'

    # Get the tag URI
    >>> sscc.get_tag_uri()
    'urn:epc:tag:sscc-96:0.0614141.1234567890'

    # If you want to encode the EPC into the EPC bank of an RFID
    # tag, you will need the hex encoded value of the tag uri.
    >>> sscc.encode()
    '3114257BF4499602D2000000'

    Decoding
    --------

    >>> sscc.decode('3114257BF4499602D2000000')
    '<urn:epc:id:sscc:0614141.1234567890>'

    EPC from SSCC Code
    ------------------

    >>> SSCC.from_sscc('106141412345678908')
    '<urn:epc:id:sscc:0614141.1234567890>'

    However, this has to lookup the company prefix length from the GS1
    prefix list and could be expensive the first time. So if you already
    know your company prefix length, then pass that along

    >>> company_prefix_len = len('0614141')
    >>> SSCC.from_sscc('106141412345678908', company_prefix_len)
    '<urn:epc:id:sscc:0614141.1234567890>'
    """

    __scheme__ = "sscc"

    class FilterValues(Enum):
        ALL_OTHERS = "0"
        RESERVED_1 = "1"
        CASE = "2"
        RESERVED_3 = "3"
        RESERVED_4 = "4"
        RESERVED_5 = "5"
        UNIT_LOAD = "6"
        RESERVED_7 = "7"

    class BinarySchemes(Enum):
        SSCC_96 = "sscc-96"

    # Implementation of SSCC Partition table that identifies
    # partition value for different lengths of GS1 company
    # prefix
    # ┌─────────┬──────────────┬────────┐
    # │PARTITION│COMPANY PREFIX│ITEM REF│
    # │    3    │    20-40     │  24-4  │
    # └─────────┴──────────────┴────────┘
    # p - partition value
    # m - Company prefix - bits
    # l - Company prefix - digits
    # n - Extension digit and serial reference bits
    PTR = namedtuple("PTR", "p m l n")
    partition_table = [
        PTR(p=0, m=40, l=12, n=18),
        PTR(p=1, m=37, l=11, n=21),
        PTR(p=2, m=34, l=10, n=24),
        PTR(p=3, m=30, l=9, n=28),
        PTR(p=4, m=27, l=8, n=31),
        PTR(p=5, m=24, l=7, n=34),
        PTR(p=6, m=20, l=6, n=38),
    ]

    def __init__(
        self,
        company_prefix,
        extension_digit,
        serial_ref,
        default_binary_scheme=BinarySchemes.SSCC_96,
        default_filter_value=FilterValues.ALL_OTHERS,
    ):
        self.company_prefix = str(company_prefix)
        self.validate_company_prefix()

        self.extension_digit = str(extension_digit)
        self.serial_ref = str(serial_ref)

        # The number of characters in the company_prefix and serial
        # must total 17
        self.extn_and_serial_ref = "{}{}".format(extension_digit, serial_ref).zfill(
            17 - len(self.company_prefix)
        )

        # Store the defaults for creating tag URIs.
        self.default_binary_scheme = default_binary_scheme
        self.default_filter_value = default_filter_value

    def get_uri_body_parts(self):
        return [
            self.company_prefix,
            self.extn_and_serial_ref,
        ]

    def validate_sscc_96(self):
        """
        The SSCC-96 encoding allows for numeric-only
        serial numbers, without leading zeros, whose value
        is less than 2^38 (that is, from 0 through
        274,877,906,943, inclusive)
        """
        try:
            int(self.extn_and_serial_ref)
        except ValueError:
            raise EncodingError(
                "`sscc-96` encoding requires numeric-only "
                "serial numbers. Serial: '{}'".format(self.serial_ref)
            )
        return True

    def _encode_sscc(self):
        """
        Encode the SSCC part of the URI
        """
        for ptr in self.partition_table:
            if ptr.l == self.company_prefix_digits:  # noqa
                break
        else:
            raise EncodingError("Length of Company Prefix is invalid")

        return utils.encode_partition_table(
            ptr.p, self.company_prefix, ptr.m, self.extn_and_serial_ref, ptr.n, 61
        )

    @classmethod
    def _decode_sscc(cls, sscc_binary):
        """
        Decode the SSCC part of the epc binary

        :return: A tuple of company prefix, serial ref
        """
        assert len(sscc_binary) == 61

        partition = int(utils.decode_integer(sscc_binary[:3]))
        for ptr in cls.partition_table:
            if ptr.p == partition:  # noqa
                break
        else:
            raise DecodingError("Length of Company Prefix is invalid")

        return utils.decode_partition_table(
            sscc_binary,
            ptr.m,
            ptr.l,
            ptr.n,
            # Total of 13 chars
            17 - ptr.l,
        )

    def encode_sscc_96(self, filter_value):
        """
        Encode the tag to binary with sscc-96 coding scheme

        See 14.5.2 on the EPC Tag Data Standard
        """
        # ┌──────────┬──────┬────────────────────────────────────┬────────┐
        # │EPC HEADER│FILTER│                SSCC                │Reserved│
        # │    8     │  3   │                 61                 │   24   │
        # ├──────────┼──────┼─────────┬──────────────┬───────────┼────────┤
        # │EPC HEADER│FILTER│PARTITION│COMPANY PREFIX│SERIAL REF │RESERVED│
        # │    8     │  3   │    3    │    20-40     │   38-18   │        │
        # └──────────┴──────┴─────────┴──────────────┴───────────┴────────┘

        # EPC Header
        # 8-bits
        #
        # for sscc-96 is 0x31
        binary = utils.encode_integer(0x31, 8)

        # Filter
        # 3 bits
        binary += utils.encode_integer(int(filter_value.value), 3)

        # SSCC = Partition + Company Prefix + Serial Ref
        # 61 bits
        binary += self._encode_sscc()

        # Fill the reserved bits with 0
        binary += "0" * 24

        assert len(binary) == 96

        return utils.bin_2_hex(binary)

    @classmethod
    def decode(cls, epc_hex):
        """
        Decode and return a SSCC object from the given EPC.
        """
        header = epc_hex[:2]
        if header == "31":
            return cls._decode_sscc_96(utils.hex_2_bin(epc_hex, 96))
        else:
            raise DecodingError("{} is not a valid header for SSCC".format(header))

    @classmethod
    def _decode_sscc_96(cls, epc_binary):
        """
        Decode and return a SSCC object from the given EPC.
        """
        if len(epc_binary) != 96:
            raise DecodingError(
                "sscc-96 EPCs should have 96 bits. Found {}".format(len(epc_binary))
            )
        # ┌──────────┬──────┬────────────────────────────────────┬────────┐
        # │EPC HEADER│FILTER│                SSCC                │Reserved│
        # │    8     │  3   │                 61                 │        │
        # └──────────┴──────┴────────────────────────────────────┴────────┘
        sscc_96_struct = struct.Struct("8s 3s 61s 24s")
        header, filter_value, sscc, reserved = sscc_96_struct.unpack(epc_binary)
        company_prefix, serial_ref = cls._decode_sscc(sscc)
        return cls(
            company_prefix,
            serial_ref[0],
            serial_ref[1:],
        )

    @classmethod
    def from_sscc(cls, sscc, company_prefix_len=None):
        """
        Create an EPC by translating SSCC

        When translating from a SSCC to the EPC, it is necessary to
        know the length of the GS1 Company Prefix that was used to
        construct the SSCC.

        This is because the length of the GS1 Company Prefix is
        variable and these digits must be separated from the
        remainder of the key to construct the EPC URI.

        You can either provide a company_prefix_len or the library will
        calculate one using a lookup table. This could be slow the first
        time around as the massive lookup table is downloaded and loaded
        into a map.

        :param sscc: Full SSCC number
        :param company_prefix_len: Length of the company prefix
        """
        if company_prefix_len is None:
            # Lookup the company prefix len if not provided.
            # This is expensive the first time
            company_prefix_len = utils.get_gcp_length(sscc)

        return cls(
            # First digit of SSCC
            extension_digit=sscc[0],
            # Second to the length of company prefix
            company_prefix=sscc[1:][:company_prefix_len],
            # After company prefix, excluding check digit
            serial_ref=sscc[1 + company_prefix_len : -1],
        )

    @property
    def sscc(self):
        """
        Return the SSCC in "plain" syntax
        """
        sscc_wo_check_digit = "".join(
            [
                self.extension_digit,
                self.company_prefix,
                self.serial_ref.zfill(16 - len(self.company_prefix)),
            ]
        )
        return sscc_wo_check_digit + utils.calculate_check_digit(sscc_wo_check_digit)

    def get_gs1_element_string(self):
        """
        Return a GS1 element string for SSCC
        """
        return "".join(
            [
                # GS1 Application identifier for SSCC is 00
                "(00)",
                self.sscc,
            ]
        )
