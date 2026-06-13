----------------------
Mémoire Parlementaire
----------------------

Mémoire Parlementaire est une plateforme de recherche et d'exploration de débats parlementaires permettant d'indexer, rechercher et analyser des archives législatives à l'aide d'Elasticsearch. L'application centralise les interventions parlementaires, les séances, les députés et les textes législatifs afin de faciliter l'accès à l'information et l'analyse des activités parlementaires.

## Fonctionnalités
------------------
. Recherche full-text rapide sur les débats parlementaires  
. Indexation des archives législatives avec Elasticsearch  
. Consultation des séances parlementaires  
. Recherche et exploration des interventions des députés  
. Accès aux informations des textes législatifs  
. Filtres avancés sur les débats et les séances  
. Statistiques globales sur les activités parlementaires  
. API REST complète pour l'accès aux données  
. Importation automatisée des données CSV  
. Mise à jour et réindexation des archives  

## Technologies utilisées
--------------------------  
. Backend:  
Python, 
FastAPI, 
Uvicorn, 
Moteur de recherche, 
Elasticsearch 8.11  
. Traitement de données:  
Pandas, 
NumPy  
. Validation et Configuration:  
Pydantic, 
Pydantic Settings, 
Python Dotenv, 
. Sécurité:  
Cryptography  
. Déploiement:  
Docker, 
Elasticsearch Docker Container  

## Cas d'usage
--------------
. Citoyen  
Rechercher rapidement les interventions parlementaires sur un sujet précis et suivre les débats publics.  
. Journaliste  
Analyser les prises de position des députés et retrouver des déclarations spécifiques dans les archives.  
. Chercheur  
Étudier l'évolution des débats législatifs, des thèmes politiques et des tendances parlementaires.  
. Étudiant  
Explorer les processus législatifs et consulter les discussions parlementaires pour des travaux académiques.  
. Institution publique  
Centraliser et rendre accessibles les archives parlementaires via une plateforme de recherche moderne.  

## Résultats
-------------  
. Recherche instantanée sur de grands volumes de documents  
. Centralisation des archives parlementaires  
. Navigation simplifiée entre députés, séances et textes législatifs  
. API REST exploitable par des applications tierces  

## Installation
---------------  
cd "Mémoire Parlementaire"  
python -m venv venv  
source venv/bin/activate  
pip install -r requirements.txt  
docker run -d \  
--name elasticsearch \  
-p 9200:9200 \  
-e "discovery.type=single-node" \  
-e "xpack.security.enabled=false" \  
docker.elastic.co/elasticsearch/elasticsearch:8.11.0  
python import_data.py  
uvicorn backend.app.main:app --reload
