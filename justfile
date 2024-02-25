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


test: clean
  docker-compose -f docker-compose.ci.yml up -d --build
  docker-compose exec -T backend poetry run pytest --cov=app --cov-report=xml

clean:
  docker-compose -f docker-compose.dev.yml down --rmi local --volumes --remove-orphans
  docker-compose -f docker-compose.ci.yml down --rmi local --volumes --remove-orphans
  docker-compose down --rmi local --volumes --remove-orphans
