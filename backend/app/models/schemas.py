from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

# Debats schemas
class Debat(BaseModel):
    id_intervention: str
    id_seance: Optional[str] = None
    date_seance: Optional[date] = None
    id_depute: Optional[str] = None
    nom_depute: Optional[str] = None
    parti: Optional[str] = None
    groupe: Optional[str] = None
    region: Optional[str] = None
    district: Optional[str] = None
    type_intervention: Optional[str] = None
    style: Optional[str] = None
    contenu_texte: str
    objet_debat: Optional[str] = None
    theme_principal: Optional[str] = None
    mots_cles: Optional[str] = None

# Deputes schemas
class Depute(BaseModel):
    numero: Optional[str] = None
    nom: str
    prenom: str
    genre: Optional[str] = None
    district: Optional[str] = None
    region: Optional[str] = None
    parti_politique: Optional[str] = None
    groupe_parlementaire: Optional[str] = None
    status: Optional[str] = "ACTIVE"
    photo_url: Optional[str] = None  # ← AJOUT

# Seances schemas
class Seance(BaseModel):
    id: str
    titre: Optional[str] = None
    date: Optional[date] = None
    heure: Optional[str] = None
    type_seance: Optional[str] = None
    lieu: Optional[str] = None
    status: Optional[str] = None
    session: Optional[str] = None

# Textes Legislatifs schemas
class TexteLegislatif(BaseModel):
    numero: str
    intitule: str
    type_texte: Optional[str] = None
    origine: Optional[str] = None
    date_depot: Optional[datetime] = None
    status: Optional[str] = None
    auteur: Optional[str] = None
    resume: Optional[str] = None

# Search request/response
class SearchRequest(BaseModel):
    query: str
    search_type: str = "all"
    filters: Optional[dict] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    page: int = 1
    size: int = 20

# Statistics
class StatisticsResponse(BaseModel):
    total_debates: int
    total_deputies: int
    total_sessions: int
    total_laws: int
    most_active_deputies: List[dict]
    most_discussed_themes: List[dict]
    debates_by_region: List[dict]
    debates_by_party: List[dict]
    timeline: List[dict]