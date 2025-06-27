"""
Cypher Snippet Toolkit for the Neo4j-Guided AI Coding Workflow

This module provides functionality to manage and search for Cypher snippets
in the Neo4j database.
"""

import json
import logging
from typing import List, Optional

import mcp.types as types
from .event_loop_manager import safe_neo4j_session
# from pydantic import Field
from neo4j import AsyncManagedTransaction, AsyncDriver

logger = logging.getLogger("mcp_neocoder.cypher_snippets")


class CypherSnippetMixin:
    """Mixin class providing Cypher snippet functionality for the Neo4jWorkflowServer."""

    def __init__(self, database: Optional[str] = None, driver: Optional[AsyncDriver] = None, *args, **kwargs):
        """
        Initialize cypher snippet mixin with keyword arguments for inheritance compatibility.

        Args:
            database: Optional[str] - The Neo4j database name.
            driver: AsyncDriver - The Neo4j async driver instance.
        """
        # Expected instance attributes:
        #   self.driver: AsyncDriver
        #   self.database: Optional[str]
        if not hasattr(self, 'database'):
            self.database = database
        if not hasattr(self, 'driver'):
            if driver is None:
                raise ValueError(
                    "Neo4j driver is not initialized or is None. "
                    "It must be provided to CypherSnippetMixin's constructor as a valid driver instance, "
                    "or initialized by a superclass."
                )
            self.driver = driver

        if self.driver is None:
            raise ValueError(
                "Neo4j driver is not initialized or is None. "
                "It must be provided to CypherSnippetMixin's constructor as a valid driver instance, "
                "or initialized by a superclass."
            )

        super().__init__(*args, **kwargs)

        # After super().__init__(), self.driver might have been set by a parent,
        # or it retains the value from above. We must ensure it's not None.
        if not hasattr(self, 'driver') or self.driver is None:
            raise ValueError(
                "Neo4j driver is not initialized or is None. "
                "It must be provided to CypherSnippetMixin's constructor as a valid driver instance, "
                "or initialized by a superclass."
            )

    async def _read_query(
        self,
        tx: AsyncManagedTransaction,
        query: str,
        params: dict[str, object]
    ) -> str:
        """Execute a read query and return results as JSON string."""
        raise NotImplementedError(
            "_read_query must be implemented by the parent class"
        )

    async def _write(
        self,
        tx: AsyncManagedTransaction,
        query: str,
        params: dict
    ):
        """Execute a write query and return results as JSON string."""
        raise NotImplementedError(
            "_write must be implemented by the parent class"
        )

    async def list_cypher_snippets(
        self,
        limit: int = 20,
        offset: int = 0,
        tag: Optional[str] = None,
        since_version: Optional[float] = None
    ) -> List[types.TextContent]:
        """List all available Cypher snippets with optional filtering."""
        # Ensure limit and offset are integers
        limit = int(limit)
        offset = int(offset)

        query = """
        MATCH (c:CypherSnippet)
        WHERE 1=1
        """

        params: dict[str, object] = {"limit": limit, "offset": offset}

        # Add optional filters
        if tag:
            query += """
            AND (c)-[:TAGGED_AS]->(:Tag {name: $tag})
            """
            params["tag"] = tag

        if since_version is not None:
            query += """
            AND c.since <= $since_version
            """
            params["since_version"] = since_version

        query += """
        RETURN c.id AS id,
               c.name AS name,
               c.description AS description,
               c.since AS since
        ORDER BY c.name
        SKIP $offset
        LIMIT $limit
        """

        try:
            async with safe_neo4j_session(self.driver, self.database or "") as session:
                results_json = await session.execute_read(
                    self._read_query,
                    query,
                    params
                )
                results = json.loads(results_json)

                if results and len(results) > 0:
                    text = "# Available Cypher Snippets\n\n"

                    if tag:
                        text += "Filtered by tag: `{}`\n\n".format(tag)
                    if since_version is not None:
                        text += (
                            "Compatible with Neo4j version: "
                            "{} and newer\n\n".format(since_version)
                        )

                    text += "| ID | Name | Since Version | Description |\n"
                    text += "| -- | ---- | ------------- | ----------- |\n"

                    for snippet in results:
                        text += (
                            "| {} | {} | {} | {} |\n".format(
                                snippet.get('id', 'N/A'),
                                snippet.get('name', 'N/A'),
                                snippet.get('since', 'N/A'),
                                snippet.get('since', 'N/A') if isinstance(snippet.get('since', None), (str, float, int)) else 'N/A',
                            )
                        )

                    return [types.TextContent(type="text", text=text)]
                else:
                    filter_msg = ""
                    if tag:
                        filter_msg += " with tag '{}'".format(tag)
                    if since_version is not None:
                        if filter_msg:
                            filter_msg += " and"
                        filter_msg += " compatible with Neo4j {}".format(since_version)

                    if filter_msg:
                        return [
                            types.TextContent(
                                type="text",
                                text="No Cypher snippets found{}.".format(filter_msg)
                            )
                        ]
                    else:
                        return [
                            types.TextContent(
                                type="text",
                                text="No Cypher snippets found in the database."
                            )
                        ]
        except Exception as e:
            logger.error("Error listing Cypher snippets: {}".format(e))
            return [
                types.TextContent(
                    type="text",
                    text="Error: {}".format(e)
                )
            ]
    async def get_cypher_snippet(
        self,
        id: str
    ) -> List[types.TextContent]:
        """Get a specific Cypher snippet by ID."""
        query = """
        MATCH (c:CypherSnippet {id: $id})
        OPTIONAL MATCH (c)-[:TAGGED_AS]->(t:Tag)
        WITH c, collect(t.name) AS tags
        RETURN c.id AS id,
               c.name AS name,
               c.syntax AS syntax,
               c.description AS description,
               c.example AS example,
               c.since AS since,
               tags
        """

        try:
            async with safe_neo4j_session(self.driver, self.database or "") as session:
                results_json = await session.execute_read(
                    self._read_query,
                    query,
                    {"id": id}
                )
                results = json.loads(results_json)

                if results and len(results) > 0:
                    snippet = results[0]
                    text = f"# Cypher Snippet: {snippet.get('name', id)}\n\n"
                    text += f"**ID:** `{snippet.get('id', id)}`\n"
                    text += f"**Neo4j Version:** {snippet.get('since', 'N/A')}\n"
                    text += f"**Neo4j Version:** {snippet.get('since', 'N/A') if isinstance(snippet.get('since', None), (str, float, int)) else 'N/A'}\n"
                    if snippet.get('tags'):
                        tags = snippet.get('tags', [])
                        tag_links = [f'`{tag}`' for tag in tags]
                        text += f"**Tags:** {', '.join(tag_links)}\n"

                    text += (
                        f"\n**Description:**\n"
                        f"{snippet.get('description', 'No description available.')}\n"
                    )

                    text += (
                        f"\n**Syntax:**\n```cypher\n"
                        f"{snippet.get('syntax', '')}\n```\n"
                    )

                    if snippet.get('example'):
                        text += (
                            f"\n**Example:**\n```cypher\n"
                            f"{snippet.get('example', '')}\n```\n"
                        )

                    return [types.TextContent(type="text", text=text)]
                else:
                    return [
                        types.TextContent(
                            type="text",
                            text=f"No Cypher snippet found with ID '{id}'"
                        )
                    ]
        except Exception as e:
            logger.error(f"Error retrieving Cypher snippet: {e}")
            return [
                types.TextContent(
                    type="text",
                    text=f"Error: {e}"
                )
            ]

    async def search_cypher_snippets(
        self,
        query_text: str,
        search_type: str = "text",
        limit: int = 10
    ) -> List[types.TextContent]:
        """Search for Cypher snippets by keyword, tag, or pattern."""
        # Ensure limit is an integer
        limit = int(limit)

        query = ""
        params = {"query_text": query_text, "limit": limit}

        if search_type.lower() == "text":
            # Text search using TEXT index
            params["search_pattern"] = f"(?i).*{query_text}.*"  # Case-insensitive
            query = """
            MATCH (c:CypherSnippet)
            WHERE c.syntax =~ $search_pattern
               OR c.description =~ $search_pattern
            RETURN c.id AS id,
                   c.name AS name,
                   c.description AS description,
                   c.since AS since,
                   c.syntax AS syntax
            ORDER BY c.name
            LIMIT $limit
            """
        elif search_type.lower() == "fulltext":
            # Full-text search using FULLTEXT index
            query = """
            CALL db.index.fulltext.queryNodes('snippet_fulltext', $query_text)
            YIELD node, score
            RETURN node.id AS id,
                   node.name AS name,
                   node.description AS description,
                   node.since AS since,
                   node.syntax AS syntax,
                   score
            ORDER BY score DESC
            LIMIT $limit
            """
        elif search_type.lower() == "tag":
            # Tag search
            query = """
            MATCH (c:CypherSnippet)-[:TAGGED_AS]->(t:Tag)
            WHERE t.name = $query_text
            RETURN c.id AS id,
                   c.name AS name,
                   c.description AS description,
                   c.since AS since,
                   c.syntax AS syntax
            ORDER BY c.name
            LIMIT $limit
            """
        else:
            error_msg = (
                f"Invalid search type: '{search_type}'. "
                f"Valid options are 'text', 'fulltext', or 'tag'."
            )
            return [types.TextContent(type="text", text=error_msg)]

        try:
            async with safe_neo4j_session(self.driver, self.database or "") as session:
                results_json = await session.execute_read(
                    self._read_query,
                    query,
                    params
                )
                results = json.loads(results_json)

                if results and len(results) > 0:
                    text = "# Cypher Snippet Search Results\n\n"
                    text += f"Query: '{query_text}' (Search type: {search_type})\n\n"

                    for i, snippet in enumerate(results, 1):
                        score_text = ""
                        if 'score' in snippet:
                            score_text = f" (Score: {snippet.get('score', 'N/A')})"

                        text += (
                            f"## {i}. {snippet.get('name', 'Unnamed Snippet')}"
                            f"{score_text}\n\n"
                        )
                        text += f"**ID:** `{snippet.get('id', 'unknown')}`\n"
                        text += (
                            f"**Description:** "
                            f"{snippet.get('description', 'No description')}\n"
                        )
                        text += (
                            f"**Syntax:** `{snippet.get('syntax', 'No syntax')}`\n\n"
                        )

                    view_details_msg = (
                        "\nUse `get_cypher_snippet(id=\"snippet-id\")` "
                        "to view full details of any result."
                    )
                    text += view_details_msg

                    return [types.TextContent(type="text", text=text)]
                else:
                    not_found_msg = (
                        f"No Cypher snippets found matching '{query_text}' "
                        f"with search type '{search_type}'."
                    )
                    return [types.TextContent(type="text", text=not_found_msg)]
        except Exception as e:
            logger.error(f"Error searching Cypher snippets: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def create_cypher_snippet(
        self,
        id: str,
        name: str,
        syntax: str,
        description: str,
        example: Optional[str] = None,
        since: Optional[float] = None,
        tags: Optional[List[str]] = None
    ) -> List[types.TextContent]:
        """Add a new Cypher snippet to the database."""
        snippet_tags = tags or []
        snippet_since = since or 5.0  # Default to Neo4j 5.0 if not specified
        snippet_since = since or 5.0  # Default to Neo4j 5.0 if not specified

        query = """
        MERGE (c:CypherSnippet {id: $id})
        ON CREATE SET c.name = $name,
                      c.syntax = $syntax,
                      c.description = $description,
                      c.since = $since,
                      c.lastUpdated = date()
        """

        params = {
            "id": id,
            "name": name,
            "syntax": syntax,
            "description": description,
            "since": float(snippet_since),  # Always store as float
            "tags": snippet_tags
        }
        if example:
            query += ", c.example = $example"
            params["example"] = example

        query += """
        WITH c, $tags AS tags
        UNWIND tags AS tag
          MERGE (t:Tag {name: tag})
          MERGE (c)-[:TAGGED_AS]->(t)
        RETURN c.id AS id, c.name AS name
        """

        try:
            async with safe_neo4j_session(self.driver, self.database or "") as session:
                results_json = await session.execute_write(
                    self._write,
                    query,
                    params
                )
                results = json.loads(results_json)

                if results and len(results) > 0:
                    success_msg = (
                        f"Successfully created Cypher snippet '{name}' "
                        f"with ID: {id}"
                    )
                    return [types.TextContent(type="text", text=success_msg)]
                else:
                    return [
                        types.TextContent(
                            type="text",
                            text="Error creating Cypher snippet"
                        )
                    ]
        except Exception as e:
            logger.error(f"Error creating Cypher snippet: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def update_cypher_snippet(
        self,
        id: str,
        name: Optional[str] = None,
        syntax: Optional[str] = None,
        description: Optional[str] = None,
        example: Optional[str] = None,
        since: Optional[float] = None,
        tags: Optional[List[str]] = None
    ) -> List[types.TextContent]:
        """Update an existing Cypher snippet."""
        # Build dynamic SET clause based on provided parameters
        set_clauses = ["c.lastUpdated = date()"]
        params: dict[str, object] = {"id": id}

        if name is not None:
            set_clauses.append("c.name = $name")
            params["name"] = name

        if syntax is not None:
            set_clauses.append("c.syntax = $syntax")
            params["syntax"] = syntax

        if description is not None:
            set_clauses.append("c.description = $description")
            params["description"] = description

        if example is not None:
            set_clauses.append("c.example = $example")
            params["example"] = example

        if since is not None:
            set_clauses.append("c.since = $since")
            params["since"] = float(since)  # Always store as float
        # Build the query
        query = f"""
        MATCH (c:CypherSnippet {{id: $id}})
        SET {', '.join(set_clauses)}
        """

        # Handle tag updates if provided
        if tags is not None:
            query += """
            WITH c
            OPTIONAL MATCH (c)-[r:TAGGED_AS]->(:Tag)
            DELETE r
            WITH c
            UNWIND $tag_list AS tag
              MERGE (t:Tag {name: tag})
              MERGE (c)-[:TAGGED_AS]->(t)
            """
            params["tag_list"] = tags

        query += """
        RETURN c.id AS id, c.name AS name
        """

        try:
            async with safe_neo4j_session(self.driver, self.database or "") as session:
                results_json = await session.execute_write(
                    self._write,
                    query,
                    params
                )
                results = json.loads(results_json)

                if results and len(results) > 0:
                    updated_name = results[0].get("name", id)
                    success_msg = (
                        f"Successfully updated Cypher snippet '{updated_name}' "
                        f"with ID: {id}"
                    )
                    return [types.TextContent(type="text", text=success_msg)]
                else:
                    not_found_msg = f"No Cypher snippet found with ID '{id}'"
                    return [types.TextContent(type="text", text=not_found_msg)]
        except Exception as e:
            logger.error(f"Error updating Cypher snippet: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def delete_cypher_snippet(
        self,
        id: str
    ) -> List[types.TextContent]:
        """Delete a Cypher snippet from the database."""
        query = """
        MATCH (c:CypherSnippet {id: $id})
        OPTIONAL MATCH (c)-[r]-()
        DELETE r, c
        RETURN count(c) AS deleted
        """

        try:
            async with safe_neo4j_session(self.driver, self.database or "") as session:
                results_json = await session.execute_write(
                    self._write,
                    query,
                    {"id": id}
                )
                results = json.loads(results_json)

                if results and results[0].get("deleted", 0) > 0:
                    success_msg = (
                        f"Successfully deleted Cypher snippet with ID: {id}"
                    )
                    return [types.TextContent(type="text", text=success_msg)]
                else:
                    not_found_msg = f"No Cypher snippet found with ID '{id}'"
                    return [types.TextContent(type="text", text=not_found_msg)]
        except Exception as e:
            logger.error(f"Error deleting Cypher snippet: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def get_cypher_tags(self) -> List[types.TextContent]:
        """Get all tags used for Cypher snippets."""
        query = """
        MATCH (t:Tag)<-[:TAGGED_AS]-(c:CypherSnippet)
        WITH t, count(c) AS snippet_count
        RETURN t.name AS name, snippet_count
        ORDER BY snippet_count DESC, name
        """

        try:
            async with safe_neo4j_session(self.driver, self.database or "") as session:
                results_json = await session.execute_read(
                    self._read_query,
                    query,
                    {}
                )
                results = json.loads(results_json)

                if results and len(results) > 0:
                    text = "# Cypher Snippet Tags\n\n"
                    text += "| Tag | Snippet Count |\n"
                    text += "| --- | ------------- |\n"

                    for tag in results:
                        text += (
                            f"| {tag.get('name', 'N/A')} | "
                            f"{tag.get('snippet_count', 0)} |\n"
                        )

                    return [types.TextContent(type="text", text=text)]
                else:
                    no_tags_msg = "No tags found for Cypher snippets."
                    return [types.TextContent(type="text", text=no_tags_msg)]
        except Exception as e:
            logger.error(f"Error retrieving Cypher tags: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]
