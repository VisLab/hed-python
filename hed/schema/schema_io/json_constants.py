"""Constants for JSON schema format."""

# JSON schema structure keys
HEADER_KEY = "header"
PROLOGUE_KEY = "prologue"
EPILOGUE_KEY = "epilogue"
TAGS_KEY = "tags"
UNIT_CLASSES_KEY = "unitClasses"
UNIT_MODIFIERS_KEY = "unitModifiers"
VALUE_CLASSES_KEY = "valueClasses"
ATTRIBUTES_KEY = "attributes"
PROPERTIES_KEY = "properties"

# Tag entry keys
NAME_KEY = "name"
DESCRIPTION_KEY = "description"
ATTRIBUTES_TAG_KEY = "attributes"
CHILDREN_KEY = "tags"  # Child tags are under "tags" key

# Unit class keys
UNITS_KEY = "units"

# Attribute keys - matching XML/mediawiki but in camelCase for JSON
TAKES_VALUE_KEY = "takesValue"
VALUE_CLASS_KEY = "valueClass"
UNIT_CLASS_KEY = "unitClass"
DEFAULT_UNITS_KEY = "defaultUnits"
EXTENSION_ALLOWED_KEY = "extensionAllowed"
REQUIRED_KEY = "required"
RECOMMENDED_KEY = "recommended"
UNIQUE_KEY = "unique"
POSITION_KEY = "position"
REQUIRE_CHILD_KEY = "requireChild"
PREDICATE_TYPE_KEY = "predicateType"
DEPRECATED_KEY = "deprecated"
DEPRECATED_FROM_KEY = "deprecatedFrom"
SUGGESTED_TAG_KEY = "suggestedTag"
RELATED_TAG_KEY = "relatedTag"
ROOTED_KEY = "rooted"
HED_ID_KEY = "hedId"
IN_LIBRARY_KEY = "inLibrary"
ANNOTATION_KEY = "annotation"
