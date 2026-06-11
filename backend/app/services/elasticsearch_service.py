from elasticsearch import Elasticsearch, ApiError
from typing import List, Dict, Optional, Any
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def _build_partial_query(query: str, text_fields: list, keyword_fields: list = None) -> dict:
    """
    Requête universelle supportant la recherche partielle dès le 1er caractère.
    - text_fields   : champs analysés (type text)  → match + match_phrase
    - keyword_fields: champs non-analysés (type keyword) → prefix + wildcard
    Si keyword_fields est None, on utilise text_fields pour tous les types de clauses.
    """
    tokens = query.strip().lower().split()
    kw_fields = keyword_fields if keyword_fields is not None else text_fields
    should_clauses = []

    for token in tokens:
        # Clauses sur champs keyword (prefix/wildcard fonctionnent bien)
        for field in kw_fields:
            should_clauses.append({"prefix":   {field: {"value": token, "boost": 2}}})
            should_clauses.append({"wildcard": {field: {"value": f"*{token}*", "boost": 1}}})

        # Clauses sur champs texte (match analysé)
        for field in text_fields:
            should_clauses.append({"match": {field: {"query": token, "boost": 3}}})

    # Phrase complète si plusieurs tokens
    if len(tokens) > 1:
        for field in text_fields:
            should_clauses.append({"match_phrase": {field: {"query": query, "boost": 5}}})
        should_clauses.append({
            "multi_match": {
                "query": query,
                "fields": [f"{f}^2" for f in text_fields],
                "type": "best_fields",
                "operator": "or",
                "boost": 4
            }
        })

    return {"bool": {"should": should_clauses, "minimum_should_match": 1}}


class ElasticsearchService:
    def __init__(self):
        self.es = None
        self.connect()

    def connect(self):
        """Connect to Elasticsearch Cloud"""
        try:
            if settings.elastic_cloud_id:
                if settings.elasticsearch_api_key:
                    self.es = Elasticsearch(
                        cloud_id=settings.elastic_cloud_id,
                        api_key=settings.elasticsearch_api_key
                    )
                else:
                    self.es = Elasticsearch(
                        cloud_id=settings.elastic_cloud_id,
                        basic_auth=(settings.elasticsearch_username, settings.elasticsearch_password)
                    )
            elif settings.elasticsearch_url:
                if settings.elasticsearch_api_key:
                    self.es = Elasticsearch(
                        settings.elasticsearch_url,
                        api_key=settings.elasticsearch_api_key
                    )
                else:
                    self.es = Elasticsearch(
                        settings.elasticsearch_url,
                        basic_auth=(settings.elasticsearch_username, settings.elasticsearch_password)
                    )
            else:
                raise Exception("No Elasticsearch configuration found.")

            if self.es.ping():
                info = self.es.info()
                logger.info(f"Connected to Elasticsearch version: {info.get('version', {}).get('number')}")
            else:
                logger.error("Failed to connect to Elasticsearch")
        except Exception as e:
            logger.error(f"Elasticsearch connection error: {e}")
            raise

    def create_indices(self):
        """Create all indices with optimized mappings for partial search"""

        # Analyzer français + custom analyzer pour recherche partielle (edge_ngram)
        common_settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "french_analyzer": {
                        "type": "french",
                        "stopwords": "_french_"
                    },
                    # Edge n-gram pour la saisie partielle dès le 1er caractère
                    "autocomplete_analyzer": {
                        "type": "custom",
                        "tokenizer": "autocomplete_tokenizer",
                        "filter": ["lowercase"]
                    },
                    "autocomplete_search_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase"]
                    }
                },
                "tokenizer": {
                    "autocomplete_tokenizer": {
                        "type": "edge_ngram",
                        "min_gram": 1,
                        "max_gram": 20,
                        "token_chars": ["letter", "digit"]
                    }
                }
            }
        }

        debats_mapping = {
            "settings": common_settings,
            "mappings": {
                "properties": {
                    "id_intervention":    {"type": "keyword"},
                    "id_seance":          {"type": "keyword"},
                    "date_seance":        {"type": "date", "format": "yyyy-MM-dd"},
                    "id_depute":          {"type": "keyword"},
                    "nom_depute": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer",
                        "search_analyzer": "autocomplete_search_analyzer",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "parti": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer",
                        "search_analyzer": "autocomplete_search_analyzer",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "groupe":   {"type": "keyword"},
                    "region": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer",
                        "search_analyzer": "autocomplete_search_analyzer",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "district": {"type": "keyword"},
                    "type_intervention": {"type": "keyword"},
                    "style":             {"type": "keyword"},
                    "contenu_texte": {
                        "type": "text",
                        "analyzer": "french_analyzer",
                        "term_vector": "with_positions_offsets"
                    },
                    "objet_debat": {
                        "type": "text",
                        "analyzer": "french_analyzer",
                        "fields": {"autocomplete": {
                            "type": "text",
                            "analyzer": "autocomplete_analyzer",
                            "search_analyzer": "autocomplete_search_analyzer"
                        }}
                    },
                    "theme_principal": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer",
                        "search_analyzer": "autocomplete_search_analyzer",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "mots_cles": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer",
                        "search_analyzer": "autocomplete_search_analyzer"
                    }
                }
            }
        }

        deputes_mapping = {
            "settings": common_settings,
            "mappings": {
                "properties": {
                    "numero": {"type": "keyword"},
                    "nom": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer",
                        "search_analyzer": "autocomplete_search_analyzer",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "prenom": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer",
                        "search_analyzer": "autocomplete_search_analyzer"
                    },
                    "genre":    {"type": "keyword"},
                    "district": {"type": "keyword"},
                    "region":   {"type": "keyword"},
                    "parti_politique": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer",
                        "search_analyzer": "autocomplete_search_analyzer",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "groupe_parlementaire": {"type": "keyword"},
                    "status":    {"type": "keyword"},
                    "photo_url": {"type": "keyword", "index": False}
                }
            }
        }

        seances_mapping = {
            "settings": common_settings,
            "mappings": {
                "properties": {
                    "id":    {"type": "keyword"},
                    "titre": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer",
                        "search_analyzer": "autocomplete_search_analyzer"
                    },
                    "date":       {"type": "date", "format": "yyyy-MM-dd"},
                    "heure":      {"type": "keyword"},
                    "type_seance":{"type": "keyword"},
                    "lieu":       {"type": "keyword"},
                    "status":     {"type": "keyword"},
                    "session": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer",
                        "search_analyzer": "autocomplete_search_analyzer",
                        "fields": {"keyword": {"type": "keyword"}}
                    }
                }
            }
        }

        legislatifs_mapping = {
            "settings": common_settings,
            "mappings": {
                "properties": {
                    "numero": {"type": "keyword"},
                    "intitule": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer",
                        "search_analyzer": "autocomplete_search_analyzer"
                    },
                    "type_texte": {"type": "keyword"},
                    "origine":    {"type": "keyword"},
                    "date_depot": {"type": "date"},
                    "status":     {"type": "keyword"},
                    "auteur": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer",
                        "search_analyzer": "autocomplete_search_analyzer"
                    },
                    "resume": {
                        "type": "text",
                        "analyzer": "french_analyzer"
                    }
                }
            }
        }

        indices = [
            (settings.index_debats,      debats_mapping),
            (settings.index_deputes,     deputes_mapping),
            (settings.index_seances,     seances_mapping),
            (settings.index_legislatifs, legislatifs_mapping)
        ]

        for index_name, mapping in indices:
            if not self.es.indices.exists(index=index_name):
                self.es.indices.create(index=index_name, body=mapping)
                logger.info(f"Created index: {index_name}")
            else:
                logger.info(f"Index already exists: {index_name}")

    def search_debats(self, query: str, filters: Optional[Dict] = None,
                     date_from: Optional[str] = None, date_to: Optional[str] = None,
                     page: int = 1, size: int = 20) -> Dict:
        """Search debates with partial search support and highlighting"""
        from_offset = (page - 1) * size
        must_conditions = []

        if query and query.strip():
            must_conditions.append(
                _build_partial_query(
                    query,
                    text_fields=["contenu_texte", "objet_debat", "theme_principal", "nom_depute", "mots_cles"],
                    keyword_fields=["nom_depute", "theme_principal", "mots_cles"]
                )
            )
        else:
            must_conditions.append({"match_all": {}})

        if filters:
            if filters.get("region"):
                must_conditions.append({"term": {"region.keyword": filters["region"]}})
            if filters.get("parti"):
                must_conditions.append({"term": {"parti.keyword": filters["parti"]}})
            if filters.get("theme"):
                must_conditions.append({"term": {"theme_principal.keyword": filters["theme"]}})

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
                    }
                }
            },
            "from": from_offset,
            "size": size,
            "sort": [{"_score": {"order": "desc"}}]
        }

        try:
            response = self.es.search(index=settings.index_debats, body=search_body)
            return {
                "total": response["hits"]["total"]["value"],
                "hits": response["hits"]["hits"],
                "aggregations": response.get("aggregations", {})
            }
        except ApiError as e:
            logger.error(f"Search error: {e}")
            return {"total": 0, "hits": [], "aggregations": {}}

    def get_statistics(self) -> Dict:
        """Get global statistics"""
        stats = {}

        for index_name, key in [
            (settings.index_debats,      "total_debates"),
            (settings.index_deputes,     "total_deputies"),
            (settings.index_seances,     "total_sessions"),
            (settings.index_legislatifs, "total_laws")
        ]:
            try:
                count = self.es.count(index=index_name)
                stats[key] = count["count"]
            except:
                stats[key] = 0

        try:
            active_body = {
                "size": 0,
                "aggs": {"top_deputies": {"terms": {"field": "nom_depute.keyword", "size": 10}}}
            }
            active_response = self.es.search(index=settings.index_debats, body=active_body)
            stats["most_active_deputies"] = [
                {"name": bucket["key"], "count": bucket["doc_count"]}
                for bucket in active_response["aggregations"]["top_deputies"]["buckets"]
                if bucket["key"]
            ]
        except:
            stats["most_active_deputies"] = []

        try:
            themes_body = {
                "size": 0,
                "aggs": {"top_themes": {"terms": {"field": "theme_principal.keyword", "size": 10}}}
            }
            themes_response = self.es.search(index=settings.index_debats, body=themes_body)
            stats["most_discussed_themes"] = [
                {"theme": bucket["key"], "count": bucket["doc_count"]}
                for bucket in themes_response["aggregations"]["top_themes"]["buckets"]
                if bucket["key"]
            ]
        except:
            stats["most_discussed_themes"] = []

        return stats

    def index_document(self, index: str, doc_id: str, document: dict):
        try:
            self.es.index(index=index, id=doc_id, document=document)
            return True
        except Exception as e:
            logger.error(f"Index error: {e}")
            return False

    def bulk_index(self, index: str, documents: List[dict], id_field: str = "id"):
        try:
            operations = []
            for doc in documents:
                doc_id = str(doc.get(id_field)) if doc.get(id_field) else None
                if doc_id:
                    operations.append({"index": {"_index": index, "_id": doc_id}})
                else:
                    operations.append({"index": {"_index": index}})
                operations.append(doc)

            response = self.es.bulk(operations=operations)
            if response.get("errors"):
                logger.error(f"Bulk index errors: {response}")
                return False
            return True
        except Exception as e:
            logger.error(f"Bulk index error: {e}")
            return False


es_service = ElasticsearchService()
