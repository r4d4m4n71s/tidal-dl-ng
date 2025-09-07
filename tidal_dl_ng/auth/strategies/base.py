"""
Base authentication strategy interface

Defines the contract for all authentication strategies following the Strategy pattern.
"""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tidal_dl_ng.enhanced_session import EnhancedTidalSession

logger = logging.getLogger(__name__)


class AuthenticationStrategy(ABC):
    """
    Abstract base class for authentication strategies.
    
    Follows the Strategy pattern to allow different authentication methods
    to be used interchangeably while maintaining the same interface.
    """
    
    @abstractmethod
    def authenticate(self, session: 'EnhancedTidalSession') -> bool:
        """
        Perform authentication using this strategy.
        
        Args:
            session: The TIDAL session to authenticate
            
        Returns:
            True if authentication was successful, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the human-readable name of this authentication strategy."""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """
        Return the priority of this strategy (lower number = higher priority).
        
        Used to determine the order in which strategies are attempted.
        """
        pass
    
    def can_authenticate(self, session: 'EnhancedTidalSession') -> bool:
        """
        Check if this strategy can be used with the given session.
        
        Override this method if the strategy has specific requirements.
        
        Args:
            session: The TIDAL session to check
            
        Returns:
            True if this strategy can be used, False otherwise
        """
        return True
    
    def _log_attempt(self) -> None:
        """Log that this authentication strategy is being attempted."""
        logger.info(f"Attempting authentication using {self.name}")
    
    def _log_success(self) -> None:
        """Log successful authentication."""
        logger.info(f"✅ Authentication successful using {self.name}")
    
    def _log_failure(self, error: Exception = None) -> None:
        """Log failed authentication."""
        error_msg = f" - {str(error)}" if error else ""
        logger.warning(f"❌ Authentication failed using {self.name}{error_msg}")
