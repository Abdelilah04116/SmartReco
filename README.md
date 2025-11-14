# SmartReco - Customer Recommendation System

SmartReco est une application web complète pour la recommandation de clients basée sur des règles métier. Le système charge un dataset (Bank Marketing), calcule des scores de priorité en utilisant uniquement des règles métier (sans machine learning), et fournit une interface utilisateur complète pour visualiser, ajuster et expliquer les règles.

## 🎯 Fonctionnalités

- **Scoring basé sur des règles métier** : Aucun modèle ML, tout est rule-based
- **Interface web moderne** : React + TypeScript avec TailwindCSS
- **API REST complète** : FastAPI avec documentation OpenAPI
- **Éditeur de règles** : Interface pour modifier les règles en temps réel
- **Visualisations** : Graphiques et tableaux pour analyser les recommandations
- **Simulation de campagnes** : Estimation de KPIs basée sur les règles
- **Explicabilité** : Détail complet des règles déclenchées pour chaque client

## 🏗️ Architecture

```
smart-reco/
├── backend/          # FastAPI application
│   ├── app/
│   │   ├── main.py           # FastAPI endpoints
│   │   ├── config.py         # Configuration
│   │   ├── schemas.py        # Pydantic models
│   │   ├── scoring_rules.py  # Rule engine
│   │   ├── recommender.py    # Recommendation logic
│   │   └── utils.py          # Utilities
│   └── tests/                # Unit tests
├── frontend/         # React + TypeScript
│   └── src/
│       ├── pages/           # Page components
│       ├── components/      # Reusable components
│       └── services/        # API client
├── nginx/            # Reverse proxy config
├── data/             # Sample dataset
└── docker-compose.yml
```

## 🚀 Démarrage rapide

### Prérequis

- Docker et Docker Compose
- (Optionnel) Python 3.11+ et Node.js 18+ pour développement local

### Avec Docker (Recommandé)

1. **Cloner le repository**
```bash
git clone <repository-url>
cd smart-reco
```

2. **Configurer les variables d'environnement** (optionnel)
```bash
cp .env.example .env
# Éditer .env selon vos besoins
```

3. **Lancer l'application**
```bash
make build
make up
```

Ou avec docker-compose directement:
```bash
docker-compose up --build
```

4. **Accéder à l'application**
- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Développement local

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 📊 Utilisation

### 1. Uploader un dataset

- Accéder à la page Overview
- Cliquer sur "Choose CSV File" et sélectionner un fichier CSV
- Le format attendu correspond au dataset Bank Marketing (voir `data/bank_sample.csv`)

### 2. Scorer les clients

- Après l'upload, cliquer sur "Run Scoring"
- Les clients sont évalués selon les règles configurées dans `rules_config.yaml`

### 3. Consulter les recommandations

- Aller à la page "Recommendations"
- Ajuster le nombre de clients (Top N)
- Exporter en CSV si nécessaire
- Cliquer sur une ligne pour voir les détails d'un client

### 4. Modifier les règles

- Dans la page Overview, section "Business Rules Configuration"
- Cliquer sur "Edit" pour une règle
- Modifier les points, le threshold, ou activer/désactiver
- Sauvegarder (nécessite une clé API - voir configuration)

## 🔧 Configuration

### Variables d'environnement

Créer un fichier `.env` à la racine:

```env
API_KEY=demo-api-key-change-in-production
DEBUG=false
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Règles métier

Les règles sont définies dans `rules_config.yaml`. Format:

```yaml
rules:
  - id: rule_1
    label: Prime Age Range
    condition: age >= 25 and age <= 45
    points: 20.0
    description: "Description de la règle"
    enabled: true
    threshold: null
```

**Opérateurs supportés:**
- Comparaisons: `==`, `!=`, `>`, `>=`, `<`, `<=`
- Logiques: `and`, `or`
- Collections: `in`, `not in`
- Regex: (via expressions)

## 📡 API Endpoints

### Health & Status
- `GET /` - Health check
- `GET /health` - Detailed health status

### Data Management
- `POST /upload` - Upload CSV dataset
- `POST /score` - Score customers (JSON body)
- `POST /score/upload` - Score uploaded dataset

### Recommendations
- `GET /recommendations?top_n=50&priority_label=high` - Get top N recommendations
- `GET /customer/{customer_id}` - Get customer details

### Rules Management
- `GET /rules` - Get all rules
- `PUT /rules/{rule_id}` - Update a rule (requires API key header: `X-API-KEY`)

### Campaign Simulation
- `POST /simulate_campaign` - Simulate campaign and get KPIs

### Exemple de requête

```bash
# Upload dataset
curl -X POST http://localhost:8000/upload \
  -F "file=@data/bank_sample.csv"

# Score customers
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"age": 35, "balance": 6000, "poutcome": "success", "job": "management"}
    ]
  }'

# Get recommendations
curl http://localhost:8000/recommendations?top_n=10
```

## 🧪 Tests

```bash
# Backend tests
cd backend
pytest app/tests/ -v

# Ou avec Docker
docker-compose exec backend pytest app/tests/ -v
```

## 📁 Structure des fichiers

### Backend

- `app/main.py` - FastAPI application et endpoints
- `app/scoring_rules.py` - Moteur d'évaluation des règles
- `app/recommender.py` - Logique de recommandation
- `app/utils.py` - Fonctions utilitaires (parsing CSV, évaluation sécurisée)
- `app/schemas.py` - Modèles Pydantic
- `app/config.py` - Configuration

### Frontend

- `src/pages/Overview.tsx` - Page principale avec KPIs et upload
- `src/pages/Recommendations.tsx` - Liste des recommandations
- `src/pages/ClientInsights.tsx` - Détails d'un client
- `src/components/RulesEditor.tsx` - Éditeur de règles
- `src/services/api.ts` - Client API

## 🔒 Sécurité

- Les endpoints de modification de règles sont protégés par une clé API (`X-API-KEY` header)
- L'évaluation des règles utilise un parser AST sécurisé (pas d'`eval()` direct)
- CORS configuré pour les origines autorisées
- Limite de taille d'upload: 50MB

## 🐳 Docker

### Services

- **backend**: FastAPI sur le port 8000
- **frontend**: Build React servi par nginx
- **nginx**: Reverse proxy sur le port 80

### Commandes utiles

```bash
# Voir les logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Redémarrer un service
docker-compose restart backend

# Rebuild après modification
docker-compose up --build
```

## 📈 Règles métier par défaut

Le système inclut 10 règles pré-configurées:

1. **Prime Age Range** (25-45 ans) - 20 points
2. **High Balance** (>$5000) - 25 points
3. **Previous Success** - 30 points
4. **Management Job** - 15 points
5. **Tertiary Education** - 10 points
6. **Married Status** - 8 points
7. **Previous Campaign Contact** - 12 points
8. **Recent Contact Days** (<30 jours) - 18 points
9. **Multiple Campaign Contacts** (>2) - -5 points (pénalité)
10. **Very High Balance** (>$20,000) - 35 points

Les seuils de priorité:
- **High**: score >= 50
- **Medium**: score >= 25
- **Low**: score < 25

## 🛠️ Développement

### Ajouter une nouvelle règle

1. Éditer `rules_config.yaml`
2. Ajouter une nouvelle entrée dans `rules`
3. Redémarrer le backend (ou recharger via API)

### Modifier le frontend

Les modifications dans `frontend/src` sont prises en compte après rebuild:
```bash
docker-compose up --build frontend
```

## 📝 Notes

- Le dataset est stocké en mémoire (pour la démo). En production, utiliser une base de données.
- Les règles sont évaluées de manière séquentielle et additive (somme des points).
- L'explicabilité est garantie: chaque score inclut la liste des règles déclenchées.

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est fourni à des fins éducatives et de démonstration.

## 🆘 Support

Pour toute question ou problème:
1. Vérifier les logs: `docker-compose logs`
2. Vérifier la santé de l'API: `curl http://localhost:8000/health`
3. Consulter la documentation API: http://localhost:8000/docs

---

**SmartReco** - Recommandation intelligente basée sur des règles métier




