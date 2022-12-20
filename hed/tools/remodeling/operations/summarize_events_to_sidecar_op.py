from hed.tools import TabularSummary
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_context import BaseContext, DISPLAY_INDENT


class SummarizeEventsToSidecarOp(BaseOp):
    """ Summarize the values that are in the columns.

    Notes: The required parameters are:
        - summary_name (str)   The name of the summary.
        - summary_filename (str)   Base filename of the summary.
        - skip_columns (list)  Names of columns to skip in the summary.
        - value_columns (list) Names of columns to treat as value columns rather than categorical columns

    The purpose of this op is to produce a summary of the values in a tabular file.

    """

    PARAMS = {
        "operation": "summarize_events_to_sidecar",
        "required_parameters": {
            "summary_name": str,
            "summary_filename": str,
            "skip_columns": list,
            "value_columns": list,
        },
        "optional_parameters": {
        }
    }

    SUMMARY_TYPE = "events_to_sidecar"

    def __init__(self, parameters):
        super().__init__(self.PARAMS, parameters)
        self.summary_name = parameters['summary_name']
        self.summary_filename = parameters['summary_filename']
        self.skip_columns = parameters['skip_columns']
        self.value_columns = parameters['value_columns']

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Create factor columns corresponding to values in a specified column.

        Parameters:
            dispatcher (Dispatcher): The dispatcher object for context.
            df (DataFrame): The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Only needed for HED operations.

        Returns:
            DataFrame: A new DataFrame with the factor columns appended.

        Side-effect:
            Updates the context.

        """

        summary = dispatcher.context_dict.get(self.summary_name, None)
        if not summary:
            summary = EventsToSidecarSummaryContext(self)
            dispatcher.context_dict[self.summary_name] = summary
        summary.update_context({'df': dispatcher.post_proc_data(df), 'name': name})
        return df


class EventsToSidecarSummaryContext(BaseContext):

    def __init__(self, sum_op):
        super().__init__(sum_op.SUMMARY_TYPE, sum_op.summary_name, sum_op.summary_filename)
        self.value_cols = sum_op.value_columns
        self.skip_cols = sum_op.skip_columns

    def update_context(self, new_context):
        tab_sum = TabularSummary(value_cols=self.value_cols, skip_cols=self.skip_cols, name=new_context["name"])
        tab_sum.update(new_context['df'], new_context['name'])
        self.summary_dict[new_context["name"]] = tab_sum

    def _get_summary_details(self, summary_info):
        """ Return the summary-specific information.

        Parameters:
            summary_info (object):  Summary to return info from

        Notes:
            Abstract method be implemented by each individual context summary.

        """

        details = {"files": summary_info.files, "total_files": summary_info.total_files,
                   "total_events": summary_info.total_events, "skip_cols": summary_info.skip_cols,
                   "sidecar": summary_info.extract_sidecar_template()}
        return {"Sidecar_details": details}

    def _merge_all(self):
        """ Return merged information.

        Returns:
           object:  Consolidated summary of information.

        Notes:
            Abstract method be implemented by each individual context summary.

        """
        return {}

    def _get_result_string(self, name, result):
        if name == "Dataset":
            return "Dataset: Currently no overall sidecar extraction is available"
        return f"{name}: {str(result)}"
