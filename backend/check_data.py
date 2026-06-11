#!/usr/bin/env python
"""Vérifier les données dans Elasticsearch"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.elasticsearch_service import es_service
from app.config import settings

def check_data():
    print("\n" + "="*60)
    print("🔍 VÉRIFICATION DES DONNÉES DANS ELASTICSEARCH")
    print("="*60)
    
    # 1. Compter les débats
    count = es_service.es.count(index=settings.index_debats)
    print(f"\n📊 Total débats: {count['count']}")
    
    # 2. Voir un échantillon de débats
    print("\n📝 Échantillon de débats:")
    sample = es_service.es.search(index=settings.index_debats, size=3)
    for hit in sample['hits']['hits']:
        source = hit['_source']
        print(f"   - ID: {source.get('id_intervention')}")
        print(f"     Région: {source.get('region')}")
        print(f"     Parti: {source.get('parti')}")
        print(f"     Thème: {source.get('theme_principal')}")
        print()
    
    # 3. Vérifier les agrégations de régions
    print("\n📍 Agrégation par région:")
    region_body = {
        "size": 0,
        "aggs": {
            "by_region": {
                "terms": {"field": "region.keyword", "size": 20}
            }
        }
    }
    region_response = es_service.es.search(index=settings.index_debats, body=region_body)
    
    buckets = region_response["aggregations"]["by_region"]["buckets"]
    if buckets:
        for bucket in buckets:
            print(f"   - {bucket['key']}: {bucket['doc_count']} débats")
    else:
        print("   ⚠️ Aucune région trouvée!")
        print("   Vérifiez que le champ 'region' contient des valeurs")
    
    # 4. Vérifier les champs disponibles
    print("\n🏷️ Structure d'un document:")
    sample_doc = es_service.es.search(index=settings.index_debats, size=1)
    if sample_doc['hits']['hits']:
        source = sample_doc['hits']['hits'][0]['_source']
        print(f"   Champs disponibles: {list(source.keys())}")
        print(f"   Valeur de region: '{source.get('region')}'")
        print(f"   Type de region: {type(source.get('region'))}")

if __name__ == "__main__":
    check_data()