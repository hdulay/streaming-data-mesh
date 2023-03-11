-- TODO: configure postgres for replication
-- pg_hba.conf & postgres.conf


create table products (
	productid int primary key,
	name varchar(63) not null,
	description varchar(63)
);
ALTER TABLE products REPLICA IDENTITY FULL;

insert into products values(1, 'p1', 'dont buy this')
