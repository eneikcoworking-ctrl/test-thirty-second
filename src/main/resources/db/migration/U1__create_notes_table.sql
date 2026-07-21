-- U1__create_notes_table.sql
-- Down-migration script to rollback V1__create_notes_table.sql
DROP INDEX IF EXISTS idx_notes_owner_created_at_desc;
DROP TABLE IF EXISTS notes;
