class EPCException(Exception):
    pass


class UnknownEncodingScheme(EPCException):
    pass


class EncodingError(EPCException):
    pass


class DecodingError(EPCException):
    pass
