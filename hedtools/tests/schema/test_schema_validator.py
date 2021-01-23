import unittest
import os
from hed.schema import schema_validator
from hed.util import error_reporter
from hed.util.error_types import SchemaWarnings

class Test(unittest.TestCase):
    # A known schema with many issues.
    schema_file = '../data/HED7.1.1.xml'

    @classmethod
    def setUpClass(cls):
        cls.error_handler = error_reporter.ErrorHandler()
        cls.schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.schema_file)

    def validate_term_base(self, input_text, expected_issues):
        for text, issues in zip(input_text, expected_issues):
            test_issues = schema_validator.validate_schema_term(text, self.error_handler)
            self.assertCountEqual(issues, test_issues)

    def validate_desc_base(self, input_descriptions, expected_issues):
        for description, issues in zip(input_descriptions, expected_issues):
            test_issues = schema_validator.validate_schema_description("dummy", description, self.error_handler)
            self.assertCountEqual(issues, test_issues)

    def test_validate_schema(self):
        issues = schema_validator.validate_schema(self.schema_path)
        self.assertTrue(isinstance(issues, list))
        self.assertTrue(len(issues) > 1)

    def test_validate_schema_term(self):
        test_terms = [
            "invalidcaps",
            "Validcaps",
            "3numberisvalid",
            "Invalidchar#",
            "@invalidcharatstart",
        ]
        expected_issues = [
            self.error_handler.format_schema_warning(SchemaWarnings.INVALID_CAPITALIZATION, test_terms[0], error_index=0, problem_char="i"),
            [],
            [],
            self.error_handler.format_schema_warning(SchemaWarnings.INVALID_CHARACTERS_IN_TAG, test_terms[3], error_index=11,
                                  problem_char="#"),
            self.error_handler.format_schema_warning(SchemaWarnings.INVALID_CAPITALIZATION, test_terms[4], error_index=0,
                                  problem_char="@"),
        ]
        self.validate_term_base(test_terms, expected_issues)

    def test_validate_schema_description(self):
        test_descs = [
            "This is a tag description with no invalid characters.",
            "This is (also) a tag description with no invalid characters.  -_:;./()+ ^",
            "This description has no invalid characters, as commas are allowed",
            "This description has multiple invalid characters at the end @$%*"
        ]
        expected_issues = [
            [],
            [],
            [],
            self.error_handler.format_schema_warning(SchemaWarnings.INVALID_CHARACTERS_IN_DESC, "dummy", test_descs[3], error_index=60,
                                  problem_char="@")
            + self.error_handler.format_schema_warning(SchemaWarnings.INVALID_CHARACTERS_IN_DESC, "dummy", test_descs[3], error_index=61,
                                  problem_char="$")
            + self.error_handler.format_schema_warning(SchemaWarnings.INVALID_CHARACTERS_IN_DESC, "dummy", test_descs[3], error_index=62,
                                  problem_char="%")
            + self.error_handler.format_schema_warning(SchemaWarnings.INVALID_CHARACTERS_IN_DESC, "dummy", test_descs[3], error_index=63,
                                  problem_char="*")
            ,
        ]
        self.validate_desc_base(test_descs, expected_issues)
