"""
Metadata obfuscation to prevent forensic fingerprinting.

This module provides methods to randomize metadata writing patterns
and add subtle variations to reduce traceability.
"""

import random
import time
from typing import Dict, Any, List, Tuple


class MetadataObfuscator:
    """Provides metadata obfuscation for forensic fingerprinting resistance."""
    
    def __init__(self):
        """Initialize the metadata obfuscator."""
        self.write_patterns = [
            # Different field ordering patterns
            ['title', 'artist', 'album', 'date', 'tracknumber'],
            ['album', 'artist', 'title', 'tracknumber', 'date'],
            ['artist', 'title', 'album', 'tracknumber', 'date'],
            ['title', 'album', 'artist', 'date', 'tracknumber'],
            ['artist', 'album', 'title', 'date', 'tracknumber'],
        ]
        
        # Timing patterns for metadata writing
        self.timing_patterns = [
            'sequential',      # Write fields one after another
            'grouped',         # Write similar fields together
            'random_delay',    # Random delays between fields
            'burst_delay',     # Fast bursts with longer pauses
        ]
        
    def obfuscate_metadata_write_order(self, metadata_dict: Dict[str, Any]) -> List[Tuple[str, Any]]:
        """
        Randomize metadata writing order.
        
        Args:
            metadata_dict: Dictionary of metadata fields
            
        Returns:
            List of (key, value) tuples in randomized order
        """
        # Select random pattern
        pattern = random.choice(self.write_patterns)
        
        # Create ordered list based on pattern
        ordered_metadata = []
        
        # First, add fields according to pattern
        for key in pattern:
            if key in metadata_dict:
                ordered_metadata.append((key, metadata_dict[key]))
                
        # Add remaining fields in random order
        remaining_keys = [k for k in metadata_dict.keys() if k not in pattern]
        random.shuffle(remaining_keys)
        
        for key in remaining_keys:
            ordered_metadata.append((key, metadata_dict[key]))
            
        return ordered_metadata
    
    def apply_write_timing(self, timing_pattern: str = None) -> float:
        """
        Apply timing delays between metadata field writes.
        
        Args:
            timing_pattern: Specific timing pattern to use
            
        Returns:
            Delay time in seconds
        """
        if timing_pattern is None:
            timing_pattern = random.choice(self.timing_patterns)
            
        if timing_pattern == 'sequential':
            # Very short, consistent delays
            return random.uniform(0.001, 0.003)
            
        elif timing_pattern == 'grouped':
            # Longer delays between groups
            return random.uniform(0.005, 0.015)
            
        elif timing_pattern == 'random_delay':
            # Random delays
            return random.uniform(0.001, 0.020)
            
        elif timing_pattern == 'burst_delay':
            # Either very fast or longer pause
            if random.random() < 0.8:
                return random.uniform(0.0001, 0.001)  # Fast
            else:
                return random.uniform(0.050, 0.100)   # Pause
                
        return 0.001  # Default minimal delay
    
    def add_metadata_variations(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add subtle variations to metadata that won't affect playback.
        
        Args:
            metadata: Original metadata dictionary
            
        Returns:
            Modified metadata dictionary
        """
        modified_metadata = metadata.copy()
        
        # Vary copyright format slightly (10% chance)
        if modified_metadata.get('copy_right') and random.random() < 0.1:
            copyright_text = modified_metadata['copy_right']
            if "©" in copyright_text:
                modified_metadata['copy_right'] = copyright_text.replace("©", "(C)")
            elif "(C)" in copyright_text:
                modified_metadata['copy_right'] = copyright_text.replace("(C)", "©")
            elif "Copyright" in copyright_text:
                modified_metadata['copy_right'] = copyright_text.replace("Copyright", "©")
                
        # Occasionally add or remove trailing spaces (5% chance)
        string_fields = ['title', 'artist', 'album', 'composer', 'albumartist']
        for field in string_fields:
            if modified_metadata.get(field) and random.random() < 0.05:
                current_value = str(modified_metadata[field])
                if random.random() < 0.5:
                    # Add trailing space
                    modified_metadata[field] = current_value + " "
                else:
                    # Remove trailing space if present
                    modified_metadata[field] = current_value.rstrip()
                    
        # Vary date format slightly (15% chance)
        if modified_metadata.get('date') and random.random() < 0.15:
            date_str = str(modified_metadata['date'])
            if len(date_str) == 10 and '-' in date_str:  # YYYY-MM-DD format
                # Sometimes use just year
                if random.random() < 0.7:
                    modified_metadata['date'] = date_str[:4]
                    
        # Vary track number format (10% chance)
        if modified_metadata.get('tracknumber') and random.random() < 0.1:
            track_num = modified_metadata['tracknumber']
            if isinstance(track_num, int):
                # Sometimes pad with zeros
                if random.random() < 0.5:
                    modified_metadata['tracknumber'] = f"{track_num:02d}"
                    
        return modified_metadata
    
    def randomize_field_capitalization(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Slightly vary capitalization in text fields (very subtle).
        
        Args:
            metadata: Original metadata dictionary
            
        Returns:
            Modified metadata dictionary
        """
        modified_metadata = metadata.copy()
        
        # Only apply to a small percentage to avoid obvious patterns
        if random.random() > 0.05:  # 95% chance to not modify
            return modified_metadata
            
        text_fields = ['title', 'album', 'artist', 'composer', 'albumartist']
        
        for field in text_fields:
            if modified_metadata.get(field) and random.random() < 0.3:
                text = str(modified_metadata[field])
                
                # Very subtle changes
                if ' And ' in text and random.random() < 0.5:
                    modified_metadata[field] = text.replace(' And ', ' and ')
                elif ' and ' in text and random.random() < 0.5:
                    modified_metadata[field] = text.replace(' and ', ' And ')
                elif ' The ' in text and random.random() < 0.3:
                    modified_metadata[field] = text.replace(' The ', ' the ')
                elif ' the ' in text and random.random() < 0.3:
                    modified_metadata[field] = text.replace(' the ', ' The ')
                    
        return modified_metadata
    
    def add_optional_fields_randomly(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Randomly include or exclude optional metadata fields.
        
        Args:
            metadata: Original metadata dictionary
            
        Returns:
            Modified metadata dictionary
        """
        modified_metadata = metadata.copy()
        
        # Optional fields that can be omitted without affecting functionality
        optional_fields = ['composer', 'lyrics', 'url_share']
        
        for field in optional_fields:
            if field in modified_metadata:
                # 10% chance to remove optional field
                if random.random() < 0.1:
                    if not modified_metadata[field] or modified_metadata[field] == "":
                        del modified_metadata[field]
                        
        return modified_metadata
    
    def simulate_metadata_writing_session(self, metadata_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Simulate a metadata writing session with realistic patterns.
        
        Args:
            metadata_items: List of metadata dictionaries
            
        Returns:
            List of processed metadata dictionaries
        """
        processed_items = []
        session_pattern = random.choice(self.timing_patterns)
        
        for i, metadata in enumerate(metadata_items):
            # Apply variations
            processed_metadata = self.add_metadata_variations(metadata)
            processed_metadata = self.randomize_field_capitalization(processed_metadata)
            processed_metadata = self.add_optional_fields_randomly(processed_metadata)
            
            # Add session-specific variations
            if i > 0:  # Not first item
                # Occasionally change patterns mid-session
                if random.random() < 0.1:
                    session_pattern = random.choice(self.timing_patterns)
                    
            processed_items.append(processed_metadata)
            
        return processed_items
    
    def get_write_delay_pattern(self, field_count: int) -> List[float]:
        """
        Generate a list of delays for writing metadata fields.
        
        Args:
            field_count: Number of fields to write
            
        Returns:
            List of delay times in seconds
        """
        delays = []
        timing_pattern = random.choice(self.timing_patterns)
        
        for i in range(field_count):
            delay = self.apply_write_timing(timing_pattern)
            delays.append(delay)
            
        return delays
    
    def obfuscate_replay_gain_values(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add tiny variations to replay gain values (inaudible but breaks patterns).
        
        Args:
            metadata: Original metadata dictionary
            
        Returns:
            Modified metadata dictionary
        """
        modified_metadata = metadata.copy()
        
        # Only modify replay gain values occasionally
        if random.random() > 0.2:  # 80% chance to not modify
            return modified_metadata
            
        replay_gain_fields = [
            'album_replay_gain', 'track_replay_gain',
            'album_peak_amplitude', 'track_peak_amplitude'
        ]
        
        for field in replay_gain_fields:
            if field in modified_metadata and modified_metadata[field]:
                original_value = float(modified_metadata[field])
                
                # Add tiny variation (±0.01 dB, inaudible)
                if 'gain' in field:
                    variation = random.uniform(-0.01, 0.01)
                    modified_metadata[field] = round(original_value + variation, 6)
                elif 'peak' in field:
                    # For peak values, add even smaller variation
                    variation = random.uniform(-0.001, 0.001)
                    new_value = max(0.0, min(1.0, original_value + variation))
                    modified_metadata[field] = round(new_value, 6)
                    
        return modified_metadata
    
    def create_metadata_fingerprint_resistance(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply comprehensive metadata obfuscation.
        
        Args:
            metadata: Original metadata dictionary
            
        Returns:
            Fully obfuscated metadata dictionary
        """
        # Apply all obfuscation techniques
        obfuscated = self.add_metadata_variations(metadata)
        obfuscated = self.randomize_field_capitalization(obfuscated)
        obfuscated = self.add_optional_fields_randomly(obfuscated)
        obfuscated = self.obfuscate_replay_gain_values(obfuscated)
        
        return obfuscated
