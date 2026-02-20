from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional, Any
import yaml

# Agregamos "GOAL_TRACKER" a los tipos permitidos para el contador de título intermedio
RuleType = Literal["DIRECT", "SPLIT_1toN", "MERGE_Nto1", "ACA_ONLY", "GOAL_TRACKER"]

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

@dataclass
class MappingRule:
    type: RuleType
    src_2018_codes: list[str] = field(default_factory=list)
    dst_2025_codes: list[str] = field(default_factory=list)

    # Propiedades para MERGE_Nto1 (fusiones parciales)
    aca_on_partial: Optional[int] = None
    aca_partial_mode: Optional[Literal["per_source", "per_rule"]] = None

    # Propiedades para ACA_ONLY (créditos directos)
    aca_credits: Optional[int] = None

    # Comentario descriptivo de la regla
    comment: Optional[str] = None
    
    # --- LA SOLUCIÓN AL ERROR ---
    # Este diccionario almacenará cualquier campo extra que venga del YAML (como 'name' o 'required_hours')
    # evitando que el programa falle por argumentos inesperados.
    extra_fields: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MappingRule:
        """
        Crea una instancia de MappingRule filtrando los campos que 
        no pertenecen a la definición de la dataclass.
        """
        # Obtenemos los nombres de los campos definidos en la clase
        class_fields = {f.name for f in cls.__dataclass_fields__.values()}
        
        # Separamos los campos conocidos de los extras
        known_args = {k: v for k, v in data.items() if k in class_fields}
        extra_args = {k: v for k, v in data.items() if k not in class_fields}
        
        # Creamos la regla y le asignamos los campos extra
        rule = cls(**known_args)
        rule.extra_fields = extra_args
        return rule

def _read_yaml(path: Path):
    """Lectura segura del archivo YAML de configuración."""
    if not path.exists():
        return []
    return yaml.safe_load(path.read_text(encoding="utf-8")) or []

def load_rules(variant: str | None = None) -> list[MappingRule]:
    """
    Carga las reglas de mapeo buscando por variante o el archivo general.
    """
    if variant:
        cand = DATA_DIR / f"mapping_rules_{variant}.yaml"
        data = _read_yaml(cand) if cand.exists() else _read_yaml(DATA_DIR / "mapping_rules.yaml")
    else:
        data = _read_yaml(DATA_DIR / "mapping_rules.yaml")

    rules: list[MappingRule] = []
    for item in data:
        # Definimos el comportamiento por defecto para las fusiones (MERGE)
        if item.get("type") == "MERGE_Nto1" and "aca_partial_mode" not in item:
            item["aca_partial_mode"] = "per_source"
            
        # Usamos el nuevo método from_dict en lugar de MappingRule(**item)
        # Esto previene el error "unexpected keyword argument"
        rules.append(MappingRule.from_dict(item))
        
    return rules