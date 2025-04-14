# Test Network Connection(s) (TNC)

A powerful, lightweight network testing tool written in Python. TNC provides comprehensive network testing capabilities without requiring any external dependencies.

## Features

- Multiple protocol support (TCP, UDP, HTTP, HTTPS, ICMP)
- Detailed connection information
- SSL/TLS certificate inspection with cipher details
- Continuous monitoring mode with interval control
- JSON output support
- Color-coded terminal output
- Cross-platform compatibility (Windows, macOS, Linux)
- Verbosity levels for detailed debugging
- No external dependencies required
- Clean, professional output format
- File output with proper line endings
- Comprehensive error handling

## Requirements

- Python 3.x
- No external packages required (uses only Python standard library)

## Installation

1. Download the `tnc.py` file
2. Make it executable (Unix-like systems):
   ```bash
   chmod +x tnc.py
   ```
3. (Optional) Move it to your PATH for global access

## Usage

Basic usage:
```bash
./tnc.py <target> [options]
```

### Basic Examples

```bash
# Basic TCP test
./tnc.py google.com

# Test specific port
./tnc.py google.com -p 443

# HTTPS test
./tnc.py google.com --protocol https

# Ping test
./tnc.py 8.8.8.8 --protocol icmp

# Continuous monitoring
./tnc.py example.com --continuous
```

### Basic Options

| Option | Description |
|--------|-------------|
| `target` | Target host or URL to test (required) |
| `-p, --port` | Target port number |
| `-v` | Increase verbosity level (use -v, -vv, or -vvv) |
| `--protocol` | Protocol to test (icmp, http, https, udp, tcp) |
| `--timeout` | Connection timeout in seconds (default: 10.0) |
| `-j, --json` | Output results in JSON format |
| `--output-file` | Write results to specified file |

### Advanced Options

| Option | Description |
|--------|-------------|
| `--continuous` | Enable continuous monitoring |
| `--interval` | Interval in seconds for continuous checks (default: 5) |
| `--count` | Number of checks to perform before exiting |
| `--method` | HTTP method to use (GET, HEAD, POST, PUT, DELETE) |
| `--headers` | Custom HTTP headers in JSON format |
| `--no-verify` | Disable SSL certificate verification |
| `-L, --follow-redirects` | Follow HTTP redirects |

## Advanced Examples

### HTTPS Test with SSL Information
```bash
./tnc.py google.com --protocol https -vvv
```

### Continuous Monitoring with JSON Output
```bash
./tnc.py cloudflare.com --continuous --interval 2 --count 5 --json
```

### HTTP Test with Custom Headers
```bash
./tnc.py api.github.com --protocol https --headers '{"User-Agent": "TNC-Tester/1.0"}'
```

### SSL Test with Certificate Verification Disabled
```bash
./tnc.py expired.badssl.com --protocol https --no-verify
```

## Output Examples

### Basic TCP Test
```
==================================================
     Test Network Connection(s) v1.0
==================================================

TCP Test Results:
Connection Status             : Success
Latency (ms)                 : 37.91
Local Endpoint               : ('192.168.1.100', 63722)
Remote Endpoint              : ('142.251.40.110', 80)
```

### HTTPS Test with SSL Information
```
==================================================
     Test Network Connection(s) v1.0
==================================================

HTTP(S) Test Results:
Status Code                  : 200
Response Time               : 321.17ms

SSL Certificate Information:
Subject CN                  : *.google.com
Organization               : Google LLC
Issuer CN                  : GTS CA 1C3
Issuer Org                 : Google Trust Services LLC
Valid From                 : Jan 10 08:16:45 2024 GMT
Valid Until                : Apr 3 08:16:44 2024 GMT
SSL/TLS Protocol           : TLSv1.3
Cipher Suite               : TLS_AES_256_GCM_SHA384 (256 bits)

Subject Alternative Names:
  *.google.com
  *.appengine.google.com
  *.bdn.dev
  *.origin-test.bdn.dev
  *.cloud.google.com
  *.crowdsource.google.com
  [...]
```

## Verbosity Levels

1. Basic (-v)
   - Connection status
   - Basic timing information
   - Error messages

2. Detailed (-vv)
   - Response headers
   - Connection endpoints
   - Basic SSL information
   - Detailed error messages

3. Debug (-vvv)
   - Full SSL certificate details
   - Cipher information
   - Protocol details
   - Debug logging
   - Complete request/response information

## Cross-Platform Support

TNC is designed to work consistently across:
- Windows
- macOS
- Linux
- Other Unix-like systems

Platform-specific features:
- Proper line endings in file output
- Appropriate command execution
- Compatible socket operations
- Correct path handling

## Error Handling

- Comprehensive error messages
- SSL/TLS error details
- Network timeout handling
- Permission checks for ICMP
- Invalid input validation
- File operation error handling

## Notes

- UDP tests may show "filtered" status due to firewall rules
- ICMP tests may require root/administrator privileges
- SSL certificate information available for HTTPS tests
- File paths are normalized for cross-platform compatibility
- Color output works on all major terminals
- Debug logging available with -vvv

## Troubleshooting

1. **SSL Certificate Issues**
   - Use `--no-verify` for self-signed certificates
   - Check certificate validity dates
   - Verify hostname matches certificate

2. **Permission Issues**
   - Run with elevated privileges for ICMP
   - Check file write permissions
   - Verify network access rights

3. **Connection Problems**
   - Increase timeout with `--timeout`
   - Check firewall settings
   - Verify target host/port

4. **Output Issues**
   - Use `-j` for machine-readable output
   - Check file write permissions
   - Verify terminal color support

## License

This tool is provided as-is under the MIT License.

## Author

Jeffrey Kroll 