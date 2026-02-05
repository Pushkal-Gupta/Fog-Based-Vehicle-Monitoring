To test the `/api/ingest` POST

to post a new vehicle data from edge

```
curl -X POST "http://localhost:8000/api/ingest" -H "Content-Type: application/json" -d @sample.json
```