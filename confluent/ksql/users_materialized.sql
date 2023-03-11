CREATE OR REPLACE TABLE USERS_MATERIALIZED AS
  select 
    after->userid, 
    LATEST_BY_OFFSET(after->first_name) as first_name, 
    LATEST_BY_OFFSET(after->last_name) as last_name, 
    LATEST_BY_OFFSET(after->phone) as phone
  from users
  GROUP BY after->userid
  EMIT CHANGES
