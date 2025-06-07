#!/usr/bin/env python3
"""
Automatic File Format Converter for NeoCoder Data Analysis

This script automatically detects file formats and converts them to CSV
for easier processing in the data analysis workflow.

Author: NeoCoder Data Analysis Team
Created: 2025
"""

import os
import sys
import json
import csv
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
import mimetypes

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_conversion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoConverter:
    """
    Automatic file format detection and conversion utility.

    Supports: CSV, JSON, Excel (XLSX, XLS), TSV, TXT
    """

    def __init__(self, downloads_dir: Optional[str] = None, output_dir: Optional[str] = None):
        """
        Initialize the converter.

        Args:
            downloads_dir: Directory to scan for files
            output_dir: Directory to save converted files
        """
        self.downloads_dir = Path(downloads_dir) if downloads_dir else Path(__file__).parent.parent / "downloads"
        self.output_dir = Path(output_dir) if output_dir else self.downloads_dir

        # Ensure directories exist
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Supported file extensions and their handlers
        self.handlers = {
            '.csv': self._handle_csv,
            '.json': self._handle_json,
            '.jsonl': self._handle_jsonl,
            '.xlsx': self._handle_excel,
            '.xls': self._handle_excel,
            '.tsv': self._handle_tsv,
            '.txt': self._handle_text,
            '.dat': self._handle_text,
        }

        logger.info("AutoConverter initialized")
        logger.info(f"Downloads directory: {self.downloads_dir}")
        logger.info(f"Output directory: {self.output_dir}")

    def detect_file_format(self, file_path: Path) -> str:
        """
        Detect file format based on extension and content.

        Args:
            file_path: Path to the file

        Returns:
            Detected format string
        """
        extension = file_path.suffix.lower()

        # Check MIME type as backup
        mime_type, _ = mimetypes.guess_type(str(file_path))

        logger.info(f"File: {file_path.name}")
        logger.info(f"Extension: {extension}")
        logger.info(f"MIME type: {mime_type}")

        return extension

    def _handle_csv(self, file_path: Path) -> Dict:
        """Handle CSV files - validate and standardize."""
        try:
            # Check if file is already valid CSV
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                sample = f.read(1024)
                f.seek(0)

                # Detect delimiter
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter

                # Read and validate
                reader = csv.DictReader(f, delimiter=delimiter)
                headers = reader.fieldnames

                if not headers:
                    raise ValueError("No headers found in CSV")

                # Count rows for validation
                row_count = sum(1 for row in reader)

                logger.info(f"CSV file validated: {len(headers)} columns, {row_count} rows")

                return {
                    'status': 'valid',
                    'format': 'csv',
                    'headers': headers,
                    'row_count': row_count,
                    'delimiter': delimiter,
                    'output_file': file_path  # File is already CSV
                }

        except Exception as e:
            logger.error(f"Error processing CSV {file_path}: {e}")
            return {'status': 'error', 'error': str(e)}

    def _handle_json(self, file_path: Path) -> Dict:
        """Handle JSON files - convert to CSV."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Determine structure
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                # Try to find main data array
                records = None
                for key, value in data.items():
                    if isinstance(value, list) and len(value) > 0:
                        records = value
                        break

                if records is None:
                    # Treat dict as single record
                    records = [data]
            else:
                raise ValueError("JSON must contain array or object")

            if not records:
                raise ValueError("No data records found in JSON")

            # Convert to CSV
            output_file = self.output_dir / f"{file_path.stem}_converted.csv"

            # Get all possible field names
            all_fields = set()
            for record in records:
                if isinstance(record, dict):
                    all_fields.update(record.keys())

            fieldnames = sorted(list(all_fields))

            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for record in records:
                    if isinstance(record, dict):
                        # Fill missing fields with empty strings
                        clean_record = {field: record.get(field, '') for field in fieldnames}
                        writer.writerow(clean_record)

            logger.info(f"JSON converted to CSV: {len(records)} records, {len(fieldnames)} columns")

            return {
                'status': 'converted',
                'format': 'json',
                'headers': fieldnames,
                'row_count': len(records),
                'output_file': output_file
            }

        except Exception as e:
            logger.error(f"Error processing JSON {file_path}: {e}")
            return {'status': 'error', 'error': str(e)}

    def _handle_jsonl(self, file_path: Path) -> Dict:
        """Handle JSON Lines files - convert to CSV."""
        try:
            records = []
            all_fields = set()

            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        try:
                            record = json.loads(line)
                            records.append(record)
                            if isinstance(record, dict):
                                all_fields.update(record.keys())
                        except json.JSONDecodeError as e:
                            logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")

            if not records:
                raise ValueError("No valid JSON records found")

            # Convert to CSV
            output_file = self.output_dir / f"{file_path.stem}_converted.csv"
            fieldnames = sorted(list(all_fields))

            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for record in records:
                    if isinstance(record, dict):
                        clean_record = {field: record.get(field, '') for field in fieldnames}
                        writer.writerow(clean_record)

            logger.info(f"JSONL converted to CSV: {len(records)} records, {len(fieldnames)} columns")

            return {
                'status': 'converted',
                'format': 'jsonl',
                'headers': fieldnames,
                'row_count': len(records),
                'output_file': output_file
            }

        except Exception as e:
            logger.error(f"Error processing JSONL {file_path}: {e}")
            return {'status': 'error', 'error': str(e)}

    def _handle_excel(self, file_path: Path) -> Dict:
        """Handle Excel files - convert to CSV."""
        try:
            # Try to import pandas/openpyxl
            try:
                import pandas as pd
            except ImportError:
                logger.error("pandas required for Excel processing. Install with: pip install pandas openpyxl")
                return {'status': 'error', 'error': 'pandas not available'}

            # Read Excel file
            excel_data = pd.read_excel(file_path, sheet_name=None)  # Read all sheets

            results = []

            for sheet_name, df in excel_data.items():
                if df.empty:
                    logger.warning(f"Sheet '{sheet_name}' is empty, skipping")
                    continue

                # Clean sheet name for filename
                clean_sheet_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '-', '_')).strip()

                # Generate output filename
                if len(excel_data) == 1:
                    output_file = self.output_dir / f"{file_path.stem}_converted.csv"
                else:
                    output_file = self.output_dir / f"{file_path.stem}_{clean_sheet_name}_converted.csv"

                # Convert to CSV
                df.to_csv(output_file, index=False, encoding='utf-8')

                logger.info(f"Excel sheet '{sheet_name}' converted: {len(df)} rows, {len(df.columns)} columns")

                results.append({
                    'sheet_name': sheet_name,
                    'headers': df.columns.tolist(),
                    'row_count': len(df),
                    'output_file': output_file
                })

            return {
                'status': 'converted',
                'format': 'excel',
                'sheets': results,
                'total_sheets': len(results)
            }

        except Exception as e:
            logger.error(f"Error processing Excel {file_path}: {e}")
            return {'status': 'error', 'error': str(e)}

    def _handle_tsv(self, file_path: Path) -> Dict:
        """Handle TSV files - convert to CSV."""
        try:
            output_file = self.output_dir / f"{file_path.stem}_converted.csv"

            with open(file_path, 'r', encoding='utf-8') as tsvfile:
                reader = csv.reader(tsvfile, delimiter='\t')

                with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)

                    headers = None
                    row_count = 0

                    for row in reader:
                        if headers is None:
                            headers = row
                        writer.writerow(row)
                        row_count += 1

            logger.info(f"TSV converted to CSV: {row_count} rows, {len(headers) if headers else 0} columns")

            return {
                'status': 'converted',
                'format': 'tsv',
                'headers': headers,
                'row_count': row_count - 1,  # Subtract header row
                'output_file': output_file
            }

        except Exception as e:
            logger.error(f"Error processing TSV {file_path}: {e}")
            return {'status': 'error', 'error': str(e)}

    def _handle_text(self, file_path: Path) -> Dict:
        """Handle text files - attempt to detect structure and convert."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sample = f.read(4096)  # Read first 4KB
                f.seek(0)

                # Try to detect delimiter
                potential_delimiters = [',', '\t', ';', '|', ' ']
                delimiter = ','  # Default

                for delim in potential_delimiters:
                    if delim in sample:
                        # Count occurrences in first few lines
                        lines = sample.split('\n')[:5]
                        counts = [line.count(delim) for line in lines if line.strip()]

                        if counts and len(set(counts)) == 1 and counts[0] > 0:
                            delimiter = delim
                            break

                # Convert using detected delimiter
                output_file = self.output_dir / f"{file_path.stem}_converted.csv"

                reader = csv.reader(f, delimiter=delimiter)

                with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)

                    headers = None
                    row_count = 0

                    for row in reader:
                        if headers is None:
                            headers = row
                        writer.writerow(row)
                        row_count += 1

            logger.info(f"Text file converted: delimiter '{delimiter}', {row_count} rows")

            return {
                'status': 'converted',
                'format': 'text',
                'delimiter': delimiter,
                'headers': headers,
                'row_count': row_count - 1,
                'output_file': output_file
            }

        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {e}")
            return {'status': 'error', 'error': str(e)}

    def process_file(self, file_path: Path) -> Dict:
        """
        Process a single file.

        Args:
            file_path: Path to the file to process

        Returns:
            Processing result dictionary
        """
        if not file_path.exists():
            return {'status': 'error', 'error': 'File not found'}

        format_type = self.detect_file_format(file_path)

        if format_type not in self.handlers:
            logger.warning(f"Unsupported file format: {format_type}")
            return {'status': 'unsupported', 'format': format_type}

        logger.info(f"Processing {file_path.name} as {format_type}")

        handler = self.handlers[format_type]
        result = handler(file_path)

        # Add metadata
        result.update({
            'input_file': file_path,
            'processed_at': str(Path(__file__).parent.parent.parent / 'data' / 'processing_timestamp.txt')
        })

        return result

    def process_directory(self, directory: Optional[Path] = None) -> List[Dict]:
        """
        Process all supported files in a directory.

        Args:
            directory: Directory to process (defaults to downloads_dir)

        Returns:
            List of processing results
        """
        target_dir = directory if directory else self.downloads_dir

        if not target_dir.exists():
            logger.error(f"Directory not found: {target_dir}")
            return []

        logger.info(f"Processing directory: {target_dir}")

        results = []
        processed_count = 0

        for file_path in target_dir.iterdir():
            if file_path.is_file() and not file_path.name.startswith('.'):
                result = self.process_file(file_path)
                results.append(result)

                if result['status'] in ['valid', 'converted']:
                    processed_count += 1

        logger.info(f"Directory processing complete: {processed_count}/{len(results)} files processed successfully")

        return results

    def generate_report(self, results: List[Dict]) -> str:
        """
        Generate a processing report.

        Args:
            results: List of processing results

        Returns:
            Formatted report string
        """
        report = []
        report.append("# Data Processing Report")
        report.append(f"Generated: {Path().cwd()}")
        report.append("")

        # Summary
        total_files = len(results)
        successful = len([r for r in results if r['status'] in ['valid', 'converted']])
        errors = len([r for r in results if r['status'] == 'error'])
        unsupported = len([r for r in results if r['status'] == 'unsupported'])

        report.append("## Summary")
        report.append(f"- Total files: {total_files}")
        report.append(f"- Successfully processed: {successful}")
        report.append(f"- Errors: {errors}")
        report.append(f"- Unsupported formats: {unsupported}")
        report.append("")

        # Detailed results
        report.append("## Detailed Results")
        report.append("")

        for i, result in enumerate(results, 1):
            status_emoji = {
                'valid': '✅',
                'converted': '🔄',
                'error': '❌',
                'unsupported': '⚠️'
            }.get(result['status'], '❓')

            report.append(f"### {i}. {result.get('input_file', 'Unknown')} {status_emoji}")
            report.append(f"- **Status:** {result['status']}")

            if result['status'] in ['valid', 'converted']:
                if 'headers' in result:
                    report.append(f"- **Columns:** {len(result['headers'])}")
                if 'row_count' in result:
                    report.append(f"- **Rows:** {result['row_count']:,}")
                if 'output_file' in result:
                    report.append(f"- **Output:** {result['output_file']}")

            if result['status'] == 'error':
                report.append(f"- **Error:** {result.get('error', 'Unknown error')}")

            report.append("")

        # Recommendations
        report.append("## Next Steps")

        if successful > 0:
            report.append("### Ready for Analysis")
            report.append("The following files are ready for data analysis:")
            report.append("")
            for result in results:
                if result['status'] in ['valid', 'converted'] and 'output_file' in result:
                    output_file = result['output_file']
                    report.append("```python")
                    report.append("load_dataset(")
                    report.append(f"    file_path=\"{output_file}\",")
                    report.append(f"    dataset_name=\"{Path(output_file).stem}\",")
                    report.append("    source_type=\"csv\"")
                    report.append(")")
                    report.append("```")
                    report.append("")

        if errors > 0:
            report.append("### Files Needing Attention")
            report.append("The following files had processing errors:")
            report.append("")
            for result in results:
                if result['status'] == 'error':
                    report.append(f"- **{result.get('input_file', 'Unknown')}**: {result.get('error', 'Unknown error')}")
            report.append("")

        return '\n'.join(report)


def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(description='Auto-convert data files for NeoCoder analysis')
    parser.add_argument('input', nargs='?', help='Input file or directory path')
    parser.add_argument('--downloads-dir', help='Downloads directory path')
    parser.add_argument('--output-dir', help='Output directory path')
    parser.add_argument('--report', action='store_true', help='Generate processing report')

    args = parser.parse_args()

    # Initialize converter
    converter = AutoConverter(
        downloads_dir=args.downloads_dir,
        output_dir=args.output_dir
    )

    if args.input:
        # Process specific file or directory
        input_path = Path(args.input)

        if input_path.is_file():
            results = [converter.process_file(input_path)]
        elif input_path.is_dir():
            results = converter.process_directory(input_path)
        else:
            logger.error(f"Input not found: {input_path}")
            return 1
    else:
        # Process downloads directory
        results = converter.process_directory()

    # Generate and display report
    if args.report or not args.input:
        report = converter.generate_report(results)
        print(report)

        # Save report to file
        report_file = converter.output_dir / 'processing_report.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"Report saved to: {report_file}")

    # Return appropriate exit code
    successful = len([r for r in results if r['status'] in ['valid', 'converted']])
    return 0 if successful > 0 else 1


if __name__ == '__main__':
    exit(main())
