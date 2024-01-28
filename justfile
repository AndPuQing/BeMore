default:
  @just --list

run:
  docker-compose up -d --build

stop:
  docker-compose down

logs:
  docker-compose logs -f

dev-run:
  docker-compose -f docker-compose.dev.yml up -d --build

dev-stop:
  docker-compose -f docker-compose.dev.yml down

dev-logs:
  docker-compose -f docker-compose.dev.yml logs -f
