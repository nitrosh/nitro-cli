"""Query builder for filtering and transforming collections."""

from typing import Any, Callable, List, Optional


class QueryBuilder:
    """Chainable query builder for filtering, sorting, and limiting collections.

    Example:
        >>> data = NitroDataStore({'posts': [{'title': 'A', 'published': True}]})
        >>> results = (data.query('posts')
        ...     .where(lambda x: x.get('published'))
        ...     .sort(key=lambda x: x.get('date', ''))
        ...     .limit(10)
        ...     .execute())
    """

    def __init__(self, collection: List[Any]):
        """Initialize the query builder.

        Args:
            collection: List to query
        """
        self._collection = collection
        self._filters: List[Callable[[Any], bool]] = []
        self._sort_key: Optional[Callable[[Any], Any]] = None
        self._sort_reverse: bool = False
        self._limit_count: Optional[int] = None
        self._offset_count: int = 0

    def where(self, predicate: Callable[[Any], bool]) -> 'QueryBuilder':
        """Add a filter condition.

        Args:
            predicate: Function(item) -> bool

        Returns:
            Self for chaining

        Example:
            >>> query.where(lambda x: x.get('published') == True)
        """
        self._filters.append(predicate)
        return self

    def sort(self, key: Optional[Callable[[Any], Any]] = None, reverse: bool = False) -> 'QueryBuilder':
        """Sort the results.

        Args:
            key: Function to extract sort key from each item
            reverse: Sort in reverse order (default: False)

        Returns:
            Self for chaining

        Example:
            >>> query.sort(key=lambda x: x.get('date'), reverse=True)
        """
        self._sort_key = key
        self._sort_reverse = reverse
        return self

    def limit(self, count: int) -> 'QueryBuilder':
        """Limit the number of results.

        Args:
            count: Maximum number of results

        Returns:
            Self for chaining

        Example:
            >>> query.limit(10)
        """
        self._limit_count = count
        return self

    def offset(self, count: int) -> 'QueryBuilder':
        """Skip a number of results.

        Args:
            count: Number of results to skip

        Returns:
            Self for chaining

        Example:
            >>> query.offset(5).limit(10)  # Skip first 5, take next 10
        """
        self._offset_count = count
        return self

    def execute(self) -> List[Any]:
        """Execute the query and return results.

        Returns:
            Filtered, sorted, and limited list

        Example:
            >>> results = query.where(...).sort(...).execute()
        """
        result = self._collection

        # Apply filters
        for filter_func in self._filters:
            result = [item for item in result if filter_func(item)]

        # Apply sorting
        if self._sort_key is not None:
            result = sorted(result, key=self._sort_key, reverse=self._sort_reverse)

        # Apply offset
        if self._offset_count > 0:
            result = result[self._offset_count:]

        # Apply limit
        if self._limit_count is not None:
            result = result[:self._limit_count]

        return result

    def count(self) -> int:
        """Count results without executing full query.

        Returns:
            Number of items that match filters

        Example:
            >>> total = query.where(lambda x: x.get('published')).count()
        """
        result = self._collection

        # Apply filters only
        for filter_func in self._filters:
            result = [item for item in result if filter_func(item)]

        return len(result)

    def first(self) -> Optional[Any]:
        """Get the first result.

        Returns:
            First matching item or None

        Example:
            >>> first_post = query.where(...).sort(...).first()
        """
        results = self.limit(1).execute()
        return results[0] if results else None

    def pluck(self, key: str) -> List[Any]:
        """Extract a single field from all results.

        Args:
            key: Key to extract from each item

        Returns:
            List of values for the specified key

        Example:
            >>> titles = query.where(...).pluck('title')
            ['Post 1', 'Post 2', ...]
        """
        results = self.execute()
        return [item.get(key) if isinstance(item, dict) else None for item in results]

    def group_by(self, key: str) -> dict:
        """Group results by a field value.

        Args:
            key: Key to group by

        Returns:
            Dictionary mapping key values to lists of items

        Example:
            >>> by_category = query.group_by('category')
            {'python': [...], 'web': [...]}
        """
        results = self.execute()
        groups = {}

        for item in results:
            if isinstance(item, dict):
                group_key = item.get(key)
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(item)

        return groups