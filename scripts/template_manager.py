#!/usr/bin/env python3
"""
Template Management Utility for Neo4j-Guided AI Coding Workflow

This script simplifies the creation, update, and management of ActionTemplates:
- Create new templates with proper versioning
- Update existing templates
- Export templates to files
- Import templates from files
- Archive outdated templates

Ensures proper versioning and maintains the isCurrent flag correctly.
"""

import sys
import logging
import argparse
import uuid
import json
from datetime import datetime
from neo4j import GraphDatabase
from pathlib import Path
from tabulate import tabulate  # pip install types-tabulate
import yaml  # pip install pyyaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Neo4jTemplateManager:
    def __init__(self, uri, username, password):
        """Initialize the Neo4j connection"""
        try:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            # Verify connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Connected to Neo4j database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            sys.exit(1)

    def close(self):
        """Close the Neo4j driver connection"""
        self.driver.close()
        logger.info("Disconnected from Neo4j database")

    def list_templates(self, keyword=None, include_inactive=False):
        """List all templates, optionally filtered by keyword"""
        query = """
        MATCH (t:ActionTemplate)
        WHERE 1=1
        """

        if keyword:
            query += "AND t.keyword = $keyword "

        if not include_inactive:
            query += "AND t.isCurrent = true "

        query += """
        RETURN t.keyword AS keyword,
               t.version AS version,
               t.isCurrent AS current,
               t.description AS description,
               t.complexity AS complexity,
               t.estimatedEffort AS estimatedEffort
        ORDER BY t.keyword, t.version DESC
        """

        params = {}
        if keyword:
            params["keyword"] = keyword

        with self.driver.session() as session:
            result = session.run(query, **params)

            templates = [{
                "keyword": record["keyword"],
                "version": record["version"],
                "current": record["current"],
                "description": record["description"],
                "complexity": record["complexity"],
                "estimatedEffort": record["estimatedEffort"]
            } for record in result]

            return templates

    def get_template(self, keyword, version=None):
        """Get a specific template by keyword and optional version"""
        query = """
        MATCH (t:ActionTemplate {keyword: $keyword})
        WHERE 1=1
        """

        if version:
            query += "AND t.version = $version "
        else:
            query += "AND t.isCurrent = true "

        query += """
        RETURN t.keyword AS keyword,
               t.version AS version,
               t.isCurrent AS current,
               t.description AS description,
               t.complexity AS complexity,
               t.estimatedEffort AS estimatedEffort,
               t.steps AS steps
        """

        params = {"keyword": keyword}
        if version:
            params["version"] = version

        with self.driver.session() as session:
            result = session.run(query, **params)
            record = result.single()

            if not record:
                return None

            template = {
                "keyword": record["keyword"],
                "version": record["version"],
                "current": record["current"],
                "description": record["description"],
                "complexity": record["complexity"],
                "estimatedEffort": record["estimatedEffort"],
                "steps": record["steps"]
            }

            return template

    def create_template(self, keyword, description, steps, version="1.0", complexity="MEDIUM", estimated_effort=30):
        """Create a new template"""
        # Check if a template with this keyword already exists
        with self.driver.session() as session:
            result = session.run("""
            MATCH (t:ActionTemplate {keyword: $keyword})
            RETURN count(t) AS count
            """, keyword=keyword)

            record = result.single()
            existing_count = record["count"] if record else 0

            if existing_count > 0:
                logger.warning(f"Templates with keyword '{keyword}' already exist. Consider updating instead.")
                return False

            # Create the new template
            result = session.run("""
            CREATE (t:ActionTemplate {
              keyword: $keyword,
              version: $version,
              isCurrent: true,
              description: $description,
              complexity: $complexity,
              estimatedEffort: $estimatedEffort,
              steps: $steps
            })
            RETURN t.keyword AS keyword, t.version AS version
            """,
            keyword=keyword,
            version=version,
            description=description,
            complexity=complexity,
            estimatedEffort=estimated_effort,
            steps=steps
            )

            record = result.single()

            if record:
                logger.info(f"Created new template: {record['keyword']} v{record['version']}")
                return True
            else:
                logger.error(f"Failed to create template '{keyword}'")
                return False

    def update_template(self, keyword, new_version, new_steps=None, new_description=None,
                        new_complexity=None, new_estimated_effort=None):
        """Update a template with a new version"""
        # Get the current template
        current = self.get_template(keyword)

        if not current:
            logger.error(f"No current template found with keyword '{keyword}'")
            return False

        # Use existing values if new ones are not provided
        steps = new_steps if new_steps is not None else current["steps"]
        description = new_description if new_description is not None else current["description"]
        complexity = new_complexity if new_complexity is not None else current["complexity"]
        estimated_effort = new_estimated_effort if new_estimated_effort is not None else current["estimatedEffort"]

        # Create a new version and update the current flag
        with self.driver.session() as session:
            # First check if the version already exists
            result = session.run("""
            MATCH (t:ActionTemplate {keyword: $keyword, version: $version})
            RETURN count(t) AS count
            """, keyword=keyword, version=new_version)

            record = result.single()
            if record and record["count"] > 0:
                logger.error(f"Template '{keyword}' version '{new_version}' already exists")
                return False

            # Start a transaction to update properly
            tx = session.begin_transaction()
            try:
                # Set current version to not current
                tx.run("""
                MATCH (old:ActionTemplate {keyword: $keyword, isCurrent: true})
                SET old.isCurrent = false
                """, keyword=keyword)

                # Create new version
                tx.run("""
                CREATE (new:ActionTemplate {
                  keyword: $keyword,
                  version: $version,
                  isCurrent: true,
                  description: $description,
                  complexity: $complexity,
                  estimatedEffort: $estimatedEffort,
                  steps: $steps
                })

                // Create a feedback node documenting the version change
                CREATE (f:Feedback {
                  id: $feedbackId,
                  content: $feedbackContent,
                  timestamp: datetime(),
                  source: 'TemplateManager',
                  severity: 'MEDIUM',
                  tags: ['version_update']
                })
                WITH f, new
                CREATE (f)-[:REGARDING]->(new)
                """,
                keyword=keyword,
                version=new_version,
                description=description,
                complexity=complexity,
                estimatedEffort=estimated_effort,
                steps=steps,
                feedbackId=str(uuid.uuid4()),
                feedbackContent=f"Updated from version {current['version']} to {new_version}"
                )

                # Commit the transaction
                tx.commit()
                logger.info(f"Updated template '{keyword}' to version '{new_version}'")
                return True

            except Exception as e:
                # Roll back on error
                tx.rollback()
                logger.error(f"Failed to update template: {e}")
                return False

    def export_template(self, keyword, output_file=None, version=None):
        """Export a template to a YAML or JSON file"""
        # Get the template
        template = self.get_template(keyword, version)

        if not template:
            logger.error(f"Template not found: '{keyword}'{' v' + version if version else ''}")
            return False

        # Default filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"template_{keyword}_v{template['version']}_{timestamp}.yaml"

        # Export data
        export_data = {
            "keyword": template["keyword"],
            "version": template["version"],
            "description": template["description"],
            "complexity": template["complexity"],
            "estimatedEffort": template["estimatedEffort"],
            "steps": template["steps"]
        }

        # Ensure directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine format from extension
        is_json = output_path.suffix.lower() in ['.json', '.jsn']

        # Write to file
        try:
            with open(output_path, 'w') as f:
                if is_json:
                    json.dump(export_data, f, indent=2)
                else:
                    yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)

            logger.info(f"Exported template '{keyword}' to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export template: {e}")
            return False

    def import_template(self, input_file, as_new_version=False):
        """Import a template from a YAML or JSON file"""
        input_path = Path(input_file)

        if not input_path.exists():
            logger.error(f"Input file not found: {input_file}")
            return False

        # Determine format from extension
        is_json = input_path.suffix.lower() in ['.json', '.jsn']

        # Read the file
        try:
            with open(input_path, 'r') as f:
                if is_json:
                    template_data = json.load(f)
                else:
                    template_data = yaml.safe_load(f)

            # Validate required fields
            required_fields = ["keyword", "version", "description", "steps"]
            for field in required_fields:
                if field not in template_data:
                    logger.error(f"Template file missing required field: {field}")
                    return False

            # Set default values for optional fields
            if "complexity" not in template_data:
                template_data["complexity"] = "MEDIUM"

            if "estimatedEffort" not in template_data:
                template_data["estimatedEffort"] = 30

            # Check if the template exists
            existing = self.get_template(template_data["keyword"])

            if existing:
                if as_new_version:
                    # Create a new version
                    new_version = template_data["version"]

                    # If the version in the file is the same as existing, increment it
                    if new_version == existing["version"]:
                        # Parse version
                        parts = new_version.split('.')
                        if len(parts) >= 2:
                            major, minor = int(parts[0]), int(parts[1])
                            new_version = f"{major}.{minor + 1}"
                        else:
                            new_version = f"{float(new_version) + 0.1:.1f}"

                        logger.info(f"Auto-incrementing version from {template_data['version']} to {new_version}")

                    # Update the template
                    return self.update_template(
                        template_data["keyword"],
                        new_version,
                        template_data["steps"],
                        template_data["description"],
                        template_data["complexity"],
                        template_data["estimatedEffort"]
                    )
                else:
                    logger.error(f"Template '{template_data['keyword']}' already exists. Use --as-new-version to update.")
                    return False
            else:
                # Create a new template
                return self.create_template(
                    template_data["keyword"],
                    template_data["description"],
                    template_data["steps"],
                    template_data["version"],
                    template_data["complexity"],
                    template_data["estimatedEffort"]
                )

        except Exception as e:
            logger.error(f"Failed to import template: {e}")
            return False

    def archive_template(self, keyword, version=None):
        """Archive a template by setting isCurrent=false"""
        # Can only archive if there's more than one version, or if version is specified
        with self.driver.session() as session:
            # Count versions
            result = session.run("""
            MATCH (t:ActionTemplate {keyword: $keyword})
            RETURN count(t) AS count
            """, keyword=keyword)

            record = result.single()
            if not record:
                logger.error(f"No templates found with keyword '{keyword}'")
                return False

            count = record["count"]

            if count == 0:
                logger.error(f"No templates found with keyword '{keyword}'")
                return False

            if count == 1 and not version:
                logger.error(f"Cannot archive the only version of template '{keyword}'. Use --version to specify.")
                return False

            # If version is specified, archive just that version
            if version:
                # Check if it's the current version
                result = session.run("""
                MATCH (t:ActionTemplate {keyword: $keyword, version: $version})
                RETURN t.isCurrent AS isCurrent
                """, keyword=keyword, version=version)

                record = result.single()
                if not record:
                    logger.error(f"Template '{keyword}' version '{version}' not found")
                    return False

                is_current = record["isCurrent"]

                if is_current:
                    logger.error("Cannot archive current version. Please update to a new version first.")
                    return False

                # Archive this version (set archived=true)
                session.run("""
                MATCH (t:ActionTemplate {keyword: $keyword, version: $version})
                SET t.archived = true, t.archiveDate = datetime()
                """, keyword=keyword, version=version)

                logger.info(f"Archived template '{keyword}' version '{version}'")
                return True
            else:
                # Archive all non-current versions
                result = session.run("""
                MATCH (t:ActionTemplate {keyword: $keyword})
                WHERE t.isCurrent = false
                SET t.archived = true, t.archiveDate = datetime()
                RETURN count(t) AS archived
                """, keyword=keyword)

                record = result.single()
                if not record:
                    logger.warning(f"No non-current versions to archive for template '{keyword}'")
                    return False

                archived = record["archived"]

                if archived > 0:
                    logger.info(f"Archived {archived} non-current versions of template '{keyword}'")
                    return True
                else:
                    logger.warning(f"No non-current versions to archive for template '{keyword}'")
                    return False

    def set_current_version(self, keyword, version):
        """Set a specific version as the current version"""
        with self.driver.session() as session:
            # Check if the version exists
            result = session.run("""
            MATCH (t:ActionTemplate {keyword: $keyword, version: $version})
            RETURN count(t) AS count
            """, keyword=keyword, version=version)

            record = result.single()
            if not record or record["count"] == 0:
                logger.error(f"Template '{keyword}' version '{version}' not found")
                return False

            # Start a transaction
            tx = session.begin_transaction()
            try:
                # Set current version to not current
                tx.run("""
                MATCH (old:ActionTemplate {keyword: $keyword, isCurrent: true})
                SET old.isCurrent = false
                """, keyword=keyword)

                # Set specified version to current
                tx.run("""
                MATCH (new:ActionTemplate {keyword: $keyword, version: $version})
                SET new.isCurrent = true

                // Create a feedback node documenting the change
                CREATE (f:Feedback {
                  id: $feedbackId,
                  content: $feedbackContent,
                  timestamp: datetime(),
                  source: 'TemplateManager',
                  severity: 'MEDIUM',
                  tags: ['version_change']
                })
                WITH f, new
                CREATE (f)-[:REGARDING]->(new)
                """,
                keyword=keyword,
                version=version,
                feedbackId=str(uuid.uuid4()),
                feedbackContent=f"Changed current version to {version}"
                )

                # Commit the transaction
                tx.commit()
                logger.info(f"Set template '{keyword}' version '{version}' as current")
                return True

            except Exception as e:
                # Roll back on error
                tx.rollback()
                logger.error(f"Failed to set current version: {e}")
                return False

    def export_all_templates(self, output_dir):
        """Export all current templates to files in a directory"""
        templates = self.list_templates()

        if not templates:
            logger.warning("No templates found to export")
            return False

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        success_count = 0
        for template in templates:
            keyword = template["keyword"]
            version = template["version"]

            output_file = output_path / f"{keyword}_{version}.yaml"
            if self.export_template(keyword, output_file):
                success_count += 1

        if success_count > 0:
            logger.info(f"Exported {success_count} templates to {output_path}")
            return True
        else:
            logger.error("Failed to export any templates")
            return False

    def import_directory(self, input_dir, as_new_version=False):
        """Import all template files from a directory"""
        input_path = Path(input_dir)

        if not input_path.exists() or not input_path.is_dir():
            logger.error(f"Input directory not found: {input_dir}")
            return False

        # Find all YAML and JSON files
        yaml_files = list(input_path.glob("*.yaml")) + list(input_path.glob("*.yml"))
        json_files = list(input_path.glob("*.json"))

        template_files = yaml_files + json_files

        if not template_files:
            logger.warning(f"No template files found in {input_dir}")
            return False

        logger.info(f"Found {len(template_files)} template files")

        success_count = 0
        for file_path in template_files:
            logger.info(f"Importing template from {file_path}")
            if self.import_template(file_path, as_new_version):
                success_count += 1

        if success_count > 0:
            logger.info(f"Successfully imported {success_count} out of {len(template_files)} templates")
            return True
        else:
            logger.error("Failed to import any templates")
            return False

def display_table(data, headers):
    """Display data in a nicely formatted table"""
    if not data:
        print("No data to display")
        return

    print(tabulate(data, headers=headers, tablefmt="grid"))
    print()


def main():
    parser = argparse.ArgumentParser(description='Neo4j Template Management Utility')
    parser.add_argument('--uri', default='bolt://localhost:7687', help='Neo4j connection URI')
    parser.add_argument('--username', default='neo4j', help='Neo4j username')
    parser.add_argument('--password', required=True, help='Neo4j password')

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # List templates
    list_parser = subparsers.add_parser('list', help='List templates')
    list_parser.add_argument('--keyword', help='Filter by keyword')
    list_parser.add_argument('--include-inactive', action='store_true', help='Include non-current versions')

    # Show template details
    show_parser = subparsers.add_parser('show', help='Show template details')
    show_parser.add_argument('--keyword', required=True, help='Template keyword')
    show_parser.add_argument('--version', help='Template version (defaults to current)')

    # Create template
    create_parser = subparsers.add_parser('create', help='Create a new template')
    create_parser.add_argument('--keyword', required=True, help='Template keyword')
    create_parser.add_argument('--description', required=True, help='Template description')
    create_parser.add_argument('--steps', required=True, help='Path to file containing steps content')
    create_parser.add_argument('--version', default='1.0', help='Template version')
    create_parser.add_argument('--complexity', default='MEDIUM', choices=['LOW', 'MEDIUM', 'HIGH'], help='Template complexity')
    create_parser.add_argument('--effort', type=int, default=30, help='Estimated effort in minutes')

    # Update template
    update_parser = subparsers.add_parser('update', help='Update a template with a new version')
    update_parser.add_argument('--keyword', required=True, help='Template keyword')
    update_parser.add_argument('--new-version', required=True, help='New version number')
    update_parser.add_argument('--steps', help='Path to file containing new steps content')
    update_parser.add_argument('--description', help='New description')
    update_parser.add_argument('--complexity', choices=['LOW', 'MEDIUM', 'HIGH'], help='New complexity')
    update_parser.add_argument('--effort', type=int, help='New estimated effort in minutes')

    # Export template
    export_parser = subparsers.add_parser('export', help='Export a template to a file')
    export_parser.add_argument('--keyword', required=True, help='Template keyword')
    export_parser.add_argument('--output', help='Output file path')
    export_parser.add_argument('--version', help='Template version (defaults to current)')

    # Import template
    import_parser = subparsers.add_parser('import', help='Import a template from a file')
    import_parser.add_argument('--input', required=True, help='Input file path')
    import_parser.add_argument('--as-new-version', action='store_true', help='Import as a new version if template exists')

    # Archive template
    archive_parser = subparsers.add_parser('archive', help='Archive a template')
    archive_parser.add_argument('--keyword', required=True, help='Template keyword')
    archive_parser.add_argument('--version', help='Specific version to archive (defaults to all non-current versions)')

    # Set current version
    current_parser = subparsers.add_parser('set-current', help='Set a specific version as current')
    current_parser.add_argument('--keyword', required=True, help='Template keyword')
    current_parser.add_argument('--version', required=True, help='Version to set as current')

    # Export all templates
    export_all_parser = subparsers.add_parser('export-all', help='Export all current templates')
    export_all_parser.add_argument('--output-dir', required=True, help='Output directory')

    # Import all templates from directory
    import_dir_parser = subparsers.add_parser('import-dir', help='Import all templates from a directory')
    import_dir_parser.add_argument('--input-dir', required=True, help='Input directory')
    import_dir_parser.add_argument('--as-new-version', action='store_true', help='Import as new versions if templates exist')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = Neo4jTemplateManager(args.uri, args.username, args.password)

    try:
        if args.command == 'list':
            templates = manager.list_templates(args.keyword, args.include_inactive)

            # Format data for display
            display_data = []
            for t in templates:
                current = "Current" if t["current"] else "Inactive"
                display_data.append([
                    t["keyword"],
                    t["version"],
                    current,
                    t["complexity"] or "N/A",
                    t["estimatedEffort"] or "N/A",
                    t["description"] or "N/A"
                ])

            display_table(display_data, ["Keyword", "Version", "Status", "Complexity", "Effort (min)", "Description"])

        elif args.command == 'show':
            template = manager.get_template(args.keyword, args.version)

            if template:
                print(f"Template: {template['keyword']} v{template['version']}")
                print(f"Status: {'Current' if template['current'] else 'Inactive'}")
                print(f"Description: {template['description']}")
                print(f"Complexity: {template['complexity']}")
                print(f"Estimated Effort: {template['estimatedEffort']} minutes")
                print("\nSteps:\n")
                print(template['steps'])
            else:
                version_str = f" v{args.version}" if args.version else ""
                print(f"Template not found: '{args.keyword}'{version_str}")

        elif args.command == 'create':
            # Read steps from file
            try:
                with open(args.steps, 'r') as f:
                    steps_content = f.read()
            except Exception as e:
                print(f"Error reading steps file: {e}")
                return

            if manager.create_template(
                args.keyword,
                args.description,
                steps_content,
                args.version,
                args.complexity,
                args.effort
            ):
                print(f"Successfully created template '{args.keyword}' v{args.version}")
            else:
                print("Failed to create template")

        elif args.command == 'update':
            # Read steps from file if provided
            steps_content = None
            if args.steps:
                try:
                    with open(args.steps, 'r') as f:
                        steps_content = f.read()
                except Exception as e:
                    print(f"Error reading steps file: {e}")
                    return

            if manager.update_template(
                args.keyword,
                args.new_version,
                steps_content,
                args.description,
                args.complexity,
                args.effort
            ):
                print(f"Successfully updated template '{args.keyword}' to v{args.new_version}")
            else:
                print("Failed to update template")

        elif args.command == 'export':
            if manager.export_template(args.keyword, args.output, args.version):
                output_file = args.output or f"template_{args.keyword}.yaml"
                print(f"Successfully exported template to {output_file}")
            else:
                print("Failed to export template")

        elif args.command == 'import':
            if manager.import_template(args.input, args.as_new_version):
                print(f"Successfully imported template from {args.input}")
            else:
                print("Failed to import template")

        elif args.command == 'archive':
            if manager.archive_template(args.keyword, args.version):
                if args.version:
                    print(f"Successfully archived template '{args.keyword}' v{args.version}")
                else:
                    print(f"Successfully archived non-current versions of template '{args.keyword}'")
            else:
                print("Failed to archive template")

        elif args.command == 'set-current':
            if manager.set_current_version(args.keyword, args.version):
                print(f"Successfully set '{args.keyword}' v{args.version} as current")
            else:
                print("Failed to set current version")

        elif args.command == 'export-all':
            if manager.export_all_templates(args.output_dir):
                print(f"Successfully exported all templates to {args.output_dir}")
            else:
                print("Failed to export templates")

        elif args.command == 'import-dir':
            if manager.import_directory(args.input_dir, args.as_new_version):
                print(f"Successfully imported templates from {args.input_dir}")
            else:
                print("Failed to import templates")

    finally:
        manager.close()


if __name__ == "__main__":
    main()
