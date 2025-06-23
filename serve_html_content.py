
import threading
import http.server
import socketserver
import webbrowser
import time
import io

def serve_html_safely(html_content, port=8000, serve_time=5):
    """Safely serve HTML content with proper error handling"""
    
    # Find available port if specified port is busy
    import socket
    for test_port in range(port, port + 10):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', test_port))
                port = test_port
                break
        except OSError:
            continue
    else:
        raise RuntimeError("Could not find available port")
    
    class SafeHTMLHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            try:
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(html_content.encode('utf-8'))
            except Exception as e:
                self.send_error(500, f"Server Error: {str(e)}")
        
        def log_message(self, format, *args):
            pass
    
    try:
        with socketserver.TCPServer(("localhost", port), SafeHTMLHandler) as httpd:
            server_thread = threading.Thread(target=httpd.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            url = f'http://localhost:{port}'
            webbrowser.open(url)
            print(f"HTML served at: {url}")
            
            time.sleep(serve_time)
            httpd.shutdown()
            print("Server stopped")
            
    except Exception as e:
        print(f"Server error: {str(e)}")