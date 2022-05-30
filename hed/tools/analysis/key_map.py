import pandas as pd
from hed.errors.exceptions import HedFileError
from hed.util.data_util import get_row_hash
from hed.util.data_util import get_new_dataframe, remove_quotes, separate_columns


class KeyMap:
    """ A map of unique column values for remapping columns.

    Attributes:
        name (str):       Name of this remap for identification purposes.
        key_cols (list):  A list of column names that will be hashed into the keys for the map.
        target_cols (list):   An optional list of column names that will be inserted into data and later remapped.

    """
    def __init__(self, key_cols, target_cols=None, name=''):
        """ Information for remapping columns of tabular files.

        Args:
            key_cols (list):       List of columns to be replaced (assumed in the DataFrame)
            target_cols(list):     List of replacement columns (assumed to not be in the DataFrame)
            name (str):            Name associated with this remap (usually a pathname of the events file).

        """

        if not key_cols:
            raise HedFileError("KeyColumnsEmpty", "KeyMap key columns must exist", "")
        self.key_cols = key_cols.copy()
        if target_cols and set(key_cols).intersection(target_cols):
            raise HedFileError("KeyTargetNotDisjoint",
                               f"Key cols {str(key_cols)} and target cols {str(target_cols)} must be disjoint", "")
        elif target_cols:
            self.target_cols = target_cols.copy()
        else:
            self.target_cols = []
        self.name = name
        x = self.key_cols + self.target_cols
        self.col_map = pd.DataFrame(columns=self.key_cols + self.target_cols)
        self.map_dict = {}
        self.count_dict = {}

    @property
    def columns(self):
        return self.key_cols + self.target_cols

    def __str__(self):
        temp_list = [f"{self.name} counts for key [{str(self.key_cols)}]:"]
        for index, row in self.col_map.iterrows():
            key_hash = get_row_hash(row, self.columns)
            temp_list.append(f"{str(list(row.values))}\t{self.count_dict[key_hash]}")
        return "\n".join(temp_list)

    def make_template(self, additional_cols=None):
        """ Return a dataframe template consisting of the unique key columns in this map plus additional columns.

        Args:
            additional_cols (list or None): Optional list of additional columns to append to the returned dataframe.

        Returns:
            DataFrame:  A dataframe containing the template.

        Raises:
            HedFileError: If additional columns are not disjoint from the key columns.

        """
        if additional_cols and set(self.key_cols).intersection(additional_cols):
            raise HedFileError("AdditionalColumnsNotDisjoint",
                               f"Additional columns {str(additional_cols)} must be disjoint from \
                                {str(self.columns)} must be disjoint", "")
        df = self.col_map[self.key_cols].copy()
        if additional_cols:
            df[additional_cols] = 'n/a'
        return df

    def remap(self, data):
        """ Remap the columns of a dataframe or columnar file.

        Args:
            data (DataFrame, str) :     Columnar data (either DataFrame or filename) whose columns are to be remapped.

        Returns:
            DataFrame:     New dataframe with columns remapped.
            list           List of row numbers that had no correspondence in the mapping.

        Raises:
            HedFileError:  If data is missing some of the key columns.

        """

        df_new = get_new_dataframe(data)
        remove_quotes(df_new)
        present_keys, missing_keys = separate_columns(df_new.columns.values.tolist(), self.key_cols)
        if missing_keys:
            raise HedFileError("MissingKeys", f"File must have key columns {str(self.key_cols)}", "")
        df_new[self.target_cols] = 'n/a'
        missing_indices = self._remap(df_new)
        return df_new, missing_indices

    def _remap(self, df):
        """ Utility method that iterates through dataframes to do the remapping.

        Args:
            df (DataFrame):    DataFrame in which to perform the mapping.

        Returns:
            list:              List of row numbers that had no correspondence in the mapping.

        """

        missing_indices = []
        for index, row in df.iterrows():
            key = get_row_hash(row, self.key_cols)
            key_value = self.map_dict.get(key, None)
            if key_value is not None:
                result = self.col_map.iloc[key_value]
                row[self.target_cols] = result[self.target_cols].values
                df.iloc[index] = row
            else:
                missing_indices.append(index)
        return missing_indices

    def resort(self):
        """ Sort the col_map in place by the key columns. """
        self.col_map.sort_values(by=self.key_cols, inplace=True, ignore_index=True)
        for index, row in self.col_map.iterrows():
            key_hash = get_row_hash(row, self.key_cols)
            self.map_dict[key_hash] = index

    def update(self, data, allow_missing=True, keep_counts=True):
        """ Update the existing map with information from data.

        Args:
            data (DataFrame or str):     DataFrame or filename of an events file or event map.
            allow_missing (bool):        If true allow missing keys and add as n/a columns.
            keep_counts (bool):          If true keep a count of the times each key is present.

        Returns:
            list:                        Indices of duplicates.

        Raises:
            HedFileError:  If there are missing keys and allow_missing is False.

        """
        df = get_new_dataframe(data)
        remove_quotes(df)
        col_list = df.columns.values.tolist()
        keys_present, keys_missing = separate_columns(col_list, self.key_cols)
        if keys_missing and not allow_missing:
            raise HedFileError("MissingKeyColumn",
                               f"make_template data does not have key columns {str(keys_missing)}", "")
        base_df = df[keys_present].copy()
        if keys_missing:
            base_df[keys_missing] = 'n/a'
        if self.target_cols:
            base_df[self.target_cols] = 'n/a'
            targets_present, targets_missing = separate_columns(col_list, self.target_cols)
            if targets_present:
                base_df[targets_present] = df[targets_present].values
        return self._update(base_df, track_duplicates=keep_counts)

    def _update(self, base_df, track_duplicates=True):
        """ Update the dictionary of key values based on information in the dataframe.

        Args:
            base_df (DataFrame):       DataFrame of consisting of the columns in the KeyMap
            track_duplicates (bool):        If true, keep counts of the indices.

        Returns:
            list:         List of key positions that appeared more than once or an empty list of no duplicates or
                          track_duplicates was false.
        """

        duplicate_indices = []
        row_list = []
        next_pos = len(self.col_map)
        for index, row in base_df.iterrows():
            key, pos_update = self._handle_update(row, row_list, next_pos, track_duplicates)
            next_pos += pos_update
            if not track_duplicates and not pos_update:
                duplicate_indices.append(index)
        if row_list:
            df = pd.DataFrame(row_list)
            self.col_map = pd.concat([self.col_map, df], axis=0, ignore_index=True)
        return duplicate_indices

    def _handle_update(self, row, row_list, next_pos, keep_counts):
        """ Update the dictionary and counts of the number of times this combination of key columns appears.

        Args:
            row (DataSeries):  Data the values in a row.
            row_list (list):   A list of rows to be appended to hold the unique rows
            next_pos (int):    Index into the

        """
        key = get_row_hash(row, self.key_cols)
        pos_update = 0
        if key not in self.map_dict:
            self.map_dict[key] = next_pos
            row_list.append(row)
            pos_update = 1
            if keep_counts:
                self.count_dict[key] = 0
        if keep_counts:
            self.count_dict[key] += 1
        return key, pos_update
