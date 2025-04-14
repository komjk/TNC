# Network Connection Tester (TNC)

A powerful, lightweight network testing tool written in Python. TNC provides comprehensive network testing capabilities without requiring any external dependencies.

## Features

- Multiple protocol support (TCP, UDP, HTTP, HTTPS, ICMP)
- Detailed connection information
- SSL/TLS certificate inspection
- Continuous monitoring mode
- JSON output support
- Color-coded terminal output
- Verbosity levels for detailed debugging
- No external dependencies required
- Clean, professional output format
- File output matching terminal output exactly

## Requirements

- Python 3.x
- No external packages required (uses only Python standard library)

## Installation

1. Download the `tnc.py` file
2. Make it executable:
   ```bash
   chmod +x tnc.py
   ```
3. (Optional) Move it to your PATH for global access

## Usage

```bash
python3 tnc.py [target] [options]
```

### Basic Options

| Option | Description |
|--------|-------------|
| `target` | Target host or URL to test (required) |
| `-p, --port` | Target port number |
| `-v, --verbose` | Increase verbosity level (use -v, -vv, or -vvv) |
| `--protocol` | Protocol to test (icmp, http, https, udp, tcp) |
| `--timeout` | Connection timeout in seconds (default: 10.0) |
| `--json` | Output results in JSON format |
| `--output-file` | Write results to specified file (overwrites existing file) |

### Advanced Options

| Option | Description |
|--------|-------------|
| `--continuous` | Enable continuous monitoring |
| `--interval` | Interval in seconds for continuous checks (default: 5) |
| `--count` | Number of checks to perform before exiting |
| `--method` | HTTP method to use (GET, HEAD, POST, PUT, DELETE) |
| `--headers` | Custom HTTP headers in JSON format |
| `--no-verify` | Disable SSL certificate verification |

## Examples

### Basic TCP Connection Test
```bash
python3 tnc.py google.com -p 80 --protocol tcp
```

### HTTPS Test with Verbose Output
```bash
python3 tnc.py https://example.com --protocol https -vv
```

### Continuous ICMP Monitoring
```bash
python3 tnc.py 8.8.8.8 --protocol icmp --continuous --interval 2 --count 5
```

### UDP Test with Maximum Verbosity
```bash
python3 tnc.py 8.8.8.8 -p 53 --protocol udp -vvv
```

### HTTP Test with Custom Headers
```bash
python3 tnc.py example.com --protocol http --headers '{"User-Agent": "CustomAgent", "Accept": "application/json"}'
```

### Save Results to File
```bash
python3 tnc.py google.com --protocol tcp --output-file results.txt
```

### JSON Output
```bash
python3 tnc.py 8.8.8.8 --protocol icmp --json
```

## Output Examples

### Basic TCP Test Output
```
==================================================
          Network Connection Tester (TNC) v1.0
==================================================

[+] TCP Connection successful to google.com:80
Latency: 37.91ms
TCP Test Results:
Connection Status             : Success
Latency (ms)                  : 37.91
Local Endpoint                : ('10.1.1.211', 63722)
Remote Endpoint               : ('142.251.40.110', 80)
```

### ICMP Test Output
```
==================================================
          Network Connection Tester (TNC) v1.0
==================================================

[+] ICMP Test Results for 8.8.8.8
Status: Host is reachable
ICMP Test Results:
Ping Status                   : Host is reachable
Latency (ms)                  : 19.774
```

### HTTPS Test Output (Verbose)
```
==================================================
          Network Connection Tester (TNC) v1.0
==================================================

[+] HTTP(S) Testing for https://example.com
Method: GET
Status Code: 200
Response time: 321.17ms

Response Headers:
Content-Type: text/html
ETag: "84238dfc8092e5d9c0dac8ef93371a07:1736799080.121134"
Last-Modified: Mon, 13 Jan 2025 20:11:20 GMT
Vary: Accept-Encoding
Cache-Control: max-age=2915
Date: Sun, 13 Apr 2025 23:10:25 GMT
Alt-Svc: h3=":443"; ma=93600,h3-29=":443"; ma=93600,quic=":443"; ma=93600; v="43"
Content-Length: 1256
Connection: keep-alive

HTTP Test Results:
Final URL                     : https://example.com
Status Code                   : 200
Response Time (ms)            : 321.17
```

### JSON Output Example
```json
{
  "icmp": {
    "success": true,
    "status": "Host is reachable",
    "latency": 17.507
  }
}
```

## Verbosity Levels

1. Basic (-v): Shows essential connection information
   - Connection status
   - Basic timing information
   - Error messages if any

2. Detailed (-vv): Includes additional details
   - Response headers
   - Detailed timing information
   - Connection endpoints
   - Redirect information
   - SSL/TLS information for HTTPS

3. Debug (-vvv): Shows maximum information
   - SSL/TLS certificate details
   - Socket options
   - Full request/response headers
   - Detailed error information
   - Request headers

## Continuous Monitoring

When using `--continuous` mode:
- Screen clears between checks
- Shows timestamp for each check
- Displays countdown to next check
- Can be stopped with Ctrl+C
- Maintains consistent output format
- Overwrites output file for each check

## Notes

- UDP tests may show "No response" even when successful, as UDP is connectionless
- ICMP tests require appropriate system permissions
- HTTPS tests include SSL/TLS certificate information at higher verbosity levels
- Custom headers should be provided in valid JSON format
- Output is color-coded for better readability (green for success, red for errors, cyan for information)
- File output exactly matches terminal output format
- Output files are overwritten rather than appended

## Troubleshooting

1. **Connection Timeouts**
   - Try increasing the timeout value: `--timeout 20`
   - Check network connectivity
   - Verify target host is reachable

2. **SSL Certificate Errors**
   - Use `--no-verify` to bypass certificate validation
   - Check system time is correct
   - Verify certificate chain is valid

3. **Permission Issues**
   - Run with appropriate permissions for ICMP tests
   - Check firewall settings
   - Verify network access rights

4. **Output Formatting**
   - Use `--json` for machine-readable output
   - Adjust verbosity level for more/less detail
   - Check terminal color support if colors aren't displaying
   - File output will match terminal output exactly

## Security Considerations

When using the Network Connection Tester (TNC), please keep the following security considerations in mind:

1. **Input Validation**: 
   - Ensure that all inputs, especially URLs and headers, are properly validated. The tool includes basic validation, but users should be cautious about the data they provide.

2. **SSL/TLS Verification**:
   - By default, SSL verification is enabled to protect against man-in-the-middle attacks. If you choose to disable SSL verification using the `--no-verify` option, be aware that this exposes you to potential security risks. Only disable SSL verification if you fully understand the implications.

3. **Error Handling**:
   - The tool logs errors using the logging module. Avoid exposing sensitive information in error messages. Review logs regularly to ensure no sensitive data is being captured.

4. **Command Injection Prevention**:
   - The tool sanitizes inputs for subprocess calls to prevent command injection vulnerabilities. Always ensure that inputs are validated before use in system commands.

5. **Network Operations**:
   - The tool implements retry logic for network operations to handle transient failures. However, be cautious when testing against unknown or untrusted hosts, as this could expose your system to risks.

6. **User Permissions**:
   - Some tests, such as ICMP, may require elevated permissions. Ensure you have the necessary permissions and understand the implications of running the tool with elevated privileges.

7. **Configuration Management**:
   - If you plan to extend the tool or integrate it with other systems, avoid hardcoding sensitive information (like API keys). Use environment variables or configuration files to manage sensitive data securely.

8. **Regular Updates**:
   - Keep the tool and any dependencies up to date to mitigate vulnerabilities. Regularly check for updates and security patches.

9. **Network Security**:
   - Be aware of your network environment when running tests. Testing against public or untrusted networks can expose your system to risks. Use a secure and trusted network whenever possible.

By following these security considerations, you can help ensure that your use of the Network Connection Tester remains secure and effective.

## License

This tool is provided as-is under the MIT License.

## Author

Jeffrey Kroll 

## Permissions
- ICMP tests may require elevated permissions. Ensure you have the necessary permissions to run these tests. 