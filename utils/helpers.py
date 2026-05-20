def get_display_id(db_id):
    """Converts a database integer ID into a clean fintech-style ID (e.g., TXN-001)."""
    return f"TXN-{db_id:03d}"
