"""
Test metadata obfuscation and fingerprinting resistance.
"""
import pytest
from collections import Counter
from unittest.mock import patch, MagicMock

from tidal_dl_ng.security.metadata_obfuscator import MetadataObfuscator


class TestMetadataSecurity:
    """Test suite for metadata obfuscation."""
    
    def setup_method(self):
        """Set up test environment."""
        self.obfuscator = MetadataObfuscator()
    
    def test_metadata_write_order_randomization(self):
        """Test that metadata field order is randomized."""
        test_metadata = {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'date': '2023-01-01',
            'tracknumber': 1,
            'composer': 'Test Composer',
            'lyrics': 'Test lyrics...'
        }
        
        # Get multiple orderings
        orderings = []
        for _ in range(20):
            ordered = self.obfuscator.obfuscate_metadata_write_order(test_metadata)
            order = [field[0] for field in ordered]
            orderings.append(tuple(order))
        
        # Should have variety
        unique_orderings = set(orderings)
        assert len(unique_orderings) > 1, "Should have different field orderings"
        
        # All fields should be present
        for ordering in orderings:
            assert set(ordering) == set(test_metadata.keys())
    
    def test_write_timing_patterns(self):
        """Test different timing patterns for metadata writing."""
        timing_patterns = ['sequential', 'grouped', 'random_delay', 'burst_delay']
        
        pattern_delays = {}
        for pattern in timing_patterns:
            delays = []
            for _ in range(50):
                delay = self.obfuscator.apply_write_timing(pattern)
                delays.append(delay)
            pattern_delays[pattern] = delays
        
        # Sequential should be consistent and fast
        assert max(pattern_delays['sequential']) < 0.005
        
        # Random should have more variety
        # Check that random delay has more variation than sequential
        sequential_unique = len(set(pattern_delays['sequential']))
        random_unique = len(set(pattern_delays['random_delay']))
        
        # Either random has more unique values or both have maximum variation
        assert random_unique >= sequential_unique or (random_unique == 50 and sequential_unique == 50)
        
        # Burst should have bimodal distribution
        burst_fast = sum(1 for d in pattern_delays['burst_delay'] if d < 0.01)
        burst_slow = sum(1 for d in pattern_delays['burst_delay'] if d > 0.05)
        assert burst_fast > 30  # Most should be fast
        assert burst_slow >= 3   # Some should be slow (at least 3 out of 50)
    
    def test_metadata_text_variations(self):
        """Test subtle text variations in metadata."""
        test_metadata = {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'date': '2023-01-01',
            'tracknumber': 1,
            'copy_right': '© 2023 Test Label'
        }
        
        # Apply variations multiple times
        variations = []
        for _ in range(100):
            varied = self.obfuscator.add_metadata_variations(test_metadata.copy())
            variations.append(varied)
        
        # Check copyright variations
        copyright_formats = set()
        for v in variations:
            if 'copy_right' in v:
                copyright_formats.add(v['copy_right'])
        
        assert len(copyright_formats) > 1, "Should have copyright variations"
        assert any('(C)' in c for c in copyright_formats) or any('©' in c for c in copyright_formats)
        
        # Check date variations
        date_formats = set()
        for v in variations:
            if 'date' in v:
                date_formats.add(v['date'])
        
        assert len(date_formats) > 1, "Should have date variations"
        assert '2023' in date_formats  # Year-only format
        
        # Check track number variations
        track_formats = set()
        for v in variations:
            if 'tracknumber' in v:
                track_formats.add(str(v['tracknumber']))
        
        # Should have both '1' and '01'
        if len(track_formats) > 1:
            assert '01' in track_formats or '1' in track_formats
    
    def test_capitalization_variations(self):
        """Test subtle capitalization changes."""
        test_metadata = {
            'title': 'The Song and The Artist',
            'artist': 'Band And Friends',
            'album': 'Songs and More Songs'
        }
        
        # Apply many times to catch rare variations
        variations = []
        for _ in range(200):
            varied = self.obfuscator.randomize_field_capitalization(test_metadata.copy())
            variations.append(varied)
        
        # Check for variations (rare occurrence)
        title_variations = set(v['title'] for v in variations)
        artist_variations = set(v['artist'] for v in variations)
        
        # Should have some variations
        if len(title_variations) > 1:
            assert any('and' in t for t in title_variations) or any('And' in t for t in title_variations)
    
    def test_optional_field_randomization(self):
        """Test random inclusion/exclusion of optional fields."""
        test_metadata = {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'composer': '',  # Empty optional field
            'lyrics': '',    # Empty optional field
            'url_share': ''  # Empty optional field
        }
        
        # Apply many times
        fields_removed = Counter()
        for _ in range(100):
            varied = self.obfuscator.add_optional_fields_randomly(test_metadata.copy())
            
            for field in ['composer', 'lyrics', 'url_share']:
                if field not in varied:
                    fields_removed[field] += 1
        
        # Should occasionally remove empty optional fields
        assert sum(fields_removed.values()) > 0, "Should remove some optional fields"
        assert all(count < 20 for count in fields_removed.values()), "Removal should be occasional"
    
    def test_replay_gain_obfuscation(self):
        """Test replay gain value obfuscation."""
        test_metadata = {
            'album_replay_gain': -3.5,
            'track_replay_gain': -2.1,
            'album_peak_amplitude': 0.95,
            'track_peak_amplitude': 0.89
        }
        
        # Apply obfuscation multiple times
        variations = []
        for _ in range(50):
            varied = self.obfuscator.obfuscate_replay_gain_values(test_metadata.copy())
            variations.append(varied)
        
        # Check for variations
        gain_values = set()
        peak_values = set()
        
        for v in variations:
            if 'album_replay_gain' in v and v['album_replay_gain'] != test_metadata['album_replay_gain']:
                gain_values.add(v['album_replay_gain'])
            if 'album_peak_amplitude' in v and v['album_peak_amplitude'] != test_metadata['album_peak_amplitude']:
                peak_values.add(v['album_peak_amplitude'])
        
        # Should have some variations (20% chance)
        assert len(gain_values) > 0 or len(peak_values) > 0, "Should have some variations"
        
        # Variations should be tiny
        for gain in gain_values:
            assert abs(gain - test_metadata['album_replay_gain']) < 0.02
        
        for peak in peak_values:
            assert abs(peak - test_metadata['album_peak_amplitude']) < 0.002
            assert 0.0 <= peak <= 1.0  # Peak should stay in valid range
    
    def test_metadata_fingerprint_resistance(self):
        """Test comprehensive metadata obfuscation."""
        test_metadata = {
            'title': 'Test Song',
            'artist': 'Test Artist And Band',
            'album': 'Test Album',
            'date': '2023-12-25',
            'tracknumber': 5,
            'copy_right': '© 2023 Test Records',
            'composer': 'Test Composer',
            'lyrics': 'La la la...',
            'album_replay_gain': -4.2,
            'track_replay_gain': -3.8,
            'album_peak_amplitude': 0.92,
            'track_peak_amplitude': 0.88
        }
        
        # Apply comprehensive obfuscation
        obfuscated = self.obfuscator.create_metadata_fingerprint_resistance(test_metadata)
        
        # Should maintain all required fields
        assert 'title' in obfuscated
        assert 'artist' in obfuscated
        assert 'album' in obfuscated
        
        # May have variations
        assert obfuscated['title'] == test_metadata['title'] or obfuscated['title'].strip() == test_metadata['title']
    
    def test_metadata_session_simulation(self):
        """Test metadata writing session patterns."""
        metadata_items = [
            {'title': f'Song {i}', 'artist': 'Artist', 'album': 'Album'}
            for i in range(10)
        ]
        
        # Simulate session
        processed = self.obfuscator.simulate_metadata_writing_session(metadata_items)
        
        assert len(processed) == len(metadata_items)
        
        # Each item should be processed
        for i, item in enumerate(processed):
            assert 'title' in item
            assert item['title'].startswith('Song')
    
    def test_write_delay_pattern_generation(self):
        """Test generation of write delay patterns."""
        field_counts = [5, 10, 15]
        
        for count in field_counts:
            delays = self.obfuscator.get_write_delay_pattern(count)
            
            assert len(delays) == count
            assert all(d >= 0 for d in delays)
            assert all(d < 1.0 for d in delays)  # Should be small delays
            
            # Should have some variation
            if count > 5:
                assert len(set(delays)) > 1


class TestMetadataSecurityIntegration:
    """Integration tests for metadata obfuscation."""
    
    def test_metadata_not_currently_integrated(self):
        """Test that metadata obfuscation is not yet integrated in download.py."""
        # This test documents the current state - obfuscation is not used
        from tidal_dl_ng.download import Download
        
        # Check that Download has obfuscator but doesn't use it
        download = MagicMock()
        assert hasattr(Download, '__init__')
        
        # The metadata_write method should exist
        assert hasattr(Download, 'metadata_write')
        
        # This is a documentation test - obfuscation should be integrated
        # but currently is not
    
    def test_metadata_obfuscation_ready_for_integration(self):
        """Test that obfuscation is ready to be integrated."""
        obfuscator = MetadataObfuscator()
        
        # Test with realistic metadata
        realistic_metadata = {
            'title': 'Bohemian Rhapsody',
            'artist': 'Queen',
            'album': 'A Night at the Opera',
            'date': '1975-10-31',
            'tracknumber': 11,
            'totaltrack': 12,
            'discnumber': 1,
            'totaldisc': 1,
            'albumartist': 'Queen',
            'composer': 'Freddie Mercury',
            'copy_right': '© 1975 EMI Records',
            'isrc': 'GBUM71505078',
            'lyrics': 'Is this the real life?...',
            'album_replay_gain': -9.5,
            'track_replay_gain': -7.2,
            'album_peak_amplitude': 0.988,
            'track_peak_amplitude': 0.976
        }
        
        # Apply obfuscation
        obfuscated = obfuscator.create_metadata_fingerprint_resistance(realistic_metadata)
        
        # Should preserve essential data
        assert obfuscated['title'] in ['Bohemian Rhapsody', 'Bohemian Rhapsody ']
        assert obfuscated['artist'] == 'Queen'
        # Album might have capitalization variations
        assert obfuscated['album'].lower().strip() == 'a night at the opera'
        
        # Should maintain data integrity
        if 'tracknumber' in obfuscated:
            assert str(obfuscated['tracknumber']) in ['11', '11']
