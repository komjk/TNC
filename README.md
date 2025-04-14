# Test Network Connection(s) (TNC)

A powerful, cross-platform network testing and diagnostics tool written in Python that works without external dependencies. TNC provides comprehensive network connectivity testing, SSL/TLS inspection, and continuous monitoring capabilities using only the Python standard library.

## Features

- **Multi-protocol Testing:** TCP, UDP, HTTP(S), and ICMP (ping)
- **Detailed Connection Information:** Latency, endpoints, response codes
- **SSL/TLS Certificate Inspection:** Complete certificate analysis with cipher details
- **Continuous Monitoring:** Track connectivity with customizable intervals
- **Flexible Output Formats:** Color-coded terminal output and structured JSON
- **Cross-platform Compatibility:** Windows, macOS, Linux
- **Verbosity Controls:** Three levels of detail for troubleshooting
- **Zero Dependencies:** Uses only the Python standard library
- **File Output:** Save test results to file with proper formatting
- **Comprehensive Error Handling:** Detailed error reporting for network issues

## Requirements

- Python 3.6 or higher
- No external packages required

## Installation

1. Download the `tnc.py` file
2. Make it executable (Unix-like systems):
   ```bash
   chmod +x tnc.py
   ```
3. (Optional) Move it to your PATH for global access:
   ```bash
   sudo cp tnc.py /usr/local/bin/tnc
   ```

## Quick Start

```bash
# Basic TCP connection test
./tnc.py google.com

# HTTPS test
./tnc.py google.com --protocol https

# Ping test
sudo ./tnc.py 8.8.8.8 --protocol icmp

# Monitor a service every 10 seconds
./tnc.py api.example.com -p 443 --continuous --interval 10
```

## Command Options

### Basic Options

| Option | Description |
|--------|-------------|
| `<target>` | Target host, IP address, or URL (required) |
| `-p, --port PORT` | Target port number |
| `-v` | Increase verbosity (use -v, -vv, or -vvv) |
| `--protocol PROTO` | Protocol to test: tcp, http, https, udp, icmp (default: tcp) |
| `--timeout SEC` | Connection timeout in seconds (default: 10.0) |
| `-j, --json` | Output results in JSON format |
| `--output-file FILE` | Write results to specified file |

### Advanced Options

| Option | Description |
|--------|-------------|
| `--continuous` | Enable continuous monitoring |
| `--interval SEC` | Interval between checks in continuous mode (default: 5) |
| `--count NUM` | Number of checks to perform before exiting |
| `--method METHOD` | HTTP method: GET, HEAD, POST, PUT, DELETE (default: GET) |
| `--headers JSON` | Custom HTTP headers in JSON format |
| `--no-verify` | Disable SSL certificate verification |
| `-L, --follow-redirects` | Follow HTTP redirects |

## Detailed Examples

### Basic TCP Connection Test
```bash
./tnc.py github.com -p 22
```
Tests TCP connectivity to GitHub's SSH port.

### HTTPS with SSL Certificate Inspection
```bash
./tnc.py google.com --protocol https -vv
```
Performs HTTPS test with detailed SSL certificate information.

### Continuous Monitoring with Custom Interval
```bash
./tnc.py api.example.com --continuous --interval 30 --count 10
```
Monitors a service every 30 seconds for 10 iterations.

### HTTP Test with Custom Headers and Method
```bash
./tnc.py api.github.com --protocol https --method GET --headers '{"Authorization": "token YOUR_TOKEN", "User-Agent": "TNC-Tester/1.0"}'
```
Makes HTTP request with custom headers and authentication.

### Testing Services Behind Redirects
```bash
./tnc.py bit.ly/examplelink --protocol https -L
```
Tests an HTTPS endpoint while following redirects.

### UDP Port Testing
```bash
./tnc.py dns.google -p 53 --protocol udp
```
Tests UDP connectivity to a DNS server.

### Saving Results to File
```bash
./tnc.py cloudflare.com --protocol https --output-file results.txt
```
Saves test results to a text file.

## Verbosity Levels

TNC provides three verbosity levels to control the amount of output:

1. **Basic** (`-v`, default)
   - Connection status (success/failure)
   - Response codes and latency
   - Basic error messages

2. **Detailed** (`-vv`)
   - All basic information
   - Full headers for HTTP/HTTPS
   - Local and remote endpoints
   - SSL certificate details

3. **Debug** (`-vvv`)
   - All detailed information
   - Complete SSL/TLS information
   - Cipher details and protocol versions
   - Internal operations logging

## Cross-Platform Considerations

- **Windows:** Full support including UDP and TCP tests
- **macOS/Linux:** ICMP tests require root privileges
- **All Platforms:** Color output supported in most terminals

## Troubleshooting

### Common Issues

- **"SSL Certificate Verification Failed"**  
  Use `--no-verify` to bypass certificate validation or check the certificate's validity.

- **"ICMP testing requires root privileges"**  
  Run with administrator/root privileges for ICMP tests.

- **"Connection timed out"**  
  Increase the timeout with `--timeout` or check firewall settings.

- **UDP showing "filtered" status**  
  Many firewalls block UDP responses; this is normal and indicates the port is likely filtered.

### Performance Tips

- For regular monitoring, use `--count` to limit test runs
- Reduce verbosity in automated scripts to minimize output
- JSON output (`-j`) is ideal for parsing in other tools

## License

This tool is provided under the MIT License.

## Author

Jeffrey Kroll 