from enum import Enum

class ErrorCodes(Enum):
    NO_DB_CONNECTION = -1
    NO_COMMAND_ARGUMENT = -2
    INVALID_COMMAND_ARGUMENT = -3
    NO_USER_UUID = -4
    INVALID_USER_UUID = -5
    ERROR_ON_GETTING_MAIN_FORMS = -6
    NO_MAIN_ENTRY_ID = -7
    INVALID_MAIN_ENTRY_ID = -8
    ERROR_ON_GETTING_CLASS_FORMS = -9
    ERROR_ON_ADDING_MAIN_FORMS = -10
    ERROR_ON_ADDING_CLASS_FORMS = -11
    NO_CONTENT = -12
    ERROR_ON_DELETING_MAIN_FORM = -13
    ERROR_ON_COPYING_MAIN_FORM = -14
    NO_FORM_TYPE = -15
    NO_CLASS_ENTRY_ID = -16
    INVALID_CLASS_ENTRY_ID = -17
    ERROR_ON_CREATING_PDF = -18
    ERROR_ON_ADDING_SAMPLE_FORMS = -19
    MAIN_FORM_COMPLETED = -20
    ERROR_ON_GETTING_SAMPLE_FORMS = -21
    INVALID_SAMPLE_ENTRY_ID = -22
    ERROR_ON_DELETING_CLASS_FORM = -23
    ERROR_ON_DELETING_SAMPLE_FORM = -24
    INVALID_CLASS_SAMPLE_ID = -25
    NO_SAMPLE_ENTRY_ID = -26
    WPFORMS_CONFIG_FILE_UNREADABLE = -27
    NO_WORKFLOW_TYPE = -28
    INCORRECT_WORKFLOW_TYPE = -29
    NO_DATABASE_CONNECTION = -30
    ERROR_ON_DECODING_FORM = -31
    PUBLISHED_ERROR = -32
    PUBLISHING_FAILED = -33
    REPORT_NOT_CREATED = -34
    ERROR_ON_GETTING_REPORT_LINK = -35
    ERROR_ON_EXECUTING_FUNCTION = -36
    ERROR_ON_EXPORTING_FORMS = -37
    ERROR_ON_IMPORTING_FORMS = -38
    
    
class FormType(Enum):
    CHECKLIST = 1
    SAMPLE = 2
    LIPID_CLASS = 3
    