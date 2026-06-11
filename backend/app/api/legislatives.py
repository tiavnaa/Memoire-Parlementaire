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
async def get_legislative_texts(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    type_texte: Optional[str] = None,
    origine: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None
):
    """Get list of legislative texts — recherche partielle dès le 1er caractère"""

    must_conditions = []

    if type_texte:
        must_conditions.append({"term": {"type_texte": type_texte}})

    if origine:
        must_conditions.append({"term": {"origine": origine}})

    if status:
        must_conditions.append({"term": {"status": status}})

    if search and search.strip():
        must_conditions.append(
            build_partial_search_query(search, ["intitule", "numero", "resume", "auteur", "type_texte"])
        )

    if not must_conditions:
        must_conditions.append({"match_all": {}})

    body = {
        "query": {"bool": {"must": must_conditions}},
        "from": (page - 1) * size,
        "size": size,
        "sort": [{"_score": {"order": "desc"}}, {"date_depot": {"order": "desc"}}]
    }

    results = es_service.es.search(index=settings.index_legislatifs, body=body)

    return {
        "total": results["hits"]["total"]["value"],
        "page": page,
        "size": size,
        "texts": [hit["_source"] for hit in results["hits"]["hits"]]
    }


@router.get("/stats/filters")
async def get_legislative_filters():
    """Get all distinct type_texte and status values for filter dropdowns"""
    body = {
        "size": 0,
        "aggs": {
            "by_type":   {"terms": {"field": "type_texte", "size": 50}},
            "by_status": {"terms": {"field": "status",     "size": 50}}
        }
    }
    try:
        res = es_service.es.search(index=settings.index_legislatifs, body=body)
        return {
            "types": [
                {"type": b["key"], "count": b["doc_count"]}
                for b in res["aggregations"]["by_type"]["buckets"]
                if b["key"]
            ],
            "statuses": [
                {"status": b["key"], "count": b["doc_count"]}
                for b in res["aggregations"]["by_status"]["buckets"]
                if b["key"]
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{text_id}")
async def get_legislative_text(text_id: str):
    """Get detailed information about a specific legislative text"""
    try:
        result = es_service.es.get(index=settings.index_legislatifs, id=text_id)
        return result["_source"]
    except Exception:
        raise HTTPException(status_code=404, detail="Text not found")
