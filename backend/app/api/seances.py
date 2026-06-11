from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.services.elasticsearch_service import es_service
from app.config import settings

router = APIRouter()


def build_partial_search_query(search: str, fields: list) -> dict:
    """
    Requête Elasticsearch partielle dès le 1er caractère :
    préfixe + wildcard + match pour chaque token et chaque field.
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
async def get_seances(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    type_seance: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """Get list of parliamentary sessions — recherche partielle dès le 1er caractère"""

    must_conditions = []

    if search and search.strip():
        must_conditions.append(
            build_partial_search_query(search, ["titre", "type_seance", "session", "lieu"])
        )

    if type_seance:
        must_conditions.append({"term": {"type_seance": type_seance}})

    if status:
        must_conditions.append({"term": {"status": status}})

    if date_from or date_to:
        date_range = {}
        if date_from:
            date_range["gte"] = date_from
        if date_to:
            date_range["lte"] = date_to
        must_conditions.append({"range": {"date": date_range}})

    if not must_conditions:
        must_conditions.append({"match_all": {}})

    body = {
        "query": {"bool": {"must": must_conditions}},
        "from": (page - 1) * size,
        "size": size,
        "sort": [{"_score": {"order": "desc"}}, {"date": {"order": "desc"}}]
    }

    results = es_service.es.search(index=settings.index_seances, body=body)

    return {
        "total": results["hits"]["total"]["value"],
        "page": page,
        "size": size,
        "seances": [hit["_source"] for hit in results["hits"]["hits"]]
    }


# ⚠ IMPORTANT : /stats/types doit être AVANT /{seance_id}
@router.get("/stats/types")
async def get_seance_types():
    """Get all distinct type_seance values for the filter dropdown"""
    body = {
        "size": 0,
        "aggs": {
            "by_type": {
                "terms": {"field": "type_seance", "size": 50}
            }
        }
    }
    try:
        res = es_service.es.search(index=settings.index_seances, body=body)
        return {
            "types": [
                {"type": b["key"], "count": b["doc_count"]}
                for b in res["aggregations"]["by_type"]["buckets"]
                if b["key"]
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{seance_id}/debates")
async def get_seance_debates(
    seance_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100)
):
    """Get all debates from a specific session"""
    body = {
        "query": {"term": {"id_seance": seance_id}},
        "from": (page - 1) * size,
        "size": size
    }
    results = es_service.es.search(index=settings.index_debats, body=body)
    return {
        "total": results["hits"]["total"]["value"],
        "page": page,
        "size": size,
        "debates": [hit["_source"] for hit in results["hits"]["hits"]]
    }


@router.get("/{seance_id}")
async def get_seance(seance_id: str):
    """Get detailed information about a specific session"""
    try:
        result = es_service.es.get(index=settings.index_seances, id=seance_id)
        return result["_source"]
    except Exception:
        raise HTTPException(status_code=404, detail="Session not found")
