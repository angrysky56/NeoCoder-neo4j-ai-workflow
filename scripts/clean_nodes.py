#!/usr/bin/env python3
"""
Manual Node Cleaning Utility for Neo4j-Guided AI Coding Workflow

This script allows for controlled cleanup and maintenance of the graph structure:
- View outdated templates
- Archive or delete old workflow executions
- Clean up orphaned nodes
- Update project file structure to match reality

The script provides a verification step before any destructive operations.
"""

import sys
import logging
import argparse
import uuid
from datetime import datetime, timedelta
from neo4j import GraphDatabase
from tabulate import tabulate
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Neo4jGraphCleaner:
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

    def find_outdated_templates(self):
        """Find outdated (non-current) templates"""
        with self.driver.session() as session:
            result = session.run("""
            MATCH (t:ActionTemplate)
            WHERE t.isCurrent = false OR t.isCurrent IS NULL
            RETURN t.keyword, t.version, t.description
            ORDER BY t.keyword, t.version
            """)

            templates = [(record["t.keyword"], record["t.version"], record["t.description"])
                        for record in result]

            if not templates:
                logger.info("No outdated templates found")
                return []

            logger.info(f"Found {len(templates)} outdated templates")
            return templates

    def find_old_workflow_executions(self, days=90):
        """Find workflow executions older than the specified number of days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")

        with self.driver.session() as session:
            result = session.run("""
            MATCH (w:WorkflowExecution)
            WHERE w.timestamp < datetime($cutoff)
            RETURN w.id, w.keywordUsed, w.timestamp, w.description
            ORDER BY w.timestamp
            """, cutoff=cutoff_str)

            executions = [(record["w.id"], record["w.keywordUsed"],
                          record["w.timestamp"], record["w.description"])
                          for record in result]

            if not executions:
                logger.info(f"No workflow executions older than {days} days found")
                return []

            logger.info(f"Found {len(executions)} workflow executions older than {days} days")
            return executions

    def find_orphaned_files(self):
        """Find file/directory nodes not linked to a project or workflow execution"""
        with self.driver.session() as session:
            result = session.run("""
            MATCH (f)
            WHERE (f:File OR f:Directory)
            AND NOT (f)<-[:CONTAINS]-()
            AND NOT (f)<-[:MODIFIED]-()
            RETURN labels(f) AS type, f.path, f.project_id
            """)

            orphans = [(record["type"][-1], record["f.path"], record["f.project_id"])
                       for record in result]

            if not orphans:
                logger.info("No orphaned file/directory nodes found")
                return []

            logger.info(f"Found {len(orphans)} orphaned file/directory nodes")
            return orphans

    def archive_workflow_executions(self, execution_ids, confirm=True):
        """Archive workflow executions by setting archived=true"""
        if not execution_ids:
            logger.info("No workflow executions to archive")
            return 0

        # Display what will be archived
        logger.info(f"Preparing to archive {len(execution_ids)} workflow executions")

        if confirm:
            confirmation = input(f"Do you want to archive {len(execution_ids)} workflow executions? (y/n): ")
            if confirmation.lower() != 'y':
                logger.info("Archive operation cancelled")
                return 0

        archive_date = datetime.now().isoformat()

        with self.driver.session() as session:
            result = session.run("""
            UNWIND $ids AS id
            MATCH (w:WorkflowExecution {id: id})
            SET w.archived = true, w.archiveDate = $archiveDate
            RETURN count(w) AS archived
            """, ids=execution_ids, archiveDate=archive_date)

            count = result.single()["archived"]
            logger.info(f"Archived {count} workflow executions")
            return count

    def delete_orphaned_files(self, file_paths, confirm=True):
        """Delete orphaned file/directory nodes"""
        if not file_paths:
            logger.info("No orphaned files to delete")
            return 0

        # Display what will be deleted
        logger.info(f"Preparing to delete {len(file_paths)} orphaned file/directory nodes")

        if confirm:
            confirmation = input(f"Do you want to delete {len(file_paths)} orphaned file nodes? (y/n): ")
            if confirmation.lower() != 'y':
                logger.info("Delete operation cancelled")
                return 0

        with self.driver.session() as session:
            result = session.run("""
            UNWIND $paths AS path
            MATCH (f)
            WHERE (f:File OR f:Directory) AND f.path = path
            AND NOT (f)<-[:CONTAINS]-()
            AND NOT (f)<-[:MODIFIED]-()
            DETACH DELETE f
            RETURN count(f) AS deleted
            """, paths=file_paths)

            count = result.single()["deleted"]
            logger.info(f"Deleted {count} orphaned file/directory nodes")
            return count

    def update_template_version(self, keyword, new_version, steps_content=None, confirm=True):
        """Create a new version of a template with updated content"""
        with self.driver.session() as session:
            # Check if the template exists
            result = session.run("""
            MATCH (t:ActionTemplate {keyword: $keyword, isCurrent: true})
            RETURN t.version, t.steps
            """, keyword=keyword)

            record = result.single()
            if not record:
                logger.error(f"No current template found with keyword '{keyword}'")
                return False

            current_version = record["t.version"]
            current_steps = record["t.steps"]

            logger.info(f"Found current template version: {current_version}")

            if steps_content is None:
                # Keep the same content
                steps_content = current_steps

            # Show preview of changes
            logger.info(
                f"Preparing to update template '{keyword}' "
                f"from version {current_version} to {new_version}"
            )

            if confirm:
                confirmation = input(
                    f"Do you want to create new version {new_version} "
                    f"for template '{keyword}'? (y/n): "
                )
                if confirmation.lower() != 'y':
                    logger.info("Update operation cancelled")
                    return False

            # Create new version and update current flag
            session.run("""
            MATCH (old:ActionTemplate {keyword: $keyword, isCurrent: true})
            SET old.isCurrent = false

            WITH old
            CREATE (new:ActionTemplate {
                keyword: $keyword,
                version: $newVersion,
                isCurrent: true,
                description: old.description,
                steps: $steps,
                complexity: old.complexity,
                estimatedEffort: old.estimatedEffort
            })

            // Create a feedback node documenting the version change
            CREATE (f:Feedback {
                id: $feedbackId,
                content: $feedbackContent,
                timestamp: datetime(),
                source: $source,
                severity: 'MEDIUM'
            })
            CREATE (f)-[:REGARDING]->(new)
            """,
            keyword=keyword,
            newVersion=new_version,
            steps=steps_content,
            feedbackId=str(uuid.uuid4()),
            feedbackContent=f"Updated from version {current_version} to {new_version}",
            source="CleaningUtility"
            )

            logger.info(f"Created new version {new_version} for template '{keyword}'")
            logger.info(f"Previous version {current_version} marked as non-current")
            return True

    def synchronize_project_files(self, project_id, real_file_paths, confirm=True):
        """Synchronize project file structure with real directory structure"""
        # Convert all paths to strings if they're Path objects
        real_file_paths = [str(p) for p in real_file_paths]

        with self.driver.session() as session:
            # Get current file structure
            result = session.run("""
            MATCH (p:Project {projectId: $projectId})-[:CONTAINS*]->(f:File)
            RETURN f.path AS path
            """, projectId=project_id)

            current_paths = [record["path"] for record in result]

            # Calculate differences
            paths_to_add = [p for p in real_file_paths if p not in current_paths]
            paths_to_remove = [p for p in current_paths if p not in real_file_paths]

            if not paths_to_add and not paths_to_remove:
                logger.info(f"Project {project_id} file structure is already in sync")
                return True

            logger.info(f"For project {project_id}:")
            logger.info(f"  - {len(paths_to_add)} paths to add")
            logger.info(f"  - {len(paths_to_remove)} paths to remove")

            if confirm:
                confirmation = input(f"Do you want to synchronize file structure for project {project_id}? (y/n): ")
                if confirmation.lower() != 'y':
                    logger.info("Synchronization cancelled")
                    return False

            # Remove outdated paths
            if paths_to_remove:
                result = session.run("""
                UNWIND $paths AS path
                MATCH (f:File {path: path, project_id: $projectId})
                DETACH DELETE f
                RETURN count(f) AS removed
                """, paths=paths_to_remove, projectId=project_id)

                removed = result.single()["removed"]
                logger.info(f"Removed {removed} outdated file nodes")

            # Add new paths
            if paths_to_add:
                # Group paths by directory to create directory structure first
                directories = {str(Path(p).parent) for p in paths_to_add if '/' in p}
                directories = sorted(directories)  # Sort to ensure parent dirs created first

                # Create directory structure
                for dir_path in directories:
                    session.run("""
                    MATCH (p:Project {projectId: $projectId})
                    MERGE (d:Directory {path: $path, project_id: $projectId})
                    MERGE (p)-[:CONTAINS]->(d)
                    """, path=dir_path, projectId=project_id)

                # Link files to their parent directories
                for file_path in paths_to_add:
                    parent_dir = str(Path(file_path).parent)
                    if parent_dir == '.':
                        # Top-level file
                        session.run("""
                        MATCH (p:Project {projectId: $projectId})
                        MERGE (f:File {path: $path, project_id: $projectId})
                        MERGE (p)-[:CONTAINS]->(f)
                        """, path=file_path, projectId=project_id)
                    else:
                        # File in subdirectory
                        session.run("""
                        MATCH (d:Directory {path: $dirPath, project_id: $projectId})
                        MERGE (f:File {path: $filePath, project_id: $projectId})
                        MERGE (d)-[:CONTAINS]->(f)
                        """, dirPath=parent_dir, filePath=file_path, projectId=project_id)

                logger.info(f"Added {len(paths_to_add)} new file nodes")

            return True


def display_table(data, headers):
    """Display data in a nicely formatted table"""
    if not data:
        print("No data to display")
        return

    print(tabulate(data, headers=headers, tablefmt="grid"))
    print()


def main():
    parser = argparse.ArgumentParser(description='Neo4j Graph Cleaning Utility')
    parser.add_argument('--uri', default='bolt://localhost:7687', help='Neo4j connection URI')
    parser.add_argument('--username', default='neo4j', help='Neo4j username')
    parser.add_argument('--password', required=True, help='Neo4j password')

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # List outdated templates
    list_templates_parser = subparsers.add_parser('list-outdated-templates', help='List outdated templates')

    # List old workflow executions
    list_executions_parser = subparsers.add_parser('list-old-executions', help='List old workflow executions')
    list_executions_parser.add_argument('--days', type=int, default=90, help='Age threshold in days')

    # List orphaned files
    list_orphans_parser = subparsers.add_parser('list-orphaned-files', help='List orphaned file nodes')

    # Archive old workflow executions
    archive_parser = subparsers.add_parser('archive-executions', help='Archive old workflow executions')
    archive_parser.add_argument('--days', type=int, default=90, help='Age threshold in days')
    archive_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')

    # Delete orphaned files
    delete_parser = subparsers.add_parser('delete-orphaned-files', help='Delete orphaned file nodes')
    delete_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')

    # Update template version
    update_parser = subparsers.add_parser('update-template', help='Update template version')
    update_parser.add_argument('--keyword', required=True, help='Template keyword')
    update_parser.add_argument('--new-version', required=True, help='New version number')
    update_parser.add_argument('--steps-file', help='File containing new steps content')
    update_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')

    # Synchronize project files
    sync_parser = subparsers.add_parser('sync-project-files', help='Synchronize project file structure')
    sync_parser.add_argument('--project-id', required=True, help='Project ID')
    sync_parser.add_argument('--directory', required=True, help='Real project directory to sync with')
    sync_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cleaner = Neo4jGraphCleaner(args.uri, args.username, args.password)

    try:
        if args.command == 'list-outdated-templates':
            templates = cleaner.find_outdated_templates()
            display_table(templates, ["Keyword", "Version", "Description"])

        elif args.command == 'list-old-executions':
            executions = cleaner.find_old_workflow_executions(args.days)
            display_table(executions, ["ID", "Keyword", "Timestamp", "Description"])

        elif args.command == 'list-orphaned-files':
            orphans = cleaner.find_orphaned_files()
            display_table(orphans, ["Type", "Path", "Project ID"])

        elif args.command == 'archive-executions':
            executions = cleaner.find_old_workflow_executions(args.days)
            if executions:
                execution_ids = [exc[0] for exc in executions]
                cleaner.archive_workflow_executions(execution_ids, not args.force)

        elif args.command == 'delete-orphaned-files':
            orphans = cleaner.find_orphaned_files()
            if orphans:
                file_paths = [orph[1] for orph in orphans]
                cleaner.delete_orphaned_files(file_paths, not args.force)

        elif args.command == 'update-template':
            steps_content = None
            if args.steps_file:
                with open(args.steps_file, 'r') as f:
                    steps_content = f.read()

            cleaner.update_template_version(
                args.keyword,
                args.new_version,
                steps_content,
                not args.force
            )

        elif args.command == 'sync-project-files':
            if not Path(args.directory).exists():
                logger.error(f"Directory not found: {args.directory}")
                return

            # Get real file paths (recursively)
            real_paths = []
            for path in Path(args.directory).rglob('*'):
                if path.is_file():
                    # Convert to relative path
                    rel_path = path.relative_to(args.directory)
                    real_paths.append(str(rel_path))

            logger.info(f"Found {len(real_paths)} files in {args.directory}")
            cleaner.synchronize_project_files(args.project_id, real_paths, not args.force)

    finally:
        cleaner.close()


if __name__ == "__main__":
    main()
