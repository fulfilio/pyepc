from .epc import HeaderHex
from .exceptions import DecodingError
from .sgtin import SGTIN
from .sscc import SSCC


__version__ = "0.5.0"


def decode(epc_hex):
    """
    Decode and return a gtin object from the given EPC.

    The returned class is based on the type of EPC.
    """
    header_class_map = {
        HeaderHex.SGTIN_96.value: SGTIN,
        HeaderHex.SGTIN_198.value: SGTIN,
        HeaderHex.SSCC.value: SSCC,
    }
    # Step 1: Extract the most significant 8 bits (or the)
    # first two characters of the epc_hex
    header = epc_hex[:2]
    try:
        header_class_map[header]
    except KeyError:
        raise DecodingError("Cannot decode EPC with header {}".format(header))

    # Step 2:
    return header_class_map[header].decode(epc_hex)
