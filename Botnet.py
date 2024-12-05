import requests
import threading
import argparse
import time
from datetime import datetime
import random
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

authorized_shells = set()

class CaptivePortalHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Welcome to the Captive Portal</h1>"
                             b"<form action='/auth' method='post'>"
                             b"Shell ID: <input type='text' name='shell_id'><br>"
                             b"<input type='submit' value='Authenticate'></form></body></html>")
        elif self.path == "/load_test":
            shell_id = self.headers.get('Shell-ID')
            if shell_id in authorized_shells:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "Load test initiated"}).encode())
                self.initiate_load_test()
            else:
                self.send_response(403)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "Unauthorized"}).encode())

    def do_POST(self):
        if self.path == "/auth":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            shell_id = self.parse_shell_id(post_data.decode('utf-8'))
            if shell_id:
                authorized_shells.add(shell_id)
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Authentication Successful</h1></body></html>")
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Authentication Failed</h1></body></html>")

    def parse_shell_id(self, data):
        for item in data.split('&'):
            if item.startswith('shell_id='):
                return item.split('=')[1]
        return None

    def initiate_load_test(self):
        botnet(args.url, args.total_requests, args.concurrency, args.num_bots, args.timeout)

def send_request(url, bot_id, timeout):
    try:
        start_time = datetime.now()
        response = requests.get(url, timeout=timeout)
        end_time = datetime.now()
        elapsed_time = (end_time - start_time).total_seconds() * 1000
        logging.info(f"Bot {bot_id} - Response Code: {response.status_code}, Elapsed Time: {elapsed_time:.2f}ms")
    except requests.exceptions.RequestException as e:
        logging.error(f"Bot {bot_id} - Request failed: {e}")

def bot_worker(bot_id, url, num_requests, concurrency, timeout):
    threads = []
    for _ in range(num_requests):
        if len(threads) >= concurrency:
            for thread in threads:
                thread.join()
            threads = []

        thread = threading.Thread(target=send_request, args=(url, bot_id, timeout))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

def botnet(url, total_requests, concurrency, num_bots, timeout):
    requests_per_bot = total_requests // num_bots
    bots = []
    start_time = datetime.now()
    for bot_id in range(num_bots):
        bot = threading.Thread(target=bot_worker, args=(bot_id, url, requests_per_bot, concurrency, timeout))
        bot.start()
        bots.append(bot)
        # Random delay to mimic more realistic botnet behavior
        time.sleep(random.uniform(0.1, 1.0))

    for bot in bots:
        bot.join()

    end_time = datetime.now()
    elapsed_time = (end_time - start_time).total_seconds()
    logging.info(f"Botnet load test completed in {elapsed_time:.2f} seconds")

def run_captive_portal(port):
    server_address = ('', port)
    httpd = HTTPServer(server_address, CaptivePortalHandler)
    logging.info(f'Starting captive portal on port {port}')
    httpd.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Botnet load testing tool with captive portal")
    parser.add_argument("url", help="URL of the server to test")
    parser.add_argument("-r", "--total-requests", type=int, default=1000, help="Total number of requests to send")
    parser.add_argument("-c", "--concurrency", type=int, default=10, help="Concurrency level per bot")
    parser.add_argument("-b", "--num-bots", type=int, default=5, help="Number of bots")
    parser.add_argument("-t", "--timeout", type=int, default=10, help="Timeout in seconds for each request")
    parser.add_argument("-p", "--port", type=int, default=8080, help="Port for the captive portal")
    args = parser.parse_args()

    logging.info(f"Starting botnet load testing tool with captive portal on port {args.port}")
    captive_portal_thread = threading.Thread(target=run_captive_portal, args=(args.port,))
    captive_portal_thread.start()

#    Explanation:

#    1. HTTP Server for Captive Portal:
#   - `CaptivePortalHandler`: Handles HTTP requests for the captive portal. It serves a simple HTML form for shell authentication.
#   - `do_GET`: Handles GET requests to serve the captive portal page and initiate load tests for authenticated shells.
#   - `do_POST`: Handles POST requests to authenticate shells.
#   - `parse_shell_id`: Parses the shell ID from the POST request data.

#    2. Authorized Shells:
#   - `authorized_shells`: A set to store authenticated shell IDs.

#    3. Load Test Integration:
#   - The `initiate_load_test` method in `CaptivePortalHandler` starts the botnet load test when an authenticated shell requests it.

#    4. Running the Captive Portal:
#   - `run_captive_portal`: Starts the HTTP server on a specified port.
#   - The main script starts the captive portal server in a separate thread.

#    Running the Script:

#    Save the script as a Python file (e.g., `botnet_captive_portal.py`) and execute it from the command line, providing the necessary arguments. For example:

```sh
python botnet_captive_portal.py http://example.com -r 1000 -c 10 -b 5 -t 10 -p 8080
```

#    This command will start a captive portal on port 8080 and perform a botnet load test on `http://example.com` with the specified parameters once a shell authenticates through the portal.
