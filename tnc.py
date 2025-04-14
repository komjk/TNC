#!/usr/bin/env python3

import argparse
import socket
import ssl
import sys
import time
import json
import http.client
import os
import subprocess
import re
import logging
import platform
import dataclasses
from urllib.parse import urlparse
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from enum import Enum

# Platform detection
SYSTEM = platform.system()
IS_WINDOWS = SYSTEM == 'Windows'
IS_MACOS = SYSTEM == 'Darwin'
IS_LINUX = SYSTEM == 'Linux'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ANSI color codes (no external colorama dependency)
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'

def is_valid_url(url: str) -> bool:
    """Validate the URL format."""
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    # Check if the URL matches the regex
    if re.match(regex, url):
        return True
    
    # Additional check for just hostname without scheme
    if re.match(r'^[a-zA-Z0-9.-]+$', url):
        return True
    
    return False

def log_error(message: str):
    logging.error(message)

def log_success(message: str):
    logging.info(message)

class Protocol(Enum):
    TCP = "tcp"
    UDP = "udp"
    HTTP = "http"
    HTTPS = "https"
    ICMP = "icmp"

@dataclass
class TestConfig:
    verbosity: int = 1
    verify_ssl: bool = True
    timeout: float = 10.0
    continuous: bool = False
    interval: int = 5
    json_output: bool = False

@dataclass
class TestResult:
    success: bool
    protocol: Protocol
    latency: Optional[float] = None
    error: Optional[str] = None
    status: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class OutputFormatter:
    def __init__(self, config: TestConfig):
        self.config = config
        
    def format_result(self, result: TestResult) -> str:
        if self.config.json_output:
            return self._format_json(result)
        return self._format_human_readable(result)
    
    def _format_json(self, result: TestResult) -> str:
        return json.dumps(dataclasses.asdict(result), indent=2)
    
    def _format_human_readable(self, result: TestResult) -> str:
        # Format human readable output with colors
        pass

class BaseNetworkTester:
    def __init__(self, config: TestConfig):
        self.config = config
        self.formatter = OutputFormatter(config)

    def validate_target(self, target: str) -> bool:
        return is_valid_url(target)

class TCPTester(BaseNetworkTester):
    def test(self, host: str, port: int) -> TestResult:
        if not self.validate_target(host):
            return TestResult(
                success=False,
                protocol=Protocol.TCP,
                error="Invalid hostname"
            )
        
        try:
            with socket.create_connection((host, port), timeout=self.config.timeout) as sock:
                # TCP test implementation
                return TestResult(
                    success=True,
                    protocol=Protocol.TCP,
                    latency=latency,
                    details={
                        'local_endpoint': sock.getsockname(),
                        'remote_endpoint': sock.getpeername()
                    }
                )
        except Exception as e:
            return TestResult(
                success=False,
                protocol=Protocol.TCP,
                error=str(e)
            )

class NetworkTestManager:
    def __init__(self, config: TestConfig):
        self.config = config
        self.testers = {
            Protocol.TCP: TCPTester(config),
            Protocol.HTTP: HTTPTester(config),
            # ... other testers
        }
    
    def run_test(self, protocol: Protocol, target: str, port: Optional[int] = None) -> TestResult:
        tester = self.testers[protocol]
        result = tester.test(target, port)
        
        formatter = OutputFormatter(self.config)
        print(formatter.format_result(result))
        
        return result

def print_aligned(key: str, value: str, color: str = Colors.WHITE) -> None:
    """Print key-value pairs aligned for better readability."""
    print(f"{color}{key:<30}: {value}{Colors.RESET}")

def write_output(results, args):
    """Write results to file if specified"""
    if args.output_file and args.output_file.strip():  # Check if output file is specified and not empty
        try:
            # Normalize path and ensure directory exists
            output_path = os.path.normpath(args.output_file)
            output_dir = os.path.dirname(output_path)
            
            # Create directory if it doesn't exist and path is not empty
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Use platform-appropriate line endings
            with open(output_path, 'w', newline='\n') as f:
                # Write the header
                f.write(f"{'='*50}\n")
                f.write(f"{' '*10}Network Connection Tester (TNC) v1.0\n")
                f.write(f"{' '*5}Test Results - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*50}\n\n")

                # Write results based on protocol
                if args.protocol == 'tcp' and 'tcp' in results:
                    tcp_result = results['tcp']
                    if tcp_result['success']:
                        f.write(f"[+] TCP Connection successful to {args.target}:{args.port or 80}\n")
                        f.write(f"Latency: {tcp_result['latency']:.2f}ms\n")
                        f.write("TCP Test Results:\n")
                        f.write("Connection Status             : Success\n")
                        f.write(f"Latency (ms)                  : {tcp_result['latency']:.2f}\n")
                        f.write(f"Local Endpoint                : {tcp_result['local_endpoint']}\n")
                        f.write(f"Remote Endpoint               : {tcp_result['remote_endpoint']}\n")
                    else:
                        f.write(f"Connection failed: {tcp_result.get('error', 'Unknown error')}\n")

                elif args.protocol in ['http', 'https'] and 'http' in results:
                    http_result = results['http']
                    f.write(f"[+] HTTP(S) Testing for {args.target}\n")
                    f.write(f"Method: {args.method}\n")
                    if 'status_code' in http_result:
                        f.write(f"Status Code: {http_result['status_code']}\n")
                        f.write(f"Response time: {http_result['elapsed']:.2f}ms\n\n")
                        if args.verbose >= 2:
                            f.write("Response Headers:\n")
                            for header, value in http_result.get('headers', {}).items():
                                f.write(f"{header}: {value}\n")
                            f.write("\n")
                            if 'ssl_info' in http_result:
                                f.write("SSL Certificate Information:\n")
                                ssl_info = http_result['ssl_info']
                                f.write(f"Subject         : {ssl_info.get('subject', {}).get('commonName', 'N/A')}\n")
                                f.write(f"Issuer          : {ssl_info.get('issuer', {}).get('commonName', 'N/A')}\n")
                                f.write(f"Valid From      : {ssl_info.get('notBefore', 'N/A')}\n")
                                f.write(f"Valid Until     : {ssl_info.get('notAfter', 'N/A')}\n")
                                f.write(f"Serial Number   : {ssl_info.get('serialNumber', 'N/A')}\n")
                                if ssl_info.get('subjectAltName'):
                                    f.write("Alternative Names:\n")
                                    for name in ssl_info['subjectAltName']:
                                        f.write(f"                  {name}\n")
                                f.write("\n")
                        f.write("HTTP Test Results:\n")
                        f.write(f"Final URL                     : {http_result.get('final_url', 'N/A')}\n")
                        f.write(f"Status Code                   : {http_result['status_code']}\n")
                        f.write(f"Response Time (ms)            : {http_result['elapsed']:.2f}\n")

                elif args.protocol == 'icmp' and 'icmp' in results:
                    icmp_result = results['icmp']
                    f.write(f"[+] ICMP Test Results for {args.target}\n")
                    f.write(f"Status: {icmp_result.get('status', 'unknown')}\n")
                    f.write("ICMP Test Results:\n")
                    f.write(f"Ping Status                   : {icmp_result.get('status', 'unknown')}\n")
                    if icmp_result.get('latency') is not None:
                        f.write(f"Latency (ms)                  : {icmp_result['latency']}\n")

                elif args.protocol == 'udp' and 'udp' in results:
                    udp_result = results['udp']
                    f.write(f"[+] UDP Testing for {args.target}:{args.port}\n")
                    f.write(f"Status: {udp_result.get('status', 'unknown')}\n")
                    f.write("UDP Test Results:\n")
                    f.write(f"UDP Status                    : {udp_result.get('status', 'unknown')}\n")
                    if udp_result.get('latency') is not None:
                        f.write(f"Latency (ms)                  : {udp_result['latency']:.2f}\n")
                    if udp_result.get('error'):
                        f.write(f"Error                         : {udp_result['error']}\n")

                f.write(f"\nTest completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        except Exception as e:
            print(f"{Colors.RED}Error writing to file '{args.output_file}': {str(e)}{Colors.RESET}")
    elif args.output_file == '':
        print(f"{Colors.YELLOW}Warning: Output file path is empty, skipping file output{Colors.RESET}")

class NetworkTester:
    def __init__(self, verbosity=1, verify_ssl=True, timeout=10.0):
        self.verbosity = verbosity
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self._setup_platform_specific()
        self.logger = logging.getLogger(__name__)
        if verbosity >= 2:
            logging.getLogger().setLevel(logging.DEBUG)

    def _setup_platform_specific(self):
        """Setup platform-specific configurations"""
        if IS_WINDOWS:
            self.ping_count_flag = '-n'
            self.ping_timeout_flag = '-w'
            self.ping_time_pattern = r'time[=<](\d+)ms'
        else:
            self.ping_count_flag = '-c'
            self.ping_timeout_flag = '-W'
            self.ping_time_pattern = r'time=(\d+\.\d+) ms'

    def get_ssl_cert_info(self, hostname: str, port: int = 443) -> dict:
        """Get SSL certificate information for a host"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    if self.verbosity >= 2:
                        self.logger.debug(f"Raw certificate data: {cert}")
                    
                    if not cert:
                        return {}
                    
                    cert_info = {
                        'subject': dict(x[0] for x in cert['subject']),
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'version': cert.get('version', 'unknown'),
                        'serialNumber': cert.get('serialNumber', 'unknown'),
                        'notBefore': cert.get('notBefore', 'unknown'),
                        'notAfter': cert.get('notAfter', 'unknown'),
                        'subjectAltName': [x[1] for x in cert.get('subjectAltName', [])],
                        'cipher': ssock.cipher(),
                        'protocol': ssock.version()
                    }
                    self.logger.debug(f"Certificate info gathered: {cert_info}")
                    return cert_info
        except Exception as e:
            self.logger.error(f"Error getting SSL certificate: {e}")
            return {}

    def test_tcp_connection(self, host: str, port: int) -> dict:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if IS_WINDOWS:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            else:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            
            start_time = time.time()
            sock.settimeout(self.timeout)
            sock.connect((host, port))
            latency = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            result = {
                'success': True,
                'latency': latency,
                'local_endpoint': sock.getsockname(),
                'remote_endpoint': sock.getpeername()
            }
            
            sock.close()
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def test_http(self, url: str, method='GET', headers=None) -> dict:
        try:
            parsed_url = urlparse(url)
            is_https = parsed_url.scheme == 'https'
            
            # Get SSL certificate info for HTTPS connections
            cert_info = {}
            if is_https:
                self.logger.debug(f"Getting SSL certificate information for {parsed_url.netloc}")
                cert_info = self.get_ssl_cert_info(parsed_url.netloc)
                if cert_info:
                    self.logger.debug("SSL certificate information obtained successfully")
                else:
                    self.logger.debug("No SSL certificate information available")
            
            start_time = time.time()
            
            # Create connection based on protocol
            if is_https:
                ssl_context = ssl._create_unverified_context() if not self.verify_ssl else ssl.create_default_context()
                conn = http.client.HTTPSConnection(
                    parsed_url.netloc,
                    timeout=self.timeout,
                    context=ssl_context
                )
            else:
                conn = http.client.HTTPConnection(
                    parsed_url.netloc,
                    timeout=self.timeout
                )
            
            path = parsed_url.path or '/'
            if parsed_url.query:
                path += '?' + parsed_url.query
            
            conn.request(method, path, headers=headers or {})
            response = conn.getresponse()
            elapsed = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            result = {
                'success': True,
                'status_code': response.status,
                'headers': dict(response.getheaders()),
                'elapsed': elapsed,
                'final_url': url,
                'protocol': 'https' if is_https else 'http',
                'method': method
            }

            # Add SSL certificate info
            if is_https and cert_info:
                result['ssl_info'] = cert_info
                self.logger.debug("Added SSL certificate info to result")
            
            conn.close()
            return result
            
        except ssl.SSLError as e:
            self.logger.error(f"SSL Error: {e}")
            return {
                'success': False,
                'error': f"SSL Error: {str(e)}",
                'protocol': 'https'
            }
        except Exception as e:
            self.logger.error(f"HTTP test error: {e}")
            return {
                'success': False,
                'error': str(e),
                'protocol': 'https' if is_https else 'http'
            }

    def test_icmp(self, host: str) -> dict:
        try:
            # Check for root privileges if needed
            if not IS_WINDOWS and os.geteuid() != 0:
                return {
                    'success': False,
                    'status': 'error',
                    'error': 'ICMP testing requires root privileges on this platform'
                }
            
            timeout_ms = int(self.timeout * 1000)
            ping_cmd = [
                'ping',
                self.ping_count_flag, '1',
                self.ping_timeout_flag, str(timeout_ms),
                host
            ]
            
            result = subprocess.run(ping_cmd, capture_output=True, text=True)
            success = result.returncode == 0
            
            # Parse latency from output if successful
            latency = None
            if success:
                match = re.search(self.ping_time_pattern, result.stdout)
                if match:
                    latency = float(match.group(1))
            
            return {
                'success': success,
                'status': 'alive' if success else 'unreachable',
                'latency': latency
            }
        except Exception as e:
            return {
                'success': False,
                'status': 'error',
                'error': str(e)
            }

    def test_udp(self, host: str, port: int) -> dict:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            if IS_WINDOWS:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(self.timeout)
            
            start_time = time.time()
            sock.sendto(b'', (host, port))
            
            try:
                sock.recvfrom(1024)
                latency = (time.time() - start_time) * 1000
                status = 'open'
            except socket.timeout:
                latency = None
                status = 'filtered'
            
            sock.close()
            return {
                'success': True,
                'status': status,
                'latency': latency
            }
        except Exception as e:
            return {
                'success': False,
                'status': 'error',
                'error': str(e)
            }

def print_usage():
    """Print a clean, user-friendly usage message"""
    print(f"{Colors.CYAN}{'='*50}")
    print(f"{' '*5}Test Network Connection(s) v1.0")
    print(f"{'='*50}{Colors.RESET}\n")
    print("Usage:")
    print("  ./tnc.py <target> [options]\n")
    print("Examples:")
    print("  ./tnc.py google.com                    # Basic TCP test")
    print("  ./tnc.py google.com -p 443             # Test specific port")
    print("  ./tnc.py google.com --protocol https   # HTTPS test")
    print("  ./tnc.py 8.8.8.8 --protocol icmp      # Ping test")
    print("  ./tnc.py example.com --continuous      # Continuous monitoring\n")
    print("Options:")
    print("  -p, --port PORT        Target port number")
    print("  -v                     Increase verbosity (max: -vvv)")
    print("  --protocol PROTO       Protocol to test (tcp|http|https|udp|icmp)")
    print("  --continuous           Enable continuous monitoring")
    print("  --interval SEC         Check interval for continuous mode (default: 5)")
    print("  --timeout SEC          Connection timeout (default: 10.0)")
    print("  --output-file FILE     Write results to file")
    print("  --no-verify           Disable SSL verification")
    print("  -j, --json            Output in JSON format")
    print(f"\nFor more details, use: {Colors.CYAN}./tnc.py -h{Colors.RESET}")

def main():
    if len(sys.argv) == 1:
        print_usage()
        sys.exit(0)
    
    parser = argparse.ArgumentParser(
        description='Test Network Connection(s) (v1.0)',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument('target', help='Target host or URL to test')
    parser.add_argument('-p', '--port', type=int, help='Target port number')
    parser.add_argument('-v', '--verbose', action='count', default=1,
                        help='Increase verbosity level (default: -v, max: -vvv)')
    parser.add_argument('-L', '--follow-redirects', action='store_true',
                        help='Follow redirects (similar to curl -L)')
    parser.add_argument('-j', '--json', action='store_true',
                        help='Output results in JSON format')
    parser.add_argument('--no-verify', action='store_true',
                        help='Disable SSL certificate verification')
    parser.add_argument('--protocol', choices=['icmp', 'http', 'https', 'udp', 'tcp'], 
                        default='tcp', help='Protocol to test (default: tcp)')
    parser.add_argument('--interval', type=int, default=5,
                        help='Interval in seconds for continuous checks (default: 5)')
    parser.add_argument('--continuous', action='store_true',
                        help='Enable continuous monitoring')
    parser.add_argument('--timeout', type=float, default=10.0,
                        help='Connection timeout in seconds (default: 10.0)')
    parser.add_argument('--method', choices=['GET', 'HEAD', 'POST', 'PUT', 'DELETE'], 
                        default='GET', help='HTTP method to use (default: GET)')
    parser.add_argument('--headers', type=str, help='Custom HTTP headers in JSON format')
    parser.add_argument('--output-file', type=str, help='Write results to this file')
    parser.add_argument('--count', type=int, help='Number of checks to perform before exiting')

    # Parse arguments
    try:
        args = parser.parse_args()
    except SystemExit:
        if len(sys.argv) == 2 and sys.argv[1] in ['-h', '--help']:
            parser.print_help()
        else:
            print_usage()
        sys.exit(1)

    # Configure logging based on verbosity
    if args.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose >= 2:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.debug(f"Verbosity level: {args.verbose}")
    
    # Cap verbosity at 3
    verbosity = min(args.verbose, 3)
    
    # Parse custom headers if provided
    custom_headers = None
    if args.headers:
        try:
            custom_headers = json.loads(args.headers)
        except json.JSONDecodeError:
            print(f"{Colors.YELLOW}Invalid JSON for headers, using defaults{Colors.RESET}")
    
    try:
        url = urlparse(args.target)
        if not url.scheme:
            url = urlparse(f'http://{args.target}')
        
        hostname = url.hostname or args.target
        port = args.port or url.port or (443 if url.scheme == 'https' else 80)

        # Initialize tester with proper verbosity
        tester = NetworkTester(verbosity=verbosity, verify_ssl=not args.no_verify, timeout=args.timeout)
        logger.debug(f"NetworkTester initialized with verbosity {verbosity}")
        
        # Check if continuous monitoring is enabled
        if args.continuous:
            count = 0
            while True:
                if os.name != 'nt':
                    os.system('clear')
                else:
                    os.system('cls')
                
                current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print(f"{Colors.CYAN}=== Test run at {current_time} ==={Colors.RESET}\n")
                
                results = {}
                if args.protocol == 'icmp':
                    results['icmp'] = tester.test_icmp(hostname)
                elif args.protocol in ['http', 'https']:
                    results['http'] = tester.test_http(url.geturl(), method=args.method, headers=custom_headers)
                    logger.debug(f"HTTP test results: {results['http']}")
                elif args.protocol == 'udp':
                    results['udp'] = tester.test_udp(hostname, port)
                elif args.protocol == 'tcp':
                    results['tcp'] = tester.test_tcp_connection(hostname, port)

                if args.json:
                    print(json.dumps(results, indent=2))
                else:
                    if args.protocol in ['http', 'https']:
                        http_result = results['http']
                        print(f"{Colors.CYAN}HTTP(S) Test Results:{Colors.RESET}")
                        print_aligned("Status Code", str(http_result.get('status_code', 'N/A')), 
                                   Colors.GREEN if http_result.get('status_code', 500) < 400 else Colors.RED)
                        print_aligned("Response Time", f"{http_result.get('elapsed', 0):.2f}ms", Colors.GREEN)
                        
                        # Check for SSL info
                        if 'ssl_info' in http_result:
                            logger.debug("SSL info found in results")
                            print_ssl_info(http_result['ssl_info'])
                        else:
                            logger.debug("No SSL info in results")
                            
                        if args.verbose >= 2:
                            print("\nResponse Headers:")
                            for header, value in http_result.get('headers', {}).items():
                                print_aligned(header, value, Colors.WHITE)
                    
                    elif args.protocol == 'tcp':
                        tcp_result = results['tcp']
                        if tcp_result['success']:
                            print_aligned("Connection Status", "Success", Colors.GREEN)
                            print_aligned("Latency (ms)", f"{tcp_result['latency']:.2f}", Colors.GREEN)
                            print_aligned("Local Endpoint", f"{tcp_result['local_endpoint']}", Colors.CYAN)
                            print_aligned("Remote Endpoint", f"{tcp_result['remote_endpoint']}", Colors.CYAN)
                        else:
                            print_aligned("Connection Status", "Failed", Colors.RED)
                            print_aligned("Error", tcp_result.get('error', 'Unknown error'), Colors.RED)
                    elif args.protocol == 'udp':
                        udp_result = results['udp']
                        print_aligned("UDP Status", udp_result.get('status', 'unknown'), 
                                   Colors.GREEN if udp_result.get('success', False) else Colors.YELLOW)
                        if udp_result.get('latency') is not None:
                            print_aligned("Latency (ms)", f"{udp_result['latency']:.2f}", Colors.GREEN)
                        if udp_result.get('error'):
                            print_aligned("Error", udp_result['error'], Colors.RED)
                    elif args.protocol == 'icmp':
                        icmp_result = results['icmp']
                        print_aligned("Ping Status", icmp_result.get('status', 'unknown'), 
                                   Colors.GREEN if icmp_result.get('success', False) else Colors.RED)
                        if 'latency' in icmp_result:
                            print_aligned("Latency (ms)", str(icmp_result['latency']), Colors.GREEN)

                write_output(results, args)
                
                count += 1
                if args.count and count >= args.count:
                    print(f"\n{Colors.CYAN}Completed {count} checks as requested.{Colors.RESET}")
                    break
                
                next_check = time.strftime("%H:%M:%S", time.localtime(time.time() + args.interval))
                print(f"\n{Colors.YELLOW}Next check at {next_check} (Ctrl+C to exit){Colors.RESET}")
                time.sleep(args.interval)
        else:
            results = {}
            if args.protocol == 'icmp':
                results['icmp'] = tester.test_icmp(hostname)
            elif args.protocol in ['http', 'https']:
                results['http'] = tester.test_http(url.geturl(), method=args.method, headers=custom_headers)
                logger.debug(f"HTTP test results: {results['http']}")
            elif args.protocol == 'udp':
                results['udp'] = tester.test_udp(hostname, port)
            elif args.protocol == 'tcp':
                results['tcp'] = tester.test_tcp_connection(hostname, port)

            if args.json:
                print(json.dumps(results, indent=2))
            else:
                if args.protocol in ['http', 'https']:
                    http_result = results['http']
                    print(f"{Colors.CYAN}HTTP(S) Test Results:{Colors.RESET}")
                    print_aligned("Status Code", str(http_result.get('status_code', 'N/A')), 
                               Colors.GREEN if http_result.get('status_code', 500) < 400 else Colors.RED)
                    print_aligned("Response Time", f"{http_result.get('elapsed', 0):.2f}ms", Colors.GREEN)
                    
                    # Check for SSL info
                    if 'ssl_info' in http_result:
                        logger.debug("SSL info found in results")
                        print_ssl_info(http_result['ssl_info'])
                    else:
                        logger.debug("No SSL info in results")
                        
                    if args.verbose >= 2:
                        print("\nResponse Headers:")
                        for header, value in http_result.get('headers', {}).items():
                            print_aligned(header, value, Colors.WHITE)
                
                elif args.protocol == 'tcp':
                    tcp_result = results['tcp']
                    if tcp_result['success']:
                        print_aligned("Connection Status", "Success", Colors.GREEN)
                        print_aligned("Latency (ms)", f"{tcp_result['latency']:.2f}", Colors.GREEN)
                        print_aligned("Local Endpoint", f"{tcp_result['local_endpoint']}", Colors.CYAN)
                        print_aligned("Remote Endpoint", f"{tcp_result['remote_endpoint']}", Colors.CYAN)
                    else:
                        print_aligned("Connection Status", "Failed", Colors.RED)
                        print_aligned("Error", tcp_result.get('error', 'Unknown error'), Colors.RED)
                elif args.protocol == 'udp':
                    udp_result = results['udp']
                    print_aligned("UDP Status", udp_result.get('status', 'unknown'), 
                               Colors.GREEN if udp_result.get('success', False) else Colors.YELLOW)
                    if udp_result.get('latency') is not None:
                        print_aligned("Latency (ms)", f"{udp_result['latency']:.2f}", Colors.GREEN)
                    if udp_result.get('error'):
                        print_aligned("Error", udp_result['error'], Colors.RED)
                elif args.protocol == 'icmp':
                    icmp_result = results['icmp']
                    print_aligned("Ping Status", icmp_result.get('status', 'unknown'), 
                               Colors.GREEN if icmp_result.get('success', False) else Colors.RED)
                    if 'latency' in icmp_result:
                        print_aligned("Latency (ms)", str(icmp_result['latency']), Colors.GREEN)
            
            write_output(results, args)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Monitoring stopped by user.{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.RED}Error: {str(e)}{Colors.RESET}")
        sys.exit(1)

def print_ssl_info(ssl_info: dict) -> None:
    """Print SSL certificate information in a formatted way."""
    print(f"\n{Colors.CYAN}SSL Certificate Information:{Colors.RESET}")
    
    # Basic certificate information
    if 'subject' in ssl_info:
        subject = ssl_info['subject']
        print_aligned("Subject CN", subject.get('commonName', 'N/A'), Colors.WHITE)
        if 'organizationName' in subject:
            print_aligned("Organization", subject['organizationName'], Colors.WHITE)
    
    if 'issuer' in ssl_info:
        issuer = ssl_info['issuer']
        print_aligned("Issuer CN", issuer.get('commonName', 'N/A'), Colors.WHITE)
        if 'organizationName' in issuer:
            print_aligned("Issuer Org", issuer['organizationName'], Colors.WHITE)
    
    print_aligned("Valid From", ssl_info.get('notBefore', 'N/A'), Colors.WHITE)
    print_aligned("Valid Until", ssl_info.get('notAfter', 'N/A'), Colors.WHITE)
    print_aligned("Serial Number", ssl_info.get('serialNumber', 'N/A'), Colors.WHITE)
    
    # Protocol and cipher information
    if ssl_info.get('protocol'):
        print_aligned("SSL/TLS Protocol", ssl_info['protocol'], Colors.WHITE)
    if ssl_info.get('cipher'):
        cipher_info = ssl_info['cipher']
        print_aligned("Cipher Suite", f"{cipher_info[0]} ({cipher_info[2]} bits)", Colors.WHITE)
    
    # Subject Alternative Names
    if ssl_info.get('subjectAltName'):
        print(f"\n{Colors.CYAN}Subject Alternative Names:{Colors.RESET}")
        for name in ssl_info['subjectAltName']:
            print(f"  {name}")

if __name__ == '__main__':
    main()