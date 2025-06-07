#!/usr/bin/env python3
"""
Batch Data Processing Pipeline for NeoCoder Data Analysis

This script processes multiple data files simultaneously, applying conversion,
cleaning, and standardization to prepare them for analysis.

Author: NeoCoder Data Analysis Team
Created: 2025
"""

import os
import sys
import json
import argparse
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BatchProcessor:
    """
    Batch processing utility for multiple data files.

    Features:
    - Parallel processing of multiple files
    - Automatic format detection and conversion
    - Data cleaning and validation
    - Progress tracking and reporting
    - Error handling and recovery
    """

    def __init__(self, input_dir: Optional[str] = None, output_dir: Optional[str] = None, max_workers: int = 4):
        """
        Initialize the batch processor.

        Args:
            input_dir: Input directory path
            output_dir: Output directory path
            max_workers: Maximum number of parallel workers
        """
        self.input_dir = Path(input_dir) if input_dir else Path(__file__).parent.parent / "downloads"
        self.output_dir = Path(output_dir) if output_dir else self.input_dir / "processed"
        self.max_workers = max_workers

        # Create directories
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Processing statistics
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'converted_files': 0,
            'cleaned_files': 0,
            'failed_files': 0,
            'skipped_files': 0,
            'start_time': None,
            'end_time': None
        }

        # Script paths
        self.scripts_dir = Path(__file__).parent
        self.converter_script = self.scripts_dir / "auto_converter.py"
        self.cleaner_script = self.scripts_dir / "data_cleaner.py"

        # Supported file extensions
        self.supported_extensions = {
            '.csv', '.json', '.jsonl', '.xlsx', '.xls',
            '.tsv', '.txt', '.dat'
        }

        logger.info("BatchProcessor initialized")
        logger.info(f"Input directory: {self.input_dir}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Max workers: {self.max_workers}")

    def discover_files(self) -> List[Path]:
        """
        Discover all processable files in the input directory.

        Returns:
            List of file paths to process
        """
        files = []

        for file_path in self.input_dir.iterdir():
            if (file_path.is_file() and
                file_path.suffix.lower() in self.supported_extensions and
                not file_path.name.startswith('.') and
                not file_path.name.endswith('_processed.csv') and
                not file_path.name.endswith('_cleaned.csv') and
                not file_path.name.endswith('_converted.csv')):

                files.append(file_path)

        logger.info(f"Discovered {len(files)} files to process")
        return files

    def process_single_file(self, file_path: Path) -> Dict:
        """
        Process a single file through the conversion and cleaning pipeline.

        Args:
            file_path: Path to the file to process

        Returns:
            Processing result dictionary
        """
        result = {
            'file_path': file_path,
            'status': 'started',
            'conversion_result': None,
            'cleaning_result': None,
            'final_output': None,
            'error': None
        }

        try:
            logger.info(f"Processing file: {file_path.name}")

            # Step 1: Conversion (if needed)
            converted_file = file_path

            if file_path.suffix.lower() != '.csv':
                logger.info(f"Converting {file_path.name}...")

                conversion_cmd = [
                    sys.executable, str(self.converter_script),
                    str(file_path),
                    '--output-dir', str(self.output_dir)
                ]

                try:
                    conversion_result = subprocess.run(
                        conversion_cmd,
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minute timeout
                    )

                    if conversion_result.returncode == 0:
                        # Find the converted file
                        converted_files = list(self.output_dir.glob(f"{file_path.stem}*_converted.csv"))
                        if converted_files:
                            converted_file = converted_files[0]
                            result['conversion_result'] = 'success'
                            self.stats['converted_files'] += 1
                            logger.info(f"Conversion successful: {converted_file.name}")
                        else:
                            # File might already be CSV
                            converted_file = file_path
                    else:
                        logger.error(f"Conversion failed for {file_path.name}: {conversion_result.stderr}")
                        result['error'] = f"Conversion failed: {conversion_result.stderr}"
                        return result

                except subprocess.TimeoutExpired:
                    logger.error(f"Conversion timeout for {file_path.name}")
                    result['error'] = "Conversion timeout"
                    return result
                except Exception as e:
                    logger.error(f"Conversion error for {file_path.name}: {e}")
                    result['error'] = f"Conversion error: {e}"
                    return result

            # Step 2: Data Cleaning
            logger.info(f"Cleaning {converted_file.name}...")

            # Determine output file name for cleaning
            if converted_file == file_path:
                # Original file was CSV
                cleaned_file = self.output_dir / f"{file_path.stem}_processed.csv"
            else:
                # File was converted
                cleaned_file = self.output_dir / f"{file_path.stem}_processed.csv"

            cleaning_cmd = [
                sys.executable, str(self.cleaner_script),
                str(converted_file),
                '--output', str(cleaned_file)
            ]

            try:
                cleaning_result = subprocess.run(
                    cleaning_cmd,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout
                )

                if cleaning_result.returncode == 0:
                    result['cleaning_result'] = 'success'
                    result['final_output'] = cleaned_file
                    result['status'] = 'completed'
                    self.stats['cleaned_files'] += 1
                    logger.info(f"Cleaning successful: {cleaned_file.name}")
                else:
                    logger.error(f"Cleaning failed for {converted_file.name}: {cleaning_result.stderr}")
                    # Still consider it processed if we have the converted file
                    if result['conversion_result'] == 'success':
                        result['final_output'] = converted_file
                        result['status'] = 'partial'
                    else:
                        result['error'] = f"Cleaning failed: {cleaning_result.stderr}"
                        return result

            except subprocess.TimeoutExpired:
                logger.error(f"Cleaning timeout for {converted_file.name}")
                result['error'] = "Cleaning timeout"
                return result
            except Exception as e:
                logger.error(f"Cleaning error for {converted_file.name}: {e}")
                result['error'] = f"Cleaning error: {e}"
                return result

            self.stats['processed_files'] += 1
            logger.info(f"File processing completed: {file_path.name}")

        except Exception as e:
            logger.error(f"Unexpected error processing {file_path.name}: {e}")
            result['error'] = f"Unexpected error: {e}"
            result['status'] = 'failed'
            self.stats['failed_files'] += 1

        return result

    def process_files(self, file_paths: List[Path]) -> List[Dict]:
        """
        Process multiple files in parallel.

        Args:
            file_paths: List of file paths to process

        Returns:
            List of processing results
        """
        if not file_paths:
            logger.info("No files to process")
            return []

        self.stats['total_files'] = len(file_paths)
        self.stats['start_time'] = datetime.now()

        logger.info(f"Starting batch processing of {len(file_paths)} files with {self.max_workers} workers")

        results = []

        # Process files in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self.process_single_file, file_path): file_path
                for file_path in file_paths
            }

            # Collect results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]

                try:
                    result = future.result()
                    results.append(result)

                    # Log progress
                    completed = len(results)
                    progress = (completed / len(file_paths)) * 100
                    logger.info(f"Progress: {completed}/{len(file_paths)} ({progress:.1f}%)")

                except Exception as e:
                    logger.error(f"Task failed for {file_path}: {e}")
                    results.append({
                        'file_path': file_path,
                        'status': 'failed',
                        'error': str(e)
                    })
                    self.stats['failed_files'] += 1

        self.stats['end_time'] = datetime.now()

        # Update final statistics
        successful_results = [r for r in results if r['status'] in ['completed', 'partial']]
        self.stats['processed_files'] = len(successful_results)

        logger.info(f"Batch processing completed: {self.stats['processed_files']}/{self.stats['total_files']} files processed")

        return results

    def generate_manifest(self, results: List[Dict]) -> Dict:
        """
        Generate a processing manifest with file locations and metadata.

        Args:
            results: Processing results

        Returns:
            Manifest dictionary
        """
        manifest = {
            'processing_info': {
                'timestamp': datetime.now().isoformat(),
                'input_directory': str(self.input_dir),
                'output_directory': str(self.output_dir),
                'processor_version': '1.0.0',
                'statistics': self.stats
            },
            'processed_files': []
        }

        for result in results:
            file_info = {
                'original_file': str(result['file_path']),
                'original_name': result['file_path'].name,
                'status': result['status'],
                'conversion_status': result.get('conversion_result'),
                'cleaning_status': result.get('cleaning_result')
            }

            if result.get('final_output'):
                file_info['processed_file'] = str(result['final_output'])
                file_info['processed_name'] = result['final_output'].name

                # Add file size information
                try:
                    original_size = result['file_path'].stat().st_size
                    processed_size = result['final_output'].stat().st_size

                    file_info['file_sizes'] = {
                        'original_bytes': original_size,
                        'processed_bytes': processed_size,
                        'size_change': processed_size - original_size
                    }
                except Exception:
                    pass

            if result.get('error'):
                file_info['error'] = result['error']

            manifest['processed_files'].append(file_info)

        return manifest

    def save_manifest(self, manifest: Dict) -> Path:
        """
        Save processing manifest to file.

        Args:
            manifest: Manifest dictionary

        Returns:
            Path to saved manifest file
        """
        manifest_file = self.output_dir / "processing_manifest.json"

        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, default=str)

        logger.info(f"Processing manifest saved: {manifest_file}")
        return manifest_file

    def generate_report(self, results: List[Dict], manifest: Dict) -> str:
        """
        Generate a comprehensive processing report.

        Args:
            results: Processing results
            manifest: Processing manifest

        Returns:
            Formatted report string
        """
        report = []
        report.append("# Batch Data Processing Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Processing summary
        stats = self.stats
        processing_time = (stats['end_time'] - stats['start_time']).total_seconds() if stats['end_time'] and stats['start_time'] else 0

        report.append("## 📊 Processing Summary")
        report.append(f"- **Input Directory:** {self.input_dir}")
        report.append(f"- **Output Directory:** {self.output_dir}")
        report.append(f"- **Total Files:** {stats['total_files']}")
        report.append(f"- **Successfully Processed:** {stats['processed_files']}")
        report.append(f"- **Files Converted:** {stats['converted_files']}")
        report.append(f"- **Files Cleaned:** {stats['cleaned_files']}")
        report.append(f"- **Failed Files:** {stats['failed_files']}")
        report.append(f"- **Processing Time:** {processing_time:.1f} seconds")
        report.append("")

        # Success rate
        success_rate = (stats['processed_files'] / stats['total_files'] * 100) if stats['total_files'] > 0 else 0

        if success_rate >= 90:
            status_emoji = "✅"
            status_text = "Excellent"
        elif success_rate >= 75:
            status_emoji = "✅"
            status_text = "Good"
        elif success_rate >= 50:
            status_emoji = "⚠️"
            status_text = "Partial"
        else:
            status_emoji = "❌"
            status_text = "Poor"

        report.append(f"## {status_emoji} Overall Status: {status_text}")
        report.append(f"**Success Rate:** {success_rate:.1f}%")
        report.append("")

        # File details
        report.append("## 📋 File Processing Details")
        report.append("")

        # Successful files
        successful_files = [r for r in results if r['status'] in ['completed', 'partial']]
        if successful_files:
            report.append("### ✅ Successfully Processed Files")
            report.append("")

            for result in successful_files:
                original_name = result['file_path'].name
                status_icon = "🔄" if result['status'] == 'partial' else "✅"

                report.append(f"#### {status_icon} {original_name}")

                if result.get('final_output'):
                    final_name = result['final_output'].name
                    report.append(f"- **Output:** {final_name}")

                if result.get('conversion_result'):
                    report.append(f"- **Converted:** {result['conversion_result']}")

                if result.get('cleaning_result'):
                    report.append(f"- **Cleaned:** {result['cleaning_result']}")

                report.append("")

        # Failed files
        failed_files = [r for r in results if r['status'] == 'failed']
        if failed_files:
            report.append("### ❌ Failed Files")
            report.append("")

            for result in failed_files:
                original_name = result['file_path'].name
                error = result.get('error', 'Unknown error')

                report.append(f"#### ❌ {original_name}")
                report.append(f"- **Error:** {error}")
                report.append("")

        # Data analysis ready files
        analysis_ready_files = [
            f for f in manifest['processed_files']
            if f['status'] == 'completed' and f.get('processed_file')
        ]

        if analysis_ready_files:
            report.append("## 🚀 Ready for Data Analysis")
            report.append("")
            report.append("The following files are cleaned and ready for analysis:")
            report.append("")

            for file_info in analysis_ready_files:
                processed_file = file_info['processed_file']
                processed_name = file_info['processed_name']

                report.append(f"### {processed_name}")
                report.append("")
                report.append("```python")
                report.append("# Load dataset for analysis")
                report.append("load_dataset(")
                report.append(f"    file_path=\"{processed_file}\",")
                report.append(f"    dataset_name=\"{Path(processed_name).stem}\",")
                report.append("    source_type=\"csv\"")
                report.append(")")
                report.append("")
                report.append("# Generate insights")
                report.append("generate_insights(dataset_id=\"DATASET_ID\")")
                report.append("```")
                report.append("")

        # Next steps
        report.append("## 📋 Next Steps")
        report.append("")

        if analysis_ready_files:
            report.append("1. **Start Data Analysis:** Use the code snippets above to load your datasets")
            report.append("2. **Explore Data:** Use `explore_dataset()` and `profile_data()` for initial exploration")
            report.append("3. **Generate Insights:** Use `generate_insights()` for automated analysis")
            report.append("4. **Create Visualizations:** Use `visualize_data()` for charts and graphs")

        if failed_files:
            report.append("5. **Address Failed Files:** Review error messages and resolve data issues")
            report.append("6. **Re-run Processing:** Process individual files after fixing issues")

        report.append("")

        # Manifest information
        report.append("## 📄 Processing Manifest")
        report.append(f"Detailed processing information saved to: `{self.output_dir}/processing_manifest.json`")
        report.append("")

        return '\n'.join(report)

    def run_batch_processing(self) -> Dict:
        """
        Run the complete batch processing pipeline.

        Returns:
            Processing summary results
        """
        logger.info("Starting batch processing pipeline...")

        # Discover files
        files = self.discover_files()

        if not files:
            logger.info("No files found to process")
            return {
                'status': 'no_files',
                'message': 'No processable files found in input directory'
            }

        # Process files
        results = self.process_files(files)

        # Generate manifest
        manifest = self.generate_manifest(results)
        manifest_file = self.save_manifest(manifest)

        # Generate report
        report = self.generate_report(results, manifest)

        # Save report
        report_file = self.output_dir / "batch_processing_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"Batch processing report saved: {report_file}")

        return {
            'status': 'completed',
            'results': results,
            'manifest': manifest,
            'report': report,
            'manifest_file': str(manifest_file),
            'report_file': str(report_file),
            'statistics': self.stats
        }


def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(description='Batch process data files for NeoCoder analysis')
    parser.add_argument('--input-dir', help='Input directory path')
    parser.add_argument('--output-dir', help='Output directory path')
    parser.add_argument('--max-workers', type=int, default=4, help='Maximum parallel workers')
    parser.add_argument('--quiet', action='store_true', help='Reduce output verbosity')

    args = parser.parse_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    # Initialize processor
    processor = BatchProcessor(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        max_workers=args.max_workers
    )

    # Run processing
    results = processor.run_batch_processing()

    if results['status'] == 'no_files':
        print(f"⚠️ {results['message']}")
        print(f"Place data files in: {processor.input_dir}")
        return 1

    elif results['status'] == 'completed':
        # Display report
        print(results['report'])

        # Return appropriate exit code
        stats = results['statistics']
        if stats['failed_files'] == 0:
            return 0  # All successful
        elif stats['processed_files'] > 0:
            return 2  # Partial success
        else:
            return 1  # All failed

    else:
        print(f"❌ Processing failed: {results.get('error', 'Unknown error')}")
        return 1


if __name__ == '__main__':
    exit(main())
