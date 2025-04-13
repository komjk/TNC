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
from urllib.parse import urlparse
from typing import Optional, Dict, Any

# ANSI color codes (no external colorama dependency)
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'

class NetworkTester:
    VERBOSITY_LEVELS = {
        1: "Basic connection info and status",
        2: "Detailed connection info and timing",
        3: "Maximum debug output with headers and certificates"
    }

    def __init__(self, verbosity: int = 1, verify_ssl: bool = True, timeout: float = 10.0):
        self.verbosity = min(verbosity, 3)
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.results: Dict[str, Any] = {}

    def print_verbose(self, level: int, message: str, color: str = Colors.WHITE) -> None:
        """Print message based on verbosity level"""
        if self.verbosity >= level:
            print(f"{color}{message}{Colors.RESET}")

    def resolve_dns(self, hostname: str) -> Dict[str, Any]:
        """Perform DNS resolution using standard socket library"""
        dns_results = {}
        try:
            self.print_verbose(1, f"\n[+] DNS Resolution for {hostname}", Colors.CYAN)
            
            # Get A records (IPv4)
            try:
                ipv4_addrs = []
                addrinfo = socket.getaddrinfo(hostname, None, socket.AF_INET)
                for addr in addrinfo:
                    if addr[4][0] not in ipv4_addrs:
                        ipv4_addrs.append(addr[4][0])
                dns_results['A'] = ipv4_addrs
                self.print_verbose(1, f"IPv4 Addresses: {', '.join(dns_results['A'])}", Colors.GREEN)
            except socket.gaierror:
                dns_results['A'] = []
                self.print_verbose(1, "No IPv4 addresses found", Colors.YELLOW)

            # Get AAAA records (IPv6) if verbosity > 1
            if self.verbosity > 1:
                try:
                    ipv6_addrs = []
                    addrinfo = socket.getaddrinfo(hostname, None, socket.AF_INET6)
                    for addr in addrinfo:
                        if addr[4][0] not in ipv6_addrs:
                            ipv6_addrs.append(addr[4][0])
                    dns_results['AAAA'] = ipv6_addrs
                    self.print_verbose(2, f"IPv6 Addresses: {', '.join(dns_results['AAAA'])}", Colors.GREEN)
                except socket.gaierror:
                    dns_results['AAAA'] = []
                    self.print_verbose(2, "No IPv6 addresses found", Colors.YELLOW)

        except socket.gaierror as e:
            dns_results['error'] = f"DNS resolution failed: {str(e)}"
            self.print_verbose(1, dns_results['error'], Colors.RED)
        
        return dns_results

    def test_tcp_connection(self, host: str, port: int) -> Dict[str, Any]:
        """Test TCP connection to host:port"""
        result = {}
        start_time = time.time()
        
        try:
            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                end_time = time.time()
                latency = (end_time - start_time) * 1000
                
                result['success'] = True
                result['latency'] = latency
                result['local_endpoint'] = sock.getsockname()
                result['remote_endpoint'] = sock.getpeername()
                
                self.print_verbose(1, f"\n[+] TCP Connection successful to {host}:{port}", Colors.GREEN)
                if result['success']:
                    self.print_verbose(1, f"Latency: {latency:.2f}ms", Colors.GREEN)
                self.print_verbose(2, f"Local endpoint: {result['local_endpoint']}", Colors.CYAN)
                self.print_verbose(2, f"Remote endpoint: {result['remote_endpoint']}", Colors.CYAN)
                
                if self.verbosity >= 3:
                    # Get socket options at highest verbosity
                    try:
                        result['socket_options'] = {
                            'TCP_NODELAY': sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY),
                            'SO_KEEPALIVE': sock.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE)
                        }
                        self.print_verbose(3, "\nSocket Options:", Colors.CYAN)
                        for opt, val in result['socket_options'].items():
                            self.print_verbose(3, f"{opt}: {val}", Colors.WHITE)
                    except Exception as e:
                        self.print_verbose(3, f"Could not get socket options: {str(e)}", Colors.YELLOW)
                
        except socket.timeout:
            # Handle timeout specifically
            result['success'] = False
            result['error'] = "Connection timed out"
            self.print_verbose(1, f"Connection timed out after {self.timeout}s", Colors.RED)
        except socket.gaierror as e:
            # Handle DNS resolution errors
            result['success'] = False
            result['error'] = f"DNS resolution failed: {str(e)}"
            self.print_verbose(1, f"DNS resolution failed: {str(e)}", Colors.RED)
        except ConnectionRefusedError:
            # Handle connection refused
            result['success'] = False
            result['error'] = "Connection refused"
            self.print_verbose(1, "Connection refused", Colors.RED)
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            self.print_verbose(1, f"Connection failed: {str(e)}", Colors.RED)
            
        return result

    def test_http(self, url: str, method: str = 'GET', headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Perform HTTP(S) testing using http.client"""
        result = {}
        parsed_url = urlparse(url)
        port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
        
        try:
            self.print_verbose(1, f"\n[+] HTTP(S) Testing for {url}", Colors.CYAN)
            self.print_verbose(2, f"Method: {method}", Colors.CYAN)
            
            start_time = time.time()
            
            # Set default headers
            custom_headers = {'User-Agent': 'tnc/1.0'}
            if headers:
                custom_headers.update(headers)
                
            self.print_verbose(3, "Request Headers:", Colors.CYAN)
            for header, value in custom_headers.items():
                self.print_verbose(3, f"{header}: {value}", Colors.WHITE)
            
            if parsed_url.scheme == 'https':
                context = ssl.create_default_context()
                if not self.verify_ssl:
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                conn = http.client.HTTPSConnection(
                    parsed_url.hostname,
                    port,
                    context=context,
                    timeout=self.timeout
                )
            else:
                conn = http.client.HTTPConnection(
                    parsed_url.hostname,
                    port,
                    timeout=self.timeout
                )

            try:
                # Follow redirects manually (max 10 redirects)
                redirect_count = 0
                current_url = url
                redirect_history = []

                while redirect_count < 10:
                    parsed = urlparse(current_url)
                    path = parsed.path or '/'
                    if parsed.query:
                        path += '?' + parsed.query

                    conn.request(method, path, headers=custom_headers)
                    response = conn.getresponse()
                    
                    if response.status in (301, 302, 303, 307, 308):
                        redirect_history.append({
                            'status': response.status,
                            'url': current_url,
                            'location': response.getheader('Location')
                        })
                        current_url = response.getheader('Location')
                        response.read()  # Clear the response
                        redirect_count += 1
                        
                        # Handle relative redirects
                        if not current_url.startswith(('http://', 'https://')):
                            current_url = f"{parsed_url.scheme}://{parsed_url.netloc}{current_url}"
                        
                        # Need to create new connection for redirects
                        conn.close()
                        parsed_redirect = urlparse(current_url)
                        if parsed_redirect.scheme == 'https':
                            conn = http.client.HTTPSConnection(
                                parsed_redirect.hostname,
                                parsed_redirect.port or 443,
                                context=context if parsed_url.scheme == 'https' else ssl.create_default_context(),
                                timeout=self.timeout
                            )
                        else:
                            conn = http.client.HTTPConnection(
                                parsed_redirect.hostname,
                                parsed_redirect.port or 80,
                                timeout=self.timeout
                            )
                    else:
                        break
                
                end_time = time.time()
                
                # Basic response info (Level 1)
                result['status_code'] = response.status
                result['elapsed'] = (end_time - start_time) * 1000
                result['final_url'] = current_url
                
                self.print_verbose(1, f"Status Code: {response.status}", 
                                Colors.GREEN if 200 <= response.status < 400 else Colors.RED)
                self.print_verbose(1, f"Response time: {result['elapsed']:.2f}ms", Colors.GREEN)
                
                # Show redirect chain
                if redirect_history:
                    self.print_verbose(1, "\nRedirect Chain:", Colors.CYAN)
                    for redirect in redirect_history:
                        self.print_verbose(1, 
                            f"{redirect['status']} -> {redirect['location']}", 
                            Colors.WHITE)
                    self.print_verbose(1, f"Final URL: {current_url}", Colors.GREEN)
                
                # Headers (Level 2)
                if self.verbosity >= 2:
                    result['headers'] = dict(response.getheaders())
                    self.print_verbose(2, "\nResponse Headers:", Colors.CYAN)
                    for header, value in response.getheaders():
                        self.print_verbose(2, f"{header}: {value}", Colors.WHITE)
                
                # SSL/TLS info (Level 3)
                if self.verbosity >= 3 and isinstance(conn, http.client.HTTPSConnection):
                    try:
                        ssl_socket = conn.sock
                        cert = ssl_socket.getpeercert()
                        result['ssl'] = {
                            'version': ssl_socket.version(),
                            'cipher': ssl_socket.cipher(),
                            'cert_expires': cert.get('notAfter', 'N/A'),
                            'issuer': dict(x[0] for x in cert.get('issuer', [])),
                            'subject': dict(x[0] for x in cert.get('subject', []))
                        }
                        self.print_verbose(3, "\nSSL/TLS Information:", Colors.CYAN)
                        self.print_verbose(3, f"SSL Version: {result['ssl']['version']}", Colors.WHITE)
                        self.print_verbose(3, f"Cipher: {result['ssl']['cipher']}", Colors.WHITE)
                        self.print_verbose(3, f"Certificate Expires: {result['ssl']['cert_expires']}", Colors.WHITE)
                        
                    except Exception as e:
                        self.print_verbose(3, f"SSL information retrieval failed: {str(e)}", Colors.YELLOW)
                
            finally:
                conn.close()
                
        except socket.timeout:
            result['error'] = "Connection timed out"
            self.print_verbose(1, f"Connection timed out after {self.timeout}s", Colors.RED)
        except ssl.SSLError as e:
            result['error'] = f"SSL Error: {str(e)}"
            self.print_verbose(1, f"SSL Error: {str(e)}", Colors.RED)
            self.print_verbose(1, "Try using --no-verify to ignore certificate validation", Colors.YELLOW)
        except http.client.HTTPException as e:
            result['error'] = f"HTTP Error: {str(e)}"
            self.print_verbose(1, f"HTTP Error: {str(e)}", Colors.RED)
        except Exception as e:
            result['error'] = str(e)
            self.print_verbose(1, f"HTTP request failed: {str(e)}", Colors.RED)
            
        return result

    def test_icmp(self, hostname: str) -> Dict[str, Any]:
        """Test ICMP (Ping) connection to host"""
        result = {'success': False}
        
        try:
            # Use platform-agnostic approach
            ping_param = '-n' if sys.platform.lower() == 'windows' else '-c'
            command = ['ping', ping_param, '1', hostname]
            
            # Execute ping command
            process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if process.returncode == 0:
                result['success'] = True
                result['status'] = "Host is reachable"
                # Extract ping time if needed
                if 'time=' in process.stdout:
                    try:
                        time_str = process.stdout.split('time=')[1].split(' ')[0]
                        result['latency'] = float(time_str)
                    except (IndexError, ValueError):
                        pass
            else:
                result['status'] = "Host is not reachable"
                result['error'] = process.stderr
                
            self.print_verbose(1, f"\n[+] ICMP Test Results for {hostname}", Colors.CYAN)
            self.print_verbose(1, f"Status: {result['status']}", 
                            Colors.GREEN if result['success'] else Colors.RED)
            
            if 'latency' in result:
                self.print_verbose(1, f"Latency (ms): {result['latency']:.2f}", Colors.GREEN)
            
        except Exception as e:
            result['error'] = str(e)
            result['status'] = f"Error: {str(e)}"
            self.print_verbose(1, f"ICMP test failed: {str(e)}", Colors.RED)
            
        return result

    def test_udp(self, host: str, port: int) -> Dict[str, Any]:
        """Test UDP connection to host:port"""
        result = {'success': False}
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)  # Set timeout to avoid hanging
            
            self.print_verbose(1, f"\n[+] UDP Testing for {host}:{port}", Colors.CYAN)
            
            start_time = time.time()
            # Send a small payload
            sock.sendto(b'tnc_udp_probe', (host, port))
            
            try:
                # Try to receive a response
                data, server = sock.recvfrom(1024)
                end_time = time.time()
                latency = (end_time - start_time) * 1000
                
                result['success'] = True
                result['latency'] = latency
                result['response'] = data.decode('utf-8', errors='ignore') if data else None
                result['status'] = "Response received"
                
                self.print_verbose(1, f"Status: {result['status']}", Colors.GREEN)
                if result['success']:
                    self.print_verbose(1, f"Latency: {latency:.2f}ms", Colors.GREEN)
                
            except socket.timeout:
                # For UDP, a timeout doesn't necessarily mean failure - the packet might have been received
                result['status'] = "No response (server might not send responses)"
                self.print_verbose(1, f"Status: {result['status']}", Colors.YELLOW)
                
        except Exception as e:
            result['error'] = str(e)
            result['status'] = f"Error: {str(e)}"
            self.print_verbose(1, f"UDP test failed: {str(e)}", Colors.RED)
        
        finally:
            if 'sock' in locals():
                sock.close()
                
        return result

def print_aligned(key: str, value: str, color: str = Colors.WHITE) -> None:
    """Print key-value pairs aligned for better readability."""
    print(f"{color}{key:<30}: {value}{Colors.RESET}")

def write_output(results, args):
    """Write results to file if specified"""
    if args.output_file:
        try:
            with open(args.output_file, 'w') as f:
                # Write the header
                f.write(f"{Colors.CYAN}{'='*50}\n")
                f.write(f"{' '*10}Network Connection Tester (TNC) v1.0\n")
                f.write(f"{' '*5}Author: Jeffrey Kroll\n")
                f.write(f"{' '*5}Description: Comprehensive network testing tool\n")
                f.write(f"{'='*50}{Colors.RESET}\n\n")

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
                        f.write("HTTP Test Results:\n")
                        f.write(f"Final URL                     : {http_result.get('final_url', 'N/A')}\n")
                        f.write(f"Status Code                   : {http_result['status_code']}\n")
                        f.write(f"Response Time (ms)            : {http_result['elapsed']:.2f}\n")

                elif args.protocol == 'icmp' and 'icmp' in results:
                    icmp_result = results['icmp']
                    f.write(f"[+] ICMP Test Results for {args.target}\n")
                    f.write(f"Status: {icmp_result['status']}\n")
                    f.write("ICMP Test Results:\n")
                    f.write(f"Ping Status                   : {icmp_result['status']}\n")
                    if 'latency' in icmp_result:
                        f.write(f"Latency (ms)                  : {icmp_result['latency']}\n")

                elif args.protocol == 'udp' and 'udp' in results:
                    udp_result = results['udp']
                    f.write(f"[+] UDP Testing for {args.target}:{args.port}\n")
                    f.write(f"Status: {udp_result['status']}\n")
                    f.write("UDP Test Results:\n")
                    f.write(f"UDP Status                    : {udp_result['status']}\n")
                    if 'latency' in udp_result:
                        f.write(f"Latency (ms)                  : {udp_result['latency']:.2f}\n")

        except Exception as e:
            print(f"{Colors.RED}Error writing to file: {str(e)}{Colors.RESET}")

def main():
    # Display execution header
    print(f"{Colors.CYAN}{'='*50}")
    print(f"{' '*5}Network Connection Tester (TNC) v1.0")
    print(f"{'='*50}{Colors.RESET}\n")
    
    parser = argparse.ArgumentParser(
        description='Network Connection Tester (v1.0)',
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
                        help='Interval in seconds for continuous checks (default: 5 seconds)')
    parser.add_argument('--continuous', action='store_true',
                        help='Enable continuous monitoring (default: disabled)')
    parser.add_argument('--timeout', type=float, default=10.0,
                        help='Connection timeout in seconds (default: 10.0)')
    parser.add_argument('--method', choices=['GET', 'HEAD', 'POST', 'PUT', 'DELETE'], 
                        default='GET', help='HTTP method to use (default: GET)')
    parser.add_argument('--headers', type=str, help='Custom HTTP headers in JSON format')
    parser.add_argument('--output-file', type=str, help='Write results to this file')
    parser.add_argument('--count', type=int, help='Number of checks to perform before exiting')
    
    args = parser.parse_args()
    
    # Cap verbosity at 3
    verbosity = min(args.verbose, 3)
    
    # Parse custom headers if provided
    custom_headers = None
    if args.headers:
        try:
            custom_headers = json.loads(args.headers)
        except json.JSONDecodeError:
            print(f"{Colors.YELLOW}Invalid JSON for headers, using defaults{Colors.RESET}")
    
    # Initialize tester
    tester = NetworkTester(verbosity=verbosity, verify_ssl=not args.no_verify, timeout=args.timeout)
    
    try:
        url = urlparse(args.target)
        if not url.scheme:
            url = urlparse(f'http://{args.target}')
        
        hostname = url.hostname or args.target
        port = args.port or url.port or (443 if url.scheme == 'https' else 80)

        # Check if continuous monitoring is enabled
        if args.continuous:
            # Continuous monitoring loop
            count = 0
            while True:
                # Clear screen for better readability in continuous mode
                if os.name != 'nt':
                    os.system('clear')
                else:
                    os.system('cls')
                
                # Show timestamp
                current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print(f"{Colors.CYAN}=== Test run at {current_time} ==={Colors.RESET}\n")
                
                results = {}
                if args.protocol == 'icmp':
                    results['icmp'] = tester.test_icmp(hostname)
                elif args.protocol in ['http', 'https']:
                    results['http'] = tester.test_http(url.geturl(), method=args.method, headers=custom_headers)
                elif args.protocol == 'udp':
                    results['udp'] = tester.test_udp(hostname, port)
                elif args.protocol == 'tcp':
                    results['tcp'] = tester.test_tcp_connection(hostname, port)

                # Output results
                if args.json:
                    print(json.dumps(results, indent=2))
                else:
                    # Print results based on the protocol tested
                    if args.protocol == 'icmp':
                        print(f"{Colors.CYAN}ICMP Test Results:{Colors.RESET}")
                        print_aligned("Ping Status", results['icmp']['status'], Colors.GREEN if results['icmp']['success'] else Colors.RED)
                        if 'latency' in results['icmp']:
                            print_aligned("Latency (ms)", str(results['icmp']['latency']), Colors.GREEN)
                    elif args.protocol in ['http', 'https']:
                        print(f"{Colors.CYAN}HTTP Test Results:{Colors.RESET}")
                        http_result = results.get('http', {})
                        print_aligned("Final URL", http_result.get('final_url', 'N/A'), Colors.CYAN)
                        print_aligned("Status Code", str(http_result.get('status_code', 'N/A')), Colors.GREEN if http_result.get('status_code', 0) < 400 else Colors.RED)
                        print_aligned("Response Time (ms)", f"{http_result.get('elapsed', 0):.2f}", Colors.GREEN)
                    elif args.protocol == 'udp':
                        print(f"{Colors.CYAN}UDP Test Results:{Colors.RESET}")
                        print_aligned("UDP Status", results['udp']['status'], Colors.GREEN if results['udp']['success'] else Colors.RED)
                        if 'latency' in results['udp']:
                            print_aligned("Latency (ms)", f"{results['udp']['latency']:.2f}", Colors.GREEN)
                    elif args.protocol == 'tcp':
                        print(f"{Colors.CYAN}TCP Test Results:{Colors.RESET}")
                        tcp_result = results['tcp']
                        if tcp_result['success']:
                            print_aligned("Connection Status", "Success", Colors.GREEN)
                            print_aligned("Latency (ms)", f"{tcp_result['latency']:.2f}", Colors.GREEN)
                            print_aligned("Local Endpoint", f"{tcp_result['local_endpoint']}", Colors.CYAN)
                            print_aligned("Remote Endpoint", f"{tcp_result['remote_endpoint']}", Colors.CYAN)
                        else:
                            print_aligned("Connection Status", "Failed", Colors.RED)
                            print_aligned("Error", tcp_result.get('error', 'Unknown error'), Colors.RED)

                # Write to output file if specified
                write_output(results, args)
                
                # Increment counter and check if we've reached the limit
                count += 1
                if args.count and count >= args.count:
                    print(f"\n{Colors.CYAN}Completed {count} checks as requested.{Colors.RESET}")
                    break
                
                # Show next check time
                next_check = time.strftime("%H:%M:%S", time.localtime(time.time() + args.interval))
                print(f"\n{Colors.YELLOW}Next check at {next_check} (Ctrl+C to exit){Colors.RESET}")
                time.sleep(args.interval)  # Wait for the specified interval before the next check
        else:
            # Perform a single check based on the specified protocol
            results = {}
            if args.protocol == 'icmp':
                results['icmp'] = tester.test_icmp(hostname)
            elif args.protocol in ['http', 'https']:
                results['http'] = tester.test_http(url.geturl(), method=args.method, headers=custom_headers)
            elif args.protocol == 'udp':
                results['udp'] = tester.test_udp(hostname, port)
            elif args.protocol == 'tcp':
                results['tcp'] = tester.test_tcp_connection(hostname, port)

            # Output results for a single check
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                # Print results based on the protocol tested
                if args.protocol == 'icmp':
                    print(f"{Colors.CYAN}ICMP Test Results:{Colors.RESET}")
                    print_aligned("Ping Status", results['icmp']['status'], Colors.GREEN if results['icmp']['success'] else Colors.RED)
                    if 'latency' in results['icmp']:
                        print_aligned("Latency (ms)", str(results['icmp']['latency']), Colors.GREEN)
                elif args.protocol in ['http', 'https']:
                    print(f"{Colors.CYAN}HTTP Test Results:{Colors.RESET}")
                    http_result = results.get('http', {})
                    print_aligned("Final URL", http_result.get('final_url', 'N/A'), Colors.CYAN)
                    print_aligned("Status Code", str(http_result.get('status_code', 'N/A')), Colors.GREEN if http_result.get('status_code', 0) < 400 else Colors.RED)
                    print_aligned("Response Time (ms)", f"{http_result.get('elapsed', 0):.2f}", Colors.GREEN)
                elif args.protocol == 'udp':
                    print(f"{Colors.CYAN}UDP Test Results:{Colors.RESET}")
                    print_aligned("UDP Status", results['udp']['status'], Colors.GREEN if results['udp']['success'] else Colors.RED)
                    if 'latency' in results['udp']:
                        print_aligned("Latency (ms)", f"{results['udp']['latency']:.2f}", Colors.GREEN)
                elif args.protocol == 'tcp':
                    print(f"{Colors.CYAN}TCP Test Results:{Colors.RESET}")
                    tcp_result = results['tcp']
                    if tcp_result['success']:
                        print_aligned("Connection Status", "Success", Colors.GREEN)
                        print_aligned("Latency (ms)", f"{tcp_result['latency']:.2f}", Colors.GREEN)
                        print_aligned("Local Endpoint", f"{tcp_result['local_endpoint']}", Colors.CYAN)
                        print_aligned("Remote Endpoint", f"{tcp_result['remote_endpoint']}", Colors.CYAN)
                    else:
                        print_aligned("Connection Status", "Failed", Colors.RED)
                        print_aligned("Error", tcp_result.get('error', 'Unknown error'), Colors.RED)
            
            # Write to output file if specified
            write_output(results, args)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Monitoring stopped by user.{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.RED}Error: {str(e)}{Colors.RESET}")
        sys.exit(1)

if __name__ == '__main__':
    main()