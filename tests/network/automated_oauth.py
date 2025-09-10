"""Automated OAuth authentication for TIDAL testing.

This module provides automated browser-based OAuth authentication
using the built-in browser automation capabilities.
"""

import re
import time
import logging
from typing import Optional, Tuple, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class AutomatedOAuthHandler:
    """Handles automated OAuth authentication using browser automation."""
    
    def __init__(self, browser_action_func):
        """Initialize with browser action function.
        
        Args:
            browser_action_func: Function to perform browser actions
        """
        self.browser_action = browser_action_func
        self.timeout = 30  # Default timeout in seconds
        
    def extract_oauth_url(self, oauth_messages: List[str]) -> Optional[str]:
        """Extract OAuth authentication URL from captured messages.
        
        Args:
            oauth_messages: List of OAuth output messages
            
        Returns:
            OAuth authentication URL if found, None otherwise
        """
        for msg in oauth_messages:
            msg_lower = msg.lower()
            
            # Look for messages containing "visit" and "http"
            if 'visit' in msg_lower and 'http' in msg_lower:
                # Extract URL using regex
                url_pattern = r'https?://[^\s]+'
                urls = re.findall(url_pattern, msg)
                
                if urls:
                    url = urls[0]
                    # Clean up URL (remove trailing punctuation)
                    url = url.rstrip('.,!?;')
                    
                    # Validate URL
                    try:
                        parsed = urlparse(url)
                        if parsed.scheme and parsed.netloc:
                            logger.info(f"Extracted OAuth URL: {url}")
                            return url
                    except Exception as e:
                        logger.warning(f"Invalid URL format: {e}")
                        continue
        
        logger.warning("No OAuth URL found in messages")
        return None
    
    def get_automation_steps(self, auth_url: str, username: str, password: str) -> List[dict]:
        """Get the automation steps for OAuth login.
        
        Args:
            auth_url: OAuth authentication URL
            username: TIDAL username
            password: TIDAL password
            
        Returns:
            List of automation steps to be executed by external browser automation
        """
        steps = [
            {
                'action': 'launch',
                'url': auth_url,
                'description': 'Launch browser at OAuth URL'
            },
            {
                'action': 'wait',
                'duration': 3,
                'description': 'Wait for page to load'
            },
            {
                'action': 'screenshot',
                'description': 'Take initial screenshot'
            }
        ]
        
        # Username field attempts
        username_selectors = [
            (400, 300),  # Common center position
            (450, 250),  # Slightly higher
            (450, 350),  # Slightly lower
        ]
        
        for x, y in username_selectors:
            steps.extend([
                {
                    'action': 'click',
                    'coordinate': f"{x},{y}",
                    'description': f'Click username field at ({x}, {y})',
                    'optional': True
                },
                {
                    'action': 'wait',
                    'duration': 1,
                    'description': 'Wait after click'
                },
                {
                    'action': 'type',
                    'text': username,
                    'description': 'Type username',
                    'optional': True
                },
                {
                    'action': 'wait',
                    'duration': 1,
                    'description': 'Wait after typing username'
                }
            ])
        
        # Password field attempts
        password_selectors = [
            (400, 350),  # Below username
            (450, 300),  # Same level as username
            (450, 400),  # Further below
        ]
        
        for x, y in password_selectors:
            steps.extend([
                {
                    'action': 'click',
                    'coordinate': f"{x},{y}",
                    'description': f'Click password field at ({x}, {y})',
                    'optional': True
                },
                {
                    'action': 'wait',
                    'duration': 1,
                    'description': 'Wait after click'
                },
                {
                    'action': 'type',
                    'text': password,
                    'description': 'Type password',
                    'optional': True
                },
                {
                    'action': 'wait',
                    'duration': 1,
                    'description': 'Wait after typing password'
                }
            ])
        
        # Login button attempts
        login_button_selectors = [
            (450, 450),  # Below password field
            (400, 400),  # Center-ish
            (450, 500),  # Lower
            (350, 450),  # Left of center
            (550, 450),  # Right of center
        ]
        
        for x, y in login_button_selectors:
            steps.extend([
                {
                    'action': 'click',
                    'coordinate': f"{x},{y}",
                    'description': f'Click login button at ({x}, {y})',
                    'optional': True
                },
                {
                    'action': 'wait',
                    'duration': 2,
                    'description': 'Wait for form submission'
                }
            ])
        
        # Wait for authentication to complete
        for i in range(10):
            steps.extend([
                {
                    'action': 'wait',
                    'duration': 2,
                    'description': f'Wait for authentication check {i+1}/10'
                },
                {
                    'action': 'screenshot',
                    'description': f'Take screenshot for authentication check {i+1}/10'
                }
            ])
        
        # Close browser
        steps.append({
            'action': 'close',
            'description': 'Close browser'
        })
        
        return steps
    
    def automated_login(self, auth_url: str, username: str, password: str) -> Tuple[bool, str]:
        """Perform automated OAuth login using browser automation.
        
        Note: This method now returns instructions for external automation
        rather than performing the automation directly.
        
        Args:
            auth_url: OAuth authentication URL
            username: TIDAL username
            password: TIDAL password
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            logger.info(f"Preparing automated OAuth login for: {auth_url}")
            
            # Get automation steps
            steps = self.get_automation_steps(auth_url, username, password)
            
            logger.info(f"Generated {len(steps)} automation steps")
            
            # Return success with instructions
            return True, f"Automation steps prepared: {len(steps)} steps ready for execution"
            
        except Exception as e:
            logger.error(f"Failed to prepare automated OAuth login: {e}")
            return False, f"Automation preparation error: {str(e)}"
    
    def is_automation_enabled(self) -> bool:
        """Check if automated OAuth is enabled via environment variable.
        
        Returns:
            True if automation is enabled, False otherwise
        """
        import os
        return os.getenv('TIDAL_OAUTH_AUTOMATION', 'true').lower() in ('true', '1', 'yes', 'on')


def create_oauth_handler(browser_action_func) -> AutomatedOAuthHandler:
    """Create an automated OAuth handler.
    
    Args:
        browser_action_func: Function to perform browser actions
        
    Returns:
        AutomatedOAuthHandler instance
    """
    return AutomatedOAuthHandler(browser_action_func)
