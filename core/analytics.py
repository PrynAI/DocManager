"""Analytics helpers for app events and reader progress."""

from datetime import datetime

from db.database import get_connection


class AnalyticsService:
    """Record and query lightweight usage analytics in SQLite."""

    def record_page_visit(self, document_id, page_number):
        """Store one reader page-visit event."""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO page_visits (document_id, page_number, timestamp)
        VALUES (?, ?, ?)
        """, (document_id, page_number, datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def get_unique_pages_viewed(self, document_id):
        """Return how many distinct pages were viewed for a document."""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT COUNT(DISTINCT page_number)
        FROM page_visits
        WHERE document_id = ?
        """, (document_id,))

        result = cursor.fetchone()[0]
        conn.close()

        return result if result else 0

    def record_app_visit(self, event_type):
        """Store one app-level event such as upload or search."""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO app_visits (event_type, timestamp)
        VALUES (?, ?)
        """, (event_type, datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def get_app_visits(self):
        """Return aggregated app event counts for the analytics dashboard."""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT event_type, COUNT(*) AS event_count
        FROM app_visits
        GROUP BY event_type
        ORDER BY event_count DESC, event_type ASC
        """)

        data = cursor.fetchall()
        conn.close()

        return data

    def reset_analytics(self):
        """Clear analytics tables without deleting documents or search data."""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM page_visits")
        cursor.execute("DELETE FROM app_visits")

        conn.commit()
        conn.close()
