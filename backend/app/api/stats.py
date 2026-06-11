from fastapi import APIRouter
from app.services.elasticsearch_service import es_service
from app.config import settings

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    
    stats = es_service.get_statistics()
    
    # Get debates by region - VERSION CORRIGÉE
    try:
        region_body = {
            "size": 0,
            "aggs": {
                "by_region": {
                    "terms": {
                        "field": "region.keyword",  # CHANGÉ: utiliser .keyword
                        "size": 20
                    }
                }
            }
        }
        region_response = es_service.es.search(index=settings.index_debats, body=region_body)
        
        regions = []
        for bucket in region_response["aggregations"]["by_region"]["buckets"]:
            if bucket["key"] and bucket["doc_count"] > 0:
                regions.append({
                    "region": bucket["key"], 
                    "count": bucket["doc_count"]
                })
        stats["debates_by_region"] = regions
        
        # Afficher dans les logs pour déboguer
        print(f"Régions trouvées: {len(regions)}")
        for r in regions[:5]:
            print(f"  {r['region']}: {r['count']}")
            
    except Exception as e:
        print(f"Erreur région: {e}")
        stats["debates_by_region"] = []
    
    # Get debates by party - VERSION CORRIGÉE
    try:
        party_body = {
            "size": 0,
            "aggs": {
                "by_party": {
                    "terms": {
                        "field": "parti.keyword",  # CHANGÉ: utiliser .keyword
                        "size": 20
                    }
                }
            }
        }
        party_response = es_service.es.search(index=settings.index_debats, body=party_body)
        
        parties = []
        for bucket in party_response["aggregations"]["by_party"]["buckets"]:
            if bucket["key"] and bucket["doc_count"] > 0:
                parties.append({
                    "party": bucket["key"], 
                    "count": bucket["doc_count"]
                })
        stats["debates_by_party"] = parties
        
    except Exception as e:
        print(f"Erreur parti: {e}")
        stats["debates_by_party"] = []
    
    # Get timeline - VERSION CORRIGÉE
    try:
        timeline_body = {
            "size": 0,
            "aggs": {
                "timeline": {
                    "date_histogram": {
                        "field": "date_seance",
                        "calendar_interval": "month",
                        "format": "yyyy-MM",
                        "min_doc_count": 0
                    }
                }
            }
        }
        timeline_response = es_service.es.search(index=settings.index_debats, body=timeline_body)
        
        timeline = []
        for bucket in timeline_response["aggregations"]["timeline"]["buckets"]:
            if bucket["key_as_string"]:
                timeline.append({
                    "date": bucket["key_as_string"], 
                    "count": bucket["doc_count"]
                })
        stats["timeline"] = timeline
        
    except Exception as e:
        print(f"Erreur timeline: {e}")
        stats["timeline"] = []
        
    
    return stats