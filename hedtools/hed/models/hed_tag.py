from hed.schema.hed_schema_constants import HedKey


class HedTag:
    """
        A single HedTag in a string, keeps track of original value and positioning
    """

    def __init__(self, hed_string, span=None, hed_schema=None):
        """

        Parameters
        ----------
        hed_string : str
            Source hed string for this tag
        span : (int, int)
            The start and end indexes of the tag in the hed_string.
        hed_schema: HedSchema or None
            A convenience parameter that will calculate canonical forms on creation.
            You will not be able to get issues out, so this is mostly discouraged outside test code or similar.
        """
        self._hed_string = hed_string
        if span is None:
            span = (0, len(hed_string))
        # This is the span into the original hed string for this tag
        self.span = span

        # If this is present, use this as the org tag for most purposes.  This is generally only filled out
        # if the tag has a name_prefix added, or is an expanded def.
        self._tag = None

        # The long form of the tag, if generated.
        self._long_tag = None

        # offset into _long_tag where the short tag starts at.
        self._short_tag_index = None

        # offset into _long_tag where the base_tag ends at.  The "base tag" is the long form with no extension/value.
        self._extension_index = None

        self._library_prefix = self._get_library_prefix(self.org_tag)

        # This is the schema this tag was converted to.
        self._schema = None
        self._schema_entry = None

        if hed_schema:
            self.convert_to_canonical_forms(hed_schema)

        self.is_definition = False

    @property
    def library_prefix(self):
        """
            Returns the library prefix for this tag if one exists.

        Returns
        -------
        prefix: str
            The library prefix, including the colon.
        """
        return self._library_prefix

    @property
    def short_tag(self):
        """
            Returns the short version of the tag, including value or extension

            Note: only valid after calling convert_to_canonical_forms
        Returns
        -------
        short_tag: str
            The short version of the tag, including value or extension
        """
        if self._short_tag_index is None:
            return str(self)

        return self._library_prefix + self._long_tag[self._short_tag_index:]

    @property
    def base_tag(self):
        """
            Returns the long version of the tag, without value or extension

            Note: only valid after calling convert_to_canonical_forms
        Returns
        -------
        base_tag: str
            The long version of the tag, without value or extension
        """
        if self._extension_index is None:
            return str(self)

        return self._long_tag[:self._extension_index]

    @property
    def short_base_tag(self):
        """
            Returns just the short non-extension portion of a tag.

            e.g. ParentNodes/Def/DefName would return just "Def"

        Returns
        -------
        base_tag: str
            The short non-extension port of a tag.
        """
        if self._extension_index is None:
            return str(self)

        return self._long_tag[self._short_tag_index:self._extension_index]

    @short_base_tag.setter
    def short_base_tag(self, new_tag_val):
        """
            Change the short term of the tag.

            Note: This does not change the long form location, so only set this on tags with the same parent node.

        Parameters
        ----------
        new_tag_val : str
            The new short_base_tag for this tag.  Generally this is used to swap def to def-expand.
        Returns
        -------

        """
        long_part = self._long_tag[:self._short_tag_index]
        self._long_tag = f"{long_part}{new_tag_val}/{self.extension_or_value_portion}"
        self._extension_index = self._short_tag_index + len(new_tag_val)

        if self._schema:
            self._update_schema_entry()

    @property
    def org_base_tag(self):
        """
            Returns the original version of the tag, without value or extension

            Warning: This could be empty if the original tag had a name_prefix prepended.
                eg a column where "Label/" is prepended, thus the column value has zero base portion.

            Note: only valid after calling convert_to_canonical_forms
        Returns
        -------
        base_tag: str
            The original version of the tag, without value or extension
        """
        if self._extension_index is None:
            return str(self)

        # This mess could be optimized better
        extension_len = len(self.extension_or_value_portion)
        if not extension_len:
            return self.tag

        org_len = len(self.tag)
        if org_len == extension_len:
            return ""

        return self.tag[:org_len - (extension_len + 1)]

    def tag_modified(self):
        """
            Returns true if this tag has been modified from its original form.

            Modifications can include adding a column name_prefix.

        Returns
        -------
        was_modified: bool

        """
        return bool(self._tag)

    @property
    def tag(self):
        """
            Returns the entire user editable attribute in the tag

            Note: only valid after calling convert_to_canonical_forms
        Returns
        -------
        tag: str
            The custom set user version of the tag.
        """
        if self._tag:
            return self._tag

        return self.org_tag

    # Honestly this should probably be removed
    # this should be replaced with a "set long tag" which updates the short and long versions automatically.
    @tag.setter
    def tag(self, new_tag_val):
        """
            Allows you to overwrite the tag output text.

            Primarily used to expand def tags.

            Note: only valid after calling convert_to_canonical_forms

        Parameters
        ----------
        new_tag_val : str
            New (implicitly long form) of tag to set
        """
        if self._long_tag:
            raise ValueError("Can only edit tags before calculating canonical forms. " +
                             "This could be updated to instead remove computed forms.")
        self._tag = new_tag_val

    @property
    def extension_or_value_portion(self):
        """Gets the extension or value portion at the end of a hed tag, if one exists

        Generally this is just the portion after the last slash.  Note: This tag must have been computed first.

        Returns
        -------
        str
            The tag name.
        """
        if self._extension_index is None:
            return str(self)

        return self._long_tag[self._extension_index + 1:]

    @property
    def long_tag(self):
        """
            Returns the long form of the tag if it exists, otherwise returns the default tag form.

        Returns
        -------
        long_tag: str
            The long form of this tag.
        """
        if self._long_tag is None:
            return str(self)
        return self._long_tag

    @property
    def org_tag(self):
        """
            Returns the original unmodified tag.

        Returns
        -------
        original_tag: str
            The original unmodified tag.
        """
        return self._hed_string[self.span[0]:self.span[1]]

    def __str__(self):
        """
        Convert this HedTag to a string

        Returns
        -------
        str
            Return the original tag if we haven't set a new tag.(e.g. short to long)
        """
        if self._long_tag:
            return self._long_tag

        if self._tag:
            return self._tag

        return self._hed_string[self.span[0]:self.span[1]]

    def _str_no_long_tag(self):
        if self._tag:
            return self._tag

        return self._hed_string[self.span[0]:self.span[1]]

    def add_prefix_if_not_present(self, required_prefix):
        """Add a name_prefix to this tag *unless* the tag is already formatted.

        This means we verify the tag does not have the required name_prefix, or any partial name_prefix

        Ex:
        Required: KnownTag1/KnownTag2
        Case 1: KnownTag1/KnownTag2/ColumnValue
            Will not be changed, has name_prefix already
        Case 2: KnownTag2/ColumnValue
            Will not be changed, has partial name_prefix already
        Case 3: ColumnValue
            Prefix will be added.

        Parameters
        ----------
        required_prefix : str
            The full name_prefix to add if not present
        """
        checking_prefix = required_prefix
        while checking_prefix:
            if self.lower().startswith(checking_prefix.lower()):
                return
            slash_index = checking_prefix.find("/") + 1
            if slash_index == 0:
                break
            checking_prefix = checking_prefix[slash_index:]
        self._tag = required_prefix + self.org_tag

    def lower(self):
        """Convenience function, equivalent to str(self).lower()"""
        return str(self).lower()

    def replace_placeholder(self, placeholder_value):
        """
            If this tag a placeholder character(#), replace them with the placeholder value.

        Parameters
        ----------
        placeholder_value : str
            Value to replace placeholder with.
        """
        if "#" in self.org_tag:
            if self._long_tag:
                # This could possibly be more efficient
                self._tag = self.org_tag.replace("#", placeholder_value)
                self._long_tag = self._long_tag.replace("#", placeholder_value)
            else:
                self._tag = self.org_tag.replace("#", placeholder_value)

    def convert_to_canonical_forms(self, hed_schema):
        """
            This updates the internal tag states from the schema, and sets the schema entry.

        Parameters
        ----------
        hed_schema : HedSchema
            The schema to use to validate this tag

        Returns
        -------
        conversion_issues: [{}]
            A list of issues found during conversion
        """
        if not hed_schema:
            return self._convert_key_tags_to_canonical_form()

        tag_entry, remainder, tag_issues = hed_schema.find_tag_entry(self, self.library_prefix)
        self._schema_entry = tag_entry
        self._schema = hed_schema
        # todo: now that we always have a schema entry, have these get values from those instead.
        if self._schema_entry:
            tag_name = tag_entry.long_tag_name
            self._long_tag = self.library_prefix + tag_name + remainder
            self._short_tag_index = len(self.library_prefix) \
                                    + len(tag_entry.long_tag_name) - len(tag_entry.short_tag_name)
            self._extension_index = len(self.library_prefix) + len(tag_name)
        else:
            self._long_tag = remainder

        return tag_issues

    def get_stripped_unit_value(self):
        """
        Returns the extension portion of the tag if it exists, without the units.

        eg 'Duration/3 ms' will return '3'

        Parameters
        ----------

        Returns
        -------
        stripped_unit_value: str
            The extension portion with the units removed.
        unit: str or None
            None if no valid unit found.
        """
        tag_unit_classes = self.unit_classes
        stripped_value, unit = self._get_tag_units_portion(tag_unit_classes)
        if stripped_value:
            return stripped_value, unit

        return self.extension_or_value_portion, None

    @property
    def unit_classes(self):
        """
            Returns a dict of all the unit classes this tag accepts.

            Returns empty dict if this is not a unit class tag.

        Parameters
        ----------
        Returns
        -------
        unit_classes: {str: HedSchemaEntry}
            A dict of unit classes this tag accepts.
        """
        if self._schema_entry:
            return self._schema_entry.unit_classes
        return {}

    @property
    def value_classes(self):
        """
            Returns a dict of all the value classes this tag accepts.

            Returns empty dict if this is not a value tag.

        Parameters
        ----------
        Returns
        -------
        value_classes: {str: HedSchemaEntry}
            A dict of value classes this tag accepts.
        """
        if self._schema_entry:
            return self._schema_entry.value_classes
        return {}

    @property
    def attributes(self):
        """
            Returns a dict of all the attributes this tag has.

            Returns empty dict if this is not a value tag.

        Parameters
        ----------
        Returns
        -------
        attributes: {str: HedSchemaEntry}
            A dict of attributes this tag has.
        """
        if self._schema_entry:
            return self._schema_entry.attributes
        return {}

    def tag_exists_in_schema(self):
        """
            Gets the schema entry for this tag.

            Note: This does NOT assure this is a valid tag.
        Returns
        -------
        tag_exists: bool
            Returns true if this tag exists
        """
        return bool(self._schema_entry)

    def is_takes_value_tag(self):
        """
            Returns true if this is a takes value tag
        Returns
        -------
        is_value_tag: bool
        """
        if self._schema_entry:
            return self._schema_entry.has_attribute(HedKey.TakesValue)
        return False

    def is_unit_class_tag(self):
        """
            Returns true if this is a unit class tag
        Returns
        -------
        is_unit_class_tag: bool
        """
        if self._schema_entry:
            return bool(self._schema_entry.unit_classes)
        return False

    def is_value_class_tag(self):
        """
            Returns true if this is a value class tag

        Returns
        -------
        is_value_class_tag: bool
        """
        if self._schema_entry:
            return bool(self._schema_entry.value_classes)
        return False

    def is_basic_tag(self):
        """
            Returns true if this is a known tag with no extension or value.

        Returns
        -------
        is_basic_tag: bool
        """
        return bool(self._schema_entry and not self.extension_or_value_portion)

    def has_attribute(self, attribute):
        """
            Returns true if this is an attribute this tag has.

        Returns
        -------
        has_attribute: bool
        """
        if self._schema_entry:
            return self._schema_entry.has_attribute(attribute)
        return False

    def is_extension_allowed_tag(self):
        """Checks to see if the tag has the 'extensionAllowed' attribute. It will strip the tag until there are no more
        slashes to check if its ancestors have the attribute.

        Parameters
        ----------
        Returns
        -------
        tag_takes_extension: bool
            True if the tag has the 'extensionAllowed' attribute. False, if otherwise.
        """
        if self.is_takes_value_tag():
            return False

        if self._schema_entry:
            return self._schema_entry.any_parent_has_attribute(HedKey.ExtensionAllowed)
        return False

    def get_tag_unit_class_units(self):
        """Gets the unit class units associated with a particular tag.

        Parameters
        ----------
        Returns
        -------
        []
            A list containing the unit class units associated with a particular tag. An empty list will be returned if
            the tag doesn't have unit class units associated with it.

        """
        units = []
        unit_classes = self.unit_classes
        for unit_class_entry in unit_classes.values():
            units += unit_class_entry.unit_class_units.keys()

        return units

    def get_unit_class_default_unit(self):
        """Gets the default unit class unit for this tag

        Parameters
        ----------
        Returns
        -------
        str
            The default unit class unit associated with the specific tag. If the tag doesn't have a unit class then an
            empty string is returned.

        """
        default_unit = ''
        unit_classes = self.unit_classes.values()
        if unit_classes:
            first_unit_class_entry = list(unit_classes)[0]
            default_unit = first_unit_class_entry.has_attribute(HedKey.DefaultUnits, return_value=True)

        return default_unit

    def base_tag_has_attribute(self, tag_attribute):
        """Checks to see if the tag has a specific attribute.

        Parameters
        ----------
        tag_attribute: str
            A tag attribute.
        Returns
        -------
        bool
            True if the tag has the specified attribute. False, if otherwise.

        """
        if not self._schema_entry:
            return False

        return self._schema_entry.base_tag_has_attribute(tag_attribute)

    def any_parent_has_attribute(self, attribute):
        """Checks to see if the tag (or any of its parents) have the given attribute.

        Parameters
        ----------
        attribute: str
            The name of the attribute to check for.
        Returns
        -------
        tag_has_attribute: bool
            True if the tag has the given attribute. False, if otherwise.
        """
        if self._schema_entry:
            return self._schema_entry.any_parent_has_attribute(attribute=attribute)

    def _update_schema_entry(self):
        """
            Sets the _schema_entry pointer based off the current schema.

        Returns
        -------

        """
        new_entry = None
        if self.extension_or_value_portion:
            new_entry = self._schema.get_tag_entry(self.base_tag.lower() + "/#")
        if new_entry is None:
            new_entry = self._schema.get_tag_entry(self.base_tag.lower())
        self._schema_entry = new_entry

    def _convert_key_tags_to_canonical_form(self):
        """
            Finds the canonical form for basic known tags such as definition and def.

            todo: This should have default HedTagEntries to point to eventually
        Returns
        -------
        issues_list: [{}]
            Always empty.
        """
        tags_to_identify = ["onset", "definition", "offset", "def-expand", "def"]
        for key_tag in tags_to_identify:
            is_key_tag = self._check_tag_starts_with(str(self), key_tag)
            if is_key_tag is not None:
                self._long_tag = str(self)
                self._extension_index = len(str(self)) - len(is_key_tag)
                self._short_tag_index = self._extension_index - len(key_tag)
                break

        return []

    @staticmethod
    def _check_tag_starts_with(hed_tag, target_tag_short_name):
        """ Check if a given tag starts with a given string, and returns the tag with name_prefix removed if it does.

        Parameters
        ----------
        hed_tag : str
            A single input tag
        target_tag_short_name : str
            The string to match e.g. find target_tag_short_name in hed_tag
        Returns
        -------
            str: the tag without the removed name_prefix, or None
        """
        hed_tag_lower = hed_tag.lower()
        found_index = hed_tag_lower.find(target_tag_short_name)

        if found_index == -1:
            return None

        if found_index == 0 or hed_tag_lower[found_index - 1] == "/":
            return hed_tag[found_index + len(target_tag_short_name):]
        return None

    def _get_library_prefix(self, org_tag):
        first_slash = org_tag.find("/")
        first_colon = org_tag.find(":")

        if first_colon != -1:
            if first_slash != -1 and first_colon > first_slash:
                return ""

            return org_tag[:first_colon + 1]
        return ""

    def _get_tag_units_portion(self, tag_unit_classes):
        """Checks to see if the specified string has a valid unit, and removes it if so.

        Parameters
        ----------
        tag_unit_classes: [UnitClassEntry]
            A list of valid unit class entries for this tag
        Returns
        -------
        stripped_value: str
            A tag_unit_values with the valid unit removed, if one was present.
            Otherwise, returns None

        """
        value, _, units = self.extension_or_value_portion.rpartition(" ")
        if not units:
            return None, None

        for unit_class_entry in tag_unit_classes.values():
            all_valid_unit_permutations = unit_class_entry.derivative_units

            possible_match = self._find_modifier_unit_entry(units, all_valid_unit_permutations)
            if possible_match and not possible_match.has_attribute(HedKey.UnitPrefix):
                return value, units

            # Repeat the above, but as a prefix
            possible_match = self._find_modifier_unit_entry(value, all_valid_unit_permutations)
            if possible_match and possible_match.has_attribute(HedKey.UnitPrefix):
                return units, value

        return None, None

    @staticmethod
    def _find_modifier_unit_entry(units, all_valid_unit_permutations):
        possible_match = all_valid_unit_permutations.get(units)
        if not possible_match or not possible_match.has_attribute(HedKey.UnitSymbol):
            possible_match = all_valid_unit_permutations.get(units.lower())
            if possible_match and possible_match.has_attribute(HedKey.UnitSymbol):
                possible_match = None

        return possible_match