#!/usr/bin/env python3
"""
War Thunder Performance Monitor
Monitors system performance while playing War Thunder
Tracks FPS, CPU, GPU, RAM, and temperatures
"""

import psutil
import time
import json
import csv
from datetime import datetime
from pathlib import Path
import threading
import sys

try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    print("Warning: GPUtil not installed. GPU monitoring disabled.")
    print("Install with: pip install gputil")


class PerformanceMonitor:
    """Monitor system performance metrics"""

    def __init__(self, log_file="war_thunder_performance.csv", interval=1.0):
        """
        Initialize the performance monitor

        Args:
            log_file: Path to CSV log file
            interval: Monitoring interval in seconds
        """
        self.log_file = Path(log_file)
        self.interval = interval
        self.running = False
        self.data_points = []

        # Create log file with headers
        self._initialize_log_file()

    def _initialize_log_file(self):
        """Create log file with CSV headers"""
        headers = [
            'timestamp',
            'cpu_percent',
            'cpu_freq_mhz',
            'ram_used_gb',
            'ram_percent',
            'ram_available_gb',
            'disk_read_mb',
            'disk_write_mb',
        ]

        if GPU_AVAILABLE:
            headers.extend([
                'gpu_name',
                'gpu_load_percent',
                'gpu_memory_used_mb',
                'gpu_memory_total_mb',
                'gpu_memory_percent',
                'gpu_temp_c'
            ])

        headers.extend([
            'cpu_temp_c',
            'network_sent_mb',
            'network_recv_mb'
        ])

        with open(self.log_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    def get_cpu_temp(self):
        """Get CPU temperature if available"""
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    # Try different sensor names
                    for name in ['coretemp', 'cpu_thermal', 'k10temp', 'zenpower']:
                        if name in temps:
                            return round(temps[name][0].current, 1)
                    # Return first available sensor
                    for sensor_list in temps.values():
                        if sensor_list:
                            return round(sensor_list[0].current, 1)
        except Exception:
            pass
        return None

    def get_gpu_info(self):
        """Get GPU information"""
        if not GPU_AVAILABLE:
            return None

        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]  # Primary GPU
                return {
                    'name': gpu.name,
                    'load': round(gpu.load * 100, 1),
                    'memory_used': round(gpu.memoryUsed, 1),
                    'memory_total': round(gpu.memoryTotal, 1),
                    'memory_percent': round((gpu.memoryUsed / gpu.memoryTotal) * 100, 1),
                    'temperature': round(gpu.temperature, 1)
                }
        except Exception as e:
            print(f"GPU monitoring error: {e}")
        return None

    def collect_metrics(self):
        """Collect current system metrics"""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_freq = psutil.cpu_freq()
        cpu_freq_current = round(cpu_freq.current, 1) if cpu_freq else None

        # RAM metrics
        ram = psutil.virtual_memory()
        ram_used_gb = round(ram.used / (1024**3), 2)
        ram_available_gb = round(ram.available / (1024**3), 2)
        ram_percent = round(ram.percent, 1)

        # Disk I/O
        disk_io = psutil.disk_io_counters()
        disk_read_mb = round(disk_io.read_bytes / (1024**2), 2)
        disk_write_mb = round(disk_io.write_bytes / (1024**2), 2)

        # Network I/O
        net_io = psutil.net_io_counters()
        network_sent_mb = round(net_io.bytes_sent / (1024**2), 2)
        network_recv_mb = round(net_io.bytes_recv / (1024**2), 2)

        # Temperature
        cpu_temp = self.get_cpu_temp()

        # GPU metrics
        gpu_info = self.get_gpu_info()

        metrics = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'cpu_percent': cpu_percent,
            'cpu_freq_mhz': cpu_freq_current,
            'ram_used_gb': ram_used_gb,
            'ram_percent': ram_percent,
            'ram_available_gb': ram_available_gb,
            'disk_read_mb': disk_read_mb,
            'disk_write_mb': disk_write_mb,
        }

        if gpu_info:
            metrics.update({
                'gpu_name': gpu_info['name'],
                'gpu_load_percent': gpu_info['load'],
                'gpu_memory_used_mb': gpu_info['memory_used'],
                'gpu_memory_total_mb': gpu_info['memory_total'],
                'gpu_memory_percent': gpu_info['memory_percent'],
                'gpu_temp_c': gpu_info['temperature']
            })
        else:
            metrics.update({
                'gpu_name': 'N/A',
                'gpu_load_percent': 0,
                'gpu_memory_used_mb': 0,
                'gpu_memory_total_mb': 0,
                'gpu_memory_percent': 0,
                'gpu_temp_c': 0
            })

        metrics.update({
            'cpu_temp_c': cpu_temp if cpu_temp else 0,
            'network_sent_mb': network_sent_mb,
            'network_recv_mb': network_recv_mb
        })

        return metrics

    def log_metrics(self, metrics):
        """Log metrics to CSV file"""
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                metrics['timestamp'],
                metrics['cpu_percent'],
                metrics['cpu_freq_mhz'],
                metrics['ram_used_gb'],
                metrics['ram_percent'],
                metrics['ram_available_gb'],
                metrics['disk_read_mb'],
                metrics['disk_write_mb'],
                metrics['gpu_name'],
                metrics['gpu_load_percent'],
                metrics['gpu_memory_used_mb'],
                metrics['gpu_memory_total_mb'],
                metrics['gpu_memory_percent'],
                metrics['gpu_temp_c'],
                metrics['cpu_temp_c'],
                metrics['network_sent_mb'],
                metrics['network_recv_mb']
            ])

    def display_metrics(self, metrics):
        """Display metrics in terminal"""
        # Clear screen
        print("\033[2J\033[H", end="")

        print("=" * 80)
        print(f"{'WAR THUNDER PERFORMANCE MONITOR':^80}")
        print("=" * 80)
        print(f"Time: {metrics['timestamp']}")
        print(f"Log file: {self.log_file}")
        print("-" * 80)

        # CPU Info
        print(f"\n📊 CPU:")
        print(f"  Usage:      {metrics['cpu_percent']:>6.1f}%")
        if metrics['cpu_freq_mhz']:
            print(f"  Frequency:  {metrics['cpu_freq_mhz']:>6.1f} MHz")
        if metrics['cpu_temp_c']:
            print(f"  Temperature: {metrics['cpu_temp_c']:>5.1f}°C")

        # RAM Info
        print(f"\n💾 RAM:")
        print(f"  Used:       {metrics['ram_used_gb']:>6.2f} GB ({metrics['ram_percent']:.1f}%)")
        print(f"  Available:  {metrics['ram_available_gb']:>6.2f} GB")

        # GPU Info
        if GPU_AVAILABLE and metrics['gpu_name'] != 'N/A':
            print(f"\n🎮 GPU:")
            print(f"  Name:       {metrics['gpu_name']}")
            print(f"  Load:       {metrics['gpu_load_percent']:>6.1f}%")
            print(f"  VRAM:       {metrics['gpu_memory_used_mb']:>6.1f} / {metrics['gpu_memory_total_mb']:.1f} MB ({metrics['gpu_memory_percent']:.1f}%)")
            print(f"  Temperature: {metrics['gpu_temp_c']:>5.1f}°C")

        # Disk I/O
        print(f"\n💿 Disk I/O (Total):")
        print(f"  Read:       {metrics['disk_read_mb']:>8.2f} MB")
        print(f"  Write:      {metrics['disk_write_mb']:>8.2f} MB")

        # Network
        print(f"\n🌐 Network (Total):")
        print(f"  Sent:       {metrics['network_sent_mb']:>8.2f} MB")
        print(f"  Received:   {metrics['network_recv_mb']:>8.2f} MB")

        print("\n" + "=" * 80)
        print("Press Ctrl+C to stop monitoring")
        print("=" * 80)

    def monitor_loop(self):
        """Main monitoring loop"""
        try:
            while self.running:
                metrics = self.collect_metrics()
                self.data_points.append(metrics)
                self.log_metrics(metrics)
                self.display_metrics(metrics)
                time.sleep(self.interval)
        except KeyboardInterrupt:
            self.stop()

    def start(self):
        """Start monitoring"""
        print(f"\n🚀 Starting War Thunder Performance Monitor...")
        print(f"📝 Logging to: {self.log_file}")
        print(f"⏱️  Sample interval: {self.interval}s")
        print("\nMonitoring will begin in 3 seconds...\n")
        time.sleep(3)

        self.running = True
        self.monitor_loop()

    def stop(self):
        """Stop monitoring"""
        self.running = False
        print("\n\n🛑 Stopping monitor...")
        self.generate_summary()

    def generate_summary(self):
        """Generate performance summary"""
        if not self.data_points:
            print("No data collected.")
            return

        print("\n" + "=" * 80)
        print(f"{'PERFORMANCE SUMMARY':^80}")
        print("=" * 80)

        # Calculate averages
        avg_cpu = sum(d['cpu_percent'] for d in self.data_points) / len(self.data_points)
        avg_ram = sum(d['ram_percent'] for d in self.data_points) / len(self.data_points)

        max_cpu = max(d['cpu_percent'] for d in self.data_points)
        max_ram = max(d['ram_percent'] for d in self.data_points)

        print(f"\n📊 Session Duration: {len(self.data_points) * self.interval:.1f} seconds ({len(self.data_points)} samples)")
        print(f"\n💻 CPU:")
        print(f"  Average: {avg_cpu:.1f}%")
        print(f"  Peak:    {max_cpu:.1f}%")

        print(f"\n💾 RAM:")
        print(f"  Average: {avg_ram:.1f}%")
        print(f"  Peak:    {max_ram:.1f}%")

        if GPU_AVAILABLE and self.data_points[0]['gpu_name'] != 'N/A':
            avg_gpu = sum(d['gpu_load_percent'] for d in self.data_points) / len(self.data_points)
            max_gpu = max(d['gpu_load_percent'] for d in self.data_points)
            avg_gpu_temp = sum(d['gpu_temp_c'] for d in self.data_points) / len(self.data_points)
            max_gpu_temp = max(d['gpu_temp_c'] for d in self.data_points)

            print(f"\n🎮 GPU:")
            print(f"  Average Load: {avg_gpu:.1f}%")
            print(f"  Peak Load:    {max_gpu:.1f}%")
            print(f"  Avg Temp:     {avg_gpu_temp:.1f}°C")
            print(f"  Max Temp:     {max_gpu_temp:.1f}°C")

        print(f"\n📝 Full log saved to: {self.log_file}")
        print("=" * 80)


def main():
    """Main entry point"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║         WAR THUNDER PERFORMANCE MONITOR                   ║
    ║                                                           ║
    ║  This tool monitors your system performance while         ║
    ║  playing War Thunder.                                     ║
    ║                                                           ║
    ║  Metrics tracked:                                         ║
    ║  • CPU usage & frequency                                  ║
    ║  • RAM usage                                              ║
    ║  • GPU usage & VRAM (if available)                        ║
    ║  • Temperatures                                           ║
    ║  • Disk & Network I/O                                     ║
    ║                                                           ║
    ║  Data is logged to CSV file for later analysis.           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    # Configuration
    log_filename = f"war_thunder_perf_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    interval = 1.0  # Sample every 1 second

    monitor = PerformanceMonitor(log_file=log_filename, interval=interval)

    try:
        monitor.start()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
