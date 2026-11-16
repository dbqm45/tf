CREATE TABLE users (
    id bigint PRIMARY KEY,
    email varchar(255) NOT NULL, -- pii: dane osobowe
    email_verified boolean NOT NULL DEFAULT false,
    status varchar(20) NOT NULL
);
