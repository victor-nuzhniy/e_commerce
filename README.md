# e_commerce

## Development

1. Create in the project root (or obtain from team member) an `.env` file with environment variables required by application.
   Refer `local/example.env` for example. You can copy it and edit during local development:

       cp local/example.env .env

2. Copy `local/docker-compose.example.yml` to the project root:

       cp local/docker-compose.example.yml ./docker-compose.yml

   Feel free to modify it for personal use (e. g. change ports, add more services).


### Local run in docker container using docker-compose

1. Ensure `.env` file has at least `POSTGRES_USER`, `POSTGRES_PASSWORD` and `POSTGRES_DB` variables
   set to any string values.
2. Run _postgres_ and _backend_ in docker containers:

       docker-compose up  # run all services defined in docker-compose file

   > :warning: If you see an error messages about failing to connect database, try running database *first*:
   >
   >     docker-compose up postgres  # wait several seconds until database is up
   >     docker-compose up backend  # in separate terminal
