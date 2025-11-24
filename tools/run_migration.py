#!/usr/bin/env python3
"""Run Alembic migration"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alembic.config import Config
from alembic import command

def run_migration():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration()

