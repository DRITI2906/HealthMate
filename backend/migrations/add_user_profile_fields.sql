-- Migration script to add full_name and date_of_birth columns to users table
ALTER TABLE users ADD COLUMN full_name VARCHAR(100);
ALTER TABLE users ADD COLUMN date_of_birth DATE;
