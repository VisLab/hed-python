


class BidsMapper:
    """Handles mapping a BIDS event study.

        Private Functions and variables column and row indexing starts at 0.
        Public functions and variables indexing starts at 1(or 2 if has column names)"""
    def __init__(self, json_def_files=None, tag_columns=None, column_prefix_dictionary=None,
                 hed_dictionary=None, attribute_columns=None):
        """Constructor for ColumnMapper

        Parameters
        ----------
        json_def_files : ColumnDefGroup or string or list
            A list of ColumnDefinitionGroups or filenames to gather ColumnDefinitions from.
        tag_columns: list
             A list of ints containing the columns that contain the HED tags.  If the column is otherwise unspecified,
             it will convert this column type to HEDTags
        column_prefix_dictionary: dict
             A dictionary with keys pertaining to the required HED tag columns that correspond to tags that need to be
             prefixed with a parent tag path. For example, prefixed_needed_tag_columns = {3: 'Event/Description',
             4: 'Event/Label/', 5: 'Event/Category/'} The third column contains tags that need Event/Description/ prepended to them,
             the fourth column contains tags that need Event/Label/ prepended to them, and the fifth column contains tags
             that needs Event/Category/ prepended to them.
        hed_dictionary: HedDictionary
            Used to create a TagValidator, which is then used to validate the entries in value and category entries.
        attribute_columns: str or int or [str] or [int]
             A list of column names or numbers to treat as attributes.
        """
        # This points to column_type entries based on column names or indexes if columns have no column_name.
        self.column_defs = {}
        # Maps column number to column_entry.  This is what's actually used by most code.
        self._final_column_map = {}

        self._column_map = None
        self._tag_columns = []
        self._column_prefix_dictionary = {}

        self._na_patterns = ["n/a", "nan"]
        self._hed_dictionary = hed_dictionary

        if json_def_files:
            self.add_json_file_defs(json_def_files)
        self.add_columns(attribute_columns)

        self.set_tag_columns(tag_columns, False)
        self.set_column_prefix_dict(column_prefix_dictionary, False)

        # finalize the column map based on initial settings.
        self._finalize_mapping()
