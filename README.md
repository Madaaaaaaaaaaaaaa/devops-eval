# devops-eval

Pipeline complet : conteneurisation, CI/CD et métriques, pour une API Flask avec base Postgres.

## Architecture

- **app/** : API Flask (`/health`, `/visit`, `/metrics`)
- **Dockerfile** : build multi-stage, image `python:3.12-slim`, utilisateur non-root, `HEALTHCHECK`
- **docker-compose.yml** : services `app`, `db` (Postgres), `prometheus`
- **.github/workflows/ci.yml** : lint, test (matrix Python 3.11/3.12, service Postgres), build, `ci-ok`
- **.github/workflows/cd.yml** : build + push sur GHCR (tags `latest`, SHA court, semver), déploiement sur runner self-hosted, vérification post-déploiement avec rollback
- **.github/actions/setup-python-deps/** : action locale réutilisable (setup Python + cache + install)
- **prometheus/** : scrape config + règles d'alerte

## Commandes pour lancer le projet en local

\`\`\`bash
git clone https://github.com/Madaaaaaaaaaaaaaa/devops-eval.git
cd devops-eval
docker compose up --build
curl localhost:8000/health
curl -X POST localhost:8000/visit
curl localhost:8000/metrics
# Prometheus : http://localhost:9090/alerts
\`\`\`

## Endpoints

- `GET /health` : vérifie la connexion à la base, renvoie 200 ou 503
- `POST /visit` : incrémente un compteur de visites en base
- `GET /metrics` : expose les métriques au format Prometheus

## Métriques exposées

- `http_requests_total{endpoint, code}` : compteur de requêtes
- `http_request_duration_seconds` : histogramme de latence par route (permet p95/p99)
- `app_version_info{version}` : jauge exposant le SHA du commit déployé

## Règles d'alerte

- **HighErrorRate5xx** : ratio des réponses 5xx sur le total > 5 % pendant 5 minutes. Seuil choisi pour capter une dégradation réelle sans alerter sur un pic isolé ; `for: 5m` filtre les faux positifs ponctuels.
- **HighLatencyP95** : p95 de latence > 500 ms pendant 10 minutes. Seuil représentant une dégradation perceptible par l'utilisateur ; `for: 10m` car la latence fluctue plus que le taux d'erreur.

## CI

Quatre jobs obligatoires : `lint` (flake8 + yamllint), `test` (matrix 3.11/3.12, service Postgres réellement utilisé, cache pip, rapports JUnit/coverage publiés), `build` (build de l'image, récupère les rapports), `ci-ok` (vert obligatoire, requis par la protection de branche `main`).

## CD

Déclenché sur push vers `main` (après CI verte via `workflow_call`) ou manuellement via `workflow_dispatch` (input `environment: production`). Construit et pousse l'image sur `ghcr.io` avec 3 tags (`latest`, SHA court, semver `1.0.<run_number>`), puis déploie sur le runner self-hosted : vérification post-déploiement avec 3 tentatives sur `/health`, rollback automatique vers le SHA précédent en cas d'échec.

## Secrets et permissions

Chaque workflow déclare des `permissions` explicites en tête (moindre privilège). Le `GITHUB_TOKEN` intégré est utilisé pour l'authentification sur GHCR, aucun secret personnalisé n'est nécessaire.

## Runner self-hosted

Un runner GitHub Actions est installé sur une machine Ubuntu (WSL2), avec Docker Engine, pour exécuter le job `deploy` et déployer réellement l'application.

## Captures

- Cache HIT sur un second run de la CI : `docs/cache-hit.png`
