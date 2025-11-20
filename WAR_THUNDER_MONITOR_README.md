# War Thunder Performance Monitor

A comprehensive system performance monitoring tool for War Thunder players to track and analyze their computer's performance while gaming.

## Features

- **Real-time Monitoring**: Track system metrics in real-time with live terminal display
- **CPU Monitoring**: Usage percentage, frequency, and temperature
- **RAM Monitoring**: Memory usage, available memory, and percentage used
- **GPU Monitoring**: Load percentage, VRAM usage, and temperature (NVIDIA GPUs)
- **Disk I/O**: Track read/write operations
- **Network I/O**: Monitor network traffic
- **Data Logging**: All metrics saved to timestamped CSV files for later analysis
- **Performance Summary**: Automatic summary report when monitoring stops

## Screenshot Analysis

Based on your War Thunder screenshot, the monitor will track:
- Current FPS: 139 (as shown in your game)
- System resource usage during gameplay
- Performance trends over time

## Installation

### Prerequisites

- Python 3.6 or higher
- pip package manager

### Install Dependencies

```bash
pip install -r war_thunder_requirements.txt
```

Or install manually:

```bash
pip install psutil gputil
```

**Note**: `gputil` is optional but recommended for NVIDIA GPU monitoring. The tool will work without it but GPU metrics will be disabled.

## Usage

### Basic Usage

1. **Start the monitor BEFORE launching War Thunder**:
   ```bash
   python war_thunder_performance.py
   ```

2. **Launch War Thunder and play normally**

3. **Monitor your performance** in the terminal window

4. **Press Ctrl+C to stop** monitoring and see the summary report

### What You'll See

```
================================================================================
                    WAR THUNDER PERFORMANCE MONITOR
================================================================================
Time: 2025-11-20 14:30:45
Log file: war_thunder_perf_20251120_143042.csv
--------------------------------------------------------------------------------

📊 CPU:
  Usage:       45.2%
  Frequency:  3600.0 MHz
  Temperature: 65.3°C

💾 RAM:
  Used:        12.45 GB (62.3%)
  Available:    7.55 GB

🎮 GPU:
  Name:       NVIDIA GeForce RTX 3060
  Load:        87.3%
  VRAM:      4523.5 / 6144.0 MB (73.6%)
  Temperature: 72.5°C

💿 Disk I/O (Total):
  Read:      1234.56 MB
  Write:      456.78 MB

🌐 Network (Total):
  Sent:       123.45 MB
  Received:   456.78 MB

================================================================================
Press Ctrl+C to stop monitoring
================================================================================
```

## Output Files

The tool generates timestamped CSV files:
- Format: `war_thunder_perf_YYYYMMDD_HHMMSS.csv`
- Example: `war_thunder_perf_20251120_143042.csv`

### CSV Columns

- `timestamp`: Date and time of measurement
- `cpu_percent`: CPU usage percentage
- `cpu_freq_mhz`: CPU frequency in MHz
- `ram_used_gb`: RAM used in GB
- `ram_percent`: RAM usage percentage
- `ram_available_gb`: Available RAM in GB
- `disk_read_mb`: Total disk read in MB
- `disk_write_mb`: Total disk write in MB
- `gpu_name`: GPU model name
- `gpu_load_percent`: GPU load percentage
- `gpu_memory_used_mb`: VRAM used in MB
- `gpu_memory_total_mb`: Total VRAM in MB
- `gpu_memory_percent`: VRAM usage percentage
- `gpu_temp_c`: GPU temperature in Celsius
- `cpu_temp_c`: CPU temperature in Celsius
- `network_sent_mb`: Total network data sent in MB
- `network_recv_mb`: Total network data received in MB

## Analyzing Your Data

### Using Excel/LibreOffice

1. Open the CSV file in Excel or LibreOffice Calc
2. Create charts to visualize:
   - CPU usage over time
   - GPU usage over time
   - Temperature trends
   - RAM usage patterns

### Using Python/Pandas

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load the data
df = pd.read_csv('war_thunder_perf_20251120_143042.csv')

# Plot CPU usage
plt.figure(figsize=(12, 6))
plt.plot(df['timestamp'], df['cpu_percent'])
plt.title('CPU Usage During War Thunder Session')
plt.xlabel('Time')
plt.ylabel('CPU %')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

## Performance Tips

Based on monitoring results:

### High CPU Usage (>80%)
- Lower graphics settings
- Close background applications
- Check for CPU-intensive processes

### High GPU Usage (>95%)
- Reduce graphics quality settings
- Lower resolution or use DLSS/FSR
- Update GPU drivers

### High RAM Usage (>85%)
- Close unnecessary applications
- Consider upgrading RAM
- Clear browser tabs

### High Temperatures
- **CPU >85°C** or **GPU >83°C**:
  - Clean dust from PC
  - Improve case airflow
  - Check thermal paste
  - Adjust fan curves

## Troubleshooting

### GPU Not Detected

If you see "GPU monitoring disabled":
```bash
pip install gputil
```

For AMD GPUs, GPU monitoring may not work as GPUtil primarily supports NVIDIA cards.

### Temperature Not Showing

CPU temperature monitoring depends on sensor availability:
- Linux: Requires `lm-sensors` installed
- Windows: Usually works out of the box
- Some systems may not expose temperature data

### Permission Errors

On Linux, you may need to run with elevated permissions for some sensors:
```bash
sudo python war_thunder_performance.py
```

## Advanced Configuration

Edit the script to customize:

```python
# In main() function:
interval = 1.0  # Change sampling rate (seconds)
```

Lower intervals (0.5s) = more detailed data but larger files
Higher intervals (2.0s) = less detail but smaller files

## System Requirements

- **OS**: Windows 10/11, Linux, macOS
- **Python**: 3.6+
- **RAM**: Minimal impact (<50MB)
- **CPU**: Negligible impact (<1%)

## Tips for Best Results

1. **Start monitoring before launching War Thunder** for baseline metrics
2. **Run for full gaming sessions** to capture performance trends
3. **Test different graphics settings** and compare CSV files
4. **Monitor temperatures** to ensure safe operating ranges
5. **Check for performance degradation** over extended sessions

## Correlating with In-Game Performance

Your screenshot shows:
- **FPS: 139**
- **Ping: 7%** (PL: 7%)

The monitor helps you understand:
- What hardware is bottlenecking your FPS
- Whether temperatures are limiting performance
- If background processes are impacting gameplay
- Memory usage trends during different game modes

## Example Analysis Workflow

1. **Baseline Test**: Monitor with low graphics settings
2. **High Settings Test**: Monitor with maximum graphics
3. **Compare CSV files** to see hardware utilization differences
4. **Find optimal settings** where GPU is 70-90% utilized
5. **Ensure temperatures** stay below 80°C for longevity

## License

Free to use and modify for personal use.

## Support

For issues or questions about the monitoring tool, check:
- Python version: `python --version`
- Installed packages: `pip list`
- Run with verbose output to see any error messages

## Changelog

### Version 1.0.0 (2025-11-20)
- Initial release
- CPU, RAM, GPU monitoring
- Temperature tracking
- CSV logging
- Real-time terminal display
- Performance summary reports
