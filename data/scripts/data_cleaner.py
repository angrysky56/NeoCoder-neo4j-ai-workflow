#!/usr/bin/env python3
"""
Data Cleaning and Validation Pipeline for NeoCoder Data Analysis

This script provides comprehensive data cleaning, validation, and standardization
capabilities for datasets before analysis.

Author: NeoCoder Data Analysis Team
Created: 2025
"""

import os
import sys
import csv
import argparse
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import statistics

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_cleaning.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataCleaner:
    """
    Comprehensive data cleaning and validation utility.

    Features:
    - Missing value handling
    - Data type standardization
    - Outlier detection and treatment
    - Column name standardization
    - Data validation and quality scoring
    """

    def __init__(self, input_file: str, output_file: Optional[str] = None):
        """
        Initialize the data cleaner.

        Args:
            input_file: Path to input CSV file
            output_file: Path to output cleaned file (optional)
        """
        self.input_file = Path(input_file)
        self.output_file = Path(output_file) if output_file else self.input_file.parent / f"{self.input_file.stem}_cleaned.csv"

        # Cleaning statistics
        self.stats = {
            'original_rows': 0,
            'cleaned_rows': 0,
            'removed_rows': 0,
            'missing_values_filled': 0,
            'outliers_detected': 0,
            'columns_renamed': 0,
            'data_types_standardized': 0
        }

        # Configuration
        self.config = {
            'remove_empty_rows': True,
            'standardize_column_names': True,
            'handle_missing_values': True,
            'detect_outliers': True,
            'standardize_data_types': True,
            'remove_duplicates': True,
            'missing_value_threshold': 0.5,  # Remove columns with >50% missing
            'outlier_method': 'iqr'  # or 'zscore'
        }

        logger.info("DataCleaner initialized")
        logger.info(f"Input file: {self.input_file}")
        logger.info(f"Output file: {self.output_file}")

    def standardize_column_name(self, col_name: str) -> str:
        """
        Standardize column name to snake_case.

        Args:
            col_name: Original column name

        Returns:
            Standardized column name
        """
        # Remove special characters and convert to lowercase
        clean_name = re.sub(r'[^\w\s]', '', str(col_name).strip())

        # Replace spaces and multiple underscores with single underscore
        clean_name = re.sub(r'[\s_]+', '_', clean_name)

        # Convert to lowercase
        clean_name = clean_name.lower()

        # Remove leading/trailing underscores
        clean_name = clean_name.strip('_')

        # Ensure name starts with letter or underscore
        if clean_name and clean_name[0].isdigit():
            clean_name = f"col_{clean_name}"

        # Handle empty names
        if not clean_name:
            clean_name = "unnamed_column"

        return clean_name

    def detect_data_type(self, values: List[str]) -> Dict[str, Any]:
        """
        Detect the most appropriate data type for a column.

        Args:
            values: List of string values

        Returns:
            Dictionary with type information
        """
        if not values:
            return {'type': 'empty', 'confidence': 1.0}

        # Clean values (remove None and empty strings)
        clean_values = [str(v).strip() for v in values if v is not None and str(v).strip()]

        if not clean_values:
            return {'type': 'empty', 'confidence': 1.0}

        total_count = len(clean_values)

        # Type detection counters
        numeric_count = 0
        integer_count = 0
        date_count = 0
        boolean_count = 0

        # Boolean values
        boolean_values = {
            'true', 'false', 'yes', 'no', 'y', 'n', '1', '0',
            'on', 'off', 'enabled', 'disabled'
        }

        # Date patterns
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',          # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',          # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',          # MM-DD-YYYY
        ]

        for value in clean_values:
            value_lower = value.lower().strip()

            # Check boolean
            if value_lower in boolean_values:
                boolean_count += 1
                continue

            # Check numeric
            try:
                float(value)
                numeric_count += 1

                # Check if integer
                if float(value).is_integer():
                    integer_count += 1

                continue
            except ValueError:
                pass

            # Check date
            for pattern in date_patterns:
                if re.match(pattern, value):
                    date_count += 1
                    break

        # Determine primary type
        if boolean_count / total_count > 0.8:
            return {'type': 'boolean', 'confidence': boolean_count / total_count}
        elif date_count / total_count > 0.7:
            return {'type': 'date', 'confidence': date_count / total_count}
        elif integer_count / total_count > 0.8:
            return {'type': 'integer', 'confidence': integer_count / total_count}
        elif numeric_count / total_count > 0.8:
            return {'type': 'numeric', 'confidence': numeric_count / total_count}
        else:
            # Check if categorical (low cardinality)
            unique_count = len(set(clean_values))
            if unique_count <= min(20, total_count * 0.5):
                return {'type': 'categorical', 'confidence': 0.8}
            else:
                return {'type': 'text', 'confidence': 0.9}

    def standardize_value(self, value: str, data_type: str) -> str:
        """
        Standardize a value based on its data type.

        Args:
            value: Original value
            data_type: Detected data type

        Returns:
            Standardized value
        """
        if not value or str(value).strip() == '':
            return ''

        value_str = str(value).strip()

        try:
            if data_type == 'boolean':
                # Standardize boolean values
                value_lower = value_str.lower()
                if value_lower in ['true', 'yes', 'y', '1', 'on', 'enabled']:
                    return 'True'
                elif value_lower in ['false', 'no', 'n', '0', 'off', 'disabled']:
                    return 'False'
                else:
                    return value_str

            elif data_type == 'numeric':
                # Standardize numeric values
                try:
                    # Remove currency symbols and commas
                    clean_val = re.sub(r'[^\d.-]', '', value_str)
                    if clean_val:
                        num_val = float(clean_val)
                        return str(num_val)
                except ValueError:
                    pass
                return value_str

            elif data_type == 'integer':
                # Standardize integer values
                try:
                    clean_val = re.sub(r'[^\d.-]', '', value_str)
                    if clean_val:
                        int_val = int(float(clean_val))
                        return str(int_val)
                except ValueError:
                    pass
                return value_str

            elif data_type == 'text':
                # Basic text cleaning
                # Remove extra whitespace
                cleaned = re.sub(r'\s+', ' ', value_str)
                return cleaned.strip()

            else:
                return value_str

        except Exception:
            return value_str

    def detect_outliers_iqr(self, values: List[float]) -> List[bool]:
        """
        Detect outliers using the IQR method.

        Args:
            values: List of numeric values

        Returns:
            List of boolean flags indicating outliers
        """
        if len(values) < 4:
            return [False] * len(values)

        # Calculate quartiles
        sorted_values = sorted(values)
        n = len(sorted_values)

        q1 = sorted_values[n // 4]
        q3 = sorted_values[3 * n // 4]
        iqr = q3 - q1

        # Calculate bounds
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        # Identify outliers
        outliers = [v < lower_bound or v > upper_bound for v in values]

        return outliers

    def detect_outliers_zscore(self, values: List[float], threshold: float = 3.0) -> List[bool]:
        """
        Detect outliers using the Z-score method.

        Args:
            values: List of numeric values
            threshold: Z-score threshold for outliers

        Returns:
            List of boolean flags indicating outliers
        """
        if len(values) < 3:
            return [False] * len(values)

        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0

        if std_val == 0:
            return [False] * len(values)

        # Calculate Z-scores
        z_scores = [abs((v - mean_val) / std_val) for v in values]

        # Identify outliers
        outliers = [z > threshold for z in z_scores]

        return outliers

    def handle_missing_values(self, data: List[Dict], column_info: Dict) -> List[Dict]:
        """
        Handle missing values in the dataset.

        Args:
            data: List of data rows
            column_info: Information about columns

        Returns:
            Data with missing values handled
        """
        if not data:
            return data

        cleaned_data = []

        for row in data:
            cleaned_row = {}

            for col_name, col_meta in column_info.items():
                value = row.get(col_name, '')

                # Check if value is missing
                if not value or str(value).strip() == '':
                    data_type = col_meta.get('type', 'text')

                    # Fill with appropriate default based on type
                    if data_type in ['numeric', 'integer']:
                        # Use median for numeric columns
                        if 'median' in col_meta:
                            cleaned_row[col_name] = str(col_meta['median'])
                        else:
                            cleaned_row[col_name] = '0'
                    elif data_type == 'boolean':
                        cleaned_row[col_name] = 'False'
                    elif data_type == 'categorical':
                        # Use mode for categorical
                        if 'mode' in col_meta:
                            cleaned_row[col_name] = str(col_meta['mode'])
                        else:
                            cleaned_row[col_name] = 'Unknown'
                    else:
                        cleaned_row[col_name] = 'Unknown'

                    self.stats['missing_values_filled'] += 1
                else:
                    cleaned_row[col_name] = value

            cleaned_data.append(cleaned_row)

        return cleaned_data

    def analyze_columns(self, data: List[Dict]) -> Dict[str, Dict]:
        """
        Analyze columns to determine types and statistics.

        Args:
            data: List of data rows

        Returns:
            Dictionary with column analysis
        """
        if not data:
            return {}

        column_info = {}
        column_names = list(data[0].keys()) if data else []

        for col_name in column_names:
            values = [row.get(col_name, '') for row in data]
            non_empty_values = [v for v in values if v and str(v).strip()]

            # Detect data type
            type_info = self.detect_data_type(values)

            col_info = {
                'original_name': col_name,
                'type': type_info['type'],
                'confidence': type_info['confidence'],
                'total_count': len(values),
                'non_empty_count': len(non_empty_values),
                'missing_count': len(values) - len(non_empty_values),
                'missing_percentage': (len(values) - len(non_empty_values)) / len(values) * 100 if values else 0
            }

            # Calculate statistics for numeric columns
            if type_info['type'] in ['numeric', 'integer'] and non_empty_values:
                try:
                    numeric_values = []
                    for v in non_empty_values:
                        try:
                            numeric_values.append(float(v))
                        except ValueError:
                            pass

                    if numeric_values:
                        col_info.update({
                            'mean': statistics.mean(numeric_values),
                            'median': statistics.median(numeric_values),
                            'min': min(numeric_values),
                            'max': max(numeric_values),
                            'std': statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0
                        })
                except Exception:
                    pass

            # Calculate mode for categorical columns
            if type_info['type'] in ['categorical', 'boolean', 'text'] and non_empty_values:
                try:
                    col_info['mode'] = statistics.mode(non_empty_values)
                except statistics.StatisticsError:
                    # Multiple modes or no mode
                    col_info['mode'] = non_empty_values[0] if non_empty_values else 'Unknown'

            column_info[col_name] = col_info

        return column_info

    def clean_data(self) -> Dict[str, Any]:
        """
        Perform comprehensive data cleaning.

        Returns:
            Cleaning results and statistics
        """
        logger.info("Starting data cleaning process...")

        # Read input data
        try:
            with open(self.input_file, 'r', encoding='utf-8', newline='') as f:
                # Detect delimiter
                sample = f.read(1024)
                f.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter

                reader = csv.DictReader(f, delimiter=delimiter)
                data = list(reader)

                self.stats['original_rows'] = len(data)
                logger.info(f"Loaded {len(data)} rows from {self.input_file}")

        except Exception as e:
            logger.error(f"Error reading input file: {e}")
            return {'status': 'error', 'error': str(e)}

        if not data:
            logger.warning("No data found in input file")
            return {'status': 'warning', 'message': 'No data to clean'}

        # Analyze columns
        logger.info("Analyzing column structure...")
        column_info = self.analyze_columns(data)

        # Standardize column names
        if self.config['standardize_column_names']:
            logger.info("Standardizing column names...")
            new_data = []
            column_mapping = {}

            for row in data:
                new_row = {}
                for old_name, value in row.items():
                    new_name = self.standardize_column_name(old_name)
                    new_row[new_name] = value

                    if old_name != new_name:
                        column_mapping[old_name] = new_name
                        self.stats['columns_renamed'] += 1

                new_data.append(new_row)

            data = new_data

            # Update column_info with new names
            new_column_info = {}
            for old_name, info in column_info.items():
                new_name = column_mapping.get(old_name, old_name)
                new_column_info[new_name] = info
                new_column_info[new_name]['standardized_name'] = new_name

            column_info = new_column_info

        # Remove columns with too many missing values
        if self.config['handle_missing_values']:
            columns_to_remove = []
            for col_name, col_info in column_info.items():
                if col_info['missing_percentage'] > self.config['missing_value_threshold'] * 100:
                    columns_to_remove.append(col_name)
                    logger.warning(f"Removing column '{col_name}' ({col_info['missing_percentage']:.1f}% missing)")

            if columns_to_remove:
                new_data = []
                for row in data:
                    new_row = {k: v for k, v in row.items() if k not in columns_to_remove}
                    new_data.append(new_row)

                data = new_data

                # Update column_info
                for col_name in columns_to_remove:
                    del column_info[col_name]

        # Handle missing values
        if self.config['handle_missing_values']:
            logger.info("Handling missing values...")
            data = self.handle_missing_values(data, column_info)

        # Standardize data types
        if self.config['standardize_data_types']:
            logger.info("Standardizing data types...")
            for row in data:
                for col_name, col_info in column_info.items():
                    if col_name in row:
                        original_value = row[col_name]
                        standardized_value = self.standardize_value(original_value, col_info['type'])

                        if original_value != standardized_value:
                            row[col_name] = standardized_value
                            self.stats['data_types_standardized'] += 1

        # Remove empty rows
        if self.config['remove_empty_rows']:
            original_count = len(data)
            data = [row for row in data if any(str(v).strip() for v in row.values())]
            removed_empty = original_count - len(data)
            self.stats['removed_rows'] += removed_empty

            if removed_empty > 0:
                logger.info(f"Removed {removed_empty} empty rows")

        # Remove duplicates
        if self.config['remove_duplicates']:
            original_count = len(data)
            seen = set()
            unique_data = []

            for row in data:
                # Create a signature for the row
                row_signature = tuple(sorted(row.items()))
                if row_signature not in seen:
                    seen.add(row_signature)
                    unique_data.append(row)

            duplicates_removed = original_count - len(unique_data)
            data = unique_data
            self.stats['removed_rows'] += duplicates_removed

            if duplicates_removed > 0:
                logger.info(f"Removed {duplicates_removed} duplicate rows")

        self.stats['cleaned_rows'] = len(data)

        # Detect outliers (for reporting, not removal)
        outlier_info = {}
        if self.config['detect_outliers']:
            logger.info("Detecting outliers...")

            for col_name, col_info in column_info.items():
                if col_info['type'] in ['numeric', 'integer']:
                    values = []
                    for row in data:
                        try:
                            val = float(row.get(col_name, 0))
                            values.append(val)
                        except (ValueError, TypeError):
                            pass

                    if len(values) > 3:
                        if self.config['outlier_method'] == 'iqr':
                            outliers = self.detect_outliers_iqr(values)
                        else:
                            outliers = self.detect_outliers_zscore(values)

                        outlier_count = sum(outliers)
                        outlier_info[col_name] = {
                            'count': outlier_count,
                            'percentage': outlier_count / len(values) * 100
                        }

                        self.stats['outliers_detected'] += outlier_count

        # Write cleaned data
        try:
            logger.info(f"Writing cleaned data to {self.output_file}")

            if data:
                fieldnames = list(data[0].keys())

                with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)

                logger.info(f"Successfully wrote {len(data)} rows to {self.output_file}")
            else:
                logger.warning("No data to write after cleaning")

        except Exception as e:
            logger.error(f"Error writing output file: {e}")
            return {'status': 'error', 'error': str(e)}

        # Generate quality score
        quality_score = self._calculate_quality_score(column_info)

        return {
            'status': 'success',
            'input_file': str(self.input_file),
            'output_file': str(self.output_file),
            'statistics': self.stats,
            'column_info': column_info,
            'outlier_info': outlier_info,
            'quality_score': quality_score
        }

    def _calculate_quality_score(self, column_info: Dict) -> float:
        """
        Calculate a data quality score (0-100).

        Args:
            column_info: Column analysis results

        Returns:
            Quality score
        """
        if not column_info:
            return 0.0

        total_score = 0.0
        max_score = 0.0

        for col_name, col_data in column_info.items():
            # Completeness score (40 points)
            completeness = (col_data['non_empty_count'] / col_data['total_count']) * 40 if col_data['total_count'] > 0 else 0

            # Type confidence score (30 points)
            type_confidence = col_data.get('confidence', 0.5) * 30

            # Consistency score (30 points) - based on standardization
            consistency = 30  # Assume good after cleaning

            col_score = completeness + type_confidence + consistency
            total_score += col_score
            max_score += 100

        return (total_score / max_score) * 100 if max_score > 0 else 0.0

    def generate_report(self, results: Dict) -> str:
        """
        Generate a cleaning report.

        Args:
            results: Cleaning results

        Returns:
            Formatted report string
        """
        report = []
        report.append("# Data Cleaning Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        if results['status'] != 'success':
            report.append("## ❌ Error")
            report.append(f"Status: {results['status']}")
            if 'error' in results:
                report.append(f"Error: {results['error']}")
            return '\n'.join(report)

        stats = results['statistics']

        # Summary
        report.append("## 📊 Summary")
        report.append(f"- **Input file:** {results['input_file']}")
        report.append(f"- **Output file:** {results['output_file']}")
        report.append(f"- **Original rows:** {stats['original_rows']:,}")
        report.append(f"- **Cleaned rows:** {stats['cleaned_rows']:,}")
        report.append(f"- **Removed rows:** {stats['removed_rows']:,}")
        report.append(f"- **Data Quality Score:** {results['quality_score']:.1f}/100")
        report.append("")

        # Cleaning actions
        report.append("## 🔧 Cleaning Actions")
        report.append(f"- **Missing values filled:** {stats['missing_values_filled']:,}")
        report.append(f"- **Columns renamed:** {stats['columns_renamed']:,}")
        report.append(f"- **Data types standardized:** {stats['data_types_standardized']:,}")
        report.append(f"- **Outliers detected:** {stats['outliers_detected']:,}")
        report.append("")

        # Column information
        report.append("## 📋 Column Analysis")

        column_info = results.get('column_info', {})
        for col_name, col_data in column_info.items():
            report.append(f"### {col_name}")
            report.append(f"- **Type:** {col_data['type']} (confidence: {col_data['confidence']:.2f})")
            report.append(f"- **Completeness:** {(col_data['non_empty_count'] / col_data['total_count'] * 100):.1f}%")

            if col_data['type'] in ['numeric', 'integer']:
                if 'mean' in col_data:
                    report.append(f"- **Mean:** {col_data['mean']:.2f}")
                    report.append(f"- **Range:** {col_data['min']:.2f} - {col_data['max']:.2f}")

            report.append("")

        # Outlier information
        outlier_info = results.get('outlier_info', {})
        if outlier_info:
            report.append("## ⚠️ Outliers Detected")
            for col_name, outlier_data in outlier_info.items():
                if outlier_data['count'] > 0:
                    report.append(f"- **{col_name}:** {outlier_data['count']} outliers ({outlier_data['percentage']:.1f}%)")
            report.append("")

        # Quality assessment
        quality_score = results['quality_score']
        report.append("## 🎯 Quality Assessment")

        if quality_score >= 90:
            report.append("✅ **Excellent** - Data is ready for analysis")
        elif quality_score >= 75:
            report.append("✅ **Good** - Data quality is acceptable for analysis")
        elif quality_score >= 60:
            report.append("⚠️ **Fair** - Some quality issues, but usable")
        else:
            report.append("❌ **Poor** - Significant quality issues detected")

        report.append("")

        # Next steps
        report.append("## 🚀 Next Steps")
        report.append("Your data has been cleaned and is ready for analysis:")
        report.append("")
        report.append("```python")
        report.append("# Load the cleaned dataset")
        report.append("load_dataset(")
        report.append(f"    file_path=\"{results['output_file']}\",")
        report.append(f"    dataset_name=\"{Path(results['output_file']).stem}\",")
        report.append("    source_type=\"csv\"")
        report.append(")")
        report.append("")
        report.append("# Start analysis")
        report.append("profile_data(dataset_id=\"DATASET_ID\")")
        report.append("calculate_statistics(dataset_id=\"DATASET_ID\")")
        report.append("```")

        return '\n'.join(report)


def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(description='Clean and validate data for NeoCoder analysis')
    parser.add_argument('input_file', help='Input CSV file path')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('--missing-threshold', type=float, default=0.5,
                      help='Threshold for removing columns with missing values (0.0-1.0)')
    parser.add_argument('--outlier-method', choices=['iqr', 'zscore'], default='iqr',
                      help='Outlier detection method')
    parser.add_argument('--no-duplicates', action='store_false', dest='remove_duplicates',
                      help='Skip duplicate removal')
    parser.add_argument('--no-standardize', action='store_false', dest='standardize_names',
                      help='Skip column name standardization')

    args = parser.parse_args()

    # Initialize cleaner
    cleaner = DataCleaner(args.input_file, args.output)

    # Update configuration
    cleaner.config.update({
        'missing_value_threshold': args.missing_threshold,
        'outlier_method': args.outlier_method,
        'remove_duplicates': args.remove_duplicates,
        'standardize_column_names': args.standardize_names
    })

    # Perform cleaning
    results = cleaner.clean_data()

    # Generate and display report
    report = cleaner.generate_report(results)
    print(report)

    # Save report
    if results['status'] == 'success':
        report_file = Path(results['output_file']).parent / f"{Path(results['output_file']).stem}_cleaning_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"Cleaning report saved to: {report_file}")
        return 0
    else:
        return 1


if __name__ == '__main__':
    exit(main())
