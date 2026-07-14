-- Rollback 110
BEGIN;
DELETE FROM re_engine.re_states WHERE state_code IN ('AP','AR','AS','BR','CT','GA','GJ','HR','HP','JH','KA','KL','MP','MH','MN','ML','MZ','NL','OD','PB','RJ','SK','TN','TS','TR','UP','UK','WB','AN','CH','DN','DL','JK','LA','LD','PY');
COMMIT;
