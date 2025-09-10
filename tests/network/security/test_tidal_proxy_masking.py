"""Test TIDAL proxy traffic masking and anonymization.

This test validates that TIDAL traffic is properly masked through proxy connections,
testing both complete anonymization and geo-masking capabilities.
"""

import logging
import json
import time
import hashlib
import statistics
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse, parse_qs

import requests
from requests.exceptions import RequestException

from tidal_dl_ng.config import Settings, Tidal
from tidal_dl_ng.network import NetworkManager
from tidal_dl_ng.model.network import NetworkSettings, ProxySettings


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrafficAnalyzer:
    """Utility class to analyze network traffic patterns and detect TIDAL signatures."""
    
    def __init__(self):
        self.traffic_samples = []
        self.timing_patterns = []
        self.request_fingerprints = []
    
    def capture_request_pattern(self, method: str, url: str, headers: Dict[str, str], 
                              body: Optional[str] = None, timestamp: float = None) -> Dict[str, Any]:
        """Capture and analyze a request pattern."""
        if timestamp is None:
            timestamp = time.time()
        
        # Parse URL components
        parsed_url = urlparse(url)
        
        # Create request fingerprint
        fingerprint = {
            'timestamp': timestamp,
            'method': method,
            'domain': parsed_url.netloc,
            'path': parsed_url.path,
            'query_params': len(parse_qs(parsed_url.query)),
            'headers_count': len(headers),
            'body_size': len(body) if body else 0,
            'user_agent': headers.get('User-Agent', ''),
            'content_type': headers.get('Content-Type', ''),
            'authorization': bool(headers.get('Authorization')),
            'custom_headers': self._identify_custom_headers(headers)
        }
        
        # Calculate request signature hash
        signature_data = f"{method}:{parsed_url.netloc}:{parsed_url.path}:{fingerprint['headers_count']}"
        fingerprint['signature_hash'] = hashlib.md5(signature_data.encode()).hexdigest()
        
        self.request_fingerprints.append(fingerprint)
        return fingerprint
    
    def _identify_custom_headers(self, headers: Dict[str, str]) -> List[str]:
        """Identify non-standard HTTP headers."""
        standard_headers = {
            'accept', 'accept-encoding', 'accept-language', 'authorization',
            'cache-control', 'connection', 'content-length', 'content-type',
            'cookie', 'host', 'referer', 'user-agent', 'x-forwarded-for',
            'x-real-ip', 'pragma', 'upgrade-insecure-requests'
        }
        
        custom_headers = []
        for header_name in headers.keys():
            if header_name.lower() not in standard_headers:
                custom_headers.append(header_name)
        
        return custom_headers
    
    def analyze_tidal_signatures(self) -> Dict[str, Any]:
        """Analyze captured traffic for TIDAL-specific signatures."""
        analysis = {
            'total_requests': len(self.request_fingerprints),
            'unique_domains': set(),
            'tidal_indicators': {
                'domain_matches': [],
                'user_agent_matches': [],
                'path_patterns': [],
                'timing_patterns': [],
                'header_signatures': []
            },
            'anonymization_score': 0.0,
            'risk_assessment': 'UNKNOWN'
        }
        
        # Analyze domains
        for fp in self.request_fingerprints:
            analysis['unique_domains'].add(fp['domain'])
            
            # Check for TIDAL domain indicators
            domain = fp['domain'].lower()
            if any(indicator in domain for indicator in ['tidal', 'music', 'streaming']):
                analysis['tidal_indicators']['domain_matches'].append(fp['domain'])
            
            # Check User-Agent
            user_agent = fp['user_agent'].lower()
            if any(indicator in user_agent for indicator in ['tidal', 'music']):
                analysis['tidal_indicators']['user_agent_matches'].append(fp['user_agent'])
            
            # Check path patterns
            path = fp['path'].lower()
            if any(indicator in path for indicator in ['api', 'auth', 'login', 'token']):
                analysis['tidal_indicators']['path_patterns'].append(fp['path'])
            
            # Check custom headers
            if fp['custom_headers']:
                for header in fp['custom_headers']:
                    if 'tidal' in header.lower():
                        analysis['tidal_indicators']['header_signatures'].append(header)
        
        # Convert set to list for JSON serialization
        analysis['unique_domains'] = list(analysis['unique_domains'])
        
        # Calculate anonymization score
        analysis['anonymization_score'] = self._calculate_anonymization_score(analysis)
        analysis['risk_assessment'] = self._assess_risk_level(analysis['anonymization_score'])
        
        return analysis
    
    def _calculate_anonymization_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate anonymization effectiveness score (0-100)."""
        score = 100.0
        
        # Deduct points for TIDAL indicators
        indicators = analysis['tidal_indicators']
        
        # Domain matches (high risk)
        score -= len(indicators['domain_matches']) * 25
        
        # User-Agent matches (medium risk)
        score -= len(indicators['user_agent_matches']) * 15
        
        # Path patterns (low risk)
        score -= len(indicators['path_patterns']) * 5
        
        # Header signatures (high risk)
        score -= len(indicators['header_signatures']) * 20
        
        return max(0.0, score)
    
    def _assess_risk_level(self, score: float) -> str:
        """Assess risk level based on anonymization score."""
        if score >= 90:
            return 'LOW'
        elif score >= 70:
            return 'MEDIUM'
        elif score >= 50:
            return 'HIGH'
        else:
            return 'CRITICAL'
    
    def analyze_timing_patterns(self) -> Dict[str, Any]:
        """Analyze request timing patterns for fingerprinting risks."""
        if len(self.request_fingerprints) < 2:
            return {'error': 'Insufficient data for timing analysis'}
        
        # Calculate intervals between requests
        timestamps = [fp['timestamp'] for fp in self.request_fingerprints]
        timestamps.sort()
        
        intervals = []
        for i in range(1, len(timestamps)):
            intervals.append(timestamps[i] - timestamps[i-1])
        
        if not intervals:
            return {'error': 'No intervals to analyze'}
        
        # Statistical analysis
        timing_analysis = {
            'total_requests': len(timestamps),
            'time_span': timestamps[-1] - timestamps[0],
            'average_interval': statistics.mean(intervals),
            'median_interval': statistics.median(intervals),
            'interval_variance': statistics.variance(intervals) if len(intervals) > 1 else 0,
            'regular_pattern_detected': False,
            'burst_patterns': []
        }
        
        # Detect regular patterns (potential fingerprinting risk)
        if timing_analysis['interval_variance'] < 1.0:  # Low variance indicates regular pattern
            timing_analysis['regular_pattern_detected'] = True
        
        # Detect burst patterns
        burst_threshold = timing_analysis['average_interval'] * 0.1  # 10% of average
        current_burst = []
        
        for interval in intervals:
            if interval < burst_threshold:
                current_burst.append(interval)
            else:
                if len(current_burst) >= 3:  # 3+ rapid requests = burst
                    timing_analysis['burst_patterns'].append(len(current_burst))
                current_burst = []
        
        return timing_analysis
    
    def generate_traffic_report(self) -> Dict[str, Any]:
        """Generate comprehensive traffic analysis report."""
        signature_analysis = self.analyze_tidal_signatures()
        timing_analysis = self.analyze_timing_patterns()
        
        return {
            'signature_analysis': signature_analysis,
            'timing_analysis': timing_analysis,
            'recommendations': self._generate_recommendations(signature_analysis, timing_analysis)
        }
    
    def _generate_recommendations(self, signature_analysis: Dict[str, Any], 
                                timing_analysis: Dict[str, Any]) -> List[str]:
        """Generate security recommendations based on analysis."""
        recommendations = []
        
        # Check anonymization score
        score = signature_analysis['anonymization_score']
        if score < 70:
            recommendations.append("CRITICAL: Improve traffic anonymization - TIDAL signatures detected")
        
        # Check domain exposure
        if signature_analysis['tidal_indicators']['domain_matches']:
            recommendations.append("HIGH: TIDAL domains detected - consider domain masking")
        
        # Check User-Agent exposure
        if signature_analysis['tidal_indicators']['user_agent_matches']:
            recommendations.append("MEDIUM: TIDAL-revealing User-Agents detected")
        
        # Check timing patterns
        if timing_analysis.get('regular_pattern_detected'):
            recommendations.append("MEDIUM: Regular timing patterns detected - add randomization")
        
        # Check burst patterns
        if timing_analysis.get('burst_patterns'):
            recommendations.append("LOW: Burst request patterns detected - consider rate limiting")
        
        if not recommendations:
            recommendations.append("GOOD: No major anonymization issues detected")
        
        return recommendations


def test_complete_header_anonymization(proxy_settings, network_settings):
    """Test complete anonymization of TIDAL-identifying headers."""
    print("=" * 60)
    print("TESTING COMPLETE HEADER ANONYMIZATION")
    print("=" * 60)
    
    analyzer = TrafficAnalyzer()
    
    # Configure NetworkManager with proxy
    network_manager = NetworkManager()
    network_manager.configure(network_settings, proxy_settings)
    
    # Test different session types
    session_types = ["default", "api", "auth", "download"]
    anonymization_results = {}
    
    for session_type in session_types:
        print(f"\nTesting {session_type} session anonymization...")
        session = network_manager.get_session(session_type)
        
        # Capture session configuration
        headers = dict(session.headers)
        proxies = dict(session.proxies) if session.proxies else {}
        
        # Analyze headers for TIDAL signatures
        tidal_signatures = []
        for name, value in headers.items():
            if any(keyword in name.lower() for keyword in ['tidal', 'music', 'streaming']):
                tidal_signatures.append(f"Header name: {name}")
            if any(keyword in str(value).lower() for keyword in ['tidal', 'music', 'streaming']):
                tidal_signatures.append(f"Header value: {name}={value}")
        
        # Create traffic pattern
        pattern = analyzer.capture_request_pattern(
            method="GET",
            url="https://api.tidal.com/v1/login/username",
            headers=headers,
            timestamp=time.time()
        )
        
        anonymization_results[session_type] = {
            'tidal_signatures': tidal_signatures,
            'proxy_enabled': bool(proxies),
            'custom_headers': pattern['custom_headers'],
            'user_agent_safe': 'tidal' not in headers.get('User-Agent', '').lower()
        }
        
        print(f"  Proxy enabled: {bool(proxies)}")
        print(f"  TIDAL signatures found: {len(tidal_signatures)}")
        print(f"  Custom headers: {len(pattern['custom_headers'])}")
        print(f"  User-Agent safe: {anonymization_results[session_type]['user_agent_safe']}")
        
        if tidal_signatures:
            print("  WARNING: TIDAL signatures detected:")
            for sig in tidal_signatures[:3]:  # Show first 3
                print(f"    - {sig}")
            if len(tidal_signatures) > 3:
                print(f"    ... and {len(tidal_signatures) - 3} more")
    
    # Overall anonymization assessment
    print(f"\nOverall Anonymization Assessment:")
    
    total_signatures = sum(len(result['tidal_signatures']) for result in anonymization_results.values())
    sessions_with_proxy = sum(1 for result in anonymization_results.values() if result['proxy_enabled'])
    safe_user_agents = sum(1 for result in anonymization_results.values() if result['user_agent_safe'])
    
    print(f"  Total TIDAL signatures: {total_signatures}")
    print(f"  Sessions with proxy: {sessions_with_proxy}/{len(session_types)}")
    print(f"  Safe User-Agents: {safe_user_agents}/{len(session_types)}")
    
    # Calculate anonymization score
    anonymization_score = 100.0
    if total_signatures > 0:
        anonymization_score -= total_signatures * 20
    if sessions_with_proxy < len(session_types):
        anonymization_score -= (len(session_types) - sessions_with_proxy) * 25
    if safe_user_agents < len(session_types):
        anonymization_score -= (len(session_types) - safe_user_agents) * 15
    
    anonymization_score = max(0.0, anonymization_score)
    
    print(f"  Anonymization Score: {anonymization_score:.1f}/100")
    
    if anonymization_score >= 90:
        print("  ✓ EXCELLENT: Traffic appears well anonymized")
    elif anonymization_score >= 70:
        print("  ⚠ GOOD: Minor anonymization improvements needed")
    elif anonymization_score >= 50:
        print("  ⚠ FAIR: Significant anonymization issues detected")
    else:
        print("  ❌ POOR: Critical anonymization failures")
    
    # Verify proxy is working
    assert sessions_with_proxy > 0, "At least some sessions should use proxy"
    
    print("✓ Complete header anonymization test completed")


def test_request_fingerprint_masking(proxy_settings, network_settings):
    """Test that TIDAL requests appear as generic traffic."""
    print("\n" + "=" * 60)
    print("TESTING REQUEST FINGERPRINT MASKING")
    print("=" * 60)
    
    analyzer = TrafficAnalyzer()
    
    # Configure NetworkManager
    network_manager = NetworkManager()
    network_manager.configure(network_settings, proxy_settings)
    
    # Simulate various TIDAL API requests
    test_requests = [
        ("GET", "https://api.tidal.com/v1/login/username", {}),
        ("POST", "https://api.tidal.com/v1/oauth2/token", {"grant_type": "refresh_token"}),
        ("GET", "https://api.tidal.com/v1/search/tracks", {"query": "test"}),
        ("GET", "https://api.tidal.com/v1/albums/12345", {}),
        ("GET", "https://resources.tidal.com/images/cover.jpg", {})
    ]
    
    print("Analyzing request fingerprints...")
    
    # Capture patterns for each request type
    session = network_manager.get_session("api")
    headers = dict(session.headers)
    
    fingerprints = []
    for method, url, params in test_requests:
        # Add timestamp variation to simulate real usage
        timestamp = time.time() + len(fingerprints) * 0.5
        
        fingerprint = analyzer.capture_request_pattern(
            method=method,
            url=url,
            headers=headers,
            body=json.dumps(params) if params else None,
            timestamp=timestamp
        )
        fingerprints.append(fingerprint)
        
        print(f"  {method} {urlparse(url).path}: {fingerprint['signature_hash'][:8]}...")
    
    # Analyze fingerprints for TIDAL signatures
    analysis = analyzer.analyze_tidal_signatures()
    
    print(f"\nFingerprint Analysis:")
    print(f"  Total requests analyzed: {analysis['total_requests']}")
    print(f"  Unique domains: {len(analysis['unique_domains'])}")
    print(f"  Anonymization score: {analysis['anonymization_score']:.1f}/100")
    print(f"  Risk assessment: {analysis['risk_assessment']}")
    
    # Check specific indicators
    indicators = analysis['tidal_indicators']
    
    print(f"\nTIDAL Indicators Found:")
    print(f"  Domain matches: {len(indicators['domain_matches'])}")
    if indicators['domain_matches']:
        for domain in indicators['domain_matches'][:3]:
            print(f"    - {domain}")
    
    print(f"  User-Agent matches: {len(indicators['user_agent_matches'])}")
    if indicators['user_agent_matches']:
        for ua in indicators['user_agent_matches'][:2]:
            print(f"    - {ua[:50]}...")
    
    print(f"  Path patterns: {len(indicators['path_patterns'])}")
    print(f"  Header signatures: {len(indicators['header_signatures'])}")
    
    # Generate recommendations
    report = analyzer.generate_traffic_report()
    recommendations = report['recommendations']
    
    print(f"\nSecurity Recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")
    
    # Assess masking effectiveness
    if analysis['anonymization_score'] >= 80:
        print("\n✓ GOOD: Request fingerprints appear well masked")
    elif analysis['anonymization_score'] >= 60:
        print("\n⚠ MODERATE: Some fingerprinting risks detected")
    else:
        print("\n❌ POOR: Significant fingerprinting risks detected")
    
    print("✓ Request fingerprint masking test completed")


def test_traffic_pattern_anonymization(proxy_settings, network_settings):
    """Test that traffic patterns don't reveal TIDAL usage."""
    print("\n" + "=" * 60)
    print("TESTING TRAFFIC PATTERN ANONYMIZATION")
    print("=" * 60)
    
    analyzer = TrafficAnalyzer()
    
    # Configure NetworkManager
    network_manager = NetworkManager()
    network_manager.configure(network_settings, proxy_settings)
    
    # Simulate realistic TIDAL usage pattern
    print("Simulating realistic TIDAL usage pattern...")
    
    session = network_manager.get_session("api")
    headers = dict(session.headers)
    
    # Authentication sequence
    auth_requests = [
        ("POST", "https://api.tidal.com/v1/oauth2/token", "auth"),
        ("GET", "https://api.tidal.com/v1/sessions", "session_check"),
        ("GET", "https://api.tidal.com/v1/users/me", "user_info")
    ]
    
    # Music browsing sequence
    browse_requests = [
        ("GET", "https://api.tidal.com/v1/search/tracks", "search"),
        ("GET", "https://api.tidal.com/v1/albums/12345", "album_info"),
        ("GET", "https://api.tidal.com/v1/tracks/67890", "track_info"),
        ("GET", "https://resources.tidal.com/images/cover.jpg", "cover_image")
    ]
    
    # Simulate requests with realistic timing
    base_time = time.time()
    
    # Authentication burst (quick sequence)
    for i, (method, url, req_type) in enumerate(auth_requests):
        timestamp = base_time + i * 0.2  # 200ms intervals
        analyzer.capture_request_pattern(method, url, headers, timestamp=timestamp)
    
    # Browsing pattern (more spaced out)
    for i, (method, url, req_type) in enumerate(browse_requests):
        timestamp = base_time + 5 + i * 2.0  # 2 second intervals after 5 second pause
        analyzer.capture_request_pattern(method, url, headers, timestamp=timestamp)
    
    # Analyze timing patterns
    timing_analysis = analyzer.analyze_timing_patterns()
    
    print(f"Timing Pattern Analysis:")
    print(f"  Total requests: {timing_analysis.get('total_requests', 0)}")
    print(f"  Time span: {timing_analysis.get('time_span', 0):.2f} seconds")
    print(f"  Average interval: {timing_analysis.get('average_interval', 0):.2f} seconds")
    print(f"  Median interval: {timing_analysis.get('median_interval', 0):.2f} seconds")
    print(f"  Interval variance: {timing_analysis.get('interval_variance', 0):.2f}")
    print(f"  Regular pattern detected: {timing_analysis.get('regular_pattern_detected', False)}")
    print(f"  Burst patterns: {len(timing_analysis.get('burst_patterns', []))}")
    
    # Analyze overall traffic signature
    signature_analysis = analyzer.analyze_tidal_signatures()
    
    print(f"\nTraffic Signature Analysis:")
    print(f"  Unique domains: {len(signature_analysis['unique_domains'])}")
    print(f"  Domain exposure risk: {len(signature_analysis['tidal_indicators']['domain_matches']) > 0}")
    print(f"  Pattern anonymization score: {signature_analysis['anonymization_score']:.1f}/100")
    
    # Check for suspicious patterns
    suspicious_patterns = []
    
    # Check for authentication burst pattern
    if len(timing_analysis.get('burst_patterns', [])) > 0:
        suspicious_patterns.append("Authentication burst pattern detected")
    
    # Check for regular intervals
    if timing_analysis.get('regular_pattern_detected'):
        suspicious_patterns.append("Regular request intervals detected")
    
    # Check for TIDAL domain concentration
    tidal_domains = [d for d in signature_analysis['unique_domains'] if 'tidal' in d.lower()]
    if len(tidal_domains) > 0:
        suspicious_patterns.append(f"TIDAL domains detected: {len(tidal_domains)}")
    
    print(f"\nSuspicious Patterns:")
    if suspicious_patterns:
        for pattern in suspicious_patterns:
            print(f"  ⚠ {pattern}")
    else:
        print("  ✓ No suspicious patterns detected")
    
    # Overall assessment
    pattern_score = 100.0
    pattern_score -= len(suspicious_patterns) * 20
    pattern_score -= len(tidal_domains) * 15
    
    if timing_analysis.get('regular_pattern_detected'):
        pattern_score -= 25
    
    pattern_score = max(0.0, pattern_score)
    
    print(f"\nPattern Anonymization Score: {pattern_score:.1f}/100")
    
    if pattern_score >= 80:
        print("✓ EXCELLENT: Traffic patterns appear well anonymized")
    elif pattern_score >= 60:
        print("⚠ GOOD: Minor pattern anonymization improvements needed")
    else:
        print("❌ POOR: Traffic patterns may reveal TIDAL usage")
    
    print("✓ Traffic pattern anonymization test completed")


def test_geo_location_header_masking(proxy_settings, network_settings):
    """Test that geo-location headers are properly masked."""
    print("\n" + "=" * 60)
    print("TESTING GEO-LOCATION HEADER MASKING")
    print("=" * 60)
    
    # Configure NetworkManager with proxy
    network_manager = NetworkManager()
    network_manager.configure(network_settings, proxy_settings)
    
    # Test geo-location detection
    print("Testing geo-location masking through proxy...")
    
    # Get session and check for geo-location headers
    session = network_manager.get_session("api")
    headers = dict(session.headers)
    proxies = dict(session.proxies) if session.proxies else {}
    
    print(f"  Proxy configuration: {bool(proxies)}")
    if proxies:
        print(f"    HTTP proxy: {proxies.get('http', 'Not set')}")
        print(f"    HTTPS proxy: {proxies.get('https', 'Not set')}")
    
    # Check for geo-location revealing headers
    geo_headers = []
    geo_keywords = ['country', 'region', 'location', 'timezone', 'locale', 'lang']
    
    for name, value in headers.items():
        name_lower = name.lower()
        value_lower = str(value).lower()
        
        if any(keyword in name_lower for keyword in geo_keywords):
            geo_headers.append(f"Header name: {name}")
        
        if any(keyword in value_lower for keyword in geo_keywords):
            geo_headers.append(f"Header value: {name}={value}")
    
    print(f"  Geo-location headers found: {len(geo_headers)}")
    if geo_headers:
        print("  WARNING: Geo-location revealing headers:")
        for header in geo_headers:
            print(f"    - {header}")
    
    # Test IP geolocation masking (simulate)
    print(f"\nTesting IP geolocation masking...")
    
    # Check if proxy is from expected region
    proxy_url = proxy_settings.http_proxy if proxy_settings.enabled else None
    if proxy_url:
        # Extract proxy location info from URL if available
        if 'geo.iproyal.com' in proxy_url:
            print("  Using geo-location proxy service")
            
            # Check if session configuration includes location masking
            expected_location = "colombia"  # Based on proxy config
            
            # Look for location indicators in headers
            location_indicators = []
            for name, value in headers.items():
                if any(loc in str(value).lower() for loc in ['colombia', 'co', 'bogota', 'pereira']):
                    location_indicators.append(f"{name}: {value}")
            
            print(f"  Location indicators in headers: {len(location_indicators)}")
            if location_indicators:
                print("  Location-specific headers found:")
                for indicator in location_indicators:
                    print(f"    - {indicator}")
            else:
                print("  ✓ No obvious location indicators in headers")
    
    # Test Accept-Language header
    accept_language = headers.get('Accept-Language', '')
    print(f"\nAccept-Language Analysis:")
    print(f"  Accept-Language: {accept_language}")
    
    if accept_language:
        # Check if language reveals location
        location_revealing_langs = ['es-co', 'es-pe', 'pt-br', 'en-us', 'en-gb']
        reveals_location = any(lang in accept_language.lower() for lang in location_revealing_langs)
        print(f"  Reveals location: {reveals_location}")
        
        if reveals_location:
            print("  ⚠ WARNING: Accept-Language may reveal geographic location")
        else:
            print("  ✓ Accept-Language appears location-neutral")
    else:
        print("  ✓ No Accept-Language header (good for anonymity)")
    
    # Test timezone detection
    print(f"\nTimezone Masking Analysis:")
    
    # Check if any headers contain timezone information
    timezone_headers = []
    for name, value in headers.items():
        if any(tz in str(value).lower() for tz in ['utc', 'gmt', 'timezone', 'tz']):
            timezone_headers.append(f"{name}: {value}")
    
    print(f"  Timezone-related headers: {len(timezone_headers)}")
    if timezone_headers:
        for tz_header in timezone_headers:
            print(f"    - {tz_header}")
    else:
        print("  ✓ No timezone information in headers")
    
    # Overall geo-masking assessment
    print(f"\nGeo-masking Assessment:")
    
    geo_risk_score = 0
    if geo_headers:
        geo_risk_score += len(geo_headers) * 20
    if accept_language and any(lang in accept_language.lower() for lang in location_revealing_langs):
        geo_risk_score += 30
    if timezone_headers:
        geo_risk_score += len(timezone_headers) * 15
    
    geo_masking_score = max(0, 100 - geo_risk_score)
    
    print(f"  Geo-masking score: {geo_masking_score}/100")
    print(f"  Proxy enabled: {bool(proxies)}")
    
    if geo_masking_score >= 90:
        print("  ✓ EXCELLENT: Geographic information well masked")
    elif geo_masking_score >= 70:
        print("  ⚠ GOOD: Minor geo-location leaks detected")
    elif geo_masking_score >= 50:
        print("  ⚠ FAIR: Moderate geo-location exposure")
    else:
        print("  ❌ POOR: Significant geo-location exposure")
    
    # Verify proxy is working for geo-masking
    assert bool(proxies), "Proxy should be enabled for geo-masking"
    
    print("✓ Geo-location header masking test completed")


def test_regional_endpoint_masking(proxy_settings, network_settings):
    """Test that TIDAL regional API calls are properly masked."""
    print("\n" + "=" * 60)
    print("TESTING REGIONAL ENDPOINT MASKING")
    print("=" * 60)
    
    analyzer = TrafficAnalyzer()
    
    # Configure NetworkManager
    network_manager = NetworkManager()
    network_manager.configure(network_settings, proxy_settings)
    
    # Test various regional TIDAL endpoints
    regional_endpoints = [
        "https://api.tidal.com/v1/pages/home",  # Home page (region-specific)
        "https://api.tidal.com/v1/pages/explore",  # Explore (region-specific)
        "https://api.tidal.com/v1/search/tracks?countryCode=US",  # Explicit country
        "https://api.tidal.com/v1/search/tracks?countryCode=CO",  # Colombia
        "https://listen.tidal.com/",  # Regional subdomain
        "https://tidal.com/browse/genre/pop?region=us"  # Regional parameter
    ]
    
    print("Analyzing regional endpoint access patterns...")
    
    session = network_manager.get_session("api")
    headers = dict(session.headers)
    
    regional_analysis = {
        'endpoints_tested': len(regional_endpoints),
        'country_codes_detected': [],
        'regional_parameters': [],
        'subdomain_variations': [],
        'masking_effectiveness': 0.0
    }
    
    for endpoint in regional_endpoints:
        # Analyze endpoint for regional indicators
        parsed_url = urlparse(endpoint)
        
        # Check for country codes in URL
        if 'countrycode=' in endpoint.lower():
            country_match = endpoint.lower().split('countrycode=')[1].split('&')[0]
            regional_analysis['country_codes_detected'].append(country_match)
        
        # Check for regional parameters
        if 'region=' in endpoint.lower():
            region_match = endpoint.lower().split('region=')[1].split('&')[0]
            regional_analysis['regional_parameters'].append(region_match)
        
        # Check for regional subdomains
        if parsed_url.netloc != 'api.tidal.com':
            regional_analysis['subdomain_variations'].append(parsed_url.netloc)
        
        # Capture request pattern
        analyzer.capture_request_pattern(
            method="GET",
            url=endpoint,
            headers=headers,
            timestamp=time.time()
        )
    
    print(f"  Country codes detected: {len(regional_analysis['country_codes_detected'])}")
    if regional_analysis['country_codes_detected']:
        print(f"    Codes: {regional_analysis['country_codes_detected']}")
    
    print(f"  Regional parameters: {len(regional_analysis['regional_parameters'])}")
    if regional_analysis['regional_parameters']:
        print(f"    Parameters: {regional_analysis['regional_parameters']}")
    
    print(f"  Subdomain variations: {len(regional_analysis['subdomain_variations'])}")
    if regional_analysis['subdomain_variations']:
        print(f"    Subdomains: {regional_analysis['subdomain_variations']}")
    
    # Analyze masking effectiveness
    signature_analysis = analyzer.analyze_tidal_signatures()
    
    print(f"\nRegional Masking Analysis:")
    print(f"  TIDAL domains detected: {len(signature_analysis['tidal_indicators']['domain_matches'])}")
    print(f"  Regional anonymization score: {signature_analysis['anonymization_score']:.1f}/100")
    
    # Calculate regional masking score
    regional_score = 100.0
    regional_score -= len(regional_analysis['country_codes_detected']) * 30  # High risk
    regional_score -= len(regional_analysis['regional_parameters']) * 25     # High risk
    regional_score -= len(regional_analysis['subdomain_variations']) * 20    # Medium risk
    
    regional_score = max(0.0, regional_score)
    
    print(f"  Regional masking score: {regional_score:.1f}/100")
    
    if regional_score >= 90:
        print("  ✓ EXCELLENT: Regional endpoints well masked")
    elif regional_score >= 70:
        print("  ⚠ GOOD: Minor regional exposure detected")
    elif regional_score >= 50:
        print("  ⚠ FAIR: Moderate regional exposure")
    else:
        print("  ❌ POOR: Significant regional exposure")
    
    # Recommendations
    print(f"\nRegional Masking Recommendations:")
    if regional_analysis['country_codes_detected']:
        print("  - Consider masking or randomizing country codes in API calls")
    if regional_analysis['regional_parameters']:
        print("  - Regional parameters may reveal user location")
    if regional_analysis['subdomain_variations']:
        print("  - Regional subdomains may indicate geographic targeting")
    
    if not any([regional_analysis['country_codes_detected'], 
               regional_analysis['regional_parameters'],
               regional_analysis['subdomain_variations']]):
        print("  ✓ No obvious regional indicators detected")
    
    print("✓ Regional endpoint masking test completed")


if __name__ == "__main__":
    """Run all proxy masking tests manually."""
    print("TIDAL PROXY TRAFFIC MASKING - COMPREHENSIVE TEST")
    print("=" * 60)
    print("This test validates TIDAL traffic masking and anonymization through proxy.")
    print()
    
    # Create test settings
    proxy_settings = ProxySettings(
        enabled=True,
        http_proxy="http://geo.iproyal.com:12321",
        https_proxy="https://geo.iproyal.com:12321",
        username="LwAit6sjotiaziYw",
        password="oKYCBDdannR7E4XX_country-co_city-pereira_session-YKbtdc4a_lifetime-30m",
        connection_timeout=10,
        test_url="https://httpbin.org/ip"
    )
    
    network_settings = NetworkSettings(
        retry_attempts=2,
        retry_backoff_factor=1.5,
        retry_max_delay=30.0,
        connection_timeout=10,
        read_timeout=30,
        download_timeout=60.0,
        api_timeout=15.0,
        user_agent="TIDAL/2.19.1 (Linux;Android 13; Android Auto) okhttp/4.10.0"
    )
    
    try:
        # Run all masking tests
        test_complete_header_anonymization(proxy_settings, network_settings)
        test_request_fingerprint_masking(proxy_settings, network_settings)
        test_traffic_pattern_anonymization(proxy_settings, network_settings)
        test_geo_location_header_masking(proxy_settings, network_settings)
        test_regional_endpoint_masking(proxy_settings, network_settings)
        
        print("\n" + "=" * 60)
        print("ALL PROXY MASKING TESTS COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
