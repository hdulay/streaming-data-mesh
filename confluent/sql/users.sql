-- TODO: configure postgres for replication
-- pg_hba.conf & postgres.conf


create table USERS (
	userid int primary key,
	first_name varchar(63) not null,
	last_name varchar(63) not null,
	phone varchar(63)
);
ALTER TABLE USERS REPLICA IDENTITY FULL;

insert into users values(1, 'foo', 'bar', '123')
