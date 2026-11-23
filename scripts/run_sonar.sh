#!/usr/bin/env bash
# Run SonarQube analysis. Needs: docker, SonarQube container 'sonarqube' on :9000, data/sonar.env (SONAR_TOKEN).
# Files are copied with `docker cp` because Windows bind mounts dropped files during the scan.
set -e
source data/sonar.env
W=${SONAR_WORK:-/tmp/sq_work}; rm -rf "$W"; mkdir -p "$W/tests" "$W/reports"
cp -r src "$W/src"; rm -rf "$W/src/ephios/static" "$W/src/ephios/locale"; cp -r tests/team "$W/tests/team"
cp reports/coverage.xml "$W/reports/"; cp sonar-project.properties "$W/"; echo "sonar.scm.disabled=true" >> "$W/sonar-project.properties"
docker rm -f sqscan >/dev/null 2>&1 || true
docker create --name sqscan --add-host=host.docker.internal:host-gateway -e SONAR_HOST_URL=http://host.docker.internal:9000 -e SONAR_TOKEN="$SONAR_TOKEN" sonarsource/sonar-scanner-cli >/dev/null
docker cp "$W/." sqscan:/usr/src/; docker start -a sqscan; docker rm -f sqscan >/dev/null
