# ZeroLevelProduct_V2

A Python-based 3D CAD modeling library using CadQuery for creating reactor components and related structures.

## Prerequisites

- **Python 3.8+** ([Download Python](https://www.python.org/downloads/))
- **pip** (comes with Python)

## Installation

### 1. Clone or Download the Repository

```bash
git clone https://github.com/pilarsg3/ZeroLevelLibrary_v2
cd ZeroLevelProduct_V2
```

Or download the ZIP file and extract it.

### 2. Create a Virtual Environment

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` appear in your terminal prompt after activation.

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- `cadquery` - 3D CAD modeling library
- `ocp_vscode` - VS Code integration for CAD visualization
- `numpy` - Numerical computing
- `matplotlib` - Plotting library
- `Shapely` - Geometric operations

## Project Structure

```
ZeroLevelProduct_V2/
├── examples/                          # Example scripts
│   ├── example_*.py                  # Individual component examples
│   ├── examples_*.py                 # Multi-component examples
│   └── examples_operation_*.py       # Operation demonstrations
├── assemble.py                        # Assembly utilities
├── build_3D_solid.py                 # 3D solid creation
├── reactor_vessel.py                 # Reactor vessel definitions
├── top_plate.py                      # Top plate components
├── utils.py                          # Utility functions
├── components_3D_primitives.py       # 3D primitive components
├── components_premade.py             # Pre-made components
├── profile_*.py                      # Profile definitions
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

## Running Examples

### Option 1: Run a Single Example Script

```bash
# Run an example
python examples/example_reactor_v0_basic_3D_components.py

# Or any other example
python examples/examples_3D_components.py
```

### Option 2: Interactive Python Shell

```bash
python
>>> from examples.example_reactor_v0_basic_3D_components import *
```

### Option 3: Using VS Code with OCP Viewer

If you're using VS Code with the `ocp_vscode` extension, you can run scripts and visualize the 3D models in the editor.

## Dependencies Overview

| Package | Version | Purpose |
|---------|---------|---------|
| cadquery | 2.7.0 | 3D CAD modeling and operations |
| ocp_vscode | 3.1.2 | VS Code visualization for 3D models |
| numpy | 2.4.3 | Numerical computations |
| matplotlib | 3.10.8 | Plotting and visualization |
| Shapely | 2.1.2 | Geometric shape operations |

## Deactivating the Virtual Environment

When you're done, deactivate the virtual environment:

```bash
deactivate
```

## Troubleshooting

### Python not found
- Ensure Python 3.8+ is installed: `python --version` or `python3 --version`
- On macOS, you may need to use `python3` instead of `python`

### Virtual environment not activating
- macOS/Linux: Try `source venv/bin/activate`
- Windows: Try `venv\Scripts\activate.bat` or `venv\Scripts\Activate.ps1` (PowerShell)

### Import errors after installation
- Ensure your virtual environment is activated (you should see `(venv)` in your terminal)
- Reinstall dependencies: `pip install -r requirements.txt`

### ModuleNotFoundError for local imports
- When running scripts from the `examples/` folder, imports use relative paths (`from ..module`)
- Always run scripts from the project root directory, not from within the `examples/` folder

## Development

### Adding New Dependencies

```bash
pip install <package-name>
pip freeze > requirements.txt
```

### Running Tests

```bash
python -m pytest test_*.py
```

## License

[Add your license information here]

## Contributing

[Add contributing guidelines here]
