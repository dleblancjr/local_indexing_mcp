"""Search implementation using SQLite FTS5."""
import logging
import sqlite3
from typing import List

from .database import Database
from .models import SearchResult

logger = logging.getLogger(__name__)


class SearchEngine:
    """Provides text search functionality using SQLite FTS5."""

    def __init__(self, database: Database):
        """
        Initialize search engine.

        Args:
            database: Database instance
        """
        self.db = database

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Search indexed content using FTS5.

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of search results sorted by relevance
        """
        if not query or not query.strip():
            return []

        # Escape special FTS5 characters
        escaped_query = self._escape_fts_query(query)

        results = []

        try:
            with self.db.get_connection() as conn:
                # Use FTS5 MATCH with snippet generation
                cursor = conn.execute("""
                    SELECT 
                        path,
                        snippet(documents, 1, '<mark>', '</mark>', '...', 32) as snippet,
                        bm25(documents) as score,
                        last_modified
                    FROM documents
                    WHERE documents MATCH ?
                    ORDER BY score
                    LIMIT ?
                """, (escaped_query, limit))

                for row in cursor:
                    results.append(SearchResult(
                        path=row['path'],
                        snippet=row['snippet'],
                        score=abs(row['score']),  # BM25 returns negative scores
                        last_modified=row['last_modified']
                    ))

                logger.info(f"Search for '{query}' returned {len(results)} results")

        except sqlite3.OperationalError as e:
            # Handle invalid FTS5 syntax
            logger.warning(f"Invalid search query '{query}': {e}")
            return []
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

        return results

    def _escape_fts_query(self, query: str) -> str:
        """
        Escape special characters in FTS5 queries.

        Args:
            query: Raw query string

        Returns:
            Escaped query safe for FTS5
        """
        # If query contains special characters, wrap it in quotes
        # This is the simplest and most reliable approach
        special_chars = {'"', "'", '-', '*', ':', '.', '(', ')', 'AND', 'OR', 'NOT'}

        # Check if query already has phrase search quotes
        if query.startswith('"') and query.endswith('"'):
            return query

        # If query contains special chars or operators, quote it
        if any(char in query for char in special_chars):
            # Escape any quotes inside the query
            escaped = query.replace('"', '""')
            return f'"{escaped}"'

        return query

    def get_document_count(self) -> int:
        """
        Get total number of indexed documents.

        Returns:
            Number of documents in index
        """
        try:
            with self.db.get_connection() as conn:
                result = conn.execute("SELECT COUNT(*) FROM documents").fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Failed to get document count: {e}")
            return 0

    def search_by_path(self, path_pattern: str, limit: int = 10) -> List[SearchResult]:
        """
        Search for documents by path pattern.

        Args:
            path_pattern: SQL LIKE pattern for path matching
            limit: Maximum number of results

        Returns:
            List of matching documents
        """
        results = []

        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        path,
                        substr(content, 1, 200) as snippet,
                        0.0 as score,
                        last_modified
                    FROM documents
                    WHERE path LIKE ?
                    ORDER BY path
                    LIMIT ?
                """, (path_pattern, limit))

                for row in cursor:
                    results.append(SearchResult(
                        path=row['path'],
                        snippet=row['snippet'] + '...' if len(row['snippet']) == 200 else row['snippet'],
                        score=row['score'],
                        last_modified=row['last_modified']
                    ))

        except Exception as e:
            logger.error(f"Path search error: {e}")

        return results
