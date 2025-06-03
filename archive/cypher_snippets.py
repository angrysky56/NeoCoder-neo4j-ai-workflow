"""
Cypher Snippet Toolkit for the Neo4j-Guided AI Coding Workflow

This module provides functionality to manage and search for Cypher snippets in the Neo4j database.
"""

import json
import logging
import typing
from typing import List, Optional, Dict, Any, Union

import mcp.types as types
from pydantic import Field
from neo4j import AsyncTransaction

logger = logging.getLogger("mcp_neocoder.cypher_snippets")


class CypherSnippetMixin:
    """Mixin class providing Cypher snippet functionality for the Neo4jWorkflowServer."""

    async def _read_query(self, tx: AsyncTransaction, query: str, params: dict) -> str:
        """Execute a read query and return results as JSON string."""
        raise NotImplementedError("_read_query must be implemented by the parent class")

    async def _write(self, tx: AsyncTransaction, query: str, params: dict):
        """Execute a write query and return results as JSON string."""
        raise NotImplementedError("_write must be implemented by the parent class")

    async def list_cypher_snippets(
        self,
        limit: int = Field(20, description="Maximum number of snippets to return"),
        offset: int = Field(0, description="Number of snippets to skip"),
        tag: Optional[str] = Field(None, description="Filter by a specific tag"),
        since_version: Optional[float] = Field(None, description="Filter snippets based on Neo4j version")
    ) -> List[types.TextContent]:
        """List all available Cypher snippets with optional filtering."""
        query = """
        MATCH (c:CypherSnippet)
        WHERE 1=1
        """

        params = {"limit": limit, "offset": offset}

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
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    text = "# Available Cypher Snippets\n\n"

                    if tag:
                        text += f"Filtered by tag: `{tag}`\n\n"
                    if since_version is not None:
                        text += f"Compatible with Neo4j version: {since_version} and newer\n\n"

                    text += "| ID | Name | Since Version | Description |\n"
                    text += "| -- | ---- | ------------- | ----------- |\n"

                    for snippet in results:
                        text += f"| {snippet.get('id', 'N/A')} | {snippet.get('name', 'N/A')} | {snippet.get('since', 'N/A')} | {snippet.get('description', 'N/A')} |\n"

                    return [types.TextContent(type="text", text=text)]
                else:
                    filter_msg = ""
                    if tag:
                        filter_msg += f" with tag '{tag}'"
                    if since_version is not None:
                        if filter_msg:
                            filter_msg += f" and"
                        filter_msg += f" compatible with Neo4j {since_version}"

                    if filter_msg:
                        return [types.TextContent(type="text", text=f"No Cypher snippets found{filter_msg}.")]
                    else:
                        return [types.TextContent(type="text", text="No Cypher snippets found in the database.")]
        except Exception as e:
            logger.error(f"Error listing Cypher snippets: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def get_cypher_snippet(
        self,
        id: str = Field(..., description="The ID of the Cypher snippet to retrieve")
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
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, {"id": id})
                results = json.loads(results_json)

                if results and len(results) > 0:
                    snippet = results[0]
                    text = f"# Cypher Snippet: {snippet.get('name', id)}\n\n"
                    text += f"**ID:** `{snippet.get('id', id)}`\n"
                    text += f"**Neo4j Version:** {snippet.get('since', 'N/A')}\n"

                    if snippet.get('tags'):
                        tags = snippet.get('tags', [])
                        text += f"**Tags:** {', '.join([f'`{tag}`' for tag in tags])}\n"

                    text += f"\n**Description:**\n{snippet.get('description', 'No description available.')}\n"

                    text += f"\n**Syntax:**\n```cypher\n{snippet.get('syntax', '')}\n```\n"

                    if snippet.get('example'):
                        text += f"\n**Example:**\n```cypher\n{snippet.get('example', '')}\n```\n"

                    return [types.TextContent(type="text", text=text)]
                else:
                    return [types.TextContent(type="text", text=f"No Cypher snippet found with ID '{id}'")]
        except Exception as e:
            logger.error(f"Error retrieving Cypher snippet: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def search_cypher_snippets(
        self,
        query_text: str = Field(..., description="Search text to match against snippet content"),
        search_type: str = Field("text", description="Search type: 'text', 'fulltext', or 'tag'"),
        limit: int = Field(10, description="Maximum number of results to return")
    ) -> List[types.TextContent]:
        """Search for Cypher snippets by keyword, tag, or pattern."""
        query = ""
        params = {"query_text": query_text, "limit": limit}

        if search_type.lower() == "text":
            # Text search using TEXT index
            params["search_pattern"] = f"(?i).*{query_text}.*"  # Case-insensitive pattern
            query = """
            MATCH (c:CypherSnippet)
            WHERE c.syntax =~ $search_pattern OR c.description =~ $search_pattern
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
            return [types.TextContent(
                type="text",
                text=f"Invalid search type: '{search_type}'. Valid options are 'text', 'fulltext', or 'tag'."
            )]

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    text = "# Cypher Snippet Search Results\n\n"
                    text += f"Query: '{query_text}' (Search type: {search_type})\n\n"

                    for i, snippet in enumerate(results, 1):
                        score_text = f" (Score: {snippet.get('score', 'N/A')})" if 'score' in snippet else ""

                        text += f"## {i}. {snippet.get('name', 'Unnamed Snippet')}{score_text}\n\n"
                        text += f"**ID:** `{snippet.get('id', 'unknown')}`\n"
                        text += f"**Description:** {snippet.get('description', 'No description')}\n"
                        text += f"**Syntax:** `{snippet.get('syntax', 'No syntax')}`\n\n"

                    text += "\nUse `get_cypher_snippet(id=\"snippet-id\")` to view full details of any result."

                    return [types.TextContent(type="text", text=text)]
                else:
                    return [types.TextContent(
                        type="text",
                        text=f"No Cypher snippets found matching '{query_text}' with search type '{search_type}'."
                    )]
        except Exception as e:
            logger.error(f"Error searching Cypher snippets: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]
    async def create_cypher_snippet(
        self,
        id: str = Field(..., description="Unique identifier for the snippet"),
        name: str = Field(..., description="Display name for the snippet"),
        syntax: str = Field(..., description="The Cypher syntax pattern"),
        description: str = Field(..., description="Description of what the snippet does"),
        example: Optional[str] = Field(None, description="An example usage of the syntax"),
        since: Optional[float] = Field(None, description="Neo4j version since the syntax is supported"),
        tags: Optional[List[str]] = Field(None, description="Tags for categorizing the snippet")
    ) -> List[types.TextContent]:
        """Add a new Cypher snippet to the database."""
        snippet_tags = tags or []
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
            "since": snippet_since,
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
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_write(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    return [types.TextContent(
                        type="text",
                        text=f"Successfully created Cypher snippet '{name}' with ID: {id}"
                    )]
                else:
                    return [types.TextContent(type="text", text="Error creating Cypher snippet")]
        except Exception as e:
            logger.error(f"Error creating Cypher snippet: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def update_cypher_snippet(
        self,
        id: str = Field(..., description="ID of the snippet to update"),
        name: Optional[str] = Field(None, description="New display name"),
        syntax: Optional[str] = Field(None, description="New syntax pattern"),
        description: Optional[str] = Field(None, description="New description"),
        example: Optional[str] = Field(None, description="New example"),
        since: Optional[float] = Field(None, description="Neo4j version update"),
        tags: Optional[List[str]] = Field(None, description="New tags (replaces existing tags)")
    ) -> List[types.TextContent]:
        """Update an existing Cypher snippet."""
        # Build dynamic SET clause based on provided parameters
        set_clauses = ["c.lastUpdated = date()"]
        params = {"id": id}

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
            params["since"] = since

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
            UNWIND $tags AS tag
              MERGE (t:Tag {name: tag})
              MERGE (c)-[:TAGGED_AS]->(t)
            """
            params["tags"] = tags

        query += """
        RETURN c.id AS id, c.name AS name
        """

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_write(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    updated_name = results[0].get("name", id)
                    return [types.TextContent(
                        type="text",
                        text=f"Successfully updated Cypher snippet '{updated_name}' with ID: {id}"
                    )]
                else:
                    return [types.TextContent(type="text", text=f"No Cypher snippet found with ID '{id}'")]
        except Exception as e:
            logger.error(f"Error updating Cypher snippet: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def delete_cypher_snippet(
        self,
        id: str = Field(..., description="ID of the snippet to delete")
    ) -> List[types.TextContent]:
        """Delete a Cypher snippet from the database."""
        query = """
        MATCH (c:CypherSnippet {id: $id})
        OPTIONAL MATCH (c)-[r]-()
        DELETE r, c
        RETURN count(c) AS deleted
        """

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_write(self._read_query, query, {"id": id})
                results = json.loads(results_json)

                if results and results[0].get("deleted", 0) > 0:
                    return [types.TextContent(
                        type="text",
                        text=f"Successfully deleted Cypher snippet with ID: {id}"
                    )]
                else:
                    return [types.TextContent(type="text", text=f"No Cypher snippet found with ID '{id}'")]
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
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, {})
                results = json.loads(results_json)

                if results and len(results) > 0:
                    text = "# Cypher Snippet Tags\n\n"
                    text += "| Tag | Snippet Count |\n"
                    text += "| --- | ------------- |\n"

                    for tag in results:
                        text += f"| {tag.get('name', 'N/A')} | {tag.get('snippet_count', 0)} |\n"

                    return [types.TextContent(type="text", text=text)]
                else:
                    return [types.TextContent(type="text", text="No tags found for Cypher snippets.")]
        except Exception as e:
            logger.error(f"Error retrieving Cypher tags: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]
