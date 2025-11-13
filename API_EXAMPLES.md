# API Examples

Exemples d'utilisation de l'API SmartReco avec curl.

## Prérequis

L'API doit être accessible sur `http://localhost:8000` (ou l'URL configurée).

## Health Check

```bash
# Health check simple
curl http://localhost:8000/

# Health check détaillé
curl http://localhost:8000/health
```

## Upload Dataset

```bash
# Upload un fichier CSV
curl -X POST http://localhost:8000/upload \
  -F "file=@data/bank_sample.csv"
```

## Score Customers

### Score avec données JSON

```bash
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {
        "age": 35,
        "job": "management",
        "marital": "married",
        "education": "tertiary",
        "balance": 6000,
        "previous": 1,
        "poutcome": "success"
      },
      {
        "age": 20,
        "job": "student",
        "marital": "single",
        "education": "secondary",
        "balance": 100,
        "previous": 0,
        "poutcome": "unknown"
      }
    ]
  }'
```

### Score le dataset uploadé

```bash
curl -X POST http://localhost:8000/score/upload
```

## Get Recommendations

```bash
# Top 50 recommandations
curl http://localhost:8000/recommendations?top_n=50

# Top 10 avec filtre high priority
curl http://localhost:8000/recommendations?top_n=10&priority_label=high

# Avec score minimum
curl http://localhost:8000/recommendations?top_n=20&min_score=30
```

## Get Customer Detail

```bash
# Remplacer {customer_id} par un ID réel
curl http://localhost:8000/customer/customer_1
```

## Get Rules

```bash
# Liste toutes les règles
curl http://localhost:8000/rules
```

## Update Rule

```bash
# Mettre à jour une règle (nécessite API key)
curl -X PUT http://localhost:8000/rules/rule_1 \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: demo-api-key-change-in-production" \
  -d '{
    "enabled": true,
    "points": 25.0
  }'
```

## Simulate Campaign

```bash
# Simuler une campagne avec top 50
curl -X POST http://localhost:8000/simulate_campaign \
  -H "Content-Type: application/json" \
  -d '{
    "top_n": 50
  }'
```

## Exemple de réponse complète

### Score Response

```json
{
  "results": [
    {
      "customer_id": "customer_0",
      "priority_score": 75.0,
      "priority_label": "high",
      "rules_fired": [
        {
          "rule_id": "rule_1",
          "rule_label": "Prime Age Range",
          "points": 20.0,
          "reason": "Prime Age Range: Customers in prime age range (25-45) are more likely to convert"
        },
        {
          "rule_id": "rule_2",
          "rule_label": "High Balance",
          "points": 25.0,
          "reason": "High Balance: Customers with high balance (>$5000) have better conversion potential"
        },
        {
          "rule_id": "rule_3",
          "rule_label": "Previous Success",
          "points": 30.0,
          "reason": "Previous Success: Customers with previous successful campaign outcome"
        }
      ],
      "explain": {
        "total_score": 75.0,
        "rules_count": 3,
        "score_breakdown": {
          "rule_1": 20.0,
          "rule_2": 25.0,
          "rule_3": 30.0
        }
      },
      "raw_data": {
        "age": 35,
        "job": "management",
        "balance": 6000,
        "poutcome": "success"
      }
    }
  ],
  "total_scored": 1,
  "summary": {
    "high": 1,
    "medium": 0,
    "low": 0,
    "total": 1
  }
}
```

### Campaign Simulation Response

```json
{
  "estimated_conversion_rate": 0.15,
  "estimated_revenue": 7500.0,
  "total_customers": 50,
  "high_priority_count": 20,
  "medium_priority_count": 20,
  "low_priority_count": 10,
  "kpis": {
    "average_score": 45.5,
    "high_priority_rate": 0.4,
    "estimated_conversions": 7.5,
    "cost_per_customer": 5.0,
    "roi": 29.0
  }
}
```

## Workflow complet

```bash
# 1. Vérifier la santé de l'API
curl http://localhost:8000/health

# 2. Uploader le dataset
curl -X POST http://localhost:8000/upload -F "file=@data/bank_sample.csv"

# 3. Scorer les clients
curl -X POST http://localhost:8000/score/upload

# 4. Obtenir les recommandations
curl http://localhost:8000/recommendations?top_n=10

# 5. Simuler une campagne
curl -X POST http://localhost:8000/simulate_campaign \
  -H "Content-Type: application/json" \
  -d '{"top_n": 10}'
```


