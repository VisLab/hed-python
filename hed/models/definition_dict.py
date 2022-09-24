from hed.models.hed_string import HedString
from hed.models.hed_group import HedGroup
from hed.errors.error_types import DefinitionErrors
from hed.errors.error_reporter import ErrorHandler
import copy
from functools import partial

from hed.models.model_constants import DefTagNames
from hed.models.hed_ops import HedOps


class DefinitionEntry:
    """ A single definition. """

    def __init__(self, name, contents, takes_value, source_context):
        """ Initialize info for a single definition.

        Parameters:
            name (str):            The label portion of this name (not including Definition/).
            contents (HedGroup):   The contents of this definition.
            takes_value (bool):    If True, expects ONE tag to have a single # sign in it.
            source_context (dict): Info about where this definition was declared.
        """
        self.name = name
        if contents:
            contents = contents.copy()
        self.contents = contents
        self.takes_value = takes_value
        self.source_context = source_context
        self.tag_dict = {}
        if contents:
            add_group_to_dict(contents, self.tag_dict)

    def get_definition(self, replace_tag, placeholder_value=None):
        """ Return a copy of the definition with the tag expanded and the placeholder plugged in.

        Parameters:
            replace_tag (HedTag): The def hed tag to replace with an expanded version
            placeholder_value (str or None):    If present and required, will replace any pound signs
                                                in the definition contents.

        Returns:
            str:          The expanded def tag name
            HedGroup:     The contents of this definition(including the def tag itself)

        Raises:
            ValueError:  If a placeholder_value is passed, but this definition doesn't have a placeholder.

        """
        if self.takes_value == (placeholder_value is None):
            return None, []

        output_contents = [replace_tag]
        name = self.name
        if self.contents:
            output_group = self.contents
            if placeholder_value:
                output_group = copy.deepcopy(self.contents)
                placeholder_tag = output_group.find_placeholder_tag()
                if not placeholder_tag:
                    raise ValueError("Internal error related to placeholders in definition mapping")
                name = f"{name}/{placeholder_value}"
                placeholder_tag.replace_placeholder(placeholder_value)

            output_contents = [replace_tag, output_group]

        output_contents = HedGroup(replace_tag._hed_string,
                                   startpos=replace_tag.span[0], endpos=replace_tag.span[1], contents=output_contents)
        return f"{DefTagNames.DEF_EXPAND_ORG_KEY}/{name}", output_contents


class DefinitionDict(HedOps):
    """ Gathers definitions from a single source.

        This class extends HedOps because it has string_funcs to check for definitions. It has no tag_funcs.

    """

    def __init__(self):
        """ Definitions to be considered a single source. """

        super().__init__()
        self.defs = {}

        # Definition related issues
        self._extract_def_issues = []

    def get_definition_issues(self):
        """ Return definition errors found during extraction.

        Returns:
            list: List of DefinitionErrors issues found. Each issue is a dictionary.

        """
        return self._extract_def_issues

    def get(self, def_name):
        return self.defs.get(def_name.lower())

    def __iter__(self):
        return iter(self.defs.items())

    def __get_string_funcs__(self, **kwargs):
        error_handler = kwargs.get("error_handler")
        return [partial(self.check_for_definitions, error_handler=error_handler)]

    def __get_tag_funcs__(self, **kwargs):
        return []

    def check_for_definitions(self, hed_string_obj, error_handler=None):
        """ Check string for definition tags, adding them to self.

        Args:
            hed_string_obj (HedString): A single hed string to gather definitions from.
            error_handler (ErrorHandler or None): Error context used to identify where definitions are found.

        Returns:
            list:  List of issues encountered in checking for definitions. Each issue is a dictionary.

        """
        new_def_issues = []
        for definition_tag, group in hed_string_obj.find_top_level_tags(anchor_tags={DefTagNames.DEFINITION_KEY}):
            def_tag_name = definition_tag.extension_or_value_portion

            # initial validation
            groups = group.groups()
            if len(groups) > 1:
                new_def_issues += \
                    ErrorHandler.format_error_with_context(error_handler,
                                                           DefinitionErrors.WRONG_NUMBER_GROUP_TAGS,
                                                           def_name=def_tag_name, tag_list=groups)
                continue
            if len(group.tags()) != 1:
                new_def_issues += \
                    ErrorHandler.format_error_with_context(error_handler,
                                                           DefinitionErrors.WRONG_NUMBER_GROUP_TAGS,
                                                           def_name=def_tag_name,
                                                           tag_list=[tag for tag in group.tags()
                                                                     if tag is not definition_tag])
                continue

            group_tag = groups[0] if groups else None

            # final validation
            # Verify no other def or def expand tags found in group
            if group_tag:
                for def_tag in group.find_def_tags(recursive=True, include_groups=0):
                    new_def_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                             DefinitionErrors.DEF_TAG_IN_DEFINITION,
                                                                             tag=def_tag,
                                                                             def_name=def_tag_name)
                    continue
            def_takes_value = def_tag_name.lower().endswith("/#")
            if def_takes_value:
                def_tag_name = def_tag_name[:-len("/#")]

            def_tag_lower = def_tag_name.lower()
            if "/" in def_tag_lower or "#" in def_tag_lower:
                new_def_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                         DefinitionErrors.INVALID_DEFINITION_EXTENSION,
                                                                         def_name=def_tag_name)
                continue

            # # Verify placeholders here.
            placeholder_tags = []
            if group_tag:
                for tag in group_tag.get_all_tags():
                    if "#" in str(tag):
                        placeholder_tags.append(tag)

            if (len(placeholder_tags) == 1) != def_takes_value:
                new_def_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                         DefinitionErrors.WRONG_NUMBER_PLACEHOLDER_TAGS,
                                                                         def_name=def_tag_name,
                                                                         tag_list=placeholder_tags,
                                                                         expected_count=1 if def_takes_value else 0)
                continue

            if error_handler:
                context = error_handler.get_error_context_copy()
            else:
                context = []
            if def_tag_lower in self.defs:
                new_def_issues += ErrorHandler.format_error_with_context(error_handler,
                                                                         DefinitionErrors.DUPLICATE_DEFINITION,
                                                                         def_name=def_tag_name)
                continue
            self.defs[def_tag_lower] = DefinitionEntry(name=def_tag_name, contents=group_tag,
                                                       takes_value=def_takes_value,
                                                       source_context=context)

        self._extract_def_issues += new_def_issues
        return new_def_issues

    @staticmethod
    def get_as_strings(def_dict):
        """ Convert the entries to strings of the contents

        Args:
            def_dict(DefinitionDict or dict): A dict of definitions

        Returns:
            dict(str: str): definition name and contents
        """
        if isinstance(def_dict, DefinitionDict):
            def_dict = def_dict.defs

        return {key: str(value.contents) for key, value in def_dict.items()}


def add_group_to_dict(group, tag_dict=None):
    """ Add the tags and their values from a HED group to a tag dictionary.

    Args:
        group (HedGroup):   Contents to add to the tag dict.
        tag_dict (dict):    The starting tag dictionary to which to add to.

    Returns:
        dict:  The updated tag_dict containing the tags with a list of values.

    Notes:
        - Expects tags to have forms calculated already.

    """
    if tag_dict is None:
        tag_dict = {}
    for tag in group.get_all_tags():
        short_base_tag = tag.short_base_tag
        value = tag.extension_or_value_portion
        value_dict = tag_dict.get(short_base_tag, {})
        if value:
            value_dict[value] = ''
        tag_dict[short_base_tag] = value_dict
    return tag_dict
