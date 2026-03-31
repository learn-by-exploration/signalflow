# mkg/domain/services/hallucination_verifier.py
"""HallucinationVerifier — validates extraction results against source text.

R-HV1 through R-HV3: Verify entities/relations exist in source text.
Filters out hallucinated extractions.
"""

from typing import Any


class HallucinationVerifier:
    """Verifies extracted entities and relations against source text."""

    def verify_entity(self, entity: dict[str, Any], text: str) -> bool:
        """Check if an extracted entity name appears in the source text."""
        name = entity.get("name", "")
        return name.lower() in text.lower()

    def verify_relation(self, relation: dict[str, Any], text: str) -> bool:
        """Check if both source and target of a relation appear in the text."""
        source = relation.get("source", "")
        target = relation.get("target", "")
        text_lower = text.lower()
        return source.lower() in text_lower and target.lower() in text_lower

    def verify_result(
        self, result: dict[str, Any], text: str
    ) -> dict[str, Any]:
        """Verify all entities and relations, filtering out hallucinations."""
        entities = result.get("entities", [])
        relations = result.get("relations", [])

        verified_entities = [e for e in entities if self.verify_entity(e, text)]
        verified_names = {e.get("name", "").lower() for e in verified_entities}

        verified_relations = [
            r for r in relations
            if self.verify_relation(r, text)
            and r.get("source", "").lower() in verified_names
            and r.get("target", "").lower() in verified_names
        ]

        return {
            "entities": verified_entities,
            "relations": verified_relations,
            "stats": {
                "entities_total": len(entities),
                "entities_verified": len(verified_entities),
                "entities_rejected": len(entities) - len(verified_entities),
                "relations_total": len(relations),
                "relations_verified": len(verified_relations),
                "relations_rejected": len(relations) - len(verified_relations),
            },
        }
