from typing import Optional

from fastapi import APIRouter, Query

from app.config import settings
from app.services.elasticsearch_service import es_service

router = APIRouter()


def build_partial_debats_query(query: str) -> dict:
    """
    Requête Elasticsearch pour les débats :
    supporte la recherche partielle dès le 1er caractère.
    Combine prefix + wildcard + match_phrase + multi_match.
    """
    tokens = query.strip().lower().split()
    should_clauses = []

    text_fields = ["contenu_texte", "objet_debat", "theme_principal", "nom_depute", "mots_cles"]

    for token in tokens:
        for field in text_fields:
            # Préfixe — priorité haute (ex: "riz" → "riz de Madagascar")
            should_clauses.append({"prefix": {field: {"value": token, "boost": 3}}})
            # Wildcard — trouve le token n'importe où dans le mot
            should_clauses.append({"wildcard": {field: {"value": f"*{token}*", "boost": 1}}})
            # Match exact — meilleur score si le mot est complet
            should_clauses.append({"match": {field: {"query": token, "boost": 4}}})

    # Phrase complète (si l'utilisateur a tapé plusieurs mots)
    if len(tokens) > 1:
        for field in ["contenu_texte", "objet_debat", "theme_principal"]:
            should_clauses.append({
                "match_phrase": {field: {"query": query, "boost": 6}}
            })
        should_clauses.append({
            "multi_match": {
                "query": query,
                "fields": ["contenu_texte^3", "objet_debat^2", "theme_principal^2", "nom_depute"],
                "type": "best_fields",
                "operator": "or",
                "boost": 5
            }
        })

    return {
        "bool": {
            "should": should_clauses,
            "minimum_should_match": 1
        }
    }


@router.get("/")
async def search_debates(
    q: str = Query(..., min_length=1, description="Search query"),
    region: Optional[str] = Query(None, description="Filter by region"),
    parti: Optional[str] = Query(None, description="Filter by political party"),
    theme: Optional[str] = Query(None, description="Filter by theme"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Results per page")
):
    must_conditions = []

    if q and q.strip():
        must_conditions.append(build_partial_debats_query(q))
    else:
        must_conditions.append({"match_all": {}})

    filters = {}
    if region:
        filters["region"] = region
        must_conditions.append({"term": {"region.keyword": region}})

    if parti:
        filters["parti"] = parti
        must_conditions.append({"term": {"parti.keyword": parti}})

    if theme:
        filters["theme"] = theme
        must_conditions.append({"term": {"theme_principal.keyword": theme}})

    if date_from or date_to:
        date_range = {}
        if date_from:
            date_range["gte"] = date_from
        if date_to:
            date_range["lte"] = date_to
        must_conditions.append({"range": {"date_seance": date_range}})

    search_body = {
        "query": {"bool": {"must": must_conditions}},
        "highlight": {
            "fields": {
                "contenu_texte": {
                    "number_of_fragments": 3,
                    "fragment_size": 200,
                    "pre_tags": ["<mark>"],
                    "post_tags": ["</mark>"]
                },
                "objet_debat": {
                    "number_of_fragments": 1,
                    "fragment_size": 150,
                    "pre_tags": ["<mark>"],
                    "post_tags": ["</mark>"]
                }
            }
        },
        "from": (page - 1) * size,
        "size": size,
        "sort": [{"_score": {"order": "desc"}}]
    }

    try:
        response = es_service.es.search(index=settings.index_debats, body=search_body)
        total = response["hits"]["total"]["value"]
        total_pages = (total + size - 1) // size if total > 0 else 0

        return {
            "success": True,
            "query": q,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": total_pages,
            "results": [
                {
                    "id": hit["_id"],
                    "score": hit.get("_score", 0),
                    "highlights": hit.get("highlight", {}),
                    "source": hit["_source"]
                }
                for hit in response["hits"]["hits"]
            ]
        }
    except Exception as e:
        return {"success": False, "query": q, "total": 0, "page": page,
                "size": size, "total_pages": 0, "results": []}


@router.get("/filters")
async def get_search_filters():
    body = {
        "size": 0,
        "aggs": {
            "regions": {"terms": {"field": "region.keyword", "size": 500}},
            "partis":  {"terms": {"field": "parti.keyword",  "size": 500}},
            "themes":  {"terms": {"field": "theme_principal.keyword", "size": 500}}
        }
    }

    response = es_service.es.search(index=settings.index_debats, body=body)

    return {
        "regions": sorted([
            bucket["key"]
            for bucket in response["aggregations"]["regions"]["buckets"]
            if bucket["key"]
        ]),
        "partis": sorted([
            bucket["key"]
            for bucket in response["aggregations"]["partis"]["buckets"]
            if bucket["key"]
        ]),
        "themes": sorted([
            bucket["key"]
            for bucket in response["aggregations"]["themes"]["buckets"]
            if bucket["key"]
        ])
    }


@router.get("/advanced")
async def advanced_search(
    q: Optional[str] = None,
    nom_depute: Optional[str] = None,
    region: Optional[str] = None,
    parti: Optional[str] = None,
    theme_principal: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    type_intervention: Optional[str] = None,
    page: int = 1,
    size: int = 20
):
    must_conditions = []

    if q and q.strip():
        must_conditions.append(build_partial_debats_query(q))

    if nom_depute:
        tokens = nom_depute.strip().lower().split()
        name_should = []
        for token in tokens:
            name_should.append({"prefix": {"nom_depute": {"value": token, "boost": 2}}})
            name_should.append({"wildcard": {"nom_depute": {"value": f"*{token}*", "boost": 1}}})
            name_should.append({"match": {"nom_depute": {"query": token, "boost": 3}}})
        must_conditions.append({"bool": {"should": name_should, "minimum_should_match": 1}})

    if region:
        must_conditions.append({"term": {"region.keyword": region}})

    if parti:
        must_conditions.append({"term": {"parti.keyword": parti}})

    if theme_principal:
        must_conditions.append({"term": {"theme_principal.keyword": theme_principal}})

    if type_intervention:
        must_conditions.append({"term": {"type_intervention.keyword": type_intervention}})

    if date_from or date_to:
        date_range = {}
        if date_from:
            date_range["gte"] = date_from
        if date_to:
            date_range["lte"] = date_to
        must_conditions.append({"range": {"date_seance": date_range}})

    if not must_conditions:
        must_conditions.append({"match_all": {}})

    body = {
        "query": {"bool": {"must": must_conditions}},
        "from": (page - 1) * size,
        "size": size,
        "sort": [{"_score": {"order": "desc"}}]
    }

    results = es_service.es.search(index=settings.index_debats, body=body)
    total = results["hits"]["total"]["value"]

    return {
        "total": total,
        "page": page,
        "size": size,
        "total_pages": (total + size - 1) // size if total > 0 else 0,
        "results": [
            {"id": hit["_id"], "source": hit["_source"]}
            for hit in results["hits"]["hits"]
        ]
    }
