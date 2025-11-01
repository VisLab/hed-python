"""
This module is used to create a HedSchema object from a JSON file or string.
"""

import json

from hed.errors.exceptions import HedFileError, HedExceptions
from hed.schema.hed_schema_constants import HedSectionKey, HedKey
from hed.schema.schema_io import json_constants
from hed.schema.schema_io.base2schema import SchemaLoader


class SchemaLoaderJSON(SchemaLoader):
    """Loads JSON schemas from filenames or strings.

    Expected usage is SchemaLoaderJSON.load(filename)

    SchemaLoaderJSON(filename) will load just the header_attributes
    """

    def __init__(self, filename, schema_as_string=None, schema=None, file_format=None, name=""):
        super().__init__(filename, schema_as_string, schema, file_format, name)
        self._json_data = None
        self._schema.source_format = ".json"

    def _open_file(self):
        """Parses a JSON file and returns the root dictionary."""
        try:
            if self.filename:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return json.loads(self.schema_as_string)
        except json.JSONDecodeError as e:
            raise HedFileError(HedExceptions.CANNOT_PARSE_JSON, str(e), self.name) from e

    def _get_header_attributes(self, json_data):
        """Gets the schema attributes from the JSON header"""
        return json_data.get(json_constants.HEADER_KEY, {})

    def _parse_data(self):
        self._json_data = self.input_data

        parse_order = {
            HedSectionKey.Properties: self._populate_properties,
            HedSectionKey.Attributes: self._populate_attributes,
            HedSectionKey.UnitModifiers: self._populate_unit_modifiers,
            HedSectionKey.UnitClasses: self._populate_unit_classes,
            HedSectionKey.ValueClasses: self._populate_value_classes,
            HedSectionKey.Tags: self._populate_tags,
        }
        
        self._schema.prologue = self._json_data.get(json_constants.PROLOGUE_KEY, "")
        self._schema.epilogue = self._json_data.get(json_constants.EPILOGUE_KEY, "")
        
        for section_key, parse_func in parse_order.items():
            parse_func()

    def _populate_tags(self):
        """Populate the tags section from JSON."""
        self._schema._initialize_attributes(HedSectionKey.Tags)
        tags_section = self._json_data.get(json_constants.TAGS_KEY, {})
        
        if json_constants.CHILDREN_KEY in tags_section:
            for tag_name, tag_data in tags_section[json_constants.CHILDREN_KEY].items():
                self._parse_tag(tag_name, tag_data, parent_name="")

    def _parse_tag(self, tag_name, tag_data, parent_name):
        """Parse a tag and its children recursively.
        
        Parameters:
            tag_name (str): The short name of the tag.
            tag_data (dict): The tag data dictionary.
            parent_name (str): The full name of the parent tag.
        """
        # Build the full tag name
        if parent_name:
            if tag_name == "#":
                full_name = f"{parent_name}/#"
            else:
                full_name = f"{parent_name}/{tag_name}"
        else:
            full_name = tag_name

        # Create the tag entry
        new_entry = self._schema._create_tag_entry(full_name, HedSectionKey.Tags)
        
        # Set description
        if json_constants.DESCRIPTION_KEY in tag_data:
            new_entry.description = tag_data[json_constants.DESCRIPTION_KEY]
        
        # Add attributes
        if json_constants.ATTRIBUTES_TAG_KEY in tag_data:
            for attr_name, attr_value in tag_data[json_constants.ATTRIBUTES_TAG_KEY].items():
                self._add_attribute(new_entry, attr_name, attr_value)

        # Add to dictionary
        self._add_to_dict_base(new_entry, HedSectionKey.Tags)

        # Parse child tags recursively
        if json_constants.CHILDREN_KEY in tag_data:
            for child_name, child_data in tag_data[json_constants.CHILDREN_KEY].items():
                self._parse_tag(child_name, child_data, full_name)

    def _populate_unit_classes(self):
        """Populate the unit classes section from JSON."""
        self._schema._initialize_attributes(HedSectionKey.UnitClasses)
        self._schema._initialize_attributes(HedSectionKey.Units)
        unit_classes_section = self._json_data.get(json_constants.UNIT_CLASSES_KEY, {})
        
        for unit_class_name, unit_class_data in unit_classes_section.items():
            # Create unit class entry
            new_entry = self._schema._create_tag_entry(unit_class_name, HedSectionKey.UnitClasses)
            
            # Set description
            if isinstance(unit_class_data, dict) and json_constants.DESCRIPTION_KEY in unit_class_data:
                new_entry.description = unit_class_data[json_constants.DESCRIPTION_KEY]
            
            # Add attributes to unit class
            if isinstance(unit_class_data, dict) and json_constants.ATTRIBUTES_TAG_KEY in unit_class_data:
                for attr_name, attr_value in unit_class_data[json_constants.ATTRIBUTES_TAG_KEY].items():
                    self._add_attribute(new_entry, attr_name, attr_value)
            
            # Add to dictionary
            unit_class_entry = self._add_to_dict_base(new_entry, HedSectionKey.UnitClasses)
            if unit_class_entry is None:
                continue
            
            # Add units - look inside the "units" key
            if isinstance(unit_class_data, dict) and json_constants.UNITS_KEY in unit_class_data:
                units_dict = unit_class_data[json_constants.UNITS_KEY]
                for unit_name, unit_data in units_dict.items():
                    unit_entry = self._schema._create_tag_entry(unit_name, HedSectionKey.Units)
                    
                    if isinstance(unit_data, dict):
                        if json_constants.DESCRIPTION_KEY in unit_data:
                            unit_entry.description = unit_data[json_constants.DESCRIPTION_KEY]
                        if json_constants.ATTRIBUTES_TAG_KEY in unit_data:
                            for attr_name, attr_value in unit_data[json_constants.ATTRIBUTES_TAG_KEY].items():
                                self._add_attribute(unit_entry, attr_name, attr_value)
                    
                    self._add_to_dict_base(unit_entry, HedSectionKey.Units)
                    # Associate the unit with the unit class
                    unit_class_entry.add_unit(unit_entry)

    def _populate_unit_modifiers(self):
        """Populate the unit modifiers section from JSON."""
        self._populate_simple_section(HedSectionKey.UnitModifiers, json_constants.UNIT_MODIFIERS_KEY)

    def _populate_value_classes(self):
        """Populate the value classes section from JSON."""
        self._populate_simple_section(HedSectionKey.ValueClasses, json_constants.VALUE_CLASSES_KEY)

    def _populate_attributes(self):
        """Populate the attributes section from JSON."""
        self._populate_simple_section(HedSectionKey.Attributes, json_constants.ATTRIBUTES_KEY)

    def _populate_properties(self):
        """Populate the properties section from JSON."""
        self._populate_simple_section(HedSectionKey.Properties, json_constants.PROPERTIES_KEY)

    def _populate_simple_section(self, section_key, json_key):
        """Populate a simple section (attributes, properties, etc.) from JSON.
        
        Parameters:
            section_key (HedSectionKey): The section key.
            json_key (str): The JSON key for this section.
        """
        self._schema._initialize_attributes(section_key)
        section_data = self._json_data.get(json_key, {})
        
        for entry_name, entry_data in section_data.items():
            # Create entry
            new_entry = self._schema._create_tag_entry(entry_name, section_key)
            
            # Set description
            if isinstance(entry_data, dict) and json_constants.DESCRIPTION_KEY in entry_data:
                new_entry.description = entry_data[json_constants.DESCRIPTION_KEY]
            
            # Add attributes
            if isinstance(entry_data, dict) and json_constants.ATTRIBUTES_TAG_KEY in entry_data:
                for attr_name, attr_value in entry_data[json_constants.ATTRIBUTES_TAG_KEY].items():
                    self._add_attribute(new_entry, attr_name, attr_value)
            
            # Add to dictionary
            self._add_to_dict_base(new_entry, section_key)

    def _add_attribute(self, entry, attr_name, attr_value):
        """Add an attribute to an entry.
        
        Parameters:
            entry: The schema entry to add the attribute to.
            attr_name (str): The attribute name.
            attr_value: The attribute value.
        """
        # Convert JSON attribute names back to HedKey constants
        hed_attr_name = self._map_json_to_hed_key(attr_name)
        
        # Keep boolean values as booleans (don't convert to strings)
        # This matches how XML stores them
        
        entry._set_attribute_value(hed_attr_name, attr_value)

    def _map_json_to_hed_key(self, json_key):
        """Map JSON attribute names to HedKey constants.
        
        Parameters:
            json_key (str): The JSON attribute name.
            
        Returns:
            str or HedKey: The HedKey constant or string.
        """
        # Reverse mapping from JSON constants to HedKey
        mapping = {
            json_constants.TAKES_VALUE_KEY: HedKey.TakesValue,
            json_constants.VALUE_CLASS_KEY: HedKey.ValueClass,
            json_constants.UNIT_CLASS_KEY: HedKey.UnitClass,
            json_constants.DEFAULT_UNITS_KEY: HedKey.DefaultUnits,
            json_constants.EXTENSION_ALLOWED_KEY: HedKey.ExtensionAllowed,
            json_constants.REQUIRED_KEY: HedKey.Required,
            json_constants.RECOMMENDED_KEY: HedKey.Recommended,
            json_constants.UNIQUE_KEY: HedKey.Unique,
            json_constants.REQUIRE_CHILD_KEY: HedKey.RequireChild,
            json_constants.DEPRECATED_KEY: "deprecated",
            json_constants.DEPRECATED_FROM_KEY: HedKey.DeprecatedFrom,
            json_constants.SUGGESTED_TAG_KEY: HedKey.SuggestedTag,
            json_constants.RELATED_TAG_KEY: HedKey.RelatedTag,
            json_constants.ROOTED_KEY: HedKey.Rooted,
            json_constants.HED_ID_KEY: "hedId",
            json_constants.IN_LIBRARY_KEY: HedKey.InLibrary,
            json_constants.ANNOTATION_KEY: "annotation",
        }
        
        return mapping.get(json_key, json_key)
