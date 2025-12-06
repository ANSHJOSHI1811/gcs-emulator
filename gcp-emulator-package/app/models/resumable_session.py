"""
ResumableSession model - tracks resumable upload sessions
"""
from datetime import datetime
from app.factory import db


class ResumableSession(db.Model):
    """ResumableSession model for tracking upload sessions"""
    __tablename__ = "resumable_sessions"
    
    session_id = db.Column(db.String(255), primary_key=True)
    bucket_id = db.Column(db.String(63), db.ForeignKey("buckets.id"), nullable=False)
    object_name = db.Column(db.String(1024), nullable=False)
    metadata_json = db.Column(db.Text)
    current_offset = db.Column(db.BigInteger, default=0)
    total_size = db.Column(db.BigInteger)
    temp_path = db.Column(db.String(1024))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index("idx_resumable_sessions_bucket", "bucket_id"),
        db.Index("idx_resumable_sessions_created", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<ResumableSession {self.session_id}>"
