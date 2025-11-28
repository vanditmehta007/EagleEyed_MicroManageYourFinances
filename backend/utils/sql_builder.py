from typing import Dict, Any, List, Optional, Tuple
import re

class SQLBuilder:
    """
    Utility module for building safe SQL filters, pagination, sorting, 
    and modular query fragments for the Query Engine.
    
    This class is designed to construct SQL queries dynamically while preventing
    SQL injection by using parameterized queries (though the actual execution 
    and parameter binding depend on the database driver/ORM used downstream).
    """

    @staticmethod
    def build_select_query(
        table: str,
        columns: List[str] = None,
        filters: Dict[str, Any] = None,
        sort_by: str = None,
        sort_order: str = "ASC",
        limit: int = None,
        offset: int = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Builds a SELECT query with filters, sorting, and pagination.
        """
        # Validate table name
        table = SQLBuilder.sanitize_identifier(table)
        
        # Construct SELECT clause
        if not columns:
            cols_str = "*"
        else:
            cols_str = ", ".join([SQLBuilder.sanitize_identifier(c) for c in columns])
            
        query = f"SELECT {cols_str} FROM {table}"
        params = {}
        
        # Construct WHERE clause
        if filters:
            where_clause, where_params = SQLBuilder.build_where_clause(filters)
            if where_clause:
                query += f" {where_clause}"
                params.update(where_params)
        
        # Construct ORDER BY clause
        if sort_by:
            query += f" {SQLBuilder.build_sorting_clause(sort_by, sort_order)}"
            
        # Construct LIMIT and OFFSET clauses
        query += f" {SQLBuilder.build_pagination_clause(limit, offset)}"
        
        return query.strip(), params

    @staticmethod
    def build_where_clause(filters: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Constructs a WHERE clause from a dictionary of filters.
        """
        if not filters:
            return "", {}
            
        conditions = []
        params = {}
        
        for key, value in filters.items():
            # Sanitize column name
            col_name = SQLBuilder.sanitize_identifier(key)
            
            # Handle dictionary value (operator)
            if isinstance(value, dict):
                for op, val in value.items():
                    param_name = f"{key}_{len(params)}"
                    
                    if op.upper() == "IN":
                        # Handle IN clause specially
                        if not isinstance(val, (list, tuple)):
                            val = [val]
                        in_params = []
                        for i, v in enumerate(val):
                            p_name = f"{param_name}_{i}"
                            in_params.append(f":{p_name}")
                            params[p_name] = v
                        conditions.append(f"{col_name} IN ({', '.join(in_params)})")
                        
                    elif op.upper() == "LIKE":
                        conditions.append(f"{col_name} LIKE :{param_name}")
                        params[param_name] = val
                        
                    elif op in [">", "<", ">=", "<=", "=", "!=", "<>"]:
                        conditions.append(f"{col_name} {op} :{param_name}")
                        params[param_name] = val
                        
            # Handle simple equality
            else:
                param_name = f"{key}_{len(params)}"
                conditions.append(f"{col_name} = :{param_name}")
                params[param_name] = value
                
        if not conditions:
            return "", {}
            
        return "WHERE " + " AND ".join(conditions), params

    @staticmethod
    def build_insert_query(table: str, data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Builds an INSERT query.
        """
        table = SQLBuilder.sanitize_identifier(table)
        columns = []
        placeholders = []
        params = {}
        
        for key, value in data.items():
            col_name = SQLBuilder.sanitize_identifier(key)
            columns.append(col_name)
            placeholders.append(f":{key}")
            params[key] = value
            
        cols_str = ", ".join(columns)
        vals_str = ", ".join(placeholders)
        
        query = f"INSERT INTO {table} ({cols_str}) VALUES ({vals_str})"
        return query, params

    @staticmethod
    def build_update_query(
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Builds an UPDATE query.
        """
        table = SQLBuilder.sanitize_identifier(table)
        set_clauses = []
        params = {}
        
        # Construct SET clause
        for key, value in data.items():
            col_name = SQLBuilder.sanitize_identifier(key)
            param_name = f"set_{key}"
            set_clauses.append(f"{col_name} = :{param_name}")
            params[param_name] = value
            
        set_str = ", ".join(set_clauses)
        
        # Construct WHERE clause
        where_clause, where_params = SQLBuilder.build_where_clause(filters)
        params.update(where_params)
        
        query = f"UPDATE {table} SET {set_str}"
        if where_clause:
            query += f" {where_clause}"
            
        return query, params

    @staticmethod
    def build_delete_query(table: str, filters: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Builds a DELETE query.
        """
        table = SQLBuilder.sanitize_identifier(table)
        
        # Construct WHERE clause
        where_clause, where_params = SQLBuilder.build_where_clause(filters)
        
        query = f"DELETE FROM {table}"
        if where_clause:
            query += f" {where_clause}"
            
        return query, where_params

    @staticmethod
    def sanitize_identifier(identifier: str) -> str:
        """
        Sanitizes a SQL identifier (table or column name) to prevent injection.
        """
        # Only allow alphanumeric and underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', identifier):
            raise ValueError(f"Invalid identifier: {identifier}")
        return identifier

    @staticmethod
    def build_pagination_clause(limit: int, offset: int) -> str:
        """
        Builds the LIMIT and OFFSET clause.
        """
        clause = ""
        if limit is not None:
            clause += f"LIMIT {int(limit)}"
        if offset is not None:
            clause += f" OFFSET {int(offset)}"
        return clause

    @staticmethod
    def build_sorting_clause(sort_by: str, sort_order: str = "ASC") -> str:
        """
        Builds the ORDER BY clause.
        """
        sort_by = SQLBuilder.sanitize_identifier(sort_by)
        order = sort_order.upper()
        if order not in ["ASC", "DESC"]:
            order = "ASC"
        return f"ORDER BY {sort_by} {order}"
