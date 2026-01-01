from app.factory import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    db.session.execute(text('ALTER TABLE instances DROP COLUMN IF EXISTS metadata;'))
    db.session.commit()
    print('✓ Dropped old metadata column')
