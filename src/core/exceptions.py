"""
Custom exceptions used throughout the scraping framework.
"""

class SpiderError(Exception):
    """
    Base exception for all spider-related errors.
    """
    pass

class DownloadError(SpiderError):
    """
    Raised when downloading page content fails.
    """
    pass

class RequestError(SpiderError):
    """
    Raised when HTTP requests fail.
    """
    pass

class APIError(SpiderError):
    """
    Raised when API request fails.
    """
    pass

class ParseError(SpiderError):
    """
    Raised when parsing HTML or JSON fails.
    """
    pass

class ConfigurationError(SpiderError):
    """
    Raised when spider configuration is invalid.
    """
    pass

class ValidationError(SpiderError):
    """
    Raised when input data validation fails.
    """
    pass

class ExportError(SpiderError):
    """
    Raised when exporting data fails.
    """
    pass