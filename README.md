# SolvMate

SolvMate is a Python-based calculation tool for Solvency II Standard Formula SCR calculations.

## Project Setup

### Prerequisites
- Python 3.8 or higher
- Git
- Visual Studio Code
- GitHub account

### Setting up a GitHub Codespace

1. Fork this repository to your GitHub account
2. Click the green "Code" button
3. Select "Open with Codespaces"
4. Click "New codespace"

### Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/SolvMate.git
cd SolvMate
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

### Branch Management

1. Create a new feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit:
```bash
git add .
git commit -m "Description of your changes"
```

3. Push changes to GitHub:
```bash
git push origin feature/your-feature-name
```

4. Create a Pull Request on GitHub to merge your changes

## Project Structure

```
SolvMate/
├── src/
│   ├── main.ipynb           # Main calculation notebook
│   ├── risks/              # Risk calculation modules
│   ├── utils/              # Utility functions
│   └── config/             # Configuration files
├── tests/                  # Test files
├── templates/              # Input file templates
├── data/                   # Input data directory
├── outputs/                # Calculation results
└── requirements.txt        # Project dependencies
```

## Development Workflow

1. Activate your virtual environment
2. Open VS Code in the project directory:
```bash
code .
```
3. Start developing in the relevant modules
4. Run tests regularly:
```bash
python -m pytest
```

## Supabase Database Interactions 

### Setup

1. Create a `.env` file in the project root:
```bash
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

2. Install required packages:
```bash
pip install supabase-py pandas python-dotenv
```

3. Initialize the Supabase client:
```python
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)
```

### Basic Operations

#### Reading Data
```python
# Read all rows from a table
response = supabase.table('table_name').select('*').execute()

# Read specific columns
response = supabase.table('table_name').select('column1, column2').execute()

# Limit results
response = supabase.table('table_name').select('*').limit(10).execute()

# Convert to Pandas DataFrame
import pandas as pd
df = pd.DataFrame(response.data)
```

#### Filtering Data
```python
# Equal to
response = supabase.table('table_name').select('*').eq('column', 'value').execute()

# Greater than
response = supabase.table('table_name').select('*').gt('column', 100).execute()

# Multiple conditions
response = (supabase.table('table_name')
    .select('*')
    .eq('status', 'active')
    .lt('age', 30)
    .execute())

# OR conditions
response = (supabase.table('table_name')
    .select('*')
    .or('column1.eq.value1,column2.eq.value2')
    .execute())
```

#### Writing Data
```python
# Insert a single row
data = {"column1": "value1", "column2": "value2"}
response = supabase.table('table_name').insert(data).execute()

# Insert multiple rows
data = [
    {"column1": "value1", "column2": "value2"},
    {"column1": "value3", "column2": "value4"}
]
response = supabase.table('table_name').insert(data).execute()
```

#### Updating Data
```python
# Update records matching a condition
response = (supabase.table('table_name')
    .update({"column1": "new_value"})
    .eq('id', 123)
    .execute())
```

#### Deleting Data
```python
# Delete records matching a condition
response = supabase.table('table_name').delete().eq('id', 123).execute()
```

### Error Handling

```python
try:
    response = supabase.table('table_name').select('*').execute()
    data = response.data
except Exception as e:
    print(f"Database error: {str(e)}")
```

### Best Practices

1. Always use environment variables for credentials
2. Handle errors appropriately
3. Use transactions for multiple operations
4. Validate data before writing to database
5. Close connections when done (handled automatically by the client)

For more detailed information, visit the [Supabase Python Client Documentation](https://supabase.com/docs/reference/python/introduction).

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Write tests for new functionality
4. Submit a pull request

## License

[Add your license information here]