# Libraries/exceptions.py

class PipelineAbortSample(Exception):
    """Abort current sample but keep pipeline running."""
    pass

class PipelineFatal(Exception):
    """Hard fatal (only for genuine program bug)"""
    pass
