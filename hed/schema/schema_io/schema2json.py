"""Allows output of HedSchema objects as .json format"""

import json
from hed.schema.hed_schema_constants import HedSectionKey, HedKey
from hed.schema.schema_io import json_constants
from hed.schema.schema_io.schema2base import Schema2Base


class Schema2JSON(Schema2Base):
    def __init__(self):
        super().__init__()
        self.json_dict = None

    # =========================================
    # Required baseclass function
    # =========================================
    def _initialize_output(self):
        self.json_dict = {}
        # Alias to output to match baseclass expectation
        self.output = self.json_dict

    def _output_header(self, attributes):
        self.json_dict[json_constants.HEADER_KEY] = attributes

    def _output_prologue(self, prologue):
        if prologue:
            self.json_dict[json_constants.PROLOGUE_KEY] = prologue

    def _output_annotations(self, hed_schema):
        pass

    def _output_extras(self, hed_schema):
        """
        Allow subclasses to add additional sections if needed.
        This is a placeholder for any additional output that needs to be done after the main sections.
        """
        pass

    def _output_epilogue(self, epilogue):
        if epilogue:
            self.json_dict[json_constants.EPILOGUE_KEY] = epilogue

    def _output_footer(self):
        pass

    def _start_section(self, key_class):
        """Start a new section in the JSON output.
        
        Parameters:
            key_class (HedSectionKey): The section key to start.
            
        Returns:
            dict: The dictionary for this section.
        """
        if key_class == HedSectionKey.Tags:
            section_key = json_constants.TAGS_KEY
        elif key_class == HedSectionKey.UnitClasses:
            section_key = json_constants.UNIT_CLASSES_KEY
        elif key_class == HedSectionKey.UnitModifiers:
            section_key = json_constants.UNIT_MODIFIERS_KEY
        elif key_class == HedSectionKey.ValueClasses:
            section_key = json_constants.VALUE_CLASSES_KEY
        elif key_class == HedSectionKey.Attributes:
            section_key = json_constants.ATTRIBUTES_KEY
        elif key_class == HedSectionKey.Properties:
            section_key = json_constants.PROPERTIES_KEY
        else:
            section_key = str(key_class)
            
        self.json_dict[section_key] = {}
        return self.json_dict[section_key]

    def _end_tag_section(self):
        pass

    def _end_units_section(self):
        pass

    def _end_section(self, section_key):
        pass

    def _write_tag_entry(self, tag_entry, parent_dict, level=0):
        """Write a tag entry to the JSON structure.
        
        Parameters:
            tag_entry (HedTagEntry): The tag entry to write.
            parent_dict (dict): The parent dictionary to add this tag to.
            level (int): The nesting level (not used in JSON as we use short names).
            
        Returns:
            dict: The dictionary for this tag entry.
        """
        # For # placeholder tags, use "#" as the key, otherwise use short_tag_name
        if tag_entry.name.endswith("/#"):
            key_name = "#"
        else:
            key_name = tag_entry.short_tag_name
        
        tag_dict = {}
        
        # Add description if present
        if tag_entry.description:
            tag_dict[json_constants.DESCRIPTION_KEY] = tag_entry.description
            
        # Add attributes if present
        if tag_entry.attributes:
            attrs = self._format_tag_attributes_json(tag_entry.attributes)
            if attrs:
                tag_dict[json_constants.ATTRIBUTES_TAG_KEY] = attrs
        
        # Create entry in parent dict
        if json_constants.CHILDREN_KEY not in parent_dict:
            parent_dict[json_constants.CHILDREN_KEY] = {}
        parent_dict[json_constants.CHILDREN_KEY][key_name] = tag_dict
        
        return tag_dict

    def _write_entry(self, entry, parent_dict, include_props=True):
        """Write a non-tag entry (unit class, unit, etc.) to the JSON structure.
        
        Parameters:
            entry (HedSchemaEntry): The entry to write.
            parent_dict (dict): The parent dictionary to add this entry to.
            include_props (bool): Whether to include properties.
            
        Returns:
            dict: The dictionary for this entry.
        """
        # Use name attribute instead of short_tag_name for non-tag entries
        entry_name = entry.name
        
        entry_dict = {}
        
        # Add description if present
        if entry.description:
            entry_dict[json_constants.DESCRIPTION_KEY] = entry.description
            
        # Add attributes if present and requested
        if include_props and entry.attributes:
            attrs = self._format_tag_attributes_json(entry.attributes)
            if attrs:
                entry_dict[json_constants.ATTRIBUTES_TAG_KEY] = attrs
        
        # For unit classes, add units section
        if hasattr(entry, 'units') and entry.units:
            entry_dict[json_constants.UNITS_KEY] = {}
            # Return the units sub-dictionary so units can be added there
            parent_dict[entry_name] = entry_dict
            return entry_dict[json_constants.UNITS_KEY]
        else:
            parent_dict[entry_name] = entry_dict
            return entry_dict

    def _format_tag_attributes_json(self, attributes):
        """Format tag attributes for JSON output.
        
        Parameters:
            attributes (dict): Dictionary with {attribute_name: attribute_value}
            
        Returns:
            dict: The formatted attributes dictionary.
        """
        json_attrs = {}
        for prop, value in attributes.items():
            # Never save InLibrary if saving merged
            if self._attribute_disallowed(prop):
                continue
                
            # Map HedKey to JSON constant names
            json_key = self._map_attribute_name(prop)
            
            if value is True or value == "true":
                json_attrs[json_key] = True
            elif value is False or value == "false":
                json_attrs[json_key] = False
            else:
                # For comma-separated values, keep as string (matches XML behavior)
                json_attrs[json_key] = value
        
        return json_attrs

    def _map_attribute_name(self, attr_name):
        """Map HedKey attribute names to JSON constant names.
        
        Parameters:
            attr_name (str or HedKey): The attribute name to map.
            
        Returns:
            str: The JSON key name.
        """
        # Create a mapping from HedKey values to JSON constants
        mapping = {
            HedKey.TakesValue: json_constants.TAKES_VALUE_KEY,
            "takesValue": json_constants.TAKES_VALUE_KEY,
            HedKey.ValueClass: json_constants.VALUE_CLASS_KEY,
            "valueClass": json_constants.VALUE_CLASS_KEY,
            HedKey.UnitClass: json_constants.UNIT_CLASS_KEY,
            "unitClass": json_constants.UNIT_CLASS_KEY,
            HedKey.DefaultUnits: json_constants.DEFAULT_UNITS_KEY,
            "defaultUnits": json_constants.DEFAULT_UNITS_KEY,
            HedKey.ExtensionAllowed: json_constants.EXTENSION_ALLOWED_KEY,
            "extensionAllowed": json_constants.EXTENSION_ALLOWED_KEY,
            HedKey.Required: json_constants.REQUIRED_KEY,
            "required": json_constants.REQUIRED_KEY,
            HedKey.Recommended: json_constants.RECOMMENDED_KEY,
            "recommended": json_constants.RECOMMENDED_KEY,
            HedKey.Unique: json_constants.UNIQUE_KEY,
            "unique": json_constants.UNIQUE_KEY,
            HedKey.RequireChild: json_constants.REQUIRE_CHILD_KEY,
            "requireChild": json_constants.REQUIRE_CHILD_KEY,
            "deprecated": json_constants.DEPRECATED_KEY,
            HedKey.DeprecatedFrom: json_constants.DEPRECATED_FROM_KEY,
            "deprecatedFrom": json_constants.DEPRECATED_FROM_KEY,
            HedKey.SuggestedTag: json_constants.SUGGESTED_TAG_KEY,
            "suggestedTag": json_constants.SUGGESTED_TAG_KEY,
            HedKey.RelatedTag: json_constants.RELATED_TAG_KEY,
            "relatedTag": json_constants.RELATED_TAG_KEY,
            HedKey.Rooted: json_constants.ROOTED_KEY,
            "rooted": json_constants.ROOTED_KEY,
            HedKey.HedID: json_constants.HED_ID_KEY,
            "hedId": json_constants.HED_ID_KEY,
            HedKey.InLibrary: json_constants.IN_LIBRARY_KEY,
            "inLibrary": json_constants.IN_LIBRARY_KEY,
            "annotation": json_constants.ANNOTATION_KEY,
        }
        
        return mapping.get(attr_name, str(attr_name))
