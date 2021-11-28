## Steps to initialize the database after first starting the containers

(1) docker-compose up
(2) mv ./api/initial_data/*.csv ./api/postgres-data
(3) docker exec -it final-master_db_1 bash
(4) psql -U postgres
(5) \c webers 
(6) \copy sales (filnr, artnr, date, discount, amount) FROM '/var/lib/postgresql/data/sales.csv' DELIMITER ',' CSV HEADER; 
(7) \copy location (filnr, street, zipcode, city, state, lat, lon) FROM '/var/lib/postgresql/data/location.csv' DELIMITER ',' CSV HEADER;