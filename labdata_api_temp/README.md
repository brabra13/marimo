# Labdata API

Internal Python API for accessing and analyzing test data from Labdata platform.

## 🚀 Quick Start

1. Launch Marimo:
```bash
marimo edit labdata_explorer.py
```

2. Start exploring your data:
```python
from labdata_api import Labdata

# Initialize connection
labdata = Labdata()

# Get a program
program = labdata.program("Zenith")

# Get a unit
unit = program.unit("ecs1")

# Access fulldata and captures
fulldata = unit.fulldata()
captures = unit.captures()
```

## 📚 Core Concepts

### Programs
Programs represent the top-level organization of test data. Each program contains multiple units.

```python
# List all available programs
labdata.program_list

# Get a specific program
program = labdata.program("Zenith")

# Iterate through units in a program
for unit in program.units():
    print(unit)
```

### Units
Units are testing entities within a program. Each unit contains fulldata and captures.

```python
# Get a specific unit
unit = program.unit("ecs1")

# Get list of units
unit_list = program.units()
```

### Fulldata
Continuous time-series data collected during tests.

```python
# Get available signals
print(unit.signal_list)
print(unit.fulldata_list)

# Get dataset for specific fulldata and signals
dataset = unit.dataset(
    fulldata_id=123,
    signals_list=["temperature", "pressure"]
)

# Access data and metadata
print(dataset.description)
print(dataset.signal_data)
print(dataset.data)  # pandas DataFrame

# Check if signal exists
if "temperature" in dataset:
    print("Temperature data available")
```

### Captures
Point-in-time measurements with statistical information.

```python
# Get all captures
captures = unit.captures()

# Access capture data
data = captures.data       # Dictionary of DataFrames with statistical measures
metadata = captures.metadata  # Capture metadata

# Available statistical measures in data:
# - min
# - max
# - average
# - stdDev
```

## 🔄 Data Iteration

### Iterating Through Units
```python
# Iterate through all units
for unit in program.units():
    print(f"Processing unit: {unit}")

# Filter specific units
selected_units = ["ecs1", "ecs2"]
for unit in program.units(selected_unit_list=selected_units):
    print(f"Processing selected unit: {unit}")
```

### Iterating Through Datasets
```python
# Get multiple datasets
signals = ["temperature", "pressure"]
fulldata_ids = [123, 124, 125]

for dataset in unit.datasets(fulldata_list=fulldata_ids, signals=signals):
    print(f"Dataset description: {dataset.description}")
    print(dataset.data)
```

## 📊 Data Processing

### Working with Pandas
All data is returned as Pandas DataFrames for easy analysis:

```python
# Basic statistics
dataset.data.describe()

# Time-series operations
dataset.data.rolling(window='1H').mean()

# Plotting with Marimo
import marimo as mo
mo.line(dataset.data)
```

### Caching
Data caching is enabled by default to improve performance:

```python
# Disable caching
labdata = Labdata(with_cache=False)

# Custom cache location
labdata = Labdata(cache_location="/custom/path/to/cache/")
```

## 🔍 Example Notebooks

1. **Basic Data Explorer** (`examples/labdata_explorer.py`):
   - Interactive program and unit selection
   - Signal visualization
   - Basic statistics

2. **Capture Analysis** (`examples/capture_analysis.py`):
   - Statistical analysis of captures
   - Trend visualization
   - Anomaly detection

3. **Time Series Analysis** (`examples/timeseries_analysis.py`):
   - Advanced signal processing
   - Custom metrics calculation
   - Comparative analysis

## 🛠 Best Practices

1. **Resource Management**
   - Use iterators for large datasets
   - Enable caching for frequently accessed data
   - Close sessions when done

2. **Error Handling**
   ```python
   try:
       dataset = unit.dataset(fulldata_id=123, signals_list=["temp"])
   except KeyError as e:
       print(f"Signal not found: {e}")
   except TimeoutError:
       print("Network error occurred")
   ```

3. **Performance Tips**
   - Request only needed signals
   - Use filtered unit lists when possible
   - Leverage pandas operations for data processing

## 🤝 Contributing

This is an internal tool. For issues or suggestions:
1. Report bugs to the internal issue tracker
2. Contact the development team
3. Submit enhancement requests through proper channels

## 📝 License

Internal use only. All rights reserved.
