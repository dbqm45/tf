-- pii: dane osobowe (inwentarz: users.phone_number)
ALTER TABLE users ADD COLUMN phone_number varchar(32);
ALTER TABLE users ADD COLUMN is_mobile boolean;
