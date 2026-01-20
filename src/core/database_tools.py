"""Database Tools - Feature 29.

Database utilities:
- Connect to databases
- Run queries
- Show table schemas
- Export/import data
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager


@dataclass
class QueryResult:
    """Result of a database query."""
    success: bool
    rows: List[Dict[str, Any]] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)
    row_count: int = 0
    affected_rows: int = 0
    execution_time: float = 0.0
    error: str = ""
    query: str = ""


@dataclass
class TableInfo:
    """Information about a database table."""
    name: str
    columns: List[Dict[str, Any]] = field(default_factory=list)
    row_count: int = 0
    indexes: List[str] = field(default_factory=list)


@dataclass
class DatabaseConnection:
    """A database connection configuration."""
    name: str
    type: str  # sqlite, mysql, postgresql
    connection_string: str
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "connection_string": self.connection_string,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatabaseConnection":
        return cls(**data)


class DatabaseTools:
    """Database utilities (SQLite focus for simplicity)."""

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize database tools."""
        self.storage_dir = storage_dir or Path.home() / ".code-agent" / "db"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.connections_file = self.storage_dir / "connections.json"
        self.connections: Dict[str, DatabaseConnection] = {}
        self.active_connection: Optional[DatabaseConnection] = None
        self._load()

    def _load(self):
        """Load saved connections."""
        if self.connections_file.exists():
            try:
                data = json.loads(self.connections_file.read_text(encoding="utf-8"))
                for conn_data in data.get("connections", []):
                    conn = DatabaseConnection.from_dict(conn_data)
                    self.connections[conn.name] = conn
            except Exception:
                pass

    def _save(self):
        """Save connections."""
        data = {
            "version": "1.0",
            "connections": [c.to_dict() for c in self.connections.values()],
        }
        self.connections_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_connection(
        self,
        name: str,
        db_type: str,
        connection_string: str,
    ) -> DatabaseConnection:
        """
        Add a database connection.

        Args:
            name: Connection name
            db_type: Database type (sqlite, mysql, postgresql)
            connection_string: Connection string or file path

        Returns:
            DatabaseConnection
        """
        conn = DatabaseConnection(
            name=name,
            type=db_type,
            connection_string=connection_string,
            created_at=datetime.now().isoformat(),
        )
        self.connections[name] = conn
        self._save()
        return conn

    def remove_connection(self, name: str) -> bool:
        """Remove a connection."""
        if name in self.connections:
            del self.connections[name]
            self._save()
            return True
        return False

    def list_connections(self) -> List[DatabaseConnection]:
        """List all connections."""
        return list(self.connections.values())

    def connect(self, name: str) -> bool:
        """Set active connection."""
        if name in self.connections:
            self.active_connection = self.connections[name]
            return True
        return False

    @contextmanager
    def _get_sqlite_connection(self, connection_string: str):
        """Get SQLite connection context."""
        conn = sqlite3.connect(connection_string)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def query(
        self,
        sql: str,
        params: Optional[Tuple] = None,
        connection_name: Optional[str] = None,
    ) -> QueryResult:
        """
        Execute a SQL query.

        Args:
            sql: SQL query
            params: Query parameters
            connection_name: Connection to use

        Returns:
            QueryResult
        """
        import time
        start_time = time.time()

        # Get connection
        if connection_name:
            conn_config = self.connections.get(connection_name)
        else:
            conn_config = self.active_connection

        if not conn_config:
            return QueryResult(
                success=False,
                error="No active database connection",
                query=sql,
            )

        result = QueryResult(query=sql, success=True)

        try:
            if conn_config.type == "sqlite":
                with self._get_sqlite_connection(conn_config.connection_string) as conn:
                    cursor = conn.cursor()

                    if params:
                        cursor.execute(sql, params)
                    else:
                        cursor.execute(sql)

                    # Check if it's a SELECT query
                    sql_upper = sql.strip().upper()
                    if sql_upper.startswith("SELECT") or sql_upper.startswith("PRAGMA"):
                        rows = cursor.fetchall()
                        if rows:
                            result.columns = list(rows[0].keys())
                            result.rows = [dict(row) for row in rows]
                            result.row_count = len(rows)
                    else:
                        conn.commit()
                        result.affected_rows = cursor.rowcount

            else:
                result.success = False
                result.error = f"Database type '{conn_config.type}' not yet supported (SQLite only)"

        except Exception as e:
            result.success = False
            result.error = str(e)

        result.execution_time = time.time() - start_time
        return result

    def get_tables(self, connection_name: Optional[str] = None) -> List[str]:
        """Get list of tables in database."""
        result = self.query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
            connection_name=connection_name,
        )

        if result.success:
            return [row["name"] for row in result.rows]
        return []

    def get_table_info(
        self,
        table_name: str,
        connection_name: Optional[str] = None,
    ) -> Optional[TableInfo]:
        """Get information about a table."""
        # Get columns
        columns_result = self.query(
            f"PRAGMA table_info({table_name})",
            connection_name=connection_name,
        )

        if not columns_result.success:
            return None

        columns = []
        for row in columns_result.rows:
            columns.append({
                "name": row["name"],
                "type": row["type"],
                "nullable": not row["notnull"],
                "default": row["dflt_value"],
                "primary_key": bool(row["pk"]),
            })

        # Get row count
        count_result = self.query(
            f"SELECT COUNT(*) as count FROM {table_name}",
            connection_name=connection_name,
        )
        row_count = count_result.rows[0]["count"] if count_result.success and count_result.rows else 0

        # Get indexes
        index_result = self.query(
            f"PRAGMA index_list({table_name})",
            connection_name=connection_name,
        )
        indexes = [row["name"] for row in index_result.rows] if index_result.success else []

        return TableInfo(
            name=table_name,
            columns=columns,
            row_count=row_count,
            indexes=indexes,
        )

    def create_table(
        self,
        table_name: str,
        columns: List[Dict[str, str]],
        connection_name: Optional[str] = None,
    ) -> QueryResult:
        """
        Create a new table.

        Args:
            table_name: Table name
            columns: List of {"name": str, "type": str, "constraints": str}
            connection_name: Connection to use

        Returns:
            QueryResult
        """
        col_defs = []
        for col in columns:
            col_def = f"{col['name']} {col['type']}"
            if col.get("constraints"):
                col_def += f" {col['constraints']}"
            col_defs.append(col_def)

        sql = f"CREATE TABLE {table_name} ({', '.join(col_defs)})"
        return self.query(sql, connection_name=connection_name)

    def insert(
        self,
        table_name: str,
        data: Dict[str, Any],
        connection_name: Optional[str] = None,
    ) -> QueryResult:
        """Insert a row into table."""
        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        return self.query(sql, tuple(data.values()), connection_name)

    def export_table(
        self,
        table_name: str,
        output_path: Path,
        format: str = "json",
        connection_name: Optional[str] = None,
    ) -> bool:
        """
        Export table to file.

        Args:
            table_name: Table to export
            output_path: Output file path
            format: Export format (json, csv)
            connection_name: Connection to use

        Returns:
            Success status
        """
        result = self.query(f"SELECT * FROM {table_name}", connection_name=connection_name)

        if not result.success:
            return False

        try:
            if format == "json":
                output_path.write_text(
                    json.dumps(result.rows, indent=2, default=str),
                    encoding="utf-8"
                )
            elif format == "csv":
                import csv
                with open(output_path, "w", newline="", encoding="utf-8") as f:
                    if result.rows:
                        writer = csv.DictWriter(f, fieldnames=result.columns)
                        writer.writeheader()
                        writer.writerows(result.rows)
            return True
        except Exception:
            return False

    def import_table(
        self,
        table_name: str,
        input_path: Path,
        format: str = "json",
        connection_name: Optional[str] = None,
    ) -> int:
        """
        Import data into table.

        Args:
            table_name: Target table
            input_path: Input file path
            format: File format (json, csv)
            connection_name: Connection to use

        Returns:
            Number of rows imported
        """
        try:
            if format == "json":
                data = json.loads(input_path.read_text(encoding="utf-8"))
            elif format == "csv":
                import csv
                with open(input_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    data = list(reader)
            else:
                return 0

            count = 0
            for row in data:
                result = self.insert(table_name, row, connection_name)
                if result.success:
                    count += 1

            return count
        except Exception:
            return 0

    def format_result(self, result: QueryResult) -> str:
        """Format query result for display."""
        lines = []
        lines.append("=" * 60)
        lines.append("  QUERY RESULT")
        lines.append("=" * 60)
        lines.append("")

        if result.error:
            lines.append(f"[ERROR] {result.error}")
        else:
            lines.append(f"Status: {'[OK]' if result.success else '[FAILED]'}")
            lines.append(f"Time: {result.execution_time:.3f}s")

            if result.rows:
                lines.append(f"Rows: {result.row_count}")
                lines.append("")

                # Simple table format
                if result.columns:
                    lines.append(" | ".join(result.columns))
                    lines.append("-" * 60)

                    for row in result.rows[:20]:
                        values = [str(row.get(col, ""))[:15] for col in result.columns]
                        lines.append(" | ".join(values))

                    if result.row_count > 20:
                        lines.append(f"... and {result.row_count - 20} more rows")
            else:
                lines.append(f"Affected Rows: {result.affected_rows}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def get_report(self, connection_name: Optional[str] = None) -> str:
        """Generate database report."""
        lines = []
        lines.append("=" * 60)
        lines.append("  DATABASE REPORT")
        lines.append("=" * 60)
        lines.append("")

        tables = self.get_tables(connection_name)

        if not tables:
            lines.append("No tables found (or no active connection)")
        else:
            lines.append(f"Tables: {len(tables)}")
            lines.append("")

            for table in tables[:10]:
                info = self.get_table_info(table, connection_name)
                if info:
                    lines.append(f"{table} ({info.row_count} rows)")
                    for col in info.columns[:5]:
                        pk = " [PK]" if col["primary_key"] else ""
                        lines.append(f"  - {col['name']}: {col['type']}{pk}")
                    if len(info.columns) > 5:
                        lines.append(f"  ... and {len(info.columns) - 5} more columns")
                    lines.append("")

            if len(tables) > 10:
                lines.append(f"... and {len(tables) - 10} more tables")

        lines.append("=" * 60)

        return "\n".join(lines)


# Global instance
_db_tools: Optional[DatabaseTools] = None


def get_database_tools() -> DatabaseTools:
    """Get or create database tools."""
    global _db_tools
    if _db_tools is None:
        _db_tools = DatabaseTools()
    return _db_tools


# Convenience functions
def db_query(sql: str, connection_name: Optional[str] = None) -> QueryResult:
    """Execute SQL query."""
    return get_database_tools().query(sql, connection_name=connection_name)


def db_tables(connection_name: Optional[str] = None) -> List[str]:
    """Get table list."""
    return get_database_tools().get_tables(connection_name)


def db_connect(name: str, db_type: str, connection_string: str) -> DatabaseConnection:
    """Add and connect to database."""
    tools = get_database_tools()
    conn = tools.add_connection(name, db_type, connection_string)
    tools.connect(name)
    return conn
