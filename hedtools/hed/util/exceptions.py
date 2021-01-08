from hed.util.error_types import SchemaErrors


class SchemaFileError(Exception):
    """Exception raised when a schema XML file cannot be parsed due to being malformed, file IO, etc."""
    def __init__(self, error_type, message, filename):
        self.error_type = error_type
        self.message = message
        self.filename = filename

    SCHEMA_ERROR_PREFIX = "ERROR: "

    def format_error_message(self, include_tabbing=True, return_string_only=False,
                             display_filename=None):
        """This takes a SchemaFileError exception and translates it to human readable

        Parameters
        ----------
        include_tabbing : bool
            Prefixes string with a tab if True
        return_string_only : bool
            If True, returns a string rather than an "error object"
        display_filename : str or None
            Overrides the filename from the error if present.
            This is useful on the web code and similar that deals with temporary filenames.
        Returns
        -------
        error_list: [{}]
            A list(of one) error formatted into a human readable dictionary.
        """
        error_prefix = self.SCHEMA_ERROR_PREFIX
        if include_tabbing:
            error_prefix = "\t" + error_prefix

        error_type, message, filename = self.error_type, self.message, self.filename
        if display_filename:
            filename = display_filename
        error_types = {
            SchemaErrors.FILE_NOT_FOUND: f"{error_prefix}{message}.  '{filename}'",
            SchemaErrors.CANNOT_PARSE_XML: f"{error_prefix}Cannot parse schema XML file: "
                                           f"{message}.  '{filename}'",
        }
        default_error_message = f'{error_prefix}Internal Error'
        error_message = error_types.get(error_type, default_error_message)

        error_object = {'code': error_type,
                        'message': error_message}

        if return_string_only:
            return error_object['message']

        return [error_object]