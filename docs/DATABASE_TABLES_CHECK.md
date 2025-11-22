# Database Tables Check

## Expected Tables from Models

### Auth Models (`app/auth/models.py`)
1. **users** - User accounts
   - id, email, fullname, tag, password, hashed_password, role, is_active, created_at
   
2. **refresh_tokens** - Refresh tokens for authentication
   - id, token, user_id (FK), expires_at, revoked, created_at
   
3. **blacklisted_tokens** - Blacklisted JWT tokens
   - id, token_hash, user_id (FK), expires_at, created_at

### Case Management Models (`app/case_management/models.py`)
4. **agencies** - Law enforcement agencies
   - id, name
   
5. **work_units** - Work units within agencies
   - id, name, agency_id (FK)
   
6. **cases** - Case records
   - id, case_number, title, description, status, main_investigator, agency_id (FK), work_unit_id (FK), notes, created_at, updated_at
   
7. **case_logs** - Case activity logs
   - id, case_id (FK), action, changed_by, change_detail, notes, status, created_at

### Evidence Management Models (`app/evidence_management/models.py`)
8. **evidence_types** - Types of evidence
   - id, name, description, category, is_active, created_at, updated_at
   
9. **evidence** - Evidence records
   - id, evidence_number, title, description, evidence_type_id (FK), case_id (FK), suspect_id (FK), file_path, file_size, file_hash, file_type, file_extension, analysis_status, analysis_progress, investigator, collected_date, notes (JSON), is_confidential, created_at, updated_at
   
10. **custody_logs** - Evidence custody logs
    - id, evidence_id (FK), event_type, event_date, person_name, person_title, person_id, location, location_type, action_description, tools_used (JSON), conditions, duration, transferred_to, transferred_from, transfer_reason, witness_name, witness_signature, verification_method, is_immutable, is_verified, verification_date, verified_by, notes, log_hash, created_at, created_by
    
11. **custody_reports** - Evidence custody reports
    - id, evidence_id (FK), report_type, report_title, report_description, generated_by, generated_date, report_data (JSON), report_file_path, report_file_hash, compliance_standard, is_verified, verified_by, verification_date, is_active, created_at

### Suspect Management Models (`app/suspect_management/models.py`)
12. **suspects** - Suspect/Witness records
    - id, name, case_name, investigator, status (Enum), case_id (FK), is_unknown, **evidence_number** (NOT evidence_id), evidence_source, created_by, created_at, updated_at

### Analytics Management Models (`app/analytics/analytics_management/models.py`)
13. **analytics_history** - Analytics history records
    - id, analytic_name, method, summary, created_by, created_at, updated_at
    
14. **analytic_device** - Analytics device mappings
    - id, analytic_id (FK), device_ids (ARRAY), created_at, updated_at
    
15. **apk_analytics** - APK analysis results
    - id, item, description, status, malware_scoring, created_at, file_id (FK), analytic_id (FK)

### Device Management Models (`app/analytics/device_management/models.py`)
16. **files** - File records
    - id, file_name, file_path, notes, created_by, type, tools, method, total_size, amount_of_data, created_at, updated_at
    
17. **devices** - Device records
    - id, file_id (FK), owner_name, phone_number, device_name, app_data_size, device_type, device_model, os_version, imei, serial_number, extraction_tool, extraction_date, extraction_method, is_encrypted, encryption_type, is_rooted, is_jailbroken, created_at, updated_at
    
18. **hash_files** - Hash file records
    - id, file_id (FK), file_name, size_bytes, path_original, created_at_original, modified_at_original, md5_hash, sha1_hash, algorithm, source_tool, file_type, created_at, updated_at
    - Indexes: idx_hash_fileid_md5, idx_hash_fileid_sha1, idx_hash_tool
    
19. **contacts** - Contact records
    - id, file_id (FK), display_name, phone_number, type, last_time_contacted, created_at, updated_at
    
20. **social_media** - Social media account records
    - id, file_id (FK), type, source, phone_number, full_name, account_name, whatsapp_id, telegram_id, instagram_id, X_id, facebook_id, tiktok_id, location, sheet_name, created_at, updated_at
    
21. **calls** - Call records
    - id, file_id (FK), direction, source, type, timestamp, duration, caller, receiver, details, thread_id, created_at, updated_at
    
22. **chat_messages** - Chat message records
    - id, file_id (FK), platform, message_text, account_name, **group_name** (NOT name), group_id, from_name, sender_number, to_name, recipient_number, timestamp, thread_id, chat_id, message_id, message_type, chat_type, status, direction, source_tool, sheet_name, created_at, updated_at

## Current Migration Status

### Existing Migrations:
1. `dc2331b01ddd` - Rename evidence_id to evidence_number in suspects (down_revision: None) ⚠️
2. `00a0ca7441c7` - Add name to chat_messages (down_revision: 9bb43e1ad8d3)
3. `9bb43e1ad8d3` - Add account_name to chat_messages
4. `70e296cc56e9` - Add chat_type and status to chat_messages
5. `a803b4f2ca97` - Rename name to group_name and add group_id (down_revision: 00a0ca7441c7)

### Issues Found:

1. **Missing Initial Migration**: Tidak ada migration yang membuat tabel-tabel utama (users, cases, evidence, suspects, dll). Sistem saat ini menggunakan `Base.metadata.create_all()` untuk membuat tabel, bukan migration.

2. **Migration Order Issue**: Migration `dc2331b01ddd` memiliki `down_revision: None`, yang berarti ini dianggap sebagai migration pertama, padahal seharusnya ada migration yang membuat tabel `suspects` terlebih dahulu.

3. **Migration Dependencies**: Beberapa migration untuk `chat_messages` memiliki dependency chain yang tidak jelas.

## Recommendations:

1. **Create Initial Migration**: Buat migration awal yang membuat semua tabel dari models menggunakan `alembic revision --autogenerate -m "initial_schema"`

2. **Fix Migration Order**: Pastikan migration `dc2331b01ddd` memiliki `down_revision` yang benar (harus setelah migration yang membuat tabel suspects).

3. **Use Migration for Schema Changes**: Hindari menggunakan `Base.metadata.create_all()` di production. Gunakan migration untuk semua perubahan schema.

4. **Verify Table Creation**: Pastikan semua 22 tabel di atas dibuat dengan benar di database.

## Action Items:

1. Generate initial migration untuk semua tabel
2. Fix migration order untuk dc2331b01ddd
3. Test migration pada database baru
4. Update docker-compose.yml migrate service untuk menggunakan migration yang benar

