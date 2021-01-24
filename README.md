# Python EPC toolkit

This package provides utilities for building, encoding, decoding
and translating EPCs.

## Installation

```
pip install pyepc
```

## Usage

### Encoding EPC from company prefix and item reference

```python
from pyepc import SGTIN

# Build an sgtin object from company prefix, item ref and serial number
company_prefix = '0614141'
item_ref = '812345'
serial = '12345'
sgtin = SGTIN(company_prefix, item_ref, serial)

# Get pure identity URI
# urn:epc:id:sgtin:0614141.812345.12345
sgtin.pure_identity_uri

# Get the tag URI
sgtin.get_tag_uri()

# Output will be
# 'urn:epc:tag:sgtin-96:1.0614141.812345.12345'
# The sgtin-96 scheme was automatically selected as the most
# efficient binary encoding scheme for a numeric serial
# number.


# To explicitly use another encoding scheme like 'sgtin-198',
# specify the encoding scheme
sgtin.get_tag_uri(SGTIN.BinarySchemes.SGTIN_198)

# output will be
# 'urn:epc:tag:sgtin-198:1.0614141.812345.12345'

# You can also change the filter value. In this case
# 1 (for POS item) was used as the default
sgtin.get_tag_uri(
    SGTIN.BinarySchemes.SGTIN_198,
    SGTIN.FilterValues.UNIT_LOAD,
)

# output will be
# 'urn:epc:tag:sgtin-198:6.0614141.812345.12345'
# The filter value is now 6

# If you want to encode the EPC into the EPC bank of an RFID
# tag, you will need the hex encoded value of the tag uri.
sgtin.encode()

# output will be
# '3034257BF7194E4000003039'

# Similar to the `get_tag_uri` methods, you can enforce which
# scheme should be used and the filter value
sgtin.encode(
    SGTIN.BinarySchemes.SGTIN_198,
    SGTIN.FilterValues.UNIT_LOAD,
)

# output will be
# '36D4257BF7194E58B266D1A800000000000000000000000000
```

### Decoding EPC from Hex value in an EPC

If you want to convert the EPC Hex back into an EPC object, you
can use the decode method.

If you don't know the type of the code, then use the decode method

```python
from pyepc import decode
sgtin = decode('3034257BF7194E4000003039')

sgtin.company_prefix
# '0614141'

sgtin.item_ref
# '812345'

sgtin.serial_number
# '12345'
```

## Additional Resources

* [EPC Tag Data Standard](https://www.gs1.org/sites/default/files/docs/epc/GS1_EPC_TDS_i1_13.pdf)
* [Encoder/Decoder on GS1 site](https://www.gs1.org/services/epc-encoderdecoder)

## Tag translation between UPC and EPC

* [GS1 EPCglobal Tag Data Translation (TDT) 1.6](https://www.gs1.org/sites/default/files/docs/epc/tdt_1_6_RatifiedStd-20111012-i2.pdf)
* [TDT Overview](https://www.gs1.org/sites/default/files/docs/epc/tdt_1_6_Intro.pdf)
