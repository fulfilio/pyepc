# Python EPC toolkit

This package provides utilities for building, encoding, decoding
and translating EPCs.

## Installation

```
pip install pyepc
```

## Usage

### SGTIN

```python
# Encoding
# --------

# Always import from the root of the package
>>> from pyepc import SGTIN

# You can build an epc object in many ways. If you are starting
# from an application that manages items and GS1 company prefixes
# then building an SGTIN from the components is the likely path
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

# Get a GTIN from the EPC
>>> sgtin.gtin
'80614141123458'

# You can also build a SGTIN object from the GTIN
# if a GTIN is what you have as a starting point
>>> sgtin = SGTIN.from_sgtin('80614141123458', serial_number='123456')
'<urn:epc:id:sgtin:0614141.812345.123456>'

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

# Decoding
# --------
>>> SGTIN.decode('36D4257BF7194E58B266D1A800000000000000000000000000')
'<urn:epc:id:sgtin:0614141.812345.12345>'

# EPC from GTIN
# -------------
# If all what you have is a GTIN, then you can build an EPC from it

>>> SGTIN.from_sgtin('80614141123458', '6789AB')
'<urn:epc:id:sgtin:0614141.812345.6789AB>'

# However, this has to lookup the company prefix length from the GS1
# prefix list and could be expensive the first time. So if you already
# know your company prefix length, then pass that along

>>> company_prefix_len = len('0614141')
>>> SGTIN.from_sgtin('80614141123458', '6789AB', company_prefix_len)
'<urn:epc:id:sgtin:0614141.812345.6789AB>'
```

### SSCC

```python
# Encoding
# --------

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

# Decoding
# --------

>>> sscc.decode('3114257BF4499602D2000000')
'<urn:epc:id:sscc:0614141.1234567890>'

# EPC from SSCC Code
# ------------------

>>> SSCC.from_sscc('106141412345678908')
'<urn:epc:id:sscc:0614141.1234567890>'

However, this has to lookup the company prefix length from the GS1
prefix list and could be expensive the first time. So if you already
know your company prefix length, then pass that along

>>> company_prefix_len = len('0614141')
>>> SSCC.from_sscc('106141412345678908', company_prefix_len)
'<urn:epc:id:sscc:0614141.1234567890>'
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
# '12345'

sgtin.serial_number
# '12345'
```

## Additional Resources

* [EPC Tag Data Standard](https://www.gs1.org/sites/default/files/docs/epc/GS1_EPC_TDS_i1_13.pdf)
* [Encoder/Decoder on GS1 site](https://www.gs1.org/services/epc-encoderdecoder)

## Tag translation between UPC and EPC

* [GS1 EPCglobal Tag Data Translation (TDT) 1.6](https://www.gs1.org/sites/default/files/docs/epc/tdt_1_6_RatifiedStd-20111012-i2.pdf)
* [TDT Overview](https://www.gs1.org/sites/default/files/docs/epc/tdt_1_6_Intro.pdf)
