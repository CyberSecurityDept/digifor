#!/usr/bin/env python3
"""
Script to check if all tables from models are created correctly in the database
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect
from app.db.base import Base
from app.db.session import engine

# Import all models to register them with Base.metadata
from app.auth.models import User, RefreshToken, BlacklistedToken
from app.case_management.models import Case, CaseLog, Agency, WorkUnit
from app.evidence_management.models import Evidence, CustodyLog, EvidenceType, CustodyReport
from app.suspect_management.models import Suspect
from app.analytics.analytics_management.models import Analytic, AnalyticDevice, ApkAnalytic
from app.analytics.device_management.models import File, Device, HashFile, Contact, Call, SocialMedia, ChatMessage

def check_tables():
    """Check if all expected tables exist in database"""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # Get all tables from models
    expected_tables = list(Base.metadata.tables.keys())
    
    print('=' * 80)
    print('DATABASE TABLE CHECK')
    print('=' * 80)
    print(f'\nExpected tables from models: {len(expected_tables)}')
    print(f'Existing tables in database: {len(existing_tables)}')
    print('\n' + '-' * 80)
    print('TABLE STATUS:')
    print('-' * 80)
    
    all_exist = True
    for table in sorted(expected_tables):
        exists = table in existing_tables
        status = '✓ EXISTS' if exists else '✗ MISSING'
        print(f'{status:12} | {table}')
        if not exists:
            all_exist = False
    
    print('\n' + '-' * 80)
    if all_exist:
        print('✓ All tables exist in database!')
    else:
        print('✗ Some tables are missing!')
        missing = set(expected_tables) - set(existing_tables)
        print(f'\nMissing tables ({len(missing)}):')
        for table in sorted(missing):
            print(f'  - {table}')
    
    # Check for extra tables in database
    extra = set(existing_tables) - set(expected_tables)
    if extra:
        print(f'\nExtra tables in database ({len(extra)}):')
        for table in sorted(extra):
            print(f'  - {table}')
    
    # Check table structures
    print('\n' + '=' * 80)
    print('TABLE STRUCTURE CHECK:')
    print('=' * 80)
    
    for table_name in sorted(expected_tables):
        if table_name not in existing_tables:
            continue
            
        print(f'\n{table_name}:')
        print('-' * 40)
        columns = inspector.get_columns(table_name)
        model_table = Base.metadata.tables.get(table_name)
        
        if model_table:
            model_columns = {col.name: col for col in model_table.columns}
            db_columns = {col['name']: col for col in columns}
            
            # Check for missing columns
            missing_cols = set(model_columns.keys()) - set(db_columns.keys())
            if missing_cols:
                print(f'  ✗ Missing columns: {", ".join(sorted(missing_cols))}')
            
            # Check for extra columns
            extra_cols = set(db_columns.keys()) - set(model_columns.keys())
            if extra_cols:
                print(f'  ⚠ Extra columns: {", ".join(sorted(extra_cols))}')
            
            # Check column types
            for col_name, model_col in model_columns.items():
                if col_name in db_columns:
                    db_col = db_columns[col_name]
                    model_type = str(model_col.type)
                    db_type = str(db_col['type'])
                    # Simple type check (can be improved)
                    if model_type != db_type and not (model_type.startswith('VARCHAR') and db_type.startswith('VARCHAR')):
                        print(f'  ⚠ Type mismatch for {col_name}: model={model_type}, db={db_type}')
            
            if not missing_cols and not extra_cols:
                print(f'  ✓ All columns match ({len(model_columns)} columns)')
        else:
            print(f'  ⚠ Model not found for table {table_name}')
    
    print('\n' + '=' * 80)
    return all_exist

if __name__ == '__main__':
    try:
        check_tables()
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

