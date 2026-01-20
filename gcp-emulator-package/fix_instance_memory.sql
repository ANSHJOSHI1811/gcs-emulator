-- Fix instances table memory column
ALTER TABLE instances RENAME COLUMN memory TO memory_mb;
