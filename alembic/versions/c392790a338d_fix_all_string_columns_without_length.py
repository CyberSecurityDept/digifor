"""fix_all_string_columns_without_length

Revision ID: c392790a338d
Revises: 5b5749ce0944
Create Date: 2025-12-05 20:25:50.178276

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'c392790a338d'
down_revision: Union[str, None] = '5b5749ce0944'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    # Helper function to safely alter column
    def alter_column_if_exists(table_name, column_name, new_type, existing_type=None, nullable=None):
        if table_name not in tables:
            return
        try:
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            if column_name in columns:
                kwargs = {'type_': new_type}
                if existing_type:
                    kwargs['existing_type'] = existing_type
                if nullable is not None:
                    kwargs['existing_nullable'] = nullable
                op.alter_column(table_name, column_name, **kwargs)
        except Exception as e:
            print(f"Warning: Could not alter {table_name}.{column_name}: {e}")
    
    # Analytics models
    alter_column_if_exists('analytics', 'analytic_name', sa.String(255), sa.String(), False)
    alter_column_if_exists('analytics', 'type', sa.String(100), sa.String(), True)
    
    # Files table
    alter_column_if_exists('files', 'file_name', sa.Text(), sa.String(), False)
    alter_column_if_exists('files', 'file_path', sa.Text(), sa.String(), False)
    alter_column_if_exists('files', 'notes', sa.Text(), sa.String(), True)
    alter_column_if_exists('files', 'created_by', sa.String(255), sa.String(), True)
    alter_column_if_exists('files', 'type', sa.String(100), sa.String(), False)
    alter_column_if_exists('files', 'tools', sa.String(100), sa.String(), True)
    alter_column_if_exists('files', 'method', sa.String(100), sa.String(), True)
    
    # Devices table
    alter_column_if_exists('devices', 'owner_name', sa.Text(), sa.String(), True)
    alter_column_if_exists('devices', 'phone_number', sa.String(50), sa.String(), True)
    alter_column_if_exists('devices', 'device_name', sa.String(255), sa.String(), True)
    alter_column_if_exists('devices', 'app_data_size', sa.String(50), sa.String(), True)
    alter_column_if_exists('devices', 'device_type', sa.String(100), sa.String(), True)
    alter_column_if_exists('devices', 'device_model', sa.String(255), sa.String(), True)
    alter_column_if_exists('devices', 'os_version', sa.String(100), sa.String(), True)
    alter_column_if_exists('devices', 'imei', sa.String(50), sa.String(), True)
    alter_column_if_exists('devices', 'serial_number', sa.String(100), sa.String(), True)
    alter_column_if_exists('devices', 'extraction_tool', sa.String(100), sa.String(), True)
    alter_column_if_exists('devices', 'extraction_method', sa.String(100), sa.String(), True)
    alter_column_if_exists('devices', 'is_encrypted', sa.String(20), sa.String(), True)
    alter_column_if_exists('devices', 'encryption_type', sa.String(100), sa.String(), True)
    alter_column_if_exists('devices', 'is_rooted', sa.String(20), sa.String(), True)
    alter_column_if_exists('devices', 'is_jailbroken', sa.String(20), sa.String(), True)
    
    # Hash files table
    alter_column_if_exists('hash_files', 'file_name', sa.Text(), sa.String(), True)
    alter_column_if_exists('hash_files', 'path_original', sa.Text(), sa.String(), True)
    alter_column_if_exists('hash_files', 'md5_hash', sa.String(32), sa.String(), True)
    alter_column_if_exists('hash_files', 'sha1_hash', sa.String(40), sa.String(), True)
    alter_column_if_exists('hash_files', 'algorithm', sa.String(50), sa.String(), True)
    alter_column_if_exists('hash_files', 'source_tool', sa.String(100), sa.String(), True)
    alter_column_if_exists('hash_files', 'file_type', sa.String(100), sa.String(), True)
    
    # Contacts table
    alter_column_if_exists('contacts', 'display_name', sa.Text(), sa.String(), True)
    alter_column_if_exists('contacts', 'phone_number', sa.String(50), sa.String(), True)
    alter_column_if_exists('contacts', 'type', sa.String(100), sa.String(), True)
    
    # Social media table
    alter_column_if_exists('social_media', 'type', sa.String(100), sa.String(), True)
    alter_column_if_exists('social_media', 'source', sa.String(100), sa.String(), True)
    alter_column_if_exists('social_media', 'phone_number', sa.String(50), sa.String(), True)
    alter_column_if_exists('social_media', 'whatsapp_id', sa.String(255), sa.String(), True)
    alter_column_if_exists('social_media', 'telegram_id', sa.String(255), sa.String(), True)
    alter_column_if_exists('social_media', 'instagram_id', sa.String(255), sa.String(), True)
    alter_column_if_exists('social_media', 'X_id', sa.String(255), sa.String(), True)
    alter_column_if_exists('social_media', 'facebook_id', sa.String(255), sa.String(), True)
    alter_column_if_exists('social_media', 'tiktok_id', sa.String(255), sa.String(), True)
    alter_column_if_exists('social_media', 'sheet_name', sa.String(255), sa.String(), True)
    
    # Calls table
    alter_column_if_exists('calls', 'direction', sa.String(50), sa.String(), True)
    alter_column_if_exists('calls', 'source', sa.String(100), sa.String(), True)
    alter_column_if_exists('calls', 'type', sa.String(100), sa.String(), True)
    alter_column_if_exists('calls', 'timestamp', sa.String(100), sa.String(), True)
    alter_column_if_exists('calls', 'duration', sa.String(50), sa.String(), True)
    alter_column_if_exists('calls', 'thread_id', sa.String(255), sa.String(), True)
    
    # Chat messages table
    alter_column_if_exists('chat_messages', 'platform', sa.String(100), sa.String(), False)
    alter_column_if_exists('chat_messages', 'account_name', sa.String(255), sa.String(), True)
    alter_column_if_exists('chat_messages', 'group_name', sa.Text(), sa.String(), True)
    alter_column_if_exists('chat_messages', 'group_id', sa.String(255), sa.String(), True)
    alter_column_if_exists('chat_messages', 'from_name', sa.Text(), sa.String(), True)
    alter_column_if_exists('chat_messages', 'sender_number', sa.String(50), sa.String(), True)
    alter_column_if_exists('chat_messages', 'to_name', sa.Text(), sa.String(), True)
    alter_column_if_exists('chat_messages', 'recipient_number', sa.String(50), sa.String(), True)
    alter_column_if_exists('chat_messages', 'timestamp', sa.String(100), sa.String(), True)
    alter_column_if_exists('chat_messages', 'thread_id', sa.String(255), sa.String(), True)
    alter_column_if_exists('chat_messages', 'chat_id', sa.String(255), sa.String(), True)
    alter_column_if_exists('chat_messages', 'message_id', sa.String(255), sa.String(), True)
    alter_column_if_exists('chat_messages', 'message_type', sa.String(100), sa.String(), True)
    alter_column_if_exists('chat_messages', 'chat_type', sa.String(100), sa.String(), True)
    alter_column_if_exists('chat_messages', 'status', sa.String(50), sa.String(), True)
    alter_column_if_exists('chat_messages', 'direction', sa.String(50), sa.String(), True)
    alter_column_if_exists('chat_messages', 'source_tool', sa.String(100), sa.String(), True)
    alter_column_if_exists('chat_messages', 'sheet_name', sa.String(255), sa.String(), True)
    
    # Analytics history table
    alter_column_if_exists('analytics_history', 'analytic_name', sa.String(255), sa.String(), False)
    alter_column_if_exists('analytics_history', 'method', sa.String(100), sa.String(), True)
    alter_column_if_exists('analytics_history', 'created_by', sa.String(255), sa.String(), True)
    
    # Analytic files table
    alter_column_if_exists('analytic_files', 'status', sa.String(50), sa.String(), True)
    alter_column_if_exists('analytic_files', 'scoring', sa.String(100), sa.String(), True)
    
    # APK analytics table
    alter_column_if_exists('apk_analytics', 'item', sa.Text(), sa.String(), True)
    alter_column_if_exists('apk_analytics', 'description', sa.Text(), sa.String(), True)
    alter_column_if_exists('apk_analytics', 'status', sa.String(50), sa.String(), True)
    alter_column_if_exists('apk_analytics', 'malware_scoring', sa.String(100), sa.String(), True)
    
    # Evidence table
    alter_column_if_exists('evidence', 'title', sa.Text(), sa.String(200), False)
    
    # Custody reports table
    alter_column_if_exists('custody_reports', 'location', sa.Text(), sa.String(200), True)
    
    # Cases table
    alter_column_if_exists('cases', 'title', sa.Text(), sa.String(255), False)
    
    # Users table
    alter_column_if_exists('users', 'fullname', sa.Text(), sa.String(255), False)
    
    # Messages table (old analytics models)
    alter_column_if_exists('messages', 'direction', sa.String(50), sa.String(), True)
    alter_column_if_exists('messages', 'source', sa.String(100), sa.String(), True)
    alter_column_if_exists('messages', 'type', sa.String(100), sa.String(), True)
    alter_column_if_exists('messages', 'timestamp', sa.String(100), sa.String(), True)
    alter_column_if_exists('messages', 'thread_id', sa.String(255), sa.String(), True)
    
    # Contacts table (old analytics models)
    alter_column_if_exists('contacts', 'type', sa.String(100), sa.String(), True)
    
    # Hashfiles table (old analytics models)
    alter_column_if_exists('hashfiles', 'name', sa.Text(), sa.String(), True)
    alter_column_if_exists('hashfiles', 'file_path', sa.Text(), sa.String(), False)


def downgrade() -> None:
    # Note: Downgrade is complex and may not be fully reversible
    # This is a simplified version
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    def alter_column_if_exists(table_name, column_name, new_type, existing_type=None, nullable=None):
        if table_name not in tables:
            return
        try:
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            if column_name in columns:
                kwargs = {'type_': new_type}
                if existing_type:
                    kwargs['existing_type'] = existing_type
                if nullable is not None:
                    kwargs['existing_nullable'] = nullable
                op.alter_column(table_name, column_name, **kwargs)
        except Exception as e:
            print(f"Warning: Could not alter {table_name}.{column_name}: {e}")
    
    # Revert changes (simplified - may need adjustment based on actual previous state)
    alter_column_if_exists('evidence', 'title', sa.String(200), sa.Text(), False)
    alter_column_if_exists('custody_reports', 'location', sa.String(200), sa.Text(), True)
    alter_column_if_exists('cases', 'title', sa.String(255), sa.Text(), False)
    alter_column_if_exists('users', 'fullname', sa.String(255), sa.Text(), False)

