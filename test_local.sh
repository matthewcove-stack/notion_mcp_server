#!/bin/bash
# Quick test script for local endpoints

echo "Testing local endpoints..."
echo ""

echo "1. Health check:"
curl -s http://localhost:3333/health | jq .
echo ""

echo "2. OpenAPI spec (first 500 chars):"
curl -s http://localhost:3333/openapi.json | jq . | head -20
echo ""

echo "3. /v1/meta without auth (should fail):"
curl -s -w "\nHTTP Status: %{http_code}\n" http://localhost:3333/v1/meta
echo ""

echo "4. /v1/meta with auth (if ACTION_API_TOKEN is set):"
if [ -n "$ACTION_API_TOKEN" ]; then
    curl -s -H "Authorization: Bearer $ACTION_API_TOKEN" http://localhost:3333/v1/meta | jq .
else
    echo "ACTION_API_TOKEN not set, skipping"
fi

