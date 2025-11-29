class AppConfig(dict):
    """
    Application configuration class.
    Inherits from dict to allow dictionary-like access to configuration values.
    Used for dependency injection to avoid binding raw dict type.
    """
    pass
