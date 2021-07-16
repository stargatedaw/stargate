"""
Provides an API for the UI to control the data model and engine.

All logic for the UI to get or set project data should be put in here and
unit tested, the UI should not modify or read project data directly.
Once data is successfully modified, these functions should commit to undo
history and notify the engine to reload the affected files.

Submodules to be imported by UI widgets should be prefixed with 'api_' to avoid
confusion with other imports
"""
