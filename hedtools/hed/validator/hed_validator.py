"""
This module contains the HedValidator class which is used to validate the tags in a HED string or a file. The file
types include .tsv, .txt,, and .xlsx. To get the validation issues after creating a HedValidator class call
the get_validation_issues() function.

"""

from hed.errors.error_types import ValidationErrors
from hed.errors.error_reporter import ErrorHandler

from hed.models.hed_string import HedString
from hed.validator.tag_validator import TagValidator
from functools import partial


class HedValidator:
    def __init__(self, hed_schema=None, check_for_warnings=False, run_semantic_validation=True):
        """Constructor for the HedValidator class.

        Parameters
        ----------
        hed_schema: HedSchema
            HedSchema object to use to use for validation
        check_for_warnings: bool
            True if the validator should check for warnings. False if the validator should only report errors.
        run_semantic_validation: bool
            True if the validator should check the HED data against a schema. False for syntax-only validation.
        Returns
        -------
        HedValidator object
            A HedValidator object.

        """
        self._tag_validator = None
        self._hed_schema = hed_schema

        self._tag_validator = TagValidator(hed_schema=self._hed_schema,
                                           check_for_warnings=check_for_warnings,
                                           run_semantic_validation=run_semantic_validation)
        self._run_semantic_validation = run_semantic_validation

    def __get_tag_ops__(self, **kwargs):
        string_validators = []
        allow_placeholders = kwargs.get("allow_placeholders")
        string_validators.append(self._tag_validator.run_hed_string_validators)
        string_validators.append(
            partial(HedString.convert_to_canonical_forms, hed_schema=self._hed_schema))
        string_validators.append(partial(self._validate_individual_tags_in_hed_string,
                                         allow_placeholders=allow_placeholders))
        return string_validators

    def __get_string_ops__(self, **kwargs):
        string_validators = [self._validate_tags_in_hed_string,
                             self._validate_groups_in_hed_string]
        return string_validators

    # todo: possibly add an equivalent to this function somewhere.
    # def validate_strings(self, hed_strings, def_mapper=None, check_for_definitions=True):
    #     """
    #         Validates any given hed_input string or list and returns a list of issues.
    #
    #     Parameters
    #     ----------
    #     hed_strings: list
    #         A list of HED strings or a single HED string.
    #     def_mapper: DefinitionMapper
    #         Any individual string is validated independently, any definitions other than those in the def_mapper will
    #         not be used outside of that specific string.
    #     check_for_definitions: bool
    #         Set this to False if you have already gathered definitions from the given hed strings.
    #     Returns
    #     -------
    #     validation_issues : [{}]
    #     """
    #     validation_issues = []
    #     for hed_string in hed_strings:
    #         string_issues = self.validate_hed_string(hed_string, def_mapper,
    #                                                  check_for_definitions=check_for_definitions)
    #         validation_issues.append(string_issues)
    #     return validation_issues

    def _validate_groups_in_hed_string(self, hed_string_obj):
        """Validates the tags at each level in a HED string. This pertains to the top-level, all groups, and nested
           groups.

         Parameters
         ----------
         hed_string_obj: HedString
            A HedString object.
         Returns
         -------
         list
             The issues associated with each level in the HED string.

         """
        validation_issues = []
        for original_tag_group, is_top_level in hed_string_obj.get_all_groups(also_return_depth=True):
            is_group = original_tag_group.is_group()
            if not original_tag_group and is_group:
                validation_issues += ErrorHandler.format_error(ValidationErrors.HED_GROUP_EMPTY,
                                                               tag=original_tag_group)
            validation_issues += self._tag_validator.run_tag_level_validators(original_tag_group.tags(), is_top_level,
                                                                              is_group)

        return validation_issues

    def _validate_tags_in_hed_string(self, hed_string_obj):
        """Validates the multi-tag properties in a hed string, eg required tags.

         Parameters
         ----------
         hed_string_obj: HedString
            A HedString  object.
         Returns
         -------
         list
             The issues associated with the tags in the HED string.

         """
        validation_issues = []
        tags = hed_string_obj.get_all_tags()
        validation_issues += self._tag_validator.run_all_tags_validators(tags)
        return validation_issues

    def _validate_individual_tags_in_hed_string(self, hed_string_obj, allow_placeholders=False):
        """Validates the individual tags in a HED string.

         Parameters
         ----------
         hed_string_obj: HedString
            A HedString  object.
         Returns
         -------
         list
             The issues associated with the individual tags in the HED string.

         """
        validation_issues = []
        tags = hed_string_obj.get_all_tags()
        for hed_tag in tags:
            validation_issues += \
                self._tag_validator.run_individual_tag_validators(hed_tag, allow_placeholders=allow_placeholders)

        return validation_issues
