# API Reference

## Authentication

All endpoints require authentication via one of:

1. **API Key Header:**
   ```
   X-API-Key: your-api-key
   ```

2. **Frappe Session Cookie:**
   ```
   Cookie: sid=your-frappe-session-id
   ```

## Endpoints

### Search

#### POST /api/search

Hybrid search (semantic + keyword with RRF fusion).

**Request:**
```json
{
  "query": "employee performance review process",
  "top_k": 5,
  "threshold": 0.5
}
```

**Response:**
```json
{
  "query": "employee performance review process",
  "results": [
    {
      "chunk_id": "uuid",
      "title": "HR Policies 2026",
      "content": "Performance reviews are conducted quarterly...",
      "source": "HR_Policies.pptx",
      "semantic_score": 0.87,
      "bm25_score": 0.65,
      "hybrid_score": 0.79,
      "score": 0.79,
      "image_type": null
    }
  ],
  "count": 5
}
```

### Health Check

#### GET /health

Returns service health status.

**Response:**
```json
{
  "status": "healthy"
}
```

### Metrics

#### GET /metrics

Returns Prometheus-format metrics (when observability enabled).

## Rate Limits

- **Default:** 100 requests/minute per API key
- **Burst:** 20 requests/second

## Error Responses

**401 Unauthorized:**
```json
{
  "detail": "Authentication required: Provide X-API-Key header or valid Frappe session"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Client Examples

### Python

```python
import httpx

response = httpx.post(
    "https://knowledge.bebang.ph/api/search",
    headers={"X-API-Key": "your-api-key"},
    json={"query": "payroll process", "top_k": 3}
)

results = response.json()
print(f"Found {results['count']} results")
for result in results['results']:
    print(f"- {result['title']}: {result['content'][:100]}")
```

### cURL

```bash
curl -X POST https://knowledge.bebang.ph/api/search \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "payroll process", "top_k": 3}'
```

### JavaScript

```javascript
const response = await fetch('https://knowledge.bebang.ph/api/search', {
  method: 'POST',
  headers: {
    'X-API-Key': 'your-api-key',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'payroll process',
    top_k: 3
  })
});

const data = await response.json();
console.log(`Found ${data.count} results`);
```
