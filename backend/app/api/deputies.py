from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.services.elasticsearch_service import es_service
from app.config import settings

router = APIRouter()


def build_partial_search_query(search: str, fields: list) -> dict:
    """
    Construit une requête Elasticsearch qui fonctionne dès le premier caractère :
    - prefix  sur chaque field (mot partiel depuis le début)
    - wildcard sur chaque field (mot partiel n'importe où)
    - match   sur chaque field (mot complet, meilleur score)
    Le tout combiné avec bool/should → OR → un seul champ suffit à matcher.
    """
    tokens = search.strip().lower().split()
    should_clauses = []

    for token in tokens:
        for field in fields:
            should_clauses.append({"prefix": {field: {"value": token, "boost": 2}}})
            should_clauses.append({"wildcard": {field: {"value": f"*{token}*", "boost": 1}}})
            should_clauses.append({"match": {field: {"query": token, "boost": 3}}})

    if len(tokens) > 1:
        should_clauses.append({
            "multi_match": {
                "query": search,
                "fields": [f"{f}^2" for f in fields],
                "type": "best_fields",
                "operator": "or",
                "boost": 4
            }
        })

    return {
        "bool": {
            "should": should_clauses,
            "minimum_should_match": 1
        }
    }


@router.get("/")
async def get_deputies(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=300),
    region: Optional[str] = None,
    parti: Optional[str] = None,
    search: Optional[str] = None
):
    """Get list of deputies with optional filters — recherche partielle dès le 1er caractère"""

    must_conditions = []

    if region:
        must_conditions.append({"term": {"region": region}})

    if parti:
        must_conditions.append({"term": {"parti_politique.keyword": parti}})

    if search and search.strip():
        must_conditions.append(
            build_partial_search_query(search, ["nom", "prenom", "parti_politique", "region", "district"])
        )

    if not must_conditions:
        must_conditions.append({"match_all": {}})

    body = {
        "query": {"bool": {"must": must_conditions}},
        "from": (page - 1) * size,
        "size": size,
        "sort": [{"_score": {"order": "desc"}}, {"nom.keyword": {"order": "asc"}}]
    }

    results = es_service.es.search(index=settings.index_deputes, body=body)

    return {
        "total": results["hits"]["total"]["value"],
        "page": page,
        "size": size,
        "deputies": [hit["_source"] for hit in results["hits"]["hits"]]
    }


@router.get("/stats/overview")
async def get_deputies_stats():
    """Get all regions and parties for filter dropdowns"""

    region_agg = {
        "size": 0,
        "aggs": {
            "by_region": {
                "terms": {"field": "region", "size": 100}
            }
        }
    }

    party_agg = {
        "size": 0,
        "aggs": {
            "by_party": {
                "terms": {"field": "parti_politique.keyword", "size": 100}
            }
        }
    }

    try:
        regions = es_service.es.search(index=settings.index_deputes, body=region_agg)
        parties = es_service.es.search(index=settings.index_deputes, body=party_agg)

        return {
            "total": es_service.es.count(index=settings.index_deputes)["count"],
            "by_region": [
                {"region": b["key"], "count": b["doc_count"]}
                for b in regions["aggregations"]["by_region"]["buckets"]
                if b["key"]
            ],
            "by_party": [
                {"party": b["key"], "count": b["doc_count"]}
                for b in parties["aggregations"]["by_party"]["buckets"]
                if b["key"]
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/interventions/by-name")
async def get_interventions_by_name(
    nom: str = Query(..., description="Nom complet du député"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    """Get all interventions of a deputy by their full name"""
    body = {
        "query": {
            "match_phrase": {
                "nom_depute": nom
            }
        },
        "from": (page - 1) * size,
        "size": size,
        "sort": [{"date_seance": {"order": "desc"}}]
    }
    try:
        results = es_service.es.search(index=settings.index_debats, body=body)
        total = results["hits"]["total"]["value"]
        hits  = results["hits"]["hits"]
        return {
            "total": total,
            "page": page,
            "size": size,
            "total_pages": (total + size - 1) // size if total > 0 else 0,
            "interventions": [h["_source"] for h in hits]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{deputy_id}")
async def get_deputy(deputy_id: str):
    """Get detailed information about a specific deputy"""
    try:
        result = es_service.es.get(index=settings.index_deputes, id=deputy_id)
        return result["_source"]
    except Exception:
        raise HTTPException(status_code=404, detail="Deputy not found")
