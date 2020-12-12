from knobs import Knob

VALIDATION_FAILED_SQS = Knob(env_name="VALIDATION_FAILED_SQS", default="",
                             description="SQS queue name for data that fails validation")
UNKNOWN_ERROR_SQS = Knob(env_name="UNKNOWN_ERROR_SQS", default="", description="All other SQS errors")
