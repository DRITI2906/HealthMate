from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Database connection string - supports both local and team shared database
# For team development, set TEAM_DATABASE_URL in .env file
# For local development, set LOCAL_DATABASE_URL or use default

# Use team database if available, otherwise fall back to local
# In database.py
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("TEAM_DATABASE_URL") or os.getenv("LOCAL_DATABASE_URL", "postgresql://...")

logger.info(f"Connecting to database: {DATABASE_URL}")

# Create engine with connection pooling and better timeout settings
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,
    pool_recycle=1800,  # Recycle connections after 30 minutes
    echo=False  # Set to True for SQL query logging (useful for debugging)
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def create_tables():
    try:
        from models import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

# Handle database migrations with better error handling and data preservation
def migrate_database():
    from models import Base
    from sqlalchemy import text, inspect
    
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # Check if medications table exists and needs migration
        if 'medications' in existing_tables:
            logger.info("Medications table exists, checking if migration is needed...")
            
            # Check if the table has the old schema (prescribed_by vs prescribedBy)
            columns = inspector.get_columns('medications')
            column_names = [col['name'] for col in columns]
            
            if 'prescribed_by' in column_names:
                logger.info("Old schema detected, migrating medications table...")
                
                # Create a temporary table to preserve data
                with engine.connect() as conn:
                    # Create temporary table with old schema
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS medications_temp (
                            id VARCHAR(50) PRIMARY KEY,
                            user_id INTEGER,
                            name VARCHAR(100) NOT NULL,
                            dosage VARCHAR(50) NOT NULL,
                            frequency VARCHAR(50) NOT NULL,
                            prescribed_by VARCHAR(100) NOT NULL,
                            start_date TIMESTAMP NOT NULL,
                            end_date TIMESTAMP,
                            total_doses INTEGER,
                            instructions TEXT,
                            created_at TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users (id)
                        )
                    """))
                    
                    # Copy data to temporary table
                    conn.execute(text("""
                        INSERT INTO medications_temp 
                        SELECT id, user_id, name, dosage, frequency, prescribed_by, 
                               start_date, end_date, total_doses, instructions, created_at
                        FROM medications
                    """))
                    
                    # Drop the old table
                    conn.execute(text("DROP TABLE medications CASCADE"))
                    conn.commit()
                    logger.info("Old medications table dropped")
                
                # Create new table with correct schema
                Base.metadata.create_all(bind=engine)
                logger.info("New medications table created with correct schema")
                
                # Copy data back with corrected column names
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO medications (id, user_id, name, dosage, frequency, 
                                                "prescribedBy", "startDate", "endDate", 
                                                "totalDoses", instructions, created_at)
                        SELECT id, user_id, name, dosage, frequency, prescribed_by, 
                               start_date, end_date, total_doses, instructions, created_at
                        FROM medications_temp
                    """))
                    
                    # Drop the temporary table
                    conn.execute(text("DROP TABLE medications_temp"))
                    conn.commit()
                    logger.info("Data migrated to new medications table")
            else:
                logger.info("Medications table already has correct schema")
        else:
            # Create all tables if they don't exist
            Base.metadata.create_all(bind=engine)
            logger.info("All database tables created successfully")
            
    except Exception as e:
        logger.error(f"Error during database migration: {e}")
        # Fallback to simple table creation
        try:
            from models import Base
            Base.metadata.create_all(bind=engine)
            logger.info("Fallback: Database tables created successfully")
        except Exception as e2:
            logger.error(f"Error in fallback table creation: {e2}")
            raise

# Test database connection
def test_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

# Initialize database on import
if __name__ == "__main__":
    test_connection()