@echo off
echo Starting Skippy AI Agent...
docker-compose up -d
echo Skippy services starting...
echo n8n available at: http://localhost:5678
echo Voice service will start automatically
echo Check logs with: docker-compose logs -f
pause