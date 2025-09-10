"""Retry strategy implementation for network operations.

This module provides exponential backoff retry logic with configurable
parameters and intelligent error handling.
"""

import time
import logging
from typing import Type

import requests
from requests.exceptions import (
    ConnectionError,
    Timeout,
    HTTPError,
    RequestException,
)

from ..model.network import NetworkSettings, NetworkResponse
from .exceptions import NetworkTimeoutError, NetworkRetryExhaustedError


logger = logging.getLogger(__name__)


class RetryStrategy:
    """Implements retry logic with exponential backoff for network operations.
    
    This class provides intelligent retry mechanisms that:
    - Use exponential backoff with jitter
    - Distinguish between retryable and non-retryable errors
    - Respect maximum retry limits and delays
    - Log retry attempts for debugging
    """
    
    def __init__(self, settings: NetworkSettings) -> None:
        """Initialize RetryStrategy with network settings.
        
        Args:
            settings: Network configuration containing retry parameters
        """
        self.settings = settings
        self._retryable_status_codes = {
            408,  # Request Timeout
            429,  # Too Many Requests
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable
            504,  # Gateway Timeout
        }
        self._retryable_exceptions = (
            ConnectionError,
            Timeout,
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ContentDecodingError,
        )
    
    def should_retry(self, response: NetworkResponse, attempt: int) -> bool:
        """Determine if a request should be retried.
        
        Args:
            response: The network response from the failed request
            attempt: Current attempt number (0-based)
            
        Returns:
            True if the request should be retried, False otherwise
        """
        # Check if we've exceeded maximum attempts
        if attempt >= self.settings.retry_attempts:
            logger.debug(f"Maximum retry attempts ({self.settings.retry_attempts}) reached")
            return False
        
        # If request was successful, no retry needed
        if response.success:
            return False
        
        # Check if the error is retryable
        if response.error:
            if self.is_retryable_error(response.error):
                logger.debug(f"Retryable error detected: {type(response.error).__name__}")
                return True
        
        # Check if status code is retryable
        if response.status_code and response.status_code in self._retryable_status_codes:
            logger.debug(f"Retryable status code detected: {response.status_code}")
            return True
        
        logger.debug(f"Non-retryable error: status={response.status_code}, error={response.error}")
        return False
    
    def calculate_delay(self, attempt: int, base_delay: float = 1.0) -> float:
        """Calculate delay before next retry using exponential backoff.
        
        Args:
            attempt: Current attempt number (0-based)
            base_delay: Base delay in seconds
            
        Returns:
            Delay in seconds before next retry
        """
        # Calculate exponential backoff: base_delay * (backoff_factor ^ attempt)
        delay = base_delay * (self.settings.retry_backoff_factor ** attempt)
        
        # Cap the delay at maximum allowed
        delay = min(delay, self.settings.retry_max_delay)
        
        # Add small jitter to prevent thundering herd
        import random
        jitter = delay * 0.1 * random.random()  # Up to 10% jitter
        delay += jitter
        
        logger.debug(f"Calculated retry delay: {delay:.2f}s for attempt {attempt + 1}")
        return delay
    
    def is_retryable_error(self, error: Exception) -> bool:
        """Check if an exception represents a retryable error.
        
        Args:
            error: The exception to check
            
        Returns:
            True if the error is retryable, False otherwise
        """
        # Check for specific retryable exception types
        if isinstance(error, self._retryable_exceptions):
            return True
        
        # Check for HTTP errors with retryable status codes
        if isinstance(error, HTTPError):
            if hasattr(error, 'response') and error.response:
                return error.response.status_code in self._retryable_status_codes
        
        # Check for timeout-related errors
        if isinstance(error, (NetworkTimeoutError, TimeoutError)):
            return True
        
        return False
    
    def wait_for_retry(self, attempt: int, base_delay: float = 1.0) -> None:
        """Wait for the calculated delay before retrying.
        
        Args:
            attempt: Current attempt number (0-based)
            base_delay: Base delay in seconds
        """
        delay = self.calculate_delay(attempt, base_delay)
        logger.info(f"Waiting {delay:.2f}s before retry attempt {attempt + 1}")
        time.sleep(delay)
    
    def create_retry_exhausted_error(
        self, 
        original_response: NetworkResponse, 
        retry_count: int
    ) -> NetworkRetryExhaustedError:
        """Create a NetworkRetryExhaustedError with context.
        
        Args:
            original_response: The final failed response
            retry_count: Number of retries that were attempted
            
        Returns:
            NetworkRetryExhaustedError with detailed context
        """
        if original_response.status_code:
            message = (
                f"Request failed after {retry_count} retries. "
                f"Final status code: {original_response.status_code}"
            )
        else:
            message = (
                f"Request failed after {retry_count} retries. "
                f"Final error: {original_response.error}"
            )
        
        return NetworkRetryExhaustedError(
            message=message,
            retry_count=retry_count,
            last_error=original_response.error
        )
