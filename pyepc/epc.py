from enum import Enum


class HeaderHex(Enum):
    """
    Enum for the header hex values.

    The header hex values are the first two characters of the EPC.

    Read section 14.2 of the GS1 EPC Tag Data Standard for more information.
    """

    SGTIN_96 = "30"
    SGTIN_198 = "36"
    SSCC = "31"


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
    def gs1_element_string(self):
        return self.get_gs1_element_string()

    def get_gs1_element_string(self):
        raise NotImplementedError()

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
        return ":".join(["urn:epc:id", self.__scheme__, uri_body])

    def __repr__(self):
        return "<{}>".format(self.pure_identity_uri)

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

        method_name = "encode_{}".format(binary_scheme.value.replace("-", "_"))

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
        validation_method = "validate_{}".format(binary_scheme.value.replace("-", "_"))
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
