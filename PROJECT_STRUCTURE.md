# Project Structure

Structure complète du projet SmartReco.

```
smart-reco/
│
├── backend/                          # Backend FastAPI
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app et endpoints
│   │   ├── config.py                # Configuration (settings)
│   │   ├── schemas.py               # Pydantic models
│   │   ├── scoring_rules.py         # Rule engine
│   │   ├── recommender.py           # Recommendation logic
│   │   ├── utils.py                 # Utilities (CSV parsing, safe eval)
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_recommender.py  # Unit tests
│   ├── Dockerfile                   # Backend Docker image
│   ├── requirements.txt             # Python dependencies
│   └── .dockerignore
│
├── frontend/                        # Frontend React + TypeScript
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Overview.tsx         # Page principale (upload, KPIs)
│   │   │   ├── Recommendations.tsx # Liste des recommandations
│   │   │   └── ClientInsights.tsx   # Détails d'un client
│   │   ├── components/
│   │   │   ├── Navbar.tsx          # Navigation
│   │   │   ├── ScoreBadge.tsx      # Badge de priorité
│   │   │   ├── KpiCard.tsx         # Carte KPI
│   │   │   ├── DataTable.tsx       # Tableau de données
│   │   │   └── RulesEditor.tsx     # Éditeur de règles
│   │   ├── services/
│   │   │   └── api.ts              # Client API (axios)
│   │   ├── App.tsx                 # App principale
│   │   ├── main.tsx                # Point d'entrée
│   │   └── index.css               # Styles Tailwind
│   ├── Dockerfile                  # Frontend Docker image
│   ├── nginx.conf                  # Nginx config pour production
│   ├── package.json                # Node dependencies
│   ├── vite.config.ts              # Vite configuration
│   ├── tailwind.config.js          # TailwindCSS config
│   ├── tsconfig.json               # TypeScript config
│   └── .dockerignore
│
├── nginx/                           # Nginx reverse proxy
│   └── conf.d/
│       └── default.conf            # Configuration nginx
│
├── data/                            # Datasets
│   └── bank_sample.csv             # Sample dataset (50 rows)
│
├── scripts/                         # Scripts utilitaires
│   └── download_dataset.sh          # Télécharger dataset complet
│
├── logs/                            # Logs (créé automatiquement)
│   └── .gitkeep
│
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions CI
│
├── docker-compose.yml               # Docker Compose configuration
├── rules_config.yaml               # Configuration des règles métier
├── Makefile                        # Makefile avec commandes utiles
├── build.sh                        # Script de build
├── run.sh                          # Script de démarrage
├── stop.sh                         # Script d'arrêt
├── .gitignore                      # Git ignore
├── env.example                     # Exemple de variables d'environnement
├── README.md                       # Documentation principale
├── API_EXAMPLES.md                 # Exemples d'utilisation API
└── PROJECT_STRUCTURE.md            # Ce fichier
```

## Description des composants principaux

### Backend (`backend/app/`)

- **main.py**: Application FastAPI avec tous les endpoints
  - `/` - Health check
  - `/upload` - Upload CSV
  - `/score` - Score customers
  - `/recommendations` - Get recommendations
  - `/customer/{id}` - Customer details
  - `/rules` - Get/update rules
  - `/simulate_campaign` - Campaign simulation

- **scoring_rules.py**: Moteur d'évaluation des règles
  - Charge les règles depuis YAML
  - Évalue les conditions de manière sécurisée
  - Gère l'activation/désactivation des règles

- **recommender.py**: Logique de recommandation
  - Score les clients
  - Génère les recommandations
  - Simule les campagnes

- **utils.py**: Fonctions utilitaires
  - `safe_eval_condition()`: Évaluation sécurisée des conditions
  - `parse_csv_data()`: Parsing CSV
  - `normalize_column_name()`: Normalisation des noms de colonnes

### Frontend (`frontend/src/`)

- **pages/**: Pages principales de l'application
  - Overview: Upload, KPIs, graphiques, éditeur de règles
  - Recommendations: Liste triable/filtrable, export CSV, simulation
  - ClientInsights: Détails d'un client, règles déclenchées

- **components/**: Composants réutilisables
  - Navbar: Navigation
  - ScoreBadge: Badge coloré pour priorité
  - KpiCard: Carte KPI
  - DataTable: Tableau avec tri
  - RulesEditor: Éditeur de règles

- **services/api.ts**: Client API
  - Wrapper axios pour tous les endpoints
  - Gestion des erreurs
  - Intercepteurs pour API key

### Configuration

- **rules_config.yaml**: Définition des règles métier
  - Format YAML avec id, label, condition, points, description
  - Supporte conditions complexes (AND/OR)

- **docker-compose.yml**: Configuration Docker
  - Services: backend, frontend, nginx
  - Volumes pour données et logs
  - Réseau interne

## Flux de données

1. **Upload**: CSV → Backend (stockage en mémoire)
2. **Scoring**: Backend évalue chaque client avec les règles
3. **Recommendations**: Backend trie et filtre par score
4. **Frontend**: Affiche les résultats avec visualisations
5. **Rules Update**: Frontend → Backend (modifie règles)
6. **Simulation**: Backend calcule KPIs estimés

## Points d'extension

- **Base de données**: Remplacer stockage en mémoire par PostgreSQL/MySQL
- **Cache**: Ajouter Redis pour cache des scores
- **ML Integration**: Interface prête pour remplacer rules par modèle ML
- **Authentication**: Ajouter système d'authentification complet
- **Real-time**: WebSockets pour updates en temps réel






