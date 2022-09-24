"""Utilities for generating and handling file names."""

import os
import pathlib
from datetime import datetime
from werkzeug.utils import secure_filename
from hed.errors.exceptions import HedFileError


def check_filename(test_file, name_prefix=None, name_suffix=None, extensions=None):
    """ Return True if correct extension, suffix, and prefix.

    Args:
        test_file (str) :           Path of filename to test.
        name_prefix (list, str, None):  An optional name_prefix or list of prefixes to accept for the base filename
        name_suffix (list, str, None):  An optional name_suffix or list of suffixes to accept for the base file name
        extensions (list, str, None):   An optional extension or list of extensions to accept for the extensions

    Returns:
        bool: True if file has the appropriate format.

    Notes:
        - Everything is converted to lower case prior to testing so this test should be case insensitive.
        - None indicates that all are accepted.


    """

    basename = os.path.basename(test_file.lower())
    if name_prefix and not get_allowed(basename, allowed_values=name_prefix, starts_with=True):
        return False
    if extensions:
        ext = get_allowed(basename, allowed_values=extensions, starts_with=False)
        if not ext:
            return False
        basename = basename[:-len(ext)]
    else:
        basename = os.path.splitext(basename)[0]
    if name_suffix and not get_allowed(basename, allowed_values=name_suffix, starts_with=False):
        return False
    return True


def get_allowed(value, allowed_values=None, starts_with=True):
    """ Returns the portion of the value that matches a value in allowed_values or None if no match.

    Args:
        value (str): value to be matched.
        allowed_values (list, str, or None):  Values to match.
        starts_with (bool):  If true match is done at beginning of string, otherwise the end.

    Notes:
        - match is done in lower case.

    """
    if not allowed_values:
        return value
    elif not isinstance(allowed_values, list):
        allowed_values = [allowed_values]
    allowed_values = [item.lower() for item in allowed_values]
    lower_value = value.lower()
    if starts_with:
        result = list(filter(lower_value.startswith, allowed_values))
    else:
        result = list(filter(lower_value.endswith, allowed_values))
    if result:
        result = result[0]
    return result


def extract_suffix_path(path, prefix_path):
    """ Return suffix of path after prefix path has been removed.

    Args:
        path (str)           path of the root directory.
        prefix_path (str)    sub-path relative to the root directory.

    Returns:
        str:   Suffix path.

    Notes:
        - This function is useful for creating files within BIDS datasets

    """

    real_prefix = os.path.normpath(os.path.realpath(prefix_path).lower())
    suffix_path = os.path.normpath(os.path.realpath(path).lower())
    return_path = os.path.normpath(os.path.realpath(path))
    if suffix_path.startswith(real_prefix):
        return_path = return_path[len(real_prefix):]
    return return_path


def generate_filename(base_name, name_prefix=None, name_suffix=None, extension=None, append_datetime=False):
    """ Generate a filename for the attachment.

    Args:
        base_name (str):   Name of the base, usually the name of the file that the issues were generated from.
        name_prefix (str): Prefix prepended to the front of the base name.
        name_suffix (str): Suffix appended to the end of the base name.
        extension (str):   Extension to use.

    Returns:
        str:  Name of the attachment other containing the issues.

    Notes:
        - The form prefix_basename_suffix + extension.

    """

    pieces = []
    if name_prefix:
        pieces = pieces + [name_prefix]
    if base_name:
        pieces.append(os.path.splitext(base_name)[0])
    if name_suffix:
        pieces = pieces + [name_suffix]
    filename = "".join(pieces)
    if append_datetime:
        now = datetime.now()
        filename = filename + '_' + now.strftime('%Y_%m_%d_T_%H_%M_%S_%f')
    if filename and extension:
        filename = filename + extension

    return secure_filename(filename)


def get_dir_dictionary(dir_path, name_prefix=None, name_suffix=None, extensions=None, skip_empty=True,
                       exclude_dirs=None):

    """ Create dictionary directory paths keys.

    Args:
        dir_path (str):               Full path of the directory tree to be traversed (no ending slash).
        name_prefix (str, None):      An optional name_prefix for the base filename.
        name_suffix (str, None):      An optional name_suffix for the base file name.
        extensions (list, None):      An optional list of file extensions.
        skip_empty (bool):            Do not put entry for directories that have no files.
        exclude_dirs (list):          List of directories to skip

    Returns:
        dict:  Dictionary with directories as keys and file lists values.

    """

    if not exclude_dirs:
        exclude_dirs = []
    dir_dict = {}
    for root, dirs, files in os.walk(dir_path, topdown=True):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        file_list = []
        for r_file in files:
            if check_filename(r_file, name_prefix, name_suffix, extensions):
                file_list.append(os.path.join(os.path.realpath(root), r_file))
        if skip_empty and not file_list:
            continue
        dir_dict[os.path.realpath(root)] = file_list
    return dir_dict


def get_filtered_by_element(file_list, elements):
    new_list = [file for file in file_list if any(substring in os.path.basename(file) for substring in elements)]
    return new_list


def get_filtered_list(file_list, name_prefix=None, name_suffix=None, extensions=None):
    """ Get list of filenames satisfying the criteria.

    Everything is converted to lower case prior to testing so this test should be case insensitive.

     Args:
         file_list (list):      List of files to test.
         name_prefix (str):     Optional name_prefix for the base filename.
         name_suffix (str):     Optional name_suffix for the base filename.
         extensions (list):     Optional list of file extensions (allows two periods (.tsv.gz)

     Returns:
         list:  The filtered file names.

     """
    filtered_files = [file for file in file_list if
                      check_filename(file, name_prefix=name_prefix, name_suffix=name_suffix, extensions=extensions)]
    return filtered_files




def get_file_list(root_path, name_prefix=None, name_suffix=None, extensions=None, exclude_dirs=None):
    """ Return paths satisfying various conditions.

    Args:
        root_path (str):              Full path of the directory tree to be traversed (no ending slash).
        name_prefix (str, None):      An optional name_prefix for the base filename.
        name_suffix (str, None):      The name_suffix of the paths to be extracted.
        extensions (list, None):      A list of extensions to be selected.
        exclude_dirs (list, None):    A list of paths to be excluded.

    Returns:
        list:   The full paths.
    """
    file_list = []
    if not exclude_dirs:
        exclude_dirs = []
    for root, dirs, files in os.walk(root_path, topdown=True):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for r_file in files:
            if check_filename(r_file, name_prefix, name_suffix, extensions):
                file_list.append(os.path.realpath(os.path.join(root, r_file)))
    return file_list


def get_path_components(root_path, this_path):
    """ Get a list of the remaining components after root path.

    Args:
        root_path (str):      A path (no trailing separator)
        this_path (str):      The path of a file or directory descendant of root_path

    Returns:
        list or None:   A list with the remaining elements directory components to the file.

    Notes: this_path must be a descendant of root_path.

    """

    base_path = os.path.realpath(root_path)
    pure_base = pathlib.PurePosixPath(base_path)
    cur_path = os.path.normpath(os.path.realpath(this_path))
    pure_cur = pathlib.PurePosixPath(cur_path)
    common_prefix = os.path.commonprefix([base_path, cur_path])
    print(f"Base path: {base_path} \nCurrent path: {cur_path}")
    print("Common prefix:", {common_prefix})
    print(f"Pure base: {pure_base}\npure_cur {pure_cur} ")
    if not common_prefix:
        raise ValueError("NoPathInCommon", f"Paths {base_path} and {cur_path} must have items in common")
    common_path = os.path.commonpath([base_path, cur_path])
    print(f"Common path: {common_path}")
    if common_path != base_path:
        return None
    rel_path = os.path.relpath(cur_path, base_path)
    the_dir = os.path.dirname(rel_path)
    if the_dir:
        return os.path.normpath(the_dir).split(os.sep)
    else:
        return []


def make_path(root_path, sub_path, filename):
    """ Get path for a file, verifying all components exist.

    Args:
        root_path (str)   path of the root directory
        sub_path (str)    sub-path relative to the root directory
        filename (str)    filename of the file

    Returns: (str)
        A valid realpath for the specified file.

    Notes: This function is useful for creating files within BIDS datasets

    """

    dir_path = os.path.realpath(os.path.join(root_path, sub_path))
    os.makedirs(dir_path, exist_ok=True)
    return os.path.realpath(os.path.join(dir_path, filename))


def parse_bids_filename(file_path):
    """ Split a filename into BIDS-relevant components.

        Args:
            file_path (str)     Path to be parsed.

        Returns: dict
            suffix (str)        BIDS suffix name.
            ext (str)           File extension (including the .).
            entity_dict (dict)  Dictionary with key-value pair being (entity type, entity value).

        Raises:
            HedFileError when filename does not conform to name-value_suffix format.

        Notes:
            into BIDS suffix, extension, and a dictionary of entity name-value pairs.

    """

    filename = os.path.splitext(os.path.basename(file_path))
    ext = filename[1].lower()
    basename = filename[0].strip()
    entity_dict = {}

    if len(basename) == 0:
        raise HedFileError("BlankFileName", f"The basename for {file_path} is blank", "")
    entity_pieces = basename.split('_')
    split_dict = _split_entity(entity_pieces[-1])
    if "bad" in split_dict:
        raise HedFileError("BadSuffixPiece",
                           f"The basename for {entity_pieces[-1]} has bad {split_dict['bad']}", "")
    if "suffix" in split_dict:
        suffix = split_dict["suffix"]
    else:
        suffix = None
        entity_dict[split_dict["key"]] = split_dict["value"]
    for pos, entity in reversed(list(enumerate(entity_pieces[:-1]))):
        split_dict = _split_entity(entity)
        if "key" not in split_dict:
            raise HedFileError("BadKeyValue", f"The piece {entity} is not in key-value form", "")
        entity_dict[split_dict["key"]] = split_dict["value"]
    return suffix, ext, entity_dict


def _split_entity(piece):
    """Splits an piece into an entity or suffix.

        Args:
            piece (str):   A string to be parsed.

        Returns:
            dict:  with entities as keys as well as the key "bad" and the key "suffix".
    """
    piece = piece.strip()
    if not piece:
        return {"bad": ""}
    split_piece = piece.split('-')
    if len(split_piece) == 1:
        return {"suffix": piece}
    if len(split_piece) == 2:
        return {"key": split_piece[0].strip(), "value": split_piece[1].strip()}
    else:
        return {"bad": piece}
