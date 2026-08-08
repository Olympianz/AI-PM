"""能力模型：结构化能力词典的加载、保存与权重计算。"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
import json


@dataclass
class CapabilityItem:
    id: str
    domain: str
    name: str
    description: str = ""
    behavioral_indicators: List[str] = field(default_factory=list)
    evidence_requirements: List[str] = field(default_factory=list)
    weight: float = 0.0
    target_level: int = 3
    sources: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CapabilityModel:
    version: int = 1
    domains: Dict[str, str] = field(default_factory=dict)
    items: List[CapabilityItem] = field(default_factory=list)

    @staticmethod
    def load(path: str) -> "CapabilityModel":
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        model = CapabilityModel(version=raw.get("version", 1),
                                domains=raw.get("domains", {}))
        model.items = [CapabilityItem(**it) for it in raw.get("items", [])]
        return model

    def save(self, path: str) -> None:
        payload = {"version": self.version, "domains": self.domains,
                   "items": [it.to_dict() for it in self.items]}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def find(self, item_id: str) -> Optional[CapabilityItem]:
        for it in self.items:
            if it.id == item_id:
                return it
        return None

    def find_by_name(self, name: str) -> Optional[CapabilityItem]:
        for it in self.items:
            if it.name == name:
                return it
        return None

    def add_item(self, item: CapabilityItem) -> None:
        if self.find(item.id) is not None:
            raise ValueError("duplicate item id: " + item.id)
        if item.domain not in self.domains:
            self.domains[item.domain] = item.domain
        self.items.append(item)

    def recompute_weights(self) -> None:
        total = sum(max(it.weight, 0.0) for it in self.items) or 1.0
        for it in self.items:
            it.weight = round(max(it.weight, 0.0) / total, 4)

    def domain_weights(self) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for it in self.items:
            out[it.domain] = out.get(it.domain, 0.0) + it.weight
        return out
