from collections import namedtuple
from enum import Enum
import struct

from . import utils
from .exceptions import EncodingError, DecodingError


class EPC(object):
    """
    A class to represent an Electronic Product Code
    """

    def __eq__(self, other):
        return self.pure_identity_uri == other.pure_identity_uri

    @property
    def company_prefix_digits(self):
        return len(self.company_prefix)

    @property
    def pure_identity_uri(self):
        """
        A representation of EPC for use in information systems.

        This URI only contains information about the EPC itself
        and *does not have* anything specific about how the tag
        will be encoded, stored or the
        """
        # X.Y.Z
        uri_body = ".".join(self.get_uri_body_parts())

        # urn:epc:id:sgtin:X.Y.Z
        return ":".join([
            "urn:epc:id",
            self.__scheme__,
            uri_body
        ])

    def __repr__(self):
        return self.pure_identity_uri

    def get_tag_uri(self, binary_scheme=None, filter_value=None):
        """
        Generate an EPC tag URI

        The tag URI (unlike pure identity URI) contains additional
        information on all control fields in the EPC memory bank,
        and specifies encoding scheme to use when converting
        to binary.

        The implementation follows the procedure outlined in
        section 12.3.2 of the EPC Tag Data Standard

        :param binary_scheme: For each scheme (sgtin, sscc), there are one
                              or more corresponding EPC Binary coding schemes
                              that determine how the EPC is encoded into
                              binary representation for use in RFID tags.

                              When there is more than one encoding scheme,
                              the user must choose the scheme, but this package
                              selects optimal defaults if no scheme is
                              selected.

        :param filter_value: The filter value (most schemes need one). If
                             not specified, this package chooses a safe
                             default.
        """
        if binary_scheme is None:
            binary_scheme = self.default_binary_scheme

        if filter_value is None:
            filter_value = self.default_filter_value

        # First validate if the epc and the binary encoding
        # scheme make sense
        self.validate(binary_scheme)

        # 1. Start with the tag prefix
        parts = ["urn:epc:tag"]

        # 2. Add the binry coding scheme
        parts.append(binary_scheme.value)

        # 3. Add the filter if one is specified
        body_parts = self.get_uri_body_parts()
        if filter_value:
            body_parts.insert(0, filter_value.value)
        parts.append(".".join(body_parts))

        # 4/5 TODO: Handle attribute bits and user memory indicators

        # Return the tag uri
        return ":".join(parts)

    def encode(self, binary_scheme=None, filter_value=None):
        """
        Encode the tag into binary form and return the hex value

        :param binary_scheme: For each scheme (sgtin, sscc), there are one
                              or more corresponding EPC Binary coding schemes
                              that determine how the EPC is encoded into
                              binary representation for use in RFID tags.

                              When there is more than one encoding scheme,
                              the user must choose the scheme, but this package
                              selects optimal defaults if no scheme is
                              selected.

        :param filter_value: The filter value (most schemes need one). If
                             not specified, this package chooses a safe
                             default.
        """
        if binary_scheme is None:
            binary_scheme = self.guess_binary_scheme()

        if filter_value is None:
            filter_value = self.default_filter_value

        method_name = 'encode_{}'.format(binary_scheme.value.replace('-', '_'))

        return getattr(self, method_name)(filter_value)

    def guess_binary_scheme(self):
        """
        Guess the binary scheme if possible. If not possible,
        the default is returned
        """
        return self.default_binary_scheme

    def validate(self, binary_scheme):
        """
        Validate the tag contents for binary scheme.
        For example, if the scheme is sgtin-96, the serial
        number must be numeric only without leading zeros.
        """
        validation_method = 'validate_{}'.format(
            binary_scheme.value.replace('-', '_')
        )
        if hasattr(self, validation_method):
            return getattr(self, validation_method)()

    def validate_company_prefix(self):
        """
        GS1 EPC Tag Data Standard supports only GS1 Company Prefixes
        between six and twelve digits in length (inclusive).
        """
        if not 6 <= len(self.company_prefix) <= 12:
            raise ValueError(
                "GS1 EPC Tag Data Standard only support prefixes "
                "between 6 and 12 digits. Got {} instead".format(
                    len(self.company_prefix)
                )
            )


def decode(epc_hex):
    """
    Decode and return a gtin object from the given EPC.

    The returned class is based on the type of EPC.
    """
    header_class_map = {
        '30': SGTIN,
        '36': SGTIN,
    }
    # Step 1: Extract the most significant 8 bits (or the)
    # first two characters of the epc_hex
    header = epc_hex[:2]
    try:
        header_class_map[header]
    except KeyError:
        raise DecodingError(
            "Cannot decode EPC with header {}".format(header)
        )

    # Step 2:
    return header_class_map[header].decode(epc_hex)


class SGTIN(EPC):
    """
    The Serialised Global Trade Item Number EPC scheme
    is used to assign a unique identity to an instance
    of a trade item, such as a specific instance of a
    product or SKU.
    """
    __scheme__ = 'sgtin'

    class FilterValues(Enum):
        ALL_OTHERS = '0'
        POS_ITEM = '1'
        CASE = '2'
        RESERVED = '3'
        INNER_PACK = '4'
        RESERVED_2 = '5'
        UNIT_LOAD = '6'
        COMPONENT = '7'

    class BinarySchemes(Enum):
        SGTIN_96 = 'sgtin-96'
        SGTIN_198 = 'sgtin-198'

    def __init__(self, company_prefix, item_ref, serial_number="0",
                 default_binary_scheme=BinarySchemes.SGTIN_96,
                 default_filter_value=FilterValues.POS_ITEM):

        self.company_prefix = str(company_prefix)
        self.validate_company_prefix()

        # Length of company prefix + item reference
        # must be 13. So if the item_ref length is
        # smaller, pad with zeros
        self.item_ref = item_ref.zfill(13 - len(self.company_prefix))

        self.serial_number = serial_number

        # Store the defaults for creating tag URIs.
        self.default_binary_scheme = default_binary_scheme
        self.default_filter_value = default_filter_value

    def get_uri_body_parts(self):
        return [
            self.company_prefix,
            self.item_ref,
            self.serial_number
        ]

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
        if len(self.serial_number) > 1 and \
                self.serial_number.startswith('0'):
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
    PTR = namedtuple('PTR', 'p m l n')
    partition_table = [
        PTR(p=0, m=40, l=12, n=4),
        PTR(p=1, m=37, l=11, n=7),
        PTR(p=2, m=34, l=10, n=10),
        PTR(p=3, m=30, l=9, n=14),
        PTR(p=4, m=27, l=8, n=17),
        PTR(p=5, m=24, l=7, n=20),
        PTR(p=6, m=20, l=6, n=24),
    ]

    def _encode_gtin(self):
        """
        Encode the GTIN part of the URI. This is common between
        sgtin-96 and sgtin-198
        """
        for ptr in self.partition_table:
            if ptr.l == self.company_prefix_digits:     # noqa
                break
        else:
            raise EncodingError("Length of Company Prefix is invalid")

        return utils.encode_partition_table(
            ptr.p,
            self.company_prefix,
            ptr.m,
            self.item_ref,
            ptr.n,
            47
        )

    @classmethod
    def _decode_gtin(cls, gtin_binary):
        """
        Decode the GTIN part of the epc binary
        """
        assert len(gtin_binary) == 47

        partition = int(utils.decode_integer(gtin_binary[:3]))
        for ptr in cls.partition_table:
            if ptr.p == partition:     # noqa
                break
        else:
            raise DecodingError("Length of Company Prefix is invalid")

        return utils.decode_partition_table(
            gtin_binary,
            ptr.m,
            ptr.l,
            ptr.n,
            # Total of 13 chars
            13 - ptr.l
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
        if header == '30':
            return cls._decode_sgtin_96(utils.hex_2_bin(epc_hex, 96))
        elif header == '36':
            return cls._decode_sgtin_198(utils.hex_2_bin(epc_hex, 198))
        else:
            raise DecodingError(
                "{} is not a valid header for SGTIN".format(
                    header
                )
            )

    @classmethod
    def _decode_sgtin_96(cls, epc_binary):
        """
        Decode and return a gtin object from the given EPC.
        """
        if len(epc_binary) != 96:
            raise DecodingError(
                "sgtin-96 EPCs should have 96 bits. Found {}".format(
                    len(epc_binary)
                )
            )
        # ┌──────────┬──────┬─────────────────────────────────┬──────┐
        # │EPC HEADER│FILTER│              GTIN               │SERIAL│
        # │    8     │  3   │               47                │ 38   │
        # └──────────┴──────┴─────────────────────────────────┴──────┘
        sgtin_96_struct = struct.Struct('8s 3s 47s 38s')
        header, filter_value, gtin, serial = sgtin_96_struct.unpack(
            epc_binary
        )
        company_prefix, item_ref = cls._decode_gtin(gtin)
        return cls(
            company_prefix,
            item_ref,
            utils.decode_integer(serial)
        )

    @classmethod
    def _decode_sgtin_198(cls, epc_binary):
        """
        Decode and return a gtin object from the given EPC.
        """
        if len(epc_binary) != 198:
            raise DecodingError(
                "sgtin-198 EPCs should have 198 bits. Found {}".format(
                    len(epc_binary)
                )
            )
        # ┌──────────┬──────┬─────────────────────────────────┬──────┐
        # │EPC HEADER│FILTER│              GTIN               │SERIAL│
        # │    8     │  3   │               47                │ 140  │
        # └──────────┴──────┴─────────────────────────────────┴──────┘

        sgtin_198_struct = struct.Struct('8s 3s 47s 140s')
        header, filter_value, gtin, serial = sgtin_198_struct.unpack(
            epc_binary
        )
        company_prefix, item_ref = cls._decode_gtin(gtin)
        return cls(
            company_prefix,
            item_ref,
            utils.decode_string(serial)
        )
