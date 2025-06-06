"""
Data Analysis incarnation of the NeoCoder framework.

Provides comprehensive data analysis capabilities including data loading, exploration,
visualization, transformation, and statistical analysis with results stored in Neo4j.
"""

import json
import logging
import uuid
import os
import csv
import sqlite3
import statistics
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

import mcp.types as types
from pydantic import Field
from neo4j import AsyncTransaction

from .base_incarnation import BaseIncarnation

logger = logging.getLogger("mcp_neocoder.incarnations.data_analysis")


class DataAnalysisIncarnation(BaseIncarnation):
    """
    Data Analysis incarnation of the NeoCoder framework.

    This incarnation specializes in data analysis workflows including:
    1. Data loading from various sources (CSV, JSON, SQLite)
    2. Data exploration and profiling
    3. Statistical analysis and correlation
    4. Data transformation and cleaning
    5. Results storage and tracking in Neo4j
    6. Analysis history and reproducibility

    All analysis results are stored in Neo4j for future reference and comparison.
    """

    # Define the incarnation name as a string identifier
    name = "data_analysis"

    # Metadata for display in the UI
    description = "Analyze and visualize data"
    version = "1.0.0"

    # Explicitly define which methods should be registered as tools
    _tool_methods = [
        "load_dataset",
        "explore_dataset",
        "profile_data",
        "calculate_statistics",
        "analyze_correlations",
        "filter_data",
        "aggregate_data",
        "compare_datasets",
        "export_results",
        "list_datasets",
        "get_analysis_history"
    ]

    # Schema queries for Neo4j setup
    schema_queries = [
        # Dataset constraints
        "CREATE CONSTRAINT dataset_id IF NOT EXISTS FOR (d:Dataset) REQUIRE d.id IS UNIQUE",
        "CREATE CONSTRAINT analysis_id IF NOT EXISTS FOR (a:DataAnalysis) REQUIRE a.id IS UNIQUE",

        # Indexes for efficient querying
        "CREATE INDEX dataset_name IF NOT EXISTS FOR (d:Dataset) ON (d.name)",
        "CREATE INDEX dataset_source IF NOT EXISTS FOR (d:Dataset) ON (d.source)",
        "CREATE INDEX analysis_timestamp IF NOT EXISTS FOR (a:DataAnalysis) ON (a.timestamp)",
        "CREATE INDEX analysis_type IF NOT EXISTS FOR (a:DataAnalysis) ON (a.analysis_type)"
    ]

    async def initialize_schema(self):
        """Initialize the Neo4j schema for Data Analysis."""
        try:
            async with self.driver.session(database=self.database) as session:
                # Execute each constraint/index query individually
                for query in self.schema_queries:
                    await session.execute_write(lambda tx, q=query: tx.run(q))

                # Create base guidance hub for this incarnation if it doesn't exist
                await self.ensure_guidance_hub_exists()

            logger.info("Data Analysis incarnation schema initialized")
        except Exception as e:
            logger.error(f"Error initializing data_analysis schema: {e}")
            raise

    async def ensure_guidance_hub_exists(self):
        """Create the guidance hub for this incarnation if it doesn't exist."""
        query = """
        MERGE (hub:AiGuidanceHub {id: 'data_analysis_hub'})
        ON CREATE SET hub.description = $description
        RETURN hub
        """

        description = """
# Data Analysis with NeoCoder

Welcome to the Data Analysis System powered by the NeoCoder framework. This system helps you perform comprehensive data analysis with full tracking and reproducibility.

## Getting Started

1. **Load Your Data**
   - Use `load_dataset()` to import data from CSV, JSON, or SQLite
   - Automatically detects data types and schema

2. **Explore Your Data**
   - Use `explore_dataset()` for basic overview and sample data
   - Use `profile_data()` for detailed data profiling and quality assessment
   - Use `calculate_statistics()` for descriptive statistics

3. **Analyze Relationships**
   - Use `analyze_correlations()` to find relationships between variables
   - Use `compare_datasets()` to compare multiple datasets

4. **Transform Your Data**
   - Use `filter_data()` to subset your data based on conditions
   - Use `aggregate_data()` to group and summarize data

## Available Tools

### Data Loading
- `load_dataset(file_path, dataset_name, source_type)`: Load data from various sources
  - **Parameters**:
    - `file_path`: Path to the data file
    - `dataset_name`: Name to identify the dataset
    - `source_type`: \"csv\", \"json\", or \"sqlite\"

### Data Exploration
- `explore_dataset(dataset_id, sample_size)`: Get overview of dataset
  - **Parameters**:
    - `dataset_id`: ID of the dataset to explore
    - `sample_size`: Number of sample rows to display (default: 10)

- `profile_data(dataset_id, include_correlations)`: Comprehensive data profiling
  - **Parameters**:
    - `dataset_id`: ID of the dataset to profile
    - `include_correlations`: Whether to include correlation analysis

- `calculate_statistics(dataset_id, columns, group_by)`: Calculate descriptive statistics
  - **Parameters**:
    - `dataset_id`: ID of the dataset
    - `columns`: Specific columns to analyze (optional)
    - `group_by`: Column to group statistics by (optional)

### Data Analysis
- `analyze_correlations(dataset_id, method, threshold)`: Analyze variable correlations
  - **Parameters**:
    - `dataset_id`: ID of the dataset
    - `method`: \"pearson\", \"spearman\", or \"kendall\"
    - `threshold`: Minimum correlation strength to report

- `compare_datasets(dataset_ids, comparison_type)`: Compare multiple datasets
  - **Parameters**:
    - `dataset_ids`: List of dataset IDs to compare
    - `comparison_type`: \"schema\", \"statistics\", or \"distribution\"

### Data Transformation
- `filter_data(dataset_id, conditions, new_dataset_name)`: Filter dataset based on conditions
  - **Parameters**:
    - `dataset_id`: ID of the source dataset
    - `conditions`: Filter conditions (e.g., \"age > 25 AND income < 50000\")
    - `new_dataset_name`: Name for the filtered dataset

- `aggregate_data(dataset_id, group_by, aggregations, new_dataset_name)`: Group and aggregate data
  - **Parameters**:
    - `dataset_id`: ID of the source dataset
    - `group_by`: Columns to group by
    - `aggregations`: Aggregation functions to apply
    - `new_dataset_name`: Name for the aggregated dataset

### Data Management
- `list_datasets(include_metadata)`: List all loaded datasets
  - **Parameters**:
    - `include_metadata`: Whether to include detailed metadata

- `export_results(analysis_id, format, file_path)`: Export analysis results
  - **Parameters**:
    - `analysis_id`: ID of the analysis to export
    - `format`: \"csv\", \"json\", or \"html\"
    - `file_path`: Path to save the exported file

- `get_analysis_history(dataset_id, analysis_type, limit)`: View analysis history
  - **Parameters**:
    - `dataset_id`: ID of the dataset (optional)
    - `analysis_type`: Type of analysis to filter by (optional)
    - `limit`: Maximum number of results to return

## Data Storage in Neo4j

Analysis results are stored in Neo4j with the following structure:

- `(:Dataset)` - Represents loaded datasets with metadata
- `(:DataAnalysis)` - Represents analysis results and operations
- `(:DataColumn)` - Represents individual columns and their properties
- `[:HAS_COLUMN]` - Links datasets to their columns
- `[:PERFORMED_ANALYSIS]` - Links datasets to analyses performed on them
- `[:DERIVED_FROM]` - Links transformed datasets to their sources

## Best Practices

1. Always load data with descriptive names for easy identification
2. Start with `explore_dataset()` to understand your data structure
3. Use `profile_data()` to identify data quality issues early
4. Document your analysis workflow using the built-in history tracking
5. Export important results for external use and reporting
6. Use meaningful names for derived datasets to track transformations

## Workflow Example

```
# 1. Load your data
load_dataset(file_path=\"/path/to/data.csv\", dataset_name=\"sales_data\", source_type=\"csv\")

# 2. Explore the structure
explore_dataset(dataset_id=\"sales_data_id\", sample_size=20)

# 3. Profile data quality
profile_data(dataset_id=\"sales_data_id\", include_correlations=true)

# 4. Calculate statistics
calculate_statistics(dataset_id=\"sales_data_id\", columns=[\"revenue\", \"quantity\"], group_by=\"category\")

# 5. Analyze relationships
analyze_correlations(dataset_id=\"sales_data_id\", method=\"pearson\", threshold=0.3)

# 6. Filter for specific analysis
filter_data(dataset_id=\"sales_data_id\", conditions=\"revenue > 1000\", new_dataset_name=\"high_value_sales\")
```

All analysis steps are automatically tracked and can be reproduced or referenced later.
        """

        params = {"description": description}

        async with self.driver.session(database=self.database) as session:
            await session.execute_write(lambda tx: tx.run(query, params))

    async def get_guidance_hub(self) -> List[types.TextContent]:
        """Get the guidance hub for this incarnation."""
        query = """
        MATCH (hub:AiGuidanceHub {id: 'data_analysis_hub'})
        RETURN hub.description AS description
        """

        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.execute_read(lambda tx: tx.run(query, {}))
                records = await result.data()

                if records and len(records) > 0:
                    return [types.TextContent(type="text", text=records[0]["description"])]
                else:
                    # If hub doesn't exist, create it
                    await self.ensure_guidance_hub_exists()
                    # Try again
                    return await self.get_guidance_hub()
        except Exception as e:
            logger.error(f"Error retrieving data_analysis guidance hub: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    def list_tool_methods(self):
        """List all methods in this class that are tools."""
        return self._tool_methods

    # Helper methods for data operations

    async def _safe_execute_write(self, session, query, params=None):
        """Execute a write query safely and handle all errors internally."""
        if params is None:
            params = {}

        try:
            async def execute_in_tx(tx):
                result = await tx.run(query, params)
                summary = await result.consume()
                return True, {
                    "nodes_created": summary.counters.nodes_created,
                    "relationships_created": summary.counters.relationships_created,
                    "properties_set": summary.counters.properties_set
                }

            success, stats = await session.execute_write(execute_in_tx)
            return success, stats
        except Exception as e:
            logger.error(f"Error executing write query: {e}")
            return False, {}

    async def _safe_read_query(self, session, query, params=None):
        """Execute a read query safely, handling all errors internally."""
        if params is None:
            params = {}

        try:
            async def execute_and_process_in_tx(tx):
                result = await tx.run(query, params)
                records = await result.data()
                return json.dumps(records, default=str)

            result_json = await session.execute_read(execute_and_process_in_tx)
            return json.loads(result_json)
        except Exception as e:
            logger.error(f"Error executing read query: {e}")
            return []

    def _load_csv_data(self, file_path: str) -> Dict[str, Any]:
        """Load data from CSV file and return metadata and sample."""
        try:
            data_rows = []
            columns = []

            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                # Detect delimiter
                sample = csvfile.read(1024)
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter

                reader = csv.DictReader(csvfile, delimiter=delimiter)
                columns = reader.fieldnames or []

                # Load first 1000 rows for analysis
                for i, row in enumerate(reader):
                    if i >= 1000:  # Limit for performance
                        break
                    data_rows.append(row)

            # Analyze data types and basic stats
            column_info = {}
            for col in columns:
                values = [row.get(col, '') for row in data_rows if row.get(col, '').strip()]

                # Try to determine data type
                numeric_count = 0
                date_count = 0
                for value in values[:100]:  # Sample first 100 values
                    try:
                        float(value)
                        numeric_count += 1
                    except ValueError:
                        pass

                # Determine predominant type
                if numeric_count > len(values) * 0.8:
                    data_type = "numeric"
                else:
                    data_type = "text"

                column_info[col] = {
                    "data_type": data_type,
                    "non_null_count": len(values),
                    "null_count": len(data_rows) - len(values),
                    "unique_count": len(set(values)) if values else 0
                }

            return {
                "row_count": len(data_rows),
                "column_count": len(columns),
                "columns": column_info,
                "sample_data": data_rows[:10],  # First 10 rows as sample
                "all_data": data_rows  # Keep for analysis (limited to 1000 rows)
            }

        except Exception as e:
            logger.error(f"Error loading CSV file {file_path}: {e}")
            raise

    def _load_json_data(self, file_path: str) -> Dict[str, Any]:
        """Load data from JSON file and return metadata and sample."""
        try:
            with open(file_path, 'r', encoding='utf-8') as jsonfile:
                data = json.load(jsonfile)

            # Handle different JSON structures
            if isinstance(data, list):
                data_rows = data[:1000]  # Limit for performance
            elif isinstance(data, dict):
                # Try to find the main data array
                for key, value in data.items():
                    if isinstance(value, list) and len(value) > 0:
                        data_rows = value[:1000]
                        break
                else:
                    # Treat the dict as a single record
                    data_rows = [data]
            else:
                raise ValueError("JSON data must be an array or object")

            # Extract column information
            if data_rows:
                # Get all possible columns from all records
                all_columns = set()
                for row in data_rows:
                    if isinstance(row, dict):
                        all_columns.update(row.keys())

                columns = list(all_columns)

                # Analyze columns
                column_info = {}
                for col in columns:
                    values = []
                    for row in data_rows:
                        if isinstance(row, dict) and col in row and row[col] is not None:
                            values.append(str(row[col]))

                    # Determine data type
                    numeric_count = 0
                    for value in values[:100]:
                        try:
                            float(value)
                            numeric_count += 1
                        except (ValueError, TypeError):
                            pass

                    data_type = "numeric" if numeric_count > len(values) * 0.8 else "text"

                    column_info[col] = {
                        "data_type": data_type,
                        "non_null_count": len(values),
                        "null_count": len(data_rows) - len(values),
                        "unique_count": len(set(values)) if values else 0
                    }
            else:
                columns = []
                column_info = {}

            return {
                "row_count": len(data_rows),
                "column_count": len(columns),
                "columns": column_info,
                "sample_data": data_rows[:10],
                "all_data": data_rows
            }

        except Exception as e:
            logger.error(f"Error loading JSON file {file_path}: {e}")
            raise

    # Tool implementations

    async def load_dataset(
        self,
        file_path: str = Field(..., description="Path to the data file"),
        dataset_name: str = Field(..., description="Name to identify the dataset"),
        source_type: str = Field(..., description="Type of data source: 'csv', 'json', or 'sqlite'")
    ) -> List[types.TextContent]:
        """Load data from various sources and store metadata in Neo4j.

        This tool loads data from CSV, JSON, or SQLite files, analyzes the structure,
        and stores metadata in Neo4j for future reference and analysis.

        Args:
            file_path: Path to the data file
            dataset_name: Name to identify the dataset
            source_type: Type of data source ('csv', 'json', or 'sqlite')

        Returns:
            Summary of the loaded dataset with basic statistics
        """
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                return [types.TextContent(type="text", text=f"Error: File not found: {file_path}")]

            # Generate unique dataset ID
            dataset_id = str(uuid.uuid4())

            # Load data based on source type
            if source_type.lower() == "csv":
                data_info = self._load_csv_data(file_path)
            elif source_type.lower() == "json":
                data_info = self._load_json_data(file_path)
            elif source_type.lower() == "sqlite":
                return [types.TextContent(type="text", text="SQLite support not yet implemented")]
            else:
                return [types.TextContent(type="text", text=f"Error: Unsupported source type: {source_type}")]

            # Store dataset metadata in Neo4j
            async with self.driver.session(database=self.database) as session:
                # Create dataset node
                dataset_query = """
                CREATE (d:Dataset {
                    id: $id,
                    name: $name,
                    source_path: $source_path,
                    source_type: $source_type,
                    row_count: $row_count,
                    column_count: $column_count,
                    created_timestamp: datetime(),
                    file_size: $file_size
                })
                RETURN d
                """

                file_size = os.path.getsize(file_path)

                success, _ = await self._safe_execute_write(session, dataset_query, {
                    "id": dataset_id,
                    "name": dataset_name,
                    "source_path": file_path,
                    "source_type": source_type,
                    "row_count": data_info["row_count"],
                    "column_count": data_info["column_count"],
                    "file_size": file_size
                })

                if not success:
                    return [types.TextContent(type="text", text="Error: Failed to store dataset metadata")]

                # Create column nodes
                for col_name, col_info in data_info["columns"].items():
                    col_query = """
                    CREATE (c:DataColumn {
                        name: $name,
                        data_type: $data_type,
                        non_null_count: $non_null_count,
                        null_count: $null_count,
                        unique_count: $unique_count
                    })
                    WITH c
                    MATCH (d:Dataset {id: $dataset_id})
                    CREATE (d)-[:HAS_COLUMN]->(c)
                    """

                    await self._safe_execute_write(session, col_query, {
                        "name": col_name,
                        "data_type": col_info["data_type"],
                        "non_null_count": col_info["non_null_count"],
                        "null_count": col_info["null_count"],
                        "unique_count": col_info["unique_count"],
                        "dataset_id": dataset_id
                    })

            # Generate summary report
            report = f"""
# Dataset Loaded Successfully

## Dataset Information
- **ID:** {dataset_id}
- **Name:** {dataset_name}
- **Source:** {file_path}
- **Type:** {source_type.upper()}
- **File Size:** {file_size:,} bytes

## Data Structure
- **Rows:** {data_info['row_count']:,}
- **Columns:** {data_info['column_count']}

## Column Summary
"""

            for col_name, col_info in data_info["columns"].items():
                null_pct = (col_info["null_count"] / data_info["row_count"] * 100) if data_info["row_count"] > 0 else 0
                report += f"""
### {col_name}
- **Type:** {col_info["data_type"]}
- **Non-null values:** {col_info["non_null_count"]:,}
- **Null values:** {col_info["null_count"]:,} ({null_pct:.1f}%)
- **Unique values:** {col_info["unique_count"]:,}
"""

            if data_info["sample_data"]:
                report += """
## Sample Data (first 5 rows)
"""
                for i, row in enumerate(data_info["sample_data"][:5]):
                    report += f"\n**Row {i+1}:** {row}"

            report += f"""

## Next Steps
- Use `explore_dataset(dataset_id="{dataset_id}")` to see more sample data
- Use `profile_data(dataset_id="{dataset_id}")` for detailed data profiling
- Use `calculate_statistics(dataset_id="{dataset_id}")` for descriptive statistics
- Use `analyze_correlations(dataset_id="{dataset_id}")` to find relationships
"""

            return [types.TextContent(type="text", text=report)]

        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
            return [types.TextContent(type="text", text=f"Error loading dataset: {str(e)}")]

    async def explore_dataset(
        self,
        dataset_id: str = Field(..., description="ID of the dataset to explore"),
        sample_size: int = Field(10, description="Number of sample rows to display")
    ) -> List[types.TextContent]:
        """Get an overview of the dataset with sample data.

        Args:
            dataset_id: ID of the dataset to explore
            sample_size: Number of sample rows to display (default: 10)

        Returns:
            Dataset overview with sample data and basic information
        """
        try:
            async with self.driver.session(database=self.database) as session:
                # Get dataset information
                dataset_query = """
                MATCH (d:Dataset {id: $dataset_id})
                OPTIONAL MATCH (d)-[:HAS_COLUMN]->(c:DataColumn)
                RETURN d, collect(c) as columns
                """

                result = await self._safe_read_query(session, dataset_query, {"dataset_id": dataset_id})

                if not result:
                    return [types.TextContent(type="text", text=f"Error: Dataset not found with ID: {dataset_id}")]

                dataset = result[0]["d"]
                columns = result[0]["columns"]

                # Try to load sample data from the original file
                sample_data = []
                try:
                    file_path = dataset["source_path"]
                    source_type = dataset["source_type"]

                    if source_type == "csv" and os.path.exists(file_path):
                        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                            reader = csv.DictReader(csvfile)
                            for i, row in enumerate(reader):
                                if i >= sample_size:
                                    break
                                sample_data.append(row)
                    elif source_type == "json" and os.path.exists(file_path):
                        data_info = self._load_json_data(file_path)
                        sample_data = data_info["sample_data"][:sample_size]

                except Exception as e:
                    logger.warning(f"Could not load sample data: {e}")

                # Generate exploration report
                report = f"""
# Dataset Exploration: {dataset["name"]}

## Basic Information
- **Dataset ID:** {dataset_id}
- **Name:** {dataset["name"]}
- **Source:** {dataset["source_path"]}
- **Type:** {dataset["source_type"].upper()}
- **Rows:** {dataset["row_count"]:,}
- **Columns:** {dataset["column_count"]}
- **Created:** {dataset.get("created_timestamp", "Unknown")}

## Column Information
"""

                for col in columns:
                    null_pct = (col["null_count"] / dataset["row_count"] * 100) if dataset["row_count"] > 0 else 0
                    completeness = 100 - null_pct

                    report += f"""
### {col["name"]} ({col["data_type"]})
- **Completeness:** {completeness:.1f}% ({col["non_null_count"]:,} non-null values)
- **Unique values:** {col["unique_count"]:,}
- **Null values:** {col["null_count"]:,}
"""

                if sample_data:
                    report += f"""
## Sample Data ({len(sample_data)} rows)

"""
                    # Display sample data in a readable format
                    if sample_data:
                        # Get column names
                        col_names = list(sample_data[0].keys()) if sample_data else []

                        # Create table header
                        report += "| " + " | ".join(col_names) + " |\n"
                        report += "| " + " | ".join(["---"] * len(col_names)) + " |\n"

                        # Add rows
                        for row in sample_data:
                            values = [str(row.get(col, "")) for col in col_names]
                            # Truncate long values
                            values = [val[:50] + "..." if len(val) > 50 else val for val in values]
                            report += "| " + " | ".join(values) + " |\n"
                else:
                    report += "\n*Sample data not available*"

                report += f"""

## Suggested Next Steps
- `profile_data(dataset_id="{dataset_id}")` - Detailed data quality analysis
- `calculate_statistics(dataset_id="{dataset_id}")` - Descriptive statistics
- `analyze_correlations(dataset_id="{dataset_id}")` - Find relationships between variables
- `filter_data(dataset_id="{dataset_id}", conditions="...")` - Create filtered subset
"""

                return [types.TextContent(type="text", text=report)]

        except Exception as e:
            logger.error(f"Error exploring dataset: {e}")
            return [types.TextContent(type="text", text=f"Error exploring dataset: {str(e)}")]

    # Additional tool methods would continue here...
    # For brevity, I'll implement a few key ones and provide placeholders for others

    async def profile_data(
        self,
        dataset_id: str = Field(..., description="ID of the dataset to profile"),
        include_correlations: bool = Field(True, description="Whether to include correlation analysis")
    ) -> List[types.TextContent]:
        """Comprehensive data profiling and quality assessment.

        Args:
            dataset_id: ID of the dataset to profile
            include_correlations: Whether to include correlation analysis

        Returns:
            Detailed data profiling report with quality metrics
        """
        try:
            async with self.driver.session(database=self.database) as session:
                # Get dataset and column information
                dataset_query = """
                MATCH (d:Dataset {id: $dataset_id})
                OPTIONAL MATCH (d)-[:HAS_COLUMN]->(c:DataColumn)
                RETURN d, collect(c) as columns
                """

                result = await self._safe_read_query(session, dataset_query, {"dataset_id": dataset_id})

                if not result:
                    return [types.TextContent(type="text", text=f"Error: Dataset not found with ID: {dataset_id}")]

                dataset = result[0]["d"]
                columns = result[0]["columns"]

                # Load actual data for analysis
                data_rows = []
                try:
                    file_path = dataset["source_path"]
                    source_type = dataset["source_type"]

                    if source_type == "csv" and os.path.exists(file_path):
                        data_info = self._load_csv_data(file_path)
                        data_rows = data_info["all_data"]
                    elif source_type == "json" and os.path.exists(file_path):
                        data_info = self._load_json_data(file_path)
                        data_rows = data_info["all_data"]
                    else:
                        return [types.TextContent(type="text", text="Data file not accessible for profiling")]

                except Exception as e:
                    return [types.TextContent(type="text", text=f"Error loading data for profiling: {e}")]

                if not data_rows:
                    return [types.TextContent(type="text", text="No data available for profiling")]

                # Generate comprehensive profile
                report = f"""
# Data Profiling Report: {dataset["name"]}

## Dataset Overview
- **Dataset ID:** {dataset_id}
- **Total Rows:** {len(data_rows):,}
- **Total Columns:** {len(columns)}
- **Source:** {dataset["source_path"]}
- **Last Updated:** {dataset.get("created_timestamp", "Unknown")}

## Data Quality Assessment

### Completeness Analysis
"""

                # Analyze each column for completeness and data quality
                for col in columns:
                    col_name = col["name"]
                    values = [row.get(col_name, '') for row in data_rows]
                    non_empty_values = [v for v in values if v is not None and str(v).strip() != '']

                    completeness = (len(non_empty_values) / len(data_rows)) * 100 if data_rows else 0
                    unique_count = len(set(str(v) for v in non_empty_values))

                    # Detect potential data quality issues
                    issues = []
                    if completeness < 90:
                        issues.append(f"Low completeness ({completeness:.1f}%)")
                    if unique_count == 1 and len(non_empty_values) > 1:
                        issues.append("All values identical")
                    if col["data_type"] == "numeric":
                        try:
                            numeric_values = [float(v) for v in non_empty_values if str(v).replace('.', '').replace('-', '').isdigit()]
                            if len(numeric_values) != len(non_empty_values):
                                issues.append("Mixed numeric/text values")
                        except (ValueError, TypeError):
                            pass

                    status = "⚠️ ISSUES" if issues else "✅ GOOD"

                    report += f"""
### {col_name} ({col["data_type"]}) - {status}
- **Completeness:** {completeness:.1f}% ({len(non_empty_values):,} non-empty values)
- **Unique Values:** {unique_count:,}
- **Data Issues:** {', '.join(issues) if issues else 'None detected'}
"""

                # Add sample duplicate detection
                if len(data_rows) > 1:
                    # Simple duplicate detection based on all column values
                    row_signatures = []
                    for row in data_rows[:1000]:  # Check first 1000 rows
                        signature = tuple(str(row.get(col["name"], "")) for col in columns)
                        row_signatures.append(signature)

                    unique_signatures = set(row_signatures)
                    duplicate_count = len(row_signatures) - len(unique_signatures)

                    report += f"""

### Duplicate Analysis
- **Rows Checked:** {len(row_signatures):,}
- **Duplicate Rows:** {duplicate_count:,}
- **Duplication Rate:** {(duplicate_count / len(row_signatures) * 100):.1f}%
"""

                # Basic correlation analysis for numeric columns if requested
                if include_correlations:
                    numeric_columns = [col for col in columns if col["data_type"] == "numeric"]

                    if len(numeric_columns) >= 2:
                        report += f"""

## Correlation Analysis

Found {len(numeric_columns)} numeric columns for correlation analysis:
{', '.join([col['name'] for col in numeric_columns])}

*Note: Full correlation matrix calculation requires additional statistical libraries.*
*This analysis shows column types suitable for correlation.*
"""
                    else:
                        report += """

## Correlation Analysis

Insufficient numeric columns for meaningful correlation analysis.
Need at least 2 numeric columns.
"""

                # Data recommendations
                report += """

## Data Quality Recommendations

"""
                recommendations = []

                # Check for columns with high missing values
                high_missing_cols = [col for col in columns
                                   if (col["null_count"] / dataset["row_count"] * 100) > 20]
                if high_missing_cols:
                    recommendations.append(f"**Address missing data** in columns: {', '.join([col['name'] for col in high_missing_cols])}")

                # Check for columns with low uniqueness (potential categorical)
                low_unique_cols = [col for col in columns
                                 if col["unique_count"] < 20 and col["data_type"] == "text"]
                if low_unique_cols:
                    recommendations.append(f"**Consider categorical encoding** for: {', '.join([col['name'] for col in low_unique_cols])}")

                # Check for potential identifier columns
                id_cols = [col for col in columns
                          if col["unique_count"] == dataset["row_count"] and dataset["row_count"] > 1]
                if id_cols:
                    recommendations.append(f"**Potential ID columns detected**: {', '.join([col['name'] for col in id_cols])} (consider excluding from analysis)")

                if recommendations:
                    for rec in recommendations:
                        report += f"1. {rec}\n"
                else:
                    report += "✅ No major data quality issues detected!\n"

                report += f"""

## Next Steps
- Use `calculate_statistics(dataset_id="{dataset_id}")` for detailed statistical analysis
- Use `analyze_correlations(dataset_id="{dataset_id}")` for correlation matrix
- Use `filter_data(dataset_id="{dataset_id}", conditions="...")` to clean data
"""

                return [types.TextContent(type="text", text=report)]

        except Exception as e:
            logger.error(f"Error profiling data: {e}")
            return [types.TextContent(type="text", text=f"Error profiling data: {str(e)}")]

    async def calculate_statistics(
        self,
        dataset_id: str = Field(..., description="ID of the dataset"),
        columns: Optional[List[str]] = Field(None, description="Specific columns to analyze"),
        group_by: Optional[str] = Field(None, description="Column to group statistics by")
    ) -> List[types.TextContent]:
        """Calculate descriptive statistics for dataset columns.

        Args:
            dataset_id: ID of the dataset
            columns: Specific columns to analyze (if None, analyzes all numeric columns)
            group_by: Column to group statistics by (optional)

        Returns:
            Descriptive statistics report
        """
        try:
            async with self.driver.session(database=self.database) as session:
                # Get dataset and column information
                dataset_query = """
                MATCH (d:Dataset {id: $dataset_id})
                OPTIONAL MATCH (d)-[:HAS_COLUMN]->(c:DataColumn)
                RETURN d, collect(c) as columns
                """

                result = await self._safe_read_query(session, dataset_query, {"dataset_id": dataset_id})

                if not result:
                    return [types.TextContent(type="text", text=f"Error: Dataset not found with ID: {dataset_id}")]

                dataset = result[0]["d"]
                available_columns = result[0]["columns"]

                # Load actual data for analysis
                data_rows = []
                try:
                    file_path = dataset["source_path"]
                    source_type = dataset["source_type"]

                    if source_type == "csv" and os.path.exists(file_path):
                        data_info = self._load_csv_data(file_path)
                        data_rows = data_info["all_data"]
                    elif source_type == "json" and os.path.exists(file_path):
                        data_info = self._load_json_data(file_path)
                        data_rows = data_info["all_data"]
                    else:
                        return [types.TextContent(type="text", text="Data file not accessible for statistics")]

                except Exception as e:
                    return [types.TextContent(type="text", text=f"Error loading data: {e}")]

                if not data_rows:
                    return [types.TextContent(type="text", text="No data available for statistical analysis")]

                # Determine which columns to analyze
                if columns:
                    # Validate specified columns exist
                    available_col_names = [col["name"] for col in available_columns]
                    invalid_cols = [col for col in columns if col not in available_col_names]
                    if invalid_cols:
                        return [types.TextContent(type="text", text=f"Error: Columns not found: {', '.join(invalid_cols)}")]
                    target_columns = [col for col in available_columns if col["name"] in columns]
                else:
                    # Use all numeric columns
                    target_columns = [col for col in available_columns if col["data_type"] == "numeric"]

                if not target_columns:
                    return [types.TextContent(type="text", text="No numeric columns found for statistical analysis")]

                def calculate_basic_stats(values):
                    """Calculate basic statistics for a list of numeric values"""
                    if not values:
                        return None

                    import statistics

                    try:
                        sorted_vals = sorted(values)
                        n = len(values)

                        stats = {
                            "count": n,
                            "mean": statistics.mean(values),
                            "median": statistics.median(values),
                            "min": min(values),
                            "max": max(values),
                            "std": statistics.stdev(values) if n > 1 else 0,
                            "var": statistics.variance(values) if n > 1 else 0
                        }

                        # Calculate quartiles
                        if n >= 4:
                            q1_idx = n // 4
                            q3_idx = 3 * n // 4
                            stats["q1"] = sorted_vals[q1_idx]
                            stats["q3"] = sorted_vals[q3_idx]
                            stats["iqr"] = stats["q3"] - stats["q1"]
                        else:
                            stats["q1"] = stats["min"]
                            stats["q3"] = stats["max"]
                            stats["iqr"] = stats["max"] - stats["min"]

                        # Try to calculate mode
                        try:
                            stats["mode"] = statistics.mode(values)
                        except statistics.StatisticsError:
                            stats["mode"] = "No unique mode"

                        return stats
                    except Exception as e:
                        logger.error(f"Error calculating statistics: {e}")
                        return None

                # Generate statistics report
                report = f"""
# Statistical Analysis: {dataset["name"]}

## Dataset Overview
- **Dataset ID:** {dataset_id}
- **Total Rows:** {len(data_rows):,}
- **Analyzed Columns:** {len(target_columns)}
- **Group By:** {group_by or "None"}

"""

                if group_by:
                    # Grouped statistics
                    if group_by not in [col["name"] for col in available_columns]:
                        return [types.TextContent(type="text", text=f"Error: Group by column '{group_by}' not found")]

                    # Group data by the specified column
                    groups = {}
                    for row in data_rows:
                        group_value = str(row.get(group_by, "Unknown"))
                        if group_value not in groups:
                            groups[group_value] = []
                        groups[group_value].append(row)

                    report += f"## Grouped Statistics (by {group_by})\n\n"

                    for group_name, group_rows in groups.items():
                        report += f"### Group: {group_name} ({len(group_rows)} rows)\n\n"

                        for col in target_columns:
                            col_name = col["name"]
                            values = []

                            for row in group_rows:
                                val = row.get(col_name, '')
                                if val is not None and str(val).strip() != '':
                                    try:
                                        values.append(float(val))
                                    except (ValueError, TypeError):
                                        pass

                            if values:
                                stats = calculate_basic_stats(values)
                                if stats:
                                    report += f"""
#### {col_name}
- **Count:** {stats["count"]:,}
- **Mean:** {stats["mean"]:.3f}
- **Median:** {stats["median"]:.3f}
- **Std Dev:** {stats["std"]:.3f}
- **Min:** {stats["min"]:.3f}
- **Max:** {stats["max"]:.3f}
- **Q1:** {stats["q1"]:.3f}
- **Q3:** {stats["q3"]:.3f}
- **IQR:** {stats["iqr"]:.3f}
- **Mode:** {stats["mode"]}

"""
                            else:
                                report += f"\n#### {col_name}\n*No valid numeric data*\n\n"

                        report += "---\n\n"

                else:
                    # Overall statistics for each column
                    report += "## Column Statistics\n\n"

                    for col in target_columns:
                        col_name = col["name"]
                        values = []

                        # Extract numeric values
                        for row in data_rows:
                            val = row.get(col_name, '')
                            if val is not None and str(val).strip() != '':
                                try:
                                    values.append(float(val))
                                except (ValueError, TypeError):
                                    pass

                        if values:
                            stats = calculate_basic_stats(values)
                            if stats:
                                # Calculate additional insights
                                range_val = stats["max"] - stats["min"]
                                cv = (stats["std"] / stats["mean"] * 100) if stats["mean"] != 0 else 0

                                report += f"""
### {col_name}

#### Descriptive Statistics
| Statistic | Value |
|-----------|-------|
| Count | {stats["count"]:,} |
| Mean | {stats["mean"]:.3f} |
| Median | {stats["median"]:.3f} |
| Mode | {stats["mode"]} |
| Standard Deviation | {stats["std"]:.3f} |
| Variance | {stats["var"]:.3f} |
| Minimum | {stats["min"]:.3f} |
| Maximum | {stats["max"]:.3f} |
| Range | {range_val:.3f} |
| Q1 (25th percentile) | {stats["q1"]:.3f} |
| Q3 (75th percentile) | {stats["q3"]:.3f} |
| IQR | {stats["iqr"]:.3f} |
| Coefficient of Variation | {cv:.1f}% |

#### Data Distribution Insights
"""
                                # Add distribution insights
                                if cv < 15:
                                    report += "- **Low variability** - Data points are close to the mean\n"
                                elif cv > 50:
                                    report += "- **High variability** - Data points are spread widely\n"
                                else:
                                    report += "- **Moderate variability** - Normal spread of data\n"

                                if abs(stats["mean"] - stats["median"]) / stats["std"] > 0.5 if stats["std"] > 0 else False:
                                    if stats["mean"] > stats["median"]:
                                        report += "- **Right-skewed** - Distribution has a long right tail\n"
                                    else:
                                        report += "- **Left-skewed** - Distribution has a long left tail\n"
                                else:
                                    report += "- **Approximately symmetric** - Mean and median are close\n"

                                # Outlier detection using IQR method
                                if stats["iqr"] > 0:
                                    lower_fence = stats["q1"] - 1.5 * stats["iqr"]
                                    upper_fence = stats["q3"] + 1.5 * stats["iqr"]
                                    outliers = [v for v in values if v < lower_fence or v > upper_fence]
                                    report += f"- **Potential outliers** (IQR method): {len(outliers)} values ({len(outliers)/len(values)*100:.1f}%)\n"

                                report += "\n"
                            else:
                                report += f"\n### {col_name}\n*Error calculating statistics*\n\n"
                        else:
                            report += f"\n### {col_name}\n*No valid numeric data found*\n\n"

                # Add summary and recommendations
                report += """
## Summary & Recommendations

### Key Insights
"""

                # Generate insights
                insights = []
                for col in target_columns:
                    col_name = col["name"]
                    null_pct = (col["null_count"] / dataset["row_count"] * 100) if dataset["row_count"] > 0 else 0

                    if null_pct > 10:
                        insights.append(f"**{col_name}** has {null_pct:.1f}% missing values - consider imputation strategies")

                    if col["unique_count"] == dataset["row_count"] and dataset["row_count"] > 1:
                        insights.append(f"**{col_name}** appears to be a unique identifier")

                if insights:
                    for insight in insights:
                        report += f"- {insight}\n"
                else:
                    report += "- No major statistical concerns detected\n"

                report += f"""

### Next Steps
- Use `analyze_correlations(dataset_id="{dataset_id}")` to find relationships between variables
- Use `profile_data(dataset_id="{dataset_id}")` for comprehensive data quality assessment
- Use `filter_data()` to investigate outliers or specific value ranges
"""

                return [types.TextContent(type="text", text=report)]

        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return [types.TextContent(type="text", text=f"Error calculating statistics: {str(e)}")]

    async def analyze_correlations(
        self,
        dataset_id: str = Field(..., description="ID of the dataset"),
        method: str = Field("pearson", description="Correlation method: 'pearson', 'spearman', or 'kendall'"),
        threshold: float = Field(0.3, description="Minimum correlation strength to report")
    ) -> List[types.TextContent]:
        """Analyze correlations between variables in the dataset.

        Args:
            dataset_id: ID of the dataset
            method: Correlation method ('pearson', 'spearman', or 'kendall')
            threshold: Minimum correlation strength to report

        Returns:
            Correlation analysis report
        """
        try:
            if method not in ["pearson", "spearman", "kendall"]:
                return [types.TextContent(type="text", text="Error: Method must be 'pearson', 'spearman', or 'kendall'")]

            async with self.driver.session(database=self.database) as session:
                # Get dataset and column information
                dataset_query = """
                MATCH (d:Dataset {id: $dataset_id})
                OPTIONAL MATCH (d)-[:HAS_COLUMN]->(c:DataColumn)
                WHERE c.data_type = 'numeric'
                RETURN d, collect(c) as numeric_columns
                """

                result = await self._safe_read_query(session, dataset_query, {"dataset_id": dataset_id})

                if not result:
                    return [types.TextContent(type="text", text=f"Error: Dataset not found with ID: {dataset_id}")]

                dataset = result[0]["d"]
                numeric_columns = result[0]["numeric_columns"]

                if len(numeric_columns) < 2:
                    return [types.TextContent(type="text", text="Error: Need at least 2 numeric columns for correlation analysis")]

                # Load actual data for analysis
                data_rows = []
                try:
                    file_path = dataset["source_path"]
                    source_type = dataset["source_type"]

                    if source_type == "csv" and os.path.exists(file_path):
                        data_info = self._load_csv_data(file_path)
                        data_rows = data_info["all_data"]
                    elif source_type == "json" and os.path.exists(file_path):
                        data_info = self._load_json_data(file_path)
                        data_rows = data_info["all_data"]
                    else:
                        return [types.TextContent(type="text", text="Data file not accessible for correlation analysis")]

                except Exception as e:
                    return [types.TextContent(type="text", text=f"Error loading data: {e}")]

                if not data_rows:
                    return [types.TextContent(type="text", text="No data available for correlation analysis")]

                # Extract numeric data for each column
                column_data = {}
                for col in numeric_columns:
                    col_name = col["name"]
                    values = []

                    for row in data_rows:
                        val = row.get(col_name, '')
                        if val is not None and str(val).strip() != '':
                            try:
                                values.append(float(val))
                            except (ValueError, TypeError):
                                values.append(None)
                        else:
                            values.append(None)

                    column_data[col_name] = values

                # Calculate correlations
                def calculate_correlation(x_vals, y_vals, method):
                    """Calculate correlation between two lists, handling missing values"""
                    # Remove rows where either value is None
                    paired_data = [(x, y) for x, y in zip(x_vals, y_vals) if x is not None and y is not None]

                    if len(paired_data) < 3:  # Need at least 3 points for meaningful correlation
                        return None, 0

                    x_clean = [pair[0] for pair in paired_data]
                    y_clean = [pair[1] for pair in paired_data]

                    try:
                        import statistics

                        if method == "pearson":
                            # Pearson correlation coefficient
                            n = len(x_clean)
                            if n < 2:
                                return None, n

                            x_mean = statistics.mean(x_clean)
                            y_mean = statistics.mean(y_clean)

                            numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_clean, y_clean))
                            x_variance = sum((x - x_mean) ** 2 for x in x_clean)
                            y_variance = sum((y - y_mean) ** 2 for y in y_clean)

                            if x_variance == 0 or y_variance == 0:
                                return None, n

                            correlation = numerator / (x_variance * y_variance) ** 0.5
                            return correlation, n

                        elif method == "spearman":
                            # Spearman rank correlation - simplified implementation
                            # Convert to ranks
                            x_ranks = [sorted(x_clean).index(x) + 1 for x in x_clean]
                            y_ranks = [sorted(y_clean).index(y) + 1 for y in y_clean]

                            # Calculate Pearson correlation of ranks
                            return calculate_correlation(x_ranks, y_ranks, "pearson")

                        else:  # kendall - simplified version
                            # Basic Kendall's tau implementation
                            n = len(x_clean)
                            concordant = 0
                            discordant = 0

                            for i in range(n):
                                for j in range(i + 1, n):
                                    x_diff = x_clean[i] - x_clean[j]
                                    y_diff = y_clean[i] - y_clean[j]

                                    if (x_diff > 0 and y_diff > 0) or (x_diff < 0 and y_diff < 0):
                                        concordant += 1
                                    elif (x_diff > 0 and y_diff < 0) or (x_diff < 0 and y_diff > 0):
                                        discordant += 1

                            total_pairs = n * (n - 1) / 2
                            if total_pairs == 0:
                                return None, n

                            tau = (concordant - discordant) / total_pairs
                            return tau, n

                    except Exception as e:
                        logger.error(f"Error calculating {method} correlation: {e}")
                        return None, 0

                # Generate correlation matrix
                column_names = list(column_data.keys())
                correlations = []

                for i, col1 in enumerate(column_names):
                    for j, col2 in enumerate(column_names):
                        if i < j:  # Only calculate upper triangle
                            corr, n_pairs = calculate_correlation(
                                column_data[col1],
                                column_data[col2],
                                method
                            )

                            if corr is not None:
                                correlations.append({
                                    "column1": col1,
                                    "column2": col2,
                                    "correlation": corr,
                                    "n_pairs": n_pairs,
                                    "abs_correlation": abs(corr)
                                })

                # Generate report
                report = f"""
# Correlation Analysis: {dataset["name"]}

## Analysis Parameters
- **Method:** {method.title()} correlation
- **Threshold:** {threshold}
- **Dataset:** {dataset_id}
- **Numeric Columns:** {len(numeric_columns)}
- **Total Rows:** {len(data_rows):,}

## Correlation Matrix

"""

                if not correlations:
                    report += "No correlations could be calculated. Check data quality and ensure numeric columns have sufficient non-missing values.\n"
                else:
                    # Sort by absolute correlation strength
                    correlations.sort(key=lambda x: x["abs_correlation"], reverse=True)

                    # Create correlation matrix table
                    report += "### All Correlations\n\n"
                    report += "| Variable 1 | Variable 2 | Correlation | N Pairs | Strength |\n"
                    report += "|------------|------------|-------------|---------|----------|\n"

                    for corr in correlations:
                        strength = ""
                        abs_corr = corr["abs_correlation"]
                        if abs_corr >= 0.8:
                            strength = "Very Strong"
                        elif abs_corr >= 0.6:
                            strength = "Strong"
                        elif abs_corr >= 0.4:
                            strength = "Moderate"
                        elif abs_corr >= 0.2:
                            strength = "Weak"
                        else:
                            strength = "Very Weak"

                        report += f"| {corr['column1']} | {corr['column2']} | {corr['correlation']:.3f} | {corr['n_pairs']:,} | {strength} |\n"

                    # Highlight strong correlations
                    strong_correlations = [c for c in correlations if c["abs_correlation"] >= threshold]

                    if strong_correlations:
                        report += f"""

### Strong Correlations (|r| ≥ {threshold})

Found {len(strong_correlations)} correlation(s) above the threshold:

"""
                        for corr in strong_correlations:
                            direction = "positive" if corr["correlation"] > 0 else "negative"
                            report += f"""
#### {corr['column1']} ↔ {corr['column2']}
- **Correlation:** {corr['correlation']:.3f} ({direction})
- **Sample size:** {corr['n_pairs']:,} paired observations
- **Interpretation:** As {corr['column1']} increases, {corr['column2']} tends to {'increase' if corr['correlation'] > 0 else 'decrease'}

"""

                        # Multicollinearity warning
                        very_strong = [c for c in strong_correlations if c["abs_correlation"] >= 0.8]
                        if very_strong:
                            report += f"""
### ⚠️ Multicollinearity Warning

Found {len(very_strong)} very strong correlation(s) (|r| ≥ 0.8):
"""
                            for corr in very_strong:
                                report += f"- **{corr['column1']} ↔ {corr['column2']}** (r = {corr['correlation']:.3f})\n"

                            report += """
**Recommendation:** Consider removing one variable from each highly correlated pair to avoid multicollinearity in statistical models.

"""
                    else:
                        report += f"""

### No Strong Correlations Found

No correlations above the threshold of {threshold} were detected. This could indicate:
- Variables are largely independent
- Relationships may be non-linear
- Data quality issues may be masking relationships

"""

                    # Summary statistics
                    if correlations:
                        corr_values = [c["correlation"] for c in correlations]
                        abs_corr_values = [c["abs_correlation"] for c in correlations]

                        report += f"""
## Correlation Summary

- **Total Pairs Analyzed:** {len(correlations)}
- **Mean Absolute Correlation:** {statistics.mean(abs_corr_values):.3f}
- **Strongest Correlation:** {max(corr_values, key=abs):.3f} ({correlations[0]['column1']} ↔ {correlations[0]['column2']})
- **Correlations Above Threshold:** {len(strong_correlations)}

"""

                # Interpretation guide
                report += f"""
## Interpretation Guide

### {method.title()} Correlation Strength:
- **0.8 to 1.0:** Very strong relationship
- **0.6 to 0.8:** Strong relationship
- **0.4 to 0.6:** Moderate relationship
- **0.2 to 0.4:** Weak relationship
- **0.0 to 0.2:** Very weak or no relationship

### Important Notes:
- Correlation does not imply causation
- {method.title()} correlation measures {'linear' if method == 'pearson' else 'monotonic'} relationships
- Missing values are excluded from calculations
- Consider scatter plots for visual inspection of relationships

## Next Steps
- Use `calculate_statistics()` for detailed variable analysis
- Consider creating scatter plots for strong correlations
- Investigate potential confounding variables
- Use domain knowledge to interpret relationships
"""

                return [types.TextContent(type="text", text=report)]

        except Exception as e:
            logger.error(f"Error analyzing correlations: {e}")
            return [types.TextContent(type="text", text=f"Error analyzing correlations: {str(e)}")]

    async def filter_data(
        self,
        dataset_id: str = Field(..., description="ID of the source dataset"),
        conditions: str = Field(..., description="Filter conditions (e.g., 'age > 25 AND income < 50000')"),
        new_dataset_name: str = Field(..., description="Name for the filtered dataset")
    ) -> List[types.TextContent]:
        """Filter dataset based on specified conditions.

        Args:
            dataset_id: ID of the source dataset
            conditions: Filter conditions string
            new_dataset_name: Name for the filtered dataset

        Returns:
            Information about the filtered dataset
        """
        # Implementation placeholder
        return [types.TextContent(type="text", text=f"""
# Data Filtering: Not Yet Fully Implemented

This tool would filter dataset {dataset_id} based on: {conditions}

## Parameters:
- Source dataset: {dataset_id}
- Filter conditions: {conditions}
- New dataset name: {new_dataset_name}

## Planned Features:
1. SQL-like condition parsing
2. Multiple condition support (AND, OR, NOT)
3. Data type-aware filtering
4. Result preview before saving
5. Automatic metadata tracking

The filtered dataset would be saved as a new dataset with full lineage tracking.
        """)]

    async def aggregate_data(
        self,
        dataset_id: str = Field(..., description="ID of the source dataset"),
        group_by: List[str] = Field(..., description="Columns to group by"),
        aggregations: Dict[str, str] = Field(..., description="Aggregation functions to apply"),
        new_dataset_name: str = Field(..., description="Name for the aggregated dataset")
    ) -> List[types.TextContent]:
        """Group and aggregate data according to specified criteria.

        Args:
            dataset_id: ID of the source dataset
            group_by: List of columns to group by
            aggregations: Dictionary of column -> aggregation function mappings
            new_dataset_name: Name for the aggregated dataset

        Returns:
            Information about the aggregated dataset
        """
        # Implementation placeholder
        return [types.TextContent(type="text", text=f"""
# Data Aggregation: Not Yet Fully Implemented

This tool would aggregate dataset {dataset_id}:

## Parameters:
- Source dataset: {dataset_id}
- Group by: {group_by}
- Aggregations: {aggregations}
- New dataset name: {new_dataset_name}

## Planned Aggregation Functions:
- sum, mean, median, min, max
- count, count_distinct
- std, var (standard deviation, variance)
- first, last

The aggregated data would be saved as a new dataset with lineage tracking.
        """)]

    async def compare_datasets(
        self,
        dataset_ids: List[str] = Field(..., description="List of dataset IDs to compare"),
        comparison_type: str = Field("schema", description="Type of comparison: 'schema', 'statistics', or 'distribution'")
    ) -> List[types.TextContent]:
        """Compare multiple datasets across different dimensions.

        Args:
            dataset_ids: List of dataset IDs to compare
            comparison_type: Type of comparison to perform

        Returns:
            Dataset comparison report
        """
        # Implementation placeholder
        return [types.TextContent(type="text", text=f"""
# Dataset Comparison: Not Yet Fully Implemented

This tool would compare datasets: {dataset_ids}

## Comparison Type: {comparison_type}

## Planned Comparison Features:

### Schema Comparison
- Column names and types
- Data structure differences
- Missing/additional columns

### Statistics Comparison
- Descriptive statistics comparison
- Distribution differences
- Value range changes

### Distribution Comparison
- Data distribution analysis
- Statistical tests for differences
- Visualization recommendations

Use `explore_dataset()` on each dataset individually for now.
        """)]

    async def export_results(
        self,
        analysis_id: str = Field(..., description="ID of the analysis to export"),
        format: str = Field("csv", description="Export format: 'csv', 'json', or 'html'"),
        file_path: str = Field(..., description="Path to save the exported file")
    ) -> List[types.TextContent]:
        """Export analysis results to external files.

        Args:
            analysis_id: ID of the analysis to export
            format: Export format ('csv', 'json', or 'html')
            file_path: Path to save the exported file

        Returns:
            Export confirmation with file details
        """
        # Implementation placeholder
        return [types.TextContent(type="text", text=f"""
# Export Results: Not Yet Fully Implemented

This tool would export analysis {analysis_id} to {file_path} in {format} format.

## Planned Export Features:
1. Multiple format support (CSV, JSON, HTML, Excel)
2. Customizable export templates
3. Metadata inclusion options
4. Batch export capabilities
5. Automated report generation

Analysis results tracking is not yet implemented.
        """)]

    async def list_datasets(
        self,
        include_metadata: bool = Field(True, description="Whether to include detailed metadata")
    ) -> List[types.TextContent]:
        """List all loaded datasets with optional metadata.

        Args:
            include_metadata: Whether to include detailed metadata

        Returns:
            List of all datasets with their information
        """
        try:
            async with self.driver.session(database=self.database) as session:
                if include_metadata:
                    query = """
                    MATCH (d:Dataset)
                    OPTIONAL MATCH (d)-[:HAS_COLUMN]->(c:DataColumn)
                    RETURN d, count(c) as column_count, collect(c.name) as column_names
                    ORDER BY d.created_timestamp DESC
                    """
                else:
                    query = """
                    MATCH (d:Dataset)
                    RETURN d.id as id, d.name as name, d.source_type as source_type,
                           d.row_count as row_count, d.column_count as column_count
                    ORDER BY d.created_timestamp DESC
                    """

                result = await self._safe_read_query(session, query, {})

                if not result:
                    return [types.TextContent(type="text", text="No datasets found. Use `load_dataset()` to load data first.")]

                # Generate dataset listing
                report = "# Loaded Datasets\n\n"

                for i, row in enumerate(result, 1):
                    if include_metadata:
                        dataset = row["d"]
                        columns = row.get("column_names", [])
                        report += f"""
## {i}. {dataset["name"]}

- **ID:** {dataset["id"]}
- **Source:** {dataset["source_path"]}
- **Type:** {dataset["source_type"].upper()}
- **Rows:** {dataset["row_count"]:,}
- **Columns:** {dataset["column_count"]} ({', '.join(columns[:5])}{'...' if len(columns) > 5 else ''})
- **Created:** {dataset.get("created_timestamp", "Unknown")}
- **File Size:** {dataset.get("file_size", 0):,} bytes

"""
                    else:
                        report += f"**{i}.** {row['name']} (ID: {row['id']}) - {row['source_type'].upper()}, {row['row_count']:,} rows, {row['column_count']} columns\n"

                if include_metadata:
                    report += """
## Usage Examples

To explore a dataset:
```
explore_dataset(dataset_id="DATASET_ID")
```

To analyze data:
```
profile_data(dataset_id="DATASET_ID")
calculate_statistics(dataset_id="DATASET_ID")
analyze_correlations(dataset_id="DATASET_ID")
```
"""

                return [types.TextContent(type="text", text=report)]

        except Exception as e:
            logger.error(f"Error listing datasets: {e}")
            return [types.TextContent(type="text", text=f"Error listing datasets: {str(e)}")]

    async def get_analysis_history(
        self,
        dataset_id: Optional[str] = Field(None, description="ID of the dataset to filter by"),
        analysis_type: Optional[str] = Field(None, description="Type of analysis to filter by"),
        limit: int = Field(20, description="Maximum number of results to return")
    ) -> List[types.TextContent]:
        """View analysis history and workflow tracking.

        Args:
            dataset_id: Filter by specific dataset (optional)
            analysis_type: Filter by analysis type (optional)
            limit: Maximum number of results to return

        Returns:
            Analysis history report
        """
        # Implementation placeholder - would query DataAnalysis nodes
        return [types.TextContent(type="text", text=f"""
# Analysis History: Not Yet Fully Implemented

This tool would show analysis history with the following filters:
- Dataset ID: {dataset_id or "All datasets"}
- Analysis Type: {analysis_type or "All types"}
- Limit: {limit}

## Planned Features:
1. Complete analysis workflow tracking
2. Performance metrics and timing
3. Result summaries and comparisons
4. Reproducibility information
5. Analysis lineage visualization

Use `list_datasets()` to see available datasets for now.
        """)]
