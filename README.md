# PyAccess

A Python library for reading Microsoft Access databases (.accdb/.mdb files) with cross-platform support using automatic backend selection.

## Features

- **Cross-platform Access database reading** - Automatic backend selection for Linux (mdbtools), Windows (pyodbc), and macOS (mdbtools)
- **Pandas integration** - Query results returned as pandas DataFrames
- **Geological database support** - Specialized classes for mining/geological data
- **Type safety** - Full type hints and error handling
- **Context manager support** - Clean resource management
- **Export capabilities** - Export data to CSV files

## Installation

### Using uv (recommended)
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the package
uv pip install pyaccess
```

### Using pip
```bash
pip install pyaccess
```

### Platform-Specific Requirements

#### Windows
On Windows, you'll need the Microsoft Access Database Engine:
1. Download from: https://www.microsoft.com/en-us/download/details.aspx?id=54920
2. Install the version (32-bit or 64-bit) that matches your Python installation
   - Check your Python: `python -c "import struct; print(struct.calcsize('P') * 8, 'bit')"`
   - 32-bit Python requires 32-bit ACE driver
   - 64-bit Python requires 64-bit ACE driver

#### Linux/macOS
No additional setup required - mdbtools will be installed automatically on first use, or you can install manually:
- **Ubuntu/Debian**: `sudo apt install mdbtools`
- **CentOS/RHEL**: `sudo yum install mdbtools`
- **macOS**: `brew install mdbtools`

### For development
```bash
# Clone the repository
git clone https://github.com/rizquuula/pyaccess.git
cd pyaccess

# Install with uv
uv pip install -e .

# Or with pip
pip install -e .
```

### System Requirements

- **Python 3.11+**
- **Platform-specific database drivers:**
  - **Windows**: Microsoft Access Database Engine (ACE) - download from Microsoft
  - **Linux/macOS**: mdbtools (automatically installed on first use)
- **Operating Systems**: Linux, Windows, macOS

## Quick Start

```python
from pyaccess import GeologicalDatabase
from pathlib import Path

# Open your Access database
db_path = Path("path/to/your/database.accdb")
with GeologicalDatabase(db_path) as db:
    print(f"Tables: {db.get_tables()}")

    # Get all drill hole collar data
    collars = db.collar.get_all_holes()
    print(f"Found {len(collars)} drill holes")

    # Get data for a specific hole
    hole_id = "DH001"
    hole_data = db.get_complete_hole_data(hole_id)
    print(f"Hole {hole_id} has {len(hole_data['survey'])} survey points")
```

## API Reference

### AccessDatabase

The base class for accessing any MS Access database.

```python
from pyaccess import AccessDatabase

# Basic usage
db = AccessDatabase("database.accdb")

# Get table list
tables = db.get_tables()

# Get table schema
table_info = db.get_table_info("my_table")

# Query data
df = db.query_table("my_table", columns=["col1", "col2"], where="col1 > 100", limit=10)

# Export to CSV
db.export_table_to_csv("my_table", "output.csv")
```

### GeologicalDatabase

Specialized class for geological/mining databases with convenient access to common tables.

```python
from pyaccess import GeologicalDatabase

db = GeologicalDatabase("geological.accdb")

# Collar data access
all_holes = db.collar.get_all_holes()
specific_hole = db.collar.get_hole_by_id("DH001")
holes_in_block = db.collar.get_holes_in_block("Block_A")

# Survey data
survey_data = db.survey.get_survey_for_hole("DH001")
all_surveys = db.survey.get_all_surveys()

# Lithology data
litho_data = db.lithology.get_lithology_for_hole("DH001")
all_litho = db.lithology.get_all_lithology()
litho_by_code = db.lithology.get_lithology_by_code("QTZ")

# Get complete hole data (collar + survey + lithology)
complete_data = db.get_complete_hole_data("DH001")

# Export hole data to CSV files
db.export_hole_to_csv("DH001", "output_directory/")
```

### Query Methods

#### query_table()

```python
# Basic query
df = db.query_table("table_name")

# With column selection
df = db.query_table("table_name", columns=["col1", "col2"])

# With filtering (pandas query syntax)
df = db.query_table("table_name", where="col1 > 100 and col2 == 'value'")

# With limit
df = db.query_table("table_name", limit=100)
```

#### WHERE Clause Syntax

The `where` parameter uses pandas query syntax:

```python
# String matching
where="hole_id == 'DH001'"

# Numeric comparisons
where="depth > 100 and depth < 200"

# Multiple conditions
where="block == 'A' and max_depth > 50"
```

## Geological Data Structure

The library is designed to work with typical geological database schemas:

- **collar**: Drill hole location and metadata (hole_id, x, y, z, max_depth, etc.)
- **survey**: Drill hole survey data (azimuth, dip, depth)
- **litho**: Lithology intervals (depth_from, depth_to, lith_code, etc.)
- **alteration**: Alteration data
- **styles**: Visualization styling
- **translation**: Code translations

## Error Handling

```python
from pyaccess import (
    AccessDatabaseError,
    DatabaseConnectionError,
    TableNotFoundError
)

try:
    db = GeologicalDatabase("database.accdb")
    data = db.query_table("nonexistent_table")
except DatabaseConnectionError:
    print("Database file not found or corrupted")
except TableNotFoundError:
    print("Table does not exist")
except AccessDatabaseError as e:
    print(f"Database error: {e}")
```

## Context Manager

Use the context manager for automatic resource management:

```python
with GeologicalDatabase("database.accdb") as db:
    data = db.collar.get_all_holes()
    # Database connection automatically closed
```

## Exporting Data

```python
# Export table to CSV
db.export_table_to_csv("collar", "collar_data.csv")

# Export with filtering
db.export_table_to_csv(
    "survey",
    "survey_data.csv",
    where="hole_id == 'DH001'",
    columns=["hole_id", "depth", "azimuth", "dip"]
)

# Export complete hole data
db.export_hole_to_csv("DH001", "hole_data/")
# Creates: DH001_collar.csv, DH001_survey.csv, DH001_lithology.csv
```

## Running Tests

```bash
# Install test dependencies
pip install pytest

# Run tests
pytest

# Run with coverage
pytest --cov=pyaccess --cov-report=html
```

## Development

### Setting up development environment

```bash
# Clone repository
git clone https://github.com/rizquuula/pyaccess.git
cd pyaccess

# Install with uv (recommended)
uv pip install -e .
uv pip install -e ".[dev]"

# Or with pip
pip install -e .
pip install pytest ruff

# Run linting
ruff check .

# Auto-format code
./auto_format_ruff.sh

# Run tests
pytest

# Build package
uv build

# Publish (see Makefile for details)
make help
```

### Project Structure

```
pyaccess/
├── src/
│   ├── pyaccess/
│   │   ├── __init__.py           # Main package exports
│   │   ├── core.py               # AccessDatabase class with automatic backend selection
│   │   ├── exceptions.py         # Custom exceptions
│   │   ├── models.py             # Data models
│   │   ├── backend/              # Backend implementations
│   │   │   ├── __init__.py       # Backend factory and platform detection
│   │   │   ├── base.py           # Abstract backend base class
│   │   │   ├── mdbtools_backend.py # Linux/macOS backend using mdbtools
│   │   │   └── pyodbc_backend.py # Windows backend using pyodbc
│   │   └── geological/
│   │       ├── __init__.py       # Geological package exports
│   │       ├── collar.py         # CollarData class
│   │       ├── database.py       # GeologicalDatabase class
│   │       ├── lithology.py      # LithologyData class
│   │       └── survey.py         # SurveyData class
├── tests/
│   ├── conftest.py               # Test configuration
│   ├── test_access_database.py   # Core database tests
│   ├── test_error_handling.py    # Error handling tests
│   └── test_geological_database.py # Geological tests
├── pyproject.toml                # Project configuration
├── uv.lock                       # Dependency lock file
├── Makefile                      # Build and publish commands
├── auto_format_ruff.sh           # Code formatting script
└── README.md                     # This file
```

## Dependencies

### Runtime Dependencies
- **pandas >= 2.0.0**: Data manipulation and analysis
- **typing-extensions >= 4.0.0**: Enhanced type hints for older Python versions
- **pip >= 25.3**: Package installer (automatically available)

### Platform-Specific Dependencies
- **Windows**: `pyodbc` + Microsoft Access Database Engine (ACE)
- **Linux/macOS**: `mdbtools` (automatically installed on first use)

### Optional Dependencies (installed automatically based on platform)
- **pyodbc >= 5.0.0**: ODBC database access for Windows
- **sqlalchemy >= 2.0.0**: SQL toolkit for Windows backend
- **sqlalchemy-access >= 2.0.0**: SQLAlchemy dialect for Access databases on Windows

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

### Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/pyaccess.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate the environment: `source venv/bin/activate` (Linux/macOS) or `venv\Scripts\activate` (Windows)
5. Install development dependencies: `pip install -e .[dev]`
6. Run tests: `pytest`
7. Make your changes
8. Run linting: `./auto_format_ruff.sh`
9. Ensure tests pass: `pytest`
10. Submit a pull request

### Code Style

- We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting
- Run `./auto_format_ruff.sh` to format your code
- Follow the existing code patterns and type hints

## Support

For issues and questions, please [create an issue](link-to-issues) or contact the maintainers.