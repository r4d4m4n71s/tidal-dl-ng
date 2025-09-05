"""
Request pattern obfuscation for human-like behavior.

This module provides methods to randomize request timing, download patterns,
and connection behavior to mimic human usage patterns.
"""

import random
import time
import numpy as np
from datetime import datetime
from typing import List, Any, Tuple


class RequestObfuscator:
    """Provides request pattern obfuscation for human-like behavior."""
    
    def __init__(self):
        """Initialize the request obfuscator."""
        self.last_request_time = 0
        self.request_history: List[float] = []
        self.session_start_time = time.time()
        self.burst_mode = False
        self.burst_end_time = 0
        
    def get_dynamic_delay(self, base_min: float = 3.0, base_max: float = 5.0) -> float:
        """
        Generate human-like delays with various patterns.
        
        Args:
            base_min: Minimum delay in seconds
            base_max: Maximum delay in seconds
            
        Returns:
            Delay time in seconds
        """
        current_hour = datetime.now().hour
        current_time = time.time()
        
        # Time-of-day factor (slower during work hours, faster at night)
        if 9 <= current_hour <= 17:
            time_factor = 1.5  # Slower during work hours
        elif 22 <= current_hour or current_hour <= 6:
            time_factor = 0.7  # Faster at night
        else:
            time_factor = 1.0
            
        # Session length factor (get slower as session progresses)
        session_duration = (current_time - self.session_start_time) / 3600  # hours
        if session_duration > 2:
            session_factor = 1.3
        elif session_duration > 1:
            session_factor = 1.1
        else:
            session_factor = 1.0
            
        # Check for burst mode
        if self.burst_mode and current_time < self.burst_end_time:
            return random.uniform(0.3, 1.0)
        elif self.burst_mode:
            self.burst_mode = False
            
        # Occasionally enter burst mode (10% chance)
        if random.random() < 0.1:
            self.burst_mode = True
            self.burst_end_time = current_time + random.uniform(30, 120)  # 30s-2min burst
            return random.uniform(0.5, 1.5)
            
        # Normal distribution with occasional outliers
        try:
            delay = np.random.normal((base_min + base_max) / 2, 0.5)
            delay = max(base_min * 0.5, min(base_max * 2, delay))
        except ImportError:
            # Fallback if numpy not available
            delay = random.uniform(base_min, base_max)
            
        # Apply factors
        delay *= time_factor * session_factor
        
        # Occasional long pause (5% chance - simulating user distraction)
        if random.random() < 0.05:
            delay += random.uniform(10, 45)
            
        # Weekend factor (slightly more relaxed)
        if datetime.now().weekday() >= 5:  # Saturday or Sunday
            delay *= 0.9
            
        return round(delay, 2)
    
    def randomize_download_order(self, items: List[Any]) -> List[Any]:
        """
        Randomize download order while maintaining some logical grouping.
        
        Args:
            items: List of items to reorder
            
        Returns:
            Reordered list of items
        """
        if len(items) <= 1:
            return items
            
        # For small lists, just add some randomness
        if len(items) <= 5:
            # 70% chance to keep original order
            if random.random() < 0.7:
                return items
            else:
                shuffled = items.copy()
                random.shuffle(shuffled)
                return shuffled
                
        # Split into chunks (simulating album/playlist listening patterns)
        chunk_size = random.randint(3, min(7, len(items) // 2))
        chunks = [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
        
        # Shuffle chunks
        random.shuffle(chunks)
        
        # Occasionally shuffle within chunks (30% chance per chunk)
        for chunk in chunks:
            if random.random() < 0.3:
                random.shuffle(chunk)
                
        # Sometimes reverse a chunk (10% chance per chunk)
        for chunk in chunks:
            if random.random() < 0.1:
                chunk.reverse()
                
        return [item for chunk in chunks for item in chunk]
    
    def get_concurrent_connections(self, base_max: int = 20) -> int:
        """
        Vary concurrent connection count based on time and session.
        
        Args:
            base_max: Base maximum connections
            
        Returns:
            Number of concurrent connections to use
        """
        current_hour = datetime.now().hour
        
        # Reduce during peak hours (simulate network congestion awareness)
        if 18 <= current_hour <= 21:  # Evening peak
            factor = 0.6
        elif 12 <= current_hour <= 14:  # Lunch peak
            factor = 0.8
        else:
            factor = 1.0
            
        # Add randomness
        connections = int(base_max * factor * random.uniform(0.6, 1.0))
        
        # Ensure minimum of 1 connection
        return max(1, connections)
    
    def should_pause_session(self) -> Tuple[bool, float]:
        """
        Determine if a session pause is needed (simulating user breaks).
        
        Returns:
            Tuple of (should_pause, pause_duration_seconds)
        """
        current_time = time.time()
        session_duration = (current_time - self.session_start_time) / 60  # minutes
        
        # More likely to pause as session gets longer
        if session_duration > 120:  # 2+ hours
            pause_chance = 0.3
        elif session_duration > 60:  # 1+ hour
            pause_chance = 0.15
        elif session_duration > 30:  # 30+ minutes
            pause_chance = 0.05
        else:
            pause_chance = 0.01
            
        if random.random() < pause_chance:
            # Pause duration: 2-15 minutes
            pause_duration = random.uniform(120, 900)
            return True, pause_duration
            
        return False, 0.0
    
    def get_retry_delay(self, attempt: int, base_delay: float = 1.0) -> float:
        """
        Get exponential backoff delay with jitter for retries.
        
        Args:
            attempt: Retry attempt number (0-based)
            base_delay: Base delay for first retry
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff with jitter
        delay = base_delay * (2 ** attempt)
        
        # Add jitter (±25%)
        jitter = delay * 0.25 * (random.random() * 2 - 1)
        delay += jitter
        
        # Cap maximum delay at 60 seconds
        delay = min(delay, 60.0)
        
        return max(0.1, delay)
    
    def simulate_user_interaction_delay(self) -> float:
        """
        Simulate delays from user interactions (reading, clicking, etc.).
        
        Returns:
            Delay in seconds
        """
        # Different types of user interactions
        interaction_type = random.choice([
            'quick_click',     # Fast interaction
            'reading',         # User reading track info
            'browsing',        # Looking through results
            'distracted'       # User got distracted
        ])
        
        if interaction_type == 'quick_click':
            return random.uniform(0.1, 0.5)
        elif interaction_type == 'reading':
            return random.uniform(2.0, 8.0)
        elif interaction_type == 'browsing':
            return random.uniform(5.0, 15.0)
        else:  # distracted
            return random.uniform(10.0, 60.0)
    
    def update_request_history(self, request_time: float) -> None:
        """
        Update request history for pattern analysis.
        
        Args:
            request_time: Timestamp of the request
        """
        self.request_history.append(request_time)
        
        # Keep only last 100 requests
        if len(self.request_history) > 100:
            self.request_history = self.request_history[-100:]
            
        self.last_request_time = request_time
    
    def get_adaptive_delay(self, recent_failures: int = 0) -> float:
        """
        Get adaptive delay based on recent failures and request history.
        
        Args:
            recent_failures: Number of recent request failures
            
        Returns:
            Adaptive delay in seconds
        """
        base_delay = 3.0
        
        # Increase delay based on recent failures
        if recent_failures > 0:
            base_delay *= (1.5 ** recent_failures)
            
        # Analyze request frequency
        if len(self.request_history) >= 2:
            recent_interval = self.request_history[-1] - self.request_history[-2]
            if recent_interval < 1.0:  # Very fast requests
                base_delay *= 2.0
                
        return self.get_dynamic_delay(base_delay, base_delay * 1.5)
