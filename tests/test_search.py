"""Tests for search functionality."""
from datetime import datetime

import pytest

from src.database import Database
from src.search import SearchEngine


class TestSearchEngine:
    """Test search engine functionality."""

    @pytest.fixture
    def search_engine_with_data(self, test_database):
        """Create search engine with sample data."""
        # Insert test documents
        with test_database.get_connection() as conn:
            documents = [
                (
                    '/docs/python_tutorial.txt',
                    'Python is a high-level programming language. '
                    'Python emphasizes code readability with significant whitespace.',
                    '2024-01-01T10:00:00'
                ),
                (
                    '/docs/java_guide.md',
                    'Java is an object-oriented programming language. '
                    'Java runs on the Java Virtual Machine (JVM).',
                    '2024-01-02T10:00:00'
                ),
                (
                    '/docs/web_development.txt',
                    'Web development involves HTML, CSS, and JavaScript. '
                    'Modern web development often uses frameworks like React or Vue.',
                    '2024-01-03T10:00:00'
                ),
                (
                    '/notes/meeting.txt',
                    'Discussed the Python project timeline and Java integration. '
                    'Web interface needs updating.',
                    '2024-01-04T10:00:00'
                ),
            ]

            for path, content, modified in documents:
                conn.execute(
                    "INSERT INTO documents (path, content, last_modified) VALUES (?, ?, ?)",
                    (path, content, modified)
                )
            conn.commit()

        return SearchEngine(test_database)

    def test_simple_search(self, search_engine_with_data):
        """Test basic search functionality."""
        results = search_engine_with_data.search("Python")

        assert len(results) > 0
        # Python tutorial should be most relevant
        assert 'python_tutorial.txt' in results[0]['path']
        assert results[0]['score'] > 0
        assert 'Python' in results[0]['snippet']

    def test_search_limit(self, search_engine_with_data):
        """Test search result limiting."""
        results = search_engine_with_data.search("programming", limit=2)

        assert len(results) <= 2

    def test_empty_query(self, search_engine_with_data):
        """Test handling of empty queries."""
        assert search_engine_with_data.search("") == []
        assert search_engine_with_data.search("   ") == []
        assert search_engine_with_data.search(None) == []

    def test_phrase_search(self, search_engine_with_data):
        """Test phrase searching."""
        # Search for exact phrase
        results = search_engine_with_data.search('"programming language"')

        assert len(results) == 2  # Python and Java docs
        for result in results:
            assert 'programming language' in result['snippet'].lower()

    def test_search_special_characters(self, search_engine_with_data):
        """Test searching with special characters."""
        # These should not crash the search
        results = search_engine_with_data.search("Python's")
        assert isinstance(results, list)

        results = search_engine_with_data.search("C++")
        assert isinstance(results, list)

        results = search_engine_with_data.search("test@example.com")
        assert isinstance(results, list)

    def test_case_insensitive_search(self, search_engine_with_data):
        """Test that search is case-insensitive."""
        results_lower = search_engine_with_data.search("python")
        results_upper = search_engine_with_data.search("PYTHON")
        results_mixed = search_engine_with_data.search("PyThOn")

        # All should return same number of results
        assert len(results_lower) == len(results_upper) == len(results_mixed)

    def test_search_ranking(self, search_engine_with_data):
        """Test that search results are properly ranked."""
        results = search_engine_with_data.search("Python")

        # Document with more occurrences of "Python" should rank higher
        assert len(results) >= 2
        # First result should have higher score than second
        assert results[0]['score'] >= results[1]['score']

    def test_snippet_generation(self, search_engine_with_data):
        """Test that snippets are properly generated."""
        results = search_engine_with_data.search("readability")
        
        assert len(results) > 0
        snippet = results[0]['snippet']
        
        # Snippet should contain the search term with mark tags
        assert 'readability' in snippet.lower() or '<mark>readability</mark>' in snippet.lower()
        # Snippet might have ellipsis for truncation (but not always)
        # Remove this assertion as FTS5 doesn't always add ellipsis

    def test_no_results(self, search_engine_with_data):
        """Test search with no matching results."""
        results = search_engine_with_data.search("NonexistentTermXYZ123")

        assert results == []

    def test_document_count(self, search_engine_with_data):
        """Test getting document count."""
        count = search_engine_with_data.get_document_count()

        assert count == 4  # We inserted 4 documents

    def test_document_count_empty(self, test_database):
        """Test document count on empty database."""
        search_engine = SearchEngine(test_database)
        count = search_engine.get_document_count()

        assert count == 0

    def test_search_by_path(self, search_engine_with_data):
        """Test searching by file path pattern."""
        # Search for all docs in /docs/ directory
        results = search_engine_with_data.search_by_path('/docs/%')

        assert len(results) == 3
        for result in results:
            assert result['path'].startswith('/docs/')

        # Search for markdown files
        results = search_engine_with_data.search_by_path('%.md')

        assert len(results) == 1
        assert results[0]['path'].endswith('.md')

    def test_search_by_path_no_results(self, search_engine_with_data):
        """Test path search with no results."""
        results = search_engine_with_data.search_by_path('/nonexistent/%')

        assert results == []

    def test_boolean_operators(self, search_engine_with_data):
        """Test search with boolean operators."""
        # AND operator (implicit)
        results = search_engine_with_data.search("Python programming")
        assert len(results) > 0

        # Should find documents containing both terms
        for result in results:
            content = result['snippet'].lower()
            # At least one term should be in snippet
            assert 'python' in content or 'programming' in content

    def test_search_error_handling(self, test_database):
        """Test search error handling."""
        search_engine = SearchEngine(test_database)

        # Invalid FTS5 syntax should be handled gracefully
        results = search_engine.search("((invalid syntax")
        assert isinstance(results, list)  # Should return empty list, not crash
