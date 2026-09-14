#!/usr/bin/env python3
"""
Portsy - Port Scanner and Route Analyzer
A highly optimized tool for detecting running services, exposed routes, and duplicate dev servers
"""

import socket
import subprocess
import json
import threading
import queue
import time
import requests
import argparse
import sys
import os
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
from urllib.parse import urlparse
import hashlib

# Try to import GUI dependencies
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext
    HAS_GUI = True
except ImportError:
    HAS_GUI = False


@dataclass
class Service:
    """Represents a service running on a port"""
    port: int
    pid: int
    process_name: str
    process_cmd: str
    protocol: str
    routes: List[str] = None
    headers: Dict[str, str] = None
    fingerprint: str = None
    response_time: float = None
    
    def __post_init__(self):
        if self.routes is None:
            self.routes = []
        if self.headers is None:
            self.headers = {}


class PortScanner:
    """High-performance port scanner with process detection"""
    
    # Predefined port ranges for different scan types
    SCAN_PRESETS = {
        'quick': {
            'ranges': [(3000, 9000), (8000, 8100)],
            'description': 'Common dev server ports'
        },
        'dev': {
            'ranges': [(3000, 3100), (4000, 4100), (5000, 5100), 
                      (8000, 8100), (9000, 9100), (8080, 8090)],
            'description': 'Extended dev server ranges'
        },
        'web': {
            'ranges': [(80, 80), (443, 443), (8080, 8080), (8443, 8443),
                      (3000, 3100), (8000, 8100), (9000, 9100)],
            'description': 'Web server ports'
        },
        'full': {
            'ranges': [(1, 65535)],
            'description': 'Complete port range (slow)'
        },
        'services': {
            'ranges': [(21, 25), (53, 53), (80, 80), (110, 110), (143, 143),
                      (443, 443), (993, 993), (995, 995), (1433, 1433),
                      (3306, 3306), (5432, 5432), (6379, 6379), (27017, 27017)],
            'description': 'Common service ports'
        }
    }
    
    def __init__(self, timeout: float = 0.5, max_workers: int = 100):
        self.timeout = timeout
        self.max_workers = max_workers
        self.services: Dict[int, Service] = {}
        
    def scan_port(self, port: int) -> bool:
        """Check if a port is open using socket"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                result = sock.connect_ex(('127.0.0.1', port))
                return result == 0
        except:
            return False
    
    def get_process_info(self, port: int) -> Optional[Tuple[int, str, str]]:
        """Get process info for a port using lsof"""
        try:
            # Use lsof for macOS/Linux
            cmd = f"lsof -i :{port} -sTCP:LISTEN -t"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.stdout:
                pid = int(result.stdout.strip().split('\n')[0])
                process = psutil.Process(pid)
                return pid, process.name(), ' '.join(process.cmdline())
        except:
            pass
        return None
    
    def scan_ports(self, start_port: int = 1, end_port: int = 65535, preset: str = None) -> Dict[int, Service]:
        """Scan a range of ports in parallel"""
        open_ports = []
        
        # Use preset if specified
        if preset and preset in self.SCAN_PRESETS:
            port_ranges = self.SCAN_PRESETS[preset]['ranges']
            ports_to_scan = []
            for start, end in port_ranges:
                ports_to_scan.extend(range(start, end + 1))
        else:
            ports_to_scan = range(start_port, end_port + 1)
        
        # First, quickly scan for open ports
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.scan_port, port): port 
                      for port in ports_to_scan}
            
            for future in as_completed(futures):
                port = futures[future]
                if future.result():
                    open_ports.append(port)
        
        # Then get process info for open ports
        for port in open_ports:
            process_info = self.get_process_info(port)
            if process_info:
                pid, name, cmd = process_info
                self.services[port] = Service(
                    port=port,
                    pid=pid,
                    process_name=name,
                    process_cmd=cmd,
                    protocol='tcp'
                )
        
        return self.services
    
    def get_scan_presets(self) -> Dict[str, str]:
        """Get available scan presets"""
        return {name: info['description'] for name, info in self.SCAN_PRESETS.items()}


class RouteDiscovery:
    """Discovers HTTP routes and endpoints"""
    
    # Framework-specific routes for comprehensive detection
    FRAMEWORK_PATHS = {
        'common': [
            '/', '/api', '/api/v1', '/api/v2', '/health', '/status',
            '/metrics', '/swagger', '/docs', '/graphql', '/admin',
            '/login', '/register', '/dashboard', '/home', '/about',
            '/.well-known', '/robots.txt', '/sitemap.xml', '/favicon.ico'
        ],
        'flask': [
            '/static', '/_debug', '/api/health', '/flask-admin',
            '/admin/static', '/debug', '/blueprint', '/api/v1', '/api/v2',
            '/health', '/status', '/metrics', '/ping', '/info', '/version',
            '/api/status', '/api/info', '/api/ping', '/api/version',
            '/api/docs', '/api/spec', '/api/swagger', '/routes'
        ],
        'django': [
            '/django-admin', '/static', '/media', '/admin/login',
            '/api-auth', '/api/schema', '/dj-rest-auth', '/accounts'
        ],
        'fastapi': [
            '/docs', '/redoc', '/openapi.json', '/api/docs',
            '/health', '/metrics', '/status', '/api/v1/health'
        ],
        'express': [
            '/api', '/users', '/auth', '/public', '/assets',
            '/socket.io', '/webpack-dev-server', '/hmr', '/api/health',
            '/api/status', '/api/info', '/api/version', '/routes'
        ],
        'rails': [
            '/rails/info', '/rails/mailers', '/assets', '/admin',
            '/api/v1', '/users', '/sessions', '/devise'
        ],
        'laravel': [
            '/api', '/admin', '/telescope', '/horizon', '/nova',
            '/broadcasting/auth', '/sanctum', '/passport'
        ],
        'gin': [
            '/ping', '/health', '/metrics', '/api/v1',
            '/swagger', '/debug/pprof', '/static'
        ],
        'gorilla': [
            '/api', '/health', '/metrics', '/static',
            '/ws', '/websocket', '/debug'
        ],
        'fiber': [
            '/api', '/health', '/metrics', '/swagger',
            '/static', '/ws', '/monitor'
        ],
        'spring': [
            '/actuator', '/actuator/health', '/actuator/metrics',
            '/actuator/info', '/api', '/swagger-ui', '/h2-console'
        ],
        'quarkus': [
            '/q/health', '/q/metrics', '/q/openapi', '/q/swagger-ui',
            '/q/dev', '/api', '/health/live', '/health/ready'
        ],
        'ollama': [
            '/api/tags', '/api/generate', '/api/chat', '/api/embeddings',
            '/api/create', '/api/show', '/api/copy', '/api/delete',
            '/api/pull', '/api/push', '/api/version', '/v1/chat/completions'
        ],
        'jupyter': [
            '/api', '/api/kernels', '/api/sessions', '/api/contents',
            '/tree', '/notebooks', '/terminals', '/lab', '/static'
        ],
        'vscode': [
            '/vscode-remote-resource', '/$vscode-remote',
            '/static', '/workbench', '/api'
        ],
        'streamlit': [
            '/_stcore', '/healthz', '/static', '/media',
            '/_stcore/health', '/_stcore/stream'
        ],
        'gradio': [
            '/api', '/api/predict', '/queue/join', '/queue/data',
            '/static', '/file', '/upload', '/component_server'
        ],
        'nginx': [
            '/nginx_status', '/status', '/server-status',
            '/server-info', '/stats'
        ],
        'apache': [
            '/server-status', '/server-info', '/stats',
            '/cgi-bin', '/icons'
        ],
        'dev_servers': [
            '/webpack-dev-server', '/__webpack_dev_server__',
            '/sockjs-node', '/__dev__', '/hot-update',
            '/hmr', '/__vite_ping', '/__vite_client'
        ]
    }
    
    # Combine all paths for full discovery
    ALL_PATHS = []
    for paths in FRAMEWORK_PATHS.values():
        ALL_PATHS.extend(paths)
    ALL_PATHS = list(set(ALL_PATHS))  # Remove duplicates
    
    def __init__(self, timeout: float = 2.0, comprehensive: bool = False):
        self.timeout = timeout
        self.comprehensive = comprehensive
        self.paths_to_check = self.ALL_PATHS if comprehensive else self.FRAMEWORK_PATHS['common']
        
    def discover_routes(self, service: Service) -> None:
        """Discover HTTP routes for a service"""
        base_url = f"http://localhost:{service.port}"
        
        try:
            # First, try to get the root
            response = requests.get(base_url, timeout=self.timeout, allow_redirects=True)
            service.response_time = response.elapsed.total_seconds()
            service.headers = dict(response.headers)
            
            # Check paths based on mode
            found_routes = []
            for path in self.paths_to_check:
                try:
                    url = f"{base_url}{path}"
                    resp = requests.head(url, timeout=self.timeout, allow_redirects=True)
                    if resp.status_code < 400:
                        found_routes.append(path)
                except:
                    pass
            
            service.routes = found_routes
            
            # Generate fingerprint based on headers and routes
            fingerprint_data = f"{service.headers.get('Server', '')}"
            fingerprint_data += f"{service.headers.get('X-Powered-By', '')}"
            fingerprint_data += f"{','.join(sorted(service.routes))}"
            service.fingerprint = hashlib.md5(fingerprint_data.encode()).hexdigest()[:8]
            
        except:
            pass


class DuplicateDetector:
    """Detects potential duplicate services"""
    
    @staticmethod
    def find_duplicates(services: Dict[int, Service]) -> Dict[str, List[Service]]:
        """Group services that might be duplicates"""
        groups = {}
        
        # Group by process name
        by_process = {}
        for service in services.values():
            key = service.process_name
            if key not in by_process:
                by_process[key] = []
            by_process[key].append(service)
        
        # Group by fingerprint
        by_fingerprint = {}
        for service in services.values():
            if service.fingerprint:
                if service.fingerprint not in by_fingerprint:
                    by_fingerprint[service.fingerprint] = []
                by_fingerprint[service.fingerprint].append(service)
        
        # Combine groups
        group_id = 0
        for process_name, process_services in by_process.items():
            if len(process_services) > 1:
                group_id += 1
                groups[f"process_{process_name}_{group_id}"] = process_services
        
        for fingerprint, fingerprint_services in by_fingerprint.items():
            if len(fingerprint_services) > 1:
                group_id += 1
                groups[f"fingerprint_{fingerprint}_{group_id}"] = fingerprint_services
                
        return groups


class CLI:
    """Command-line interface"""
    
    def __init__(self):
        self.scanner = PortScanner()
        self.route_discovery = RouteDiscovery()
        self.duplicate_detector = DuplicateDetector()
        
    def run(self, args):
        """Run the CLI"""
        # Show scan mode info
        if args.preset:
            preset_info = self.scanner.SCAN_PRESETS.get(args.preset, {})
            print(f"🔍 Running {args.preset} scan: {preset_info.get('description', '')}")
            if args.preset == 'full':
                print("⚠️  Full scan may take several minutes...")
        else:
            print(f"🔍 Scanning ports {args.start_port}-{args.end_port}...")
        
        # Configure route discovery
        if args.comprehensive_routes:
            self.route_discovery.comprehensive = True
            self.route_discovery.paths_to_check = self.route_discovery.ALL_PATHS
            print("🌐 Using comprehensive route discovery (all frameworks)")
        
        # Scan ports
        if args.preset:
            services = self.scanner.scan_ports(preset=args.preset)
        else:
            services = self.scanner.scan_ports(args.start_port, args.end_port)
        print(f"✅ Found {len(services)} open ports")
        
        # Discover routes
        if not args.no_routes:
            route_mode = "comprehensive" if args.comprehensive_routes else "standard"
            print(f"🌐 Discovering HTTP routes ({route_mode} mode)...")
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(self.route_discovery.discover_routes, service) 
                          for service in services.values()]
                for future in as_completed(futures):
                    pass
        
        # Display results
        self.display_services(services)
        
        # Find duplicates
        if not args.no_duplicates:
            duplicates = self.duplicate_detector.find_duplicates(services)
            if duplicates:
                self.display_duplicates(duplicates)
        
        # Export to JSON if requested
        if args.json:
            self.export_json(services, args.json)
            
    def display_services(self, services: Dict[int, Service]):
        """Display services in a table format"""
        print("\n📋 Running Services:")
        print("-" * 120)
        print(f"{'Port':<8} {'PID':<8} {'Process':<20} {'Routes':<40} {'Response Time':<15}")
        print("-" * 120)
        
        for port, service in sorted(services.items()):
            routes_str = ', '.join(service.routes[:3])
            if len(service.routes) > 3:
                routes_str += f" (+{len(service.routes)-3} more)"
            
            response_time = f"{service.response_time*1000:.1f}ms" if service.response_time else "N/A"
            
            print(f"{port:<8} {service.pid:<8} {service.process_name:<20} "
                  f"{routes_str:<40} {response_time:<15}")
    
    def display_duplicates(self, duplicates: Dict[str, List[Service]]):
        """Display potential duplicate services"""
        print("\n⚠️  Potential Duplicate Services:")
        for group_name, services in duplicates.items():
            print(f"\n🔄 {group_name}:")
            for service in services:
                print(f"   - Port {service.port}: {service.process_name} "
                      f"(PID: {service.pid})")
    
    def export_json(self, services: Dict[int, Service], filename: str):
        """Export results to JSON"""
        data = {
            "scan_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "services": {str(port): asdict(service) for port, service in services.items()}
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n💾 Results exported to {filename}")
    
    def show_presets(self):
        """Show available scan presets"""
        print("\n📋 Available Scan Presets:")
        presets = self.scanner.get_scan_presets()
        for name, description in presets.items():
            print(f"  {name:<10} - {description}")
        print("\nUsage: portsy.py --cli --preset [preset_name]")


class GUI:
    """Graphical user interface using Tkinter"""
    
    def __init__(self):
        self.scanner = PortScanner()
        self.route_discovery = RouteDiscovery()
        self.duplicate_detector = DuplicateDetector()
        self.services = {}
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the GUI"""
        self.root = tk.Tk()
        self.root.title("Portsy - Port Scanner & Route Analyzer")
        self.root.geometry("1000x700")
        
        # Control panel
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(control_frame, text="Port Range:").pack(side='left', padx=5)
        self.start_port = ttk.Entry(control_frame, width=10)
        self.start_port.insert(0, "3000")
        self.start_port.pack(side='left', padx=5)
        
        ttk.Label(control_frame, text="to").pack(side='left')
        self.end_port = ttk.Entry(control_frame, width=10)
        self.end_port.insert(0, "9000")
        self.end_port.pack(side='left', padx=5)
        
        self.scan_button = ttk.Button(control_frame, text="Scan", command=self.scan)
        self.scan_button.pack(side='left', padx=20)
        
        self.discover_routes_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Discover Routes", 
                       variable=self.discover_routes_var).pack(side='left', padx=5)
        
        self.find_duplicates_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Find Duplicates", 
                       variable=self.find_duplicates_var).pack(side='left', padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(fill='x', padx=10, pady=5)
        
        # Results notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Services tab
        services_frame = ttk.Frame(self.notebook)
        self.notebook.add(services_frame, text='Services')
        
        # Create treeview for services
        columns = ('Port', 'PID', 'Process', 'Routes', 'Response Time')
        self.services_tree = ttk.Treeview(services_frame, columns=columns, show='tree headings')
        
        for col in columns:
            self.services_tree.heading(col, text=col)
            self.services_tree.column(col, width=150)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(services_frame, orient='vertical', command=self.services_tree.yview)
        hsb = ttk.Scrollbar(services_frame, orient='horizontal', command=self.services_tree.xview)
        self.services_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.services_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        services_frame.grid_rowconfigure(0, weight=1)
        services_frame.grid_columnconfigure(0, weight=1)
        
        # Duplicates tab
        duplicates_frame = ttk.Frame(self.notebook)
        self.notebook.add(duplicates_frame, text='Duplicates')
        
        self.duplicates_text = scrolledtext.ScrolledText(duplicates_frame, wrap=tk.WORD)
        self.duplicates_text.pack(fill='both', expand=True)
        
        # Status bar
        self.status = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN)
        self.status.pack(fill='x', side='bottom')
        
    def scan(self):
        """Run scan in a separate thread"""
        self.scan_button.config(state='disabled')
        self.progress.start()
        self.status.config(text="Scanning...")
        
        # Clear previous results
        for item in self.services_tree.get_children():
            self.services_tree.delete(item)
        self.duplicates_text.delete(1.0, tk.END)
        
        # Run scan in thread
        thread = threading.Thread(target=self._scan_thread)
        thread.daemon = True
        thread.start()
        
    def _scan_thread(self):
        """Scan thread worker"""
        try:
            start = int(self.start_port.get())
            end = int(self.end_port.get())
            
            # Scan ports
            self.services = self.scanner.scan_ports(start, end)
            
            # Discover routes
            if self.discover_routes_var.get():
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [executor.submit(self.route_discovery.discover_routes, service) 
                              for service in self.services.values()]
                    for future in as_completed(futures):
                        pass
            
            # Update UI
            self.root.after(0, self._update_results)
            
        except Exception as e:
            self.root.after(0, lambda: self.status.config(text=f"Error: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.scan_button.config(state='normal'))
            self.root.after(0, self.progress.stop)
    
    def _update_results(self):
        """Update results in UI"""
        # Update services tree
        for port, service in sorted(self.services.items()):
            routes_str = ', '.join(service.routes[:3])
            if len(service.routes) > 3:
                routes_str += f" (+{len(service.routes)-3} more)"
            
            response_time = f"{service.response_time*1000:.1f}ms" if service.response_time else "N/A"
            
            self.services_tree.insert('', 'end', values=(
                port, service.pid, service.process_name, routes_str, response_time
            ))
        
        # Find and display duplicates
        if self.find_duplicates_var.get():
            duplicates = self.duplicate_detector.find_duplicates(self.services)
            if duplicates:
                self.duplicates_text.insert('end', "Potential Duplicate Services Found:\n\n")
                for group_name, services in duplicates.items():
                    self.duplicates_text.insert('end', f"{group_name}:\n")
                    for service in services:
                        self.duplicates_text.insert('end', 
                            f"  - Port {service.port}: {service.process_name} "
                            f"(PID: {service.pid})\n")
                    self.duplicates_text.insert('end', "\n")
            else:
                self.duplicates_text.insert('end', "No duplicate services detected.")
        
        self.status.config(text=f"Found {len(self.services)} services")
    
    def run(self):
        """Run the GUI"""
        self.root.mainloop()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Portsy - Port Scanner and Route Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                     # Quick scan (CLI default)
  %(prog)s --preset dev        # Scan common dev server ranges
  %(prog)s --preset full       # Full port scan (1-65535)
  %(prog)s --comprehensive-routes # Deep route discovery
  %(prog)s --list-presets      # Show available scan presets
  %(prog)s --json out.json     # Export results to JSON
  %(prog)s --gui               # Launch GUI interface
        """
    )
    
    parser.add_argument('--gui', action='store_true', help='Use graphical interface (default is CLI)')
    parser.add_argument('-s', '--start-port', type=int, default=3000, 
                       help='Start port (default: 3000)')
    parser.add_argument('-e', '--end-port', type=int, default=9000, 
                       help='End port (default: 9000)')
    parser.add_argument('--preset', choices=['quick', 'dev', 'web', 'full', 'services'],
                       help='Use predefined port ranges')
    parser.add_argument('--comprehensive-routes', action='store_true',
                       help='Check all framework-specific routes')
    parser.add_argument('--list-presets', action='store_true',
                       help='List available scan presets and exit')
    parser.add_argument('--no-routes', action='store_true', 
                       help='Skip route discovery')
    parser.add_argument('--no-duplicates', action='store_true', 
                       help='Skip duplicate detection')
    parser.add_argument('-j', '--json', help='Export results to JSON file')
    parser.add_argument('-t', '--timeout', type=float, default=0.5,
                       help='Socket timeout in seconds (default: 0.5)')
    
    args = parser.parse_args()
    
    # Handle list presets early exit
    if args.list_presets:
        scanner = PortScanner()
        print("\n📋 Available Scan Presets:")
        presets = scanner.get_scan_presets()
        for name, description in presets.items():
            print(f"  {name:<10} - {description}")
        return
    
    # Default to CLI if no --gui flag specified
    if not hasattr(args, 'gui') or not args.gui:
        # Use CLI by default
        cli = CLI()
        cli.scanner.timeout = args.timeout
        cli.run(args)
    else:
        # Use GUI only if explicitly requested
        if not HAS_GUI:
            print("GUI not available. Please install tkinter.")
            sys.exit(1)
        gui = GUI()
        gui.run()


if __name__ == "__main__":
    main()