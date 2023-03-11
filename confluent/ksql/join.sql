-- drop table CLICK_USERS;
CREATE OR REPLACE STREAM CLICK_USERS AS
select 
  c.ip,
  c.userid userid,
  c.agent agent,
  c.request request,
  c.status status,
  u.first_name first_name,
  u.last_name last_name,
  u.phone phone
from clickstream c
join USERS_MATERIALIZED u on c.userid = u.userid
EMIT CHANGES
