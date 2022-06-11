import unittest
import os

from hed import schema
from hed.models import HedString


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/')
        hed_xml_file = os.path.join(cls.base_data_dir, "schema_test_data/HED8.0.0t.xml")
        cls.hed_schema = schema.load_schema(hed_xml_file)

    def test_remove_groups(self):
        from hed.models.definition_dict import DefTagNames
        basic_definition_string = "(Definition/TestDef, (Keypad-key/TestDef1,Keyboard-key/TestDef2))"
        basic_definition_string_repeated = f"{basic_definition_string},{basic_definition_string}"
        def_string_with_repeat = HedString(basic_definition_string_repeated, self.hed_schema)
        definition_tags = def_string_with_repeat.find_tags({DefTagNames.DEFINITION_KEY},
                                                           recursive=True, include_groups=1)
        definition_tag2 = definition_tags[1]
        def_string_with_repeat.remove([definition_tag2])
        remaining_children = def_string_with_repeat.get_all_groups()
        for child in remaining_children:
            if child is definition_tag2:
                self.assertFalse(False, "Definition tag not removed successfully")

        basic_definition_string_repeated_subgroup = \
            f"{basic_definition_string},{basic_definition_string}, ({basic_definition_string})"
        def_string_with_repeat = HedString(basic_definition_string_repeated_subgroup, self.hed_schema)
        definition_tags = def_string_with_repeat.find_tags({DefTagNames.DEFINITION_KEY},
                                                           recursive=True, include_groups=1)
        definition_tag3 = definition_tags[2]
        def_string_with_repeat.remove([definition_tag3])
        remaining_children = def_string_with_repeat.get_all_groups()
        for child in remaining_children:
            if child is definition_tag3:
                self.assertFalse(False, "Nested definition tag not removed successfully")

        basic_definition_string_repeated_subgroup = \
            f"{basic_definition_string},{basic_definition_string}, ({basic_definition_string})"
        def_string_with_repeat = HedString(basic_definition_string_repeated_subgroup, self.hed_schema)
        definition_tags = def_string_with_repeat.find_tags({DefTagNames.DEFINITION_KEY},
                                                           recursive=True, include_groups=1)
        definition_tag2 = definition_tags[1]
        def_string_with_repeat.remove([definition_tag2])
        remaining_children = def_string_with_repeat.get_all_groups()
        for child in remaining_children:
            if child is definition_tag2:
                self.assertFalse(False, "Nested definition tag not removed successfully")

    def test_find_tags_with_term(self):
        basic_hed_string = \
            "(Keypad-key/TestDef1,Keyboard-key/TestDef2, Item/Object, Event), Event, Object, Geometric-object"
        basic_hed_string_obj = HedString(basic_hed_string, self.hed_schema)
        # works
        located_tags = basic_hed_string_obj.find_tags_with_term("Object", recursive=True, include_groups=0)
        self.assertEqual(len(located_tags), 5)
        # located tags now has found all 5 hed tags

        # This will find no tags
        located_tags = basic_hed_string_obj.find_tags_with_term("bject", recursive=True, include_groups=0)
        self.assertEqual(len(located_tags), 0)

        # this will also find no tags
        located_tags = basic_hed_string_obj.find_tags_with_term("Item/Object", recursive=True, include_groups=0)
        self.assertEqual(len(located_tags), 0)


if __name__ == '__main__':
    unittest.main()
