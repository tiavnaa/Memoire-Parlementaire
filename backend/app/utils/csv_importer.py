import pandas as pd
import numpy as np
from typing import List, Any
from app.services.elasticsearch_service import es_service
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class CSVImporter:
    def __init__(self):
        self.es = es_service
    
    def clean_value(self, value: Any) -> Any:
        """Clean NaN and None values"""
        if pd.isna(value) or value == "" or value == "nan":
            return None
        return value
    
    def import_deputes(self, file_path: str):
        """Import deputies data"""
        df = pd.read_csv(file_path)
        df = df.replace({np.nan: None})
        
        documents = []
        for _, row in df.iterrows():
            doc = {
                "numero": self.clean_value(row.get("numero")),
                "nom": self.clean_value(row.get("nom")),
                "prenom": self.clean_value(row.get("prenom")),
                "genre": self.clean_value(row.get("genre")),
                "district": self.clean_value(row.get("district")),
                "region": self.clean_value(row.get("region")),
                "parti_politique": self.clean_value(row.get("parti_politique")),
                "groupe_parlementaire": self.clean_value(row.get("groupe_parlementaire")),
                "status": self.clean_value(row.get("status")) or "ACTIVE",
                "photo_url": self.clean_value(row.get("photo_url"))  # ← AJOUT
            }
            
            if doc["numero"]:
                documents.append(doc)
        
        if documents:
            self.es.bulk_index(settings.index_deputes, documents, id_field="numero")
        
        logger.info(f"Imported {len(documents)} deputies")
        return len(documents)
    
    def import_seances(self, file_path: str):
        """Import seances data"""
        df = pd.read_csv(file_path)
        df = df.replace({np.nan: None})
        
        documents = []
        for _, row in df.iterrows():
            doc = {
                "id": self.clean_value(row.get("id")),
                "titre": self.clean_value(row.get("titre")),
                "date": self.clean_value(row.get("date")),
                "heure": self.clean_value(row.get("heure")),
                "type_seance": self.clean_value(row.get("type_seance")),
                "lieu": self.clean_value(row.get("lieu")),
                "status": self.clean_value(row.get("status")),
                "session": self.clean_value(row.get("session"))
            }
            
            if doc["id"]:
                documents.append(doc)
        
        if documents:
            self.es.bulk_index(settings.index_seances, documents, id_field="id")
        
        logger.info(f"Imported {len(documents)} seances")
        return len(documents)
    
    def import_legislatifs(self, file_path: str):
        """Import legislative texts"""
        df = pd.read_csv(file_path)
        df = df.replace({np.nan: None})
        
        documents = []
        for _, row in df.iterrows():
            doc = {
                "numero": self.clean_value(row.get("numero")),
                "intitule": self.clean_value(row.get("intitule")),
                "type_texte": self.clean_value(row.get("type_texte")),
                "origine": self.clean_value(row.get("origine")),
                "date_depot": self.clean_value(row.get("date_depot")),
                "status": self.clean_value(row.get("status")),
                "auteur": self.clean_value(row.get("auteur")),
                "resume": self.clean_value(row.get("resume"))
            }
            
            if doc["numero"]:
                documents.append(doc)
        
        if documents:
            self.es.bulk_index(settings.index_legislatifs, documents, id_field="numero")
        
        logger.info(f"Imported {len(documents)} legislative texts")
        return len(documents)
    
    def import_debats(self, file_path: str):
        """Import debates data"""
        try:
            df = pd.read_csv(file_path)
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")
            return 0
        
        df = df.replace({np.nan: None})
        
        documents = []
        for _, row in df.iterrows():
            doc = {
                "id_intervention": self.clean_value(row.get("id_intervention")),
                "id_seance": self.clean_value(row.get("id_seance")),
                "date_seance": self.clean_value(row.get("date_seance")),
                "id_depute": self.clean_value(row.get("id_depute")),
                "nom_depute": self.clean_value(row.get("nom_depute")),
                "parti": self.clean_value(row.get("parti")),
                "groupe": self.clean_value(row.get("groupe")),
                "region": self.clean_value(row.get("region")),
                "district": self.clean_value(row.get("district")),
                "type_intervention": self.clean_value(row.get("type_intervention")),
                "style": self.clean_value(row.get("style")),
                "contenu_texte": self.clean_value(row.get("contenu_texte")) or "",
                "objet_debat": self.clean_value(row.get("objet_debat")),
                "theme_principal": self.clean_value(row.get("theme_principal")),
                "mots_cles": self.clean_value(row.get("mots_cles"))
            }
            
            if doc["id_intervention"]:
                documents.append(doc)
        
        if documents:
            chunk_size = 500
            for i in range(0, len(documents), chunk_size):
                chunk = documents[i:i+chunk_size]
                self.es.bulk_index(settings.index_debats, chunk, id_field="id_intervention")
        
        logger.info(f"Imported {len(documents)} debates")
        return len(documents)
    
    def run_full_import(self, data_dir: str = "data/"):
        """Run full import of all CSV files"""
        results = {}
        
        # Create indices first
        self.es.create_indices()
        
        # Import in order
        results["deputes"] = self.import_deputes(f"{data_dir}/deputes.csv")
        results["seances"] = self.import_seances(f"{data_dir}/seances.csv")
        results["legislatifs"] = self.import_legislatifs(f"{data_dir}/textes_legislatifs.csv")
        results["debats"] = self.import_debats(f"{data_dir}/debats_publics.csv")
        
        return results

csv_importer = CSVImporter()