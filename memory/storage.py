import sqlite3
from pathlib import Path
import json

class MemoryStorage:
    def __init__(self,user_id):
        self.path=Path("memory")/user_id
        self.path.mkdir(parents=True,exist_ok=True)
        self.db=self.path/"memory.db"
        self.conn=sqlite3.connect(
            self.db,
            check_same_thread=False
        )
        self.conn.row_factory=sqlite3.Row
        self.cursor=self.conn.cursor()
        self._create_tables()
    def _create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS facts(
            id TEXT PRIMARY KEY,
            text TEXT,
            category TEXT,
            importance INTEGER,
            created TEXT,
            updated TEXT,
            last_used TEXT,
            used INTEGER,
            embedding TEXT,
            metadata TEXT
        )
        """)
        self.conn.commit()
    def insert_fact(self,fact):
        embedding=None
        if fact.embedding is not None:
            try:
                embedding=json.dumps(fact.embedding.tolist())
            except AttributeError:
                embedding=json.dumps(fact.embedding)
        self.cursor.execute("""
        INSERT OR REPLACE INTO facts
        VALUES(?,?,?,?,?,?,?,?,?,?)
        """,(
            fact.id,
            fact.text,
            fact.category,
            fact.importance,
            fact.created,
            fact.updated,
            fact.last_used,
            fact.used,
            embedding,
            json.dumps(fact.metadata or {})
        ))
        self.conn.commit()
    def update_fact(self,fact):
        embedding=None
        if fact.embedding is not None:
            try:
                embedding=json.dumps(fact.embedding.tolist())
            except AttributeError:
                embedding=json.dumps(fact.embedding)
        self.cursor.execute("""
        UPDATE facts
        SET
            text=?,
            category=?,
            importance=?,
            updated=?,
            last_used=?,
            used=?,
            embedding=?,
            metadata=?
        WHERE id=?
        """,(
            fact.text,
            fact.category,
            fact.importance,
            fact.updated,
            fact.last_used,
            fact.used,
            embedding,
            json.dumps(fact.metadata or {}),
            fact.id
        ))
        self.conn.commit()
    def get_by_category(self,category):
        rows=self.cursor.execute(
            "SELECT * FROM facts WHERE category=?",
            (category,)
        ).fetchall()
        return rows
    def get_all(self):
        return self.cursor.execute("""
        SELECT *
        FROM facts
        ORDER BY importance DESC,
                 used DESC,
                 updated DESC
        """).fetchall()
    def delete(self,fact_id):
        self.cursor.execute(
            "DELETE FROM facts WHERE id=?",
            (fact_id,)
        )
        self.conn.commit()
    def vacuum(self):
        self.cursor.execute("VACUUM")
        self.conn.commit()
    def close(self):
        self.conn.close()