"""
Legacy query interface for backward compatibility.
This allows old code to work while migrating to the new connector.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class LegacyQuery:
    """
    Backward-compatible query interface that mimics the old ConnectorQuery.
    Uses the new DatabaseConnector internally.
    """
    
    def __init__(self, connector, tablename: str, is_single: bool = False, 
                 unique_identy = None, single_item = None):
        self.connector = connector
        self.tablename = tablename
        self.is_single = is_single
        self.unique_identy = unique_identy
        
        # Get columns from connector
        self._columns = connector.columns.get(tablename, [])
        self._primary_column = connector.primary_columns.get(tablename, 'id')
        
        # Query state
        self._order = self._primary_column
        self._group_by = None
        self._group_bys = None
        self._group_by_args = {}
        self._action = "SELECT"
        self.select_filters = []
        self._max_per_page = None
        self._current_page = None
        self.update_filters = []
        self.adding_fields = []
        self._items = None
        self._col_summname = self._primary_column
        self.adds = []
        
        if is_single and unique_identy is not None:
            self.add_filter("equal", **{self._primary_column: unique_identy})
            self._items = [single_item] if single_item else []
    
    def _build_query(self):
        """Build SQL query from current state"""
        if self._action == "SELECT":
            return self._build_select()
        elif self._action == "UPDATE":
            return self._build_update()
        elif self._action == "ADD":
            return self._build_insert()
        elif self._action == "DELETE":
            return self._build_delete()
        elif self._action == "COUNT":
            return self._build_count()
        return None, None
    
    def _build_select(self):
        """Build SELECT query"""
        columns = ', '.join(self._columns) if self._columns else '*'
        query = f"SELECT {columns} FROM {self.tablename}"
        params = []
        
        # Build WHERE clause
        where_clauses = []
        for column, value, filter_type in self.select_filters:
            if filter_type == "equal":
                if value is None:
                    where_clauses.append(f"{column} IS NULL")
                else:
                    where_clauses.append(f"{column} = %s")
                    params.append(value)
            elif filter_type == "unequal":
                if value is None:
                    where_clauses.append(f"{column} IS NOT NULL")
                else:
                    where_clauses.append(f"{column} != %s")
                    params.append(value)
            elif filter_type == "more":
                where_clauses.append(f"{column} > %s")
                params.append(value)
            elif filter_type == "less":
                where_clauses.append(f"{column} < %s")
                params.append(value)
            elif filter_type == "like":
                where_clauses.append(f"{column} ILIKE %s")
                params.append(f"%{value}%")
            elif filter_type == "startswith":
                where_clauses.append(f"{column} ILIKE %s")
                params.append(f"{value}%")
            elif filter_type == "endswith":
                where_clauses.append(f"{column} ILIKE %s")
                params.append(f"%{value}")
            elif filter_type == "in":
                where_clauses.append(f"{column} = ANY(%s)")
                params.append(value)
        
        if where_clauses:
            query += f" WHERE {' AND '.join(where_clauses)}"
        
        # ORDER BY
        if self._order:
            query += f" ORDER BY {self._order} DESC"
        
        # Pagination
        if self._max_per_page is not None:
            offset = (self._current_page or 0) * self._max_per_page
            query += f" LIMIT {self._max_per_page} OFFSET {offset}"
        
        return query, tuple(params)
    
    def _build_update(self):
        """Build UPDATE query"""
        if not self.update_filters:
            return None, None
        
        set_clauses = []
        params = []
        
        for column, value in self.update_filters:
            if value is None:
                set_clauses.append(f"{column} = NULL")
            else:
                set_clauses.append(f"{column} = %s")
                params.append(value)
        
        query = f"UPDATE {self.tablename} SET {', '.join(set_clauses)}"
        
        # WHERE clause
        where_clauses = []
        for column, value, filter_type in self.select_filters:
            if filter_type == "equal":
                where_clauses.append(f"{column} = %s")
                params.append(value)
        
        if where_clauses:
            query += f" WHERE {' AND '.join(where_clauses)}"
        
        if self._columns:
            query += f" RETURNING {', '.join(self._columns)}"
        
        return query, tuple(params)
    
    def _build_insert(self):
        """Build INSERT query"""
        if not self.adds:
            return None, None
        
        # Use first add to determine columns
        first_add = self.adds[0]
        columns = [item[0] for item in first_add]
        
        query = f"INSERT INTO {self.tablename} ({', '.join(columns)}) VALUES "
        
        all_params = []
        value_groups = []
        
        for add in self.adds:
            placeholders = ', '.join(['%s'] * len(add))
            value_groups.append(f"({placeholders})")
            for item in add:
                all_params.append(item[1])
        
        query += ', '.join(value_groups)
        
        if self._columns:
            query += f" RETURNING {', '.join(self._columns)}"
        
        return query, tuple(all_params)
    
    def _build_delete(self):
        """Build DELETE query"""
        query = f"DELETE FROM {self.tablename}"
        params = []
        
        where_clauses = []
        for column, value, filter_type in self.select_filters:
            if filter_type == "equal":
                where_clauses.append(f"{column} = %s")
                params.append(value)
        
        if where_clauses:
            query += f" WHERE {' AND '.join(where_clauses)}"
        
        return query, tuple(params)
    
    def _build_count(self):
        """Build COUNT query"""
        query = f"SELECT COUNT(*) as count FROM {self.tablename}"
        params = []
        
        where_clauses = []
        for column, value, filter_type in self.select_filters:
            if filter_type == "equal":
                where_clauses.append(f"{column} = %s")
                params.append(value)
        
        if where_clauses:
            query += f" WHERE {' AND '.join(where_clauses)}"
        
        return query, tuple(params)
    
    def exec(self):
        """Execute the built query"""
        if self.is_single and self._items:
            return self._items
        
        query, params = self._build_query()
        if not query:
            return []
        
        try:
            if self._action == "COUNT":
                result = self.connector.fetch_one(query, params)
                return result['count'] if result else 0
            elif self._action == "DELETE":
                self.connector.execute(query, params)
                return True
            elif self._action in ["SELECT", "UPDATE", "ADD"]:
                results = self.connector.fetch_all(query, params)
                
                # Convert to list of dicts
                if results:
                    return [dict(row) for row in results]
                return []
            else:
                return []
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def _init_items(self):
        """Initialize item objects from results"""
        result = []
        for each in self._items:
            result.append(LegacyQuery(self.connector, self.tablename, 
                                      is_single=True, unique_identy=each.get(self._primary_column), 
                                      single_item=each))
        return result
    
    @property
    def items(self):
        """Get all items as objects"""
        self._items = self.exec()
        return self._init_items()
    
    @property
    def item(self):
        """Get single item"""
        self._items = self.exec()
        items = self._init_items()
        return items[0] if items else None
    
    def clear_add(self):
        """Clear pending adds"""
        self._action = "SELECT"
        self.adds = []
        return self
    
    def add_filter(self, filter_type, **kwargs):
        """Add a filter"""
        if self._action == "ADD" and self.adds:
            raise ValueError("Unadded data. clear them with .clear_add()")
        
        self._action = "SELECT"
        for k, v in kwargs.items():
            self.select_filters.append((k, v, filter_type))
            if filter_type == "equal" and k == self._primary_column:
                self.is_single = True
                self.unique_identy = v
        return self
    
    def get(self, **kwargs):
        """Filter by equality"""
        return self.add_filter("equal", **kwargs)
    
    def equal(self, **kwargs):
        """Alias for get"""
        return self.add_filter("equal", **kwargs)
    
    def all(self):
        """Return all (no filter)"""
        return self
    
    def unequal(self, **kwargs):
        """Filter by inequality"""
        return self.add_filter("unequal", **kwargs)
    
    def more(self, **kwargs):
        """Filter by greater than"""
        return self.add_filter("more", **kwargs)
    
    def less(self, **kwargs):
        """Filter by less than"""
        return self.add_filter("less", **kwargs)
    
    def like(self, **kwargs):
        """Filter by LIKE (case-insensitive)"""
        return self.add_filter("like", **kwargs)
    
    def startswith(self, **kwargs):
        """Filter by starts with"""
        return self.add_filter("startswith", **kwargs)
    
    def endswith(self, **kwargs):
        """Filter by ends with"""
        return self.add_filter("endswith", **kwargs)
    
    def contains(self, **kwargs):
        """Filter by contains (for arrays)"""
        return self.add_filter("in", **kwargs)
    
    def any(self, **kwargs):
        """Filter by any match"""
        return self.add_filter("in", **kwargs)
    
    def update(self, **kwargs):
        """Set up update operation"""
        self._action = "UPDATE"
        for k, v in kwargs.items():
            self.update_filters.append((k, v))
        return self
    
    def delete(self, **kwargs):
        """Set up delete operation"""
        self.add_filter("equal", **kwargs)
        self._action = "DELETE"
        return self
    
    def order_by(self, *args):
        """Set order by column"""
        if args:
            self._order = args[0]
        return self
    
    def group_by(self, *args):
        """Set group by (simplified)"""
        self._action = "GROUP_BY"
        if args:
            self._group_by = args[0]
        return self
    
    def count(self, name: str = "", distinct: bool = False):
        """Count operation"""
        self._action = "COUNT"
        return self
    
    def summ(self, name: str, is_overall: bool = False):
        """Sum operation (simplified)"""
        return self
    
    def add(self, **kwargs):
        """Add new record"""
        self._action = "ADD"
        fields = []
        
        for k, v in kwargs.items():
            if self._columns and k not in self._columns:
                raise ValueError(f"Table {self.tablename} has no column {k}")
            fields.append((k, v))
        
        self.adds.append(fields)
        return self
    
    def page(self, page: int):
        """Set page number"""
        self._current_page = page - 1
        return self
    
    def per_page(self, count: int):
        """Set items per page"""
        self._max_per_page = count
        return self
    
    def at(self, position: int):
        """Get item at position"""
        return self._items[position] if self._items else None
    
    def __getitem__(self, key):
        """Dictionary-like access"""
        if not self._items:
            self._items = self.exec()
        
        if isinstance(key, int):
            return self._items[key] if key < len(self._items) else None
        elif isinstance(key, str):
            if self.is_single and self._items:
                return self._items[0].get(key)
            return [item.get(key) for item in self._items] if self._items else []
        elif isinstance(key, tuple):
            return [{k: item.get(k) for k in key} for item in self._items] if self._items else []
        elif isinstance(key, slice):
            return self._items[key] if self._items else []
        return None
    
    def copy(self):
        """Create a copy of this query"""
        import copy
        new_copy = LegacyQuery(self.connector, self.tablename)
        new_copy._columns = self._columns.copy()
        new_copy._primary_column = self._primary_column
        new_copy.is_single = copy.deepcopy(self.is_single)
        new_copy.unique_identy = copy.deepcopy(self.unique_identy)
        new_copy._order = self._order
        new_copy._group_by = self._group_by
        new_copy._group_bys = copy.deepcopy(self._group_bys)
        new_copy._group_by_args = copy.deepcopy(self._group_by_args)
        new_copy._action = self._action
        new_copy.select_filters = copy.deepcopy(self.select_filters)
        new_copy._max_per_page = self._max_per_page
        new_copy._current_page = self._current_page
        new_copy.update_filters = copy.deepcopy(self.update_filters)
        new_copy.adding_fields = copy.deepcopy(self.adding_fields)
        new_copy._items = copy.deepcopy(self._items)
        new_copy.adds = copy.deepcopy(self.adds)
        return new_copy
    
    def __repr__(self):
        if self.is_single:
            return f"<Single Item ({self._primary_column}={self.unique_identy})>"
        return f"<LegacyQuery({self._action}, table={self.tablename})>"
