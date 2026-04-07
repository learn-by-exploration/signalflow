# mkg/domain/services/seed_loader.py
"""SeedDataLoader — loads initial graph data from structured dicts.

Populates the knowledge graph with foundational entities and
relationships for the semiconductor supply chain and markets.
"""

import logging
from typing import Any

from mkg.domain.interfaces.graph_storage import GraphStorage

logger = logging.getLogger(__name__)


class SeedDataLoader:
    """Loads seed data into a GraphStorage backend."""

    def __init__(self, storage: GraphStorage) -> None:
        self._storage = storage

    async def load_entities(self, entities: list[dict[str, Any]]) -> int:
        """Load entities, returning count of successfully loaded."""
        count = 0
        for entity_data in entities:
            name = entity_data.get("name", "")
            if not name:
                logger.warning("Skipping entity with empty name: %s", entity_data)
                continue
            entity_id = entity_data.get("id")
            entity_type = entity_data.get("entity_type", "Company")
            canonical = entity_data.get("canonical_name", name)
            properties = {
                "name": name,
                "canonical_name": canonical,
            }
            # Copy extra properties
            for key in entity_data:
                if key not in ("id", "entity_type", "name", "canonical_name"):
                    properties[key] = entity_data[key]

            await self._storage.merge_entity(
                entity_type=entity_type,
                match_properties={"canonical_name": canonical},
                properties=properties,
            )
            # Ensure entity has the right ID if specified
            if entity_id:
                existing = await self._storage.find_entities(
                    filters={"canonical_name": canonical}
                )
                if existing and existing[0].get("id") != entity_id:
                    # For in-memory: re-create with explicit ID
                    await self._storage.delete_entity(existing[0]["id"])
                    await self._storage.create_entity(
                        entity_type=entity_type,
                        properties=properties,
                        entity_id=entity_id,
                    )
            count += 1
        return count

    async def load_edges(self, edges: list[dict[str, Any]]) -> int:
        """Load edges, returning count of successfully loaded."""
        count = 0
        for edge_data in edges:
            source_id = edge_data["source_id"]
            target_id = edge_data["target_id"]
            relation_type = edge_data["relation_type"]
            properties = {
                "weight": edge_data.get("weight", 0.5),
                "confidence": edge_data.get("confidence", 0.5),
            }
            for key in edge_data:
                if key not in ("source_id", "target_id", "relation_type", "weight", "confidence", "id"):
                    properties[key] = edge_data[key]
            await self._storage.create_edge(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type,
                properties=properties,
                edge_id=edge_data.get("id"),
            )
            count += 1
        return count

    async def load(self, seed_data: dict[str, Any]) -> dict[str, int]:
        """Load full seed data (entities + edges)."""
        entities_loaded = await self.load_entities(seed_data.get("entities", []))
        edges_loaded = await self.load_edges(seed_data.get("edges", []))
        return {
            "entities_loaded": entities_loaded,
            "edges_loaded": edges_loaded,
        }


def get_default_seed_data() -> dict[str, Any]:
    """Return default seed data covering SignalFlow's tracked symbols.

    Maps all 31 tracked symbols (15 stocks, 10 crypto, 6 forex) to MKG
    entities with realistic supply chain / competitive relationships.
    """
    return {
        "entities": [
            # ── Indian Stocks (NSE) ──
            {"id": "reliance", "entity_type": "Company", "name": "Reliance Industries", "canonical_name": "RELIANCE", "ticker": "RELIANCE.NS", "sector": "energy"},
            {"id": "tcs", "entity_type": "Company", "name": "Tata Consultancy Services", "canonical_name": "TCS", "ticker": "TCS.NS", "sector": "it"},
            {"id": "hdfcbank", "entity_type": "Company", "name": "HDFC Bank", "canonical_name": "HDFCBANK", "ticker": "HDFCBANK.NS", "sector": "banking"},
            {"id": "infy", "entity_type": "Company", "name": "Infosys", "canonical_name": "INFOSYS", "ticker": "INFY.NS", "sector": "it"},
            {"id": "itc", "entity_type": "Company", "name": "ITC Limited", "canonical_name": "ITC", "ticker": "ITC.NS", "sector": "fmcg"},
            {"id": "icicibank", "entity_type": "Company", "name": "ICICI Bank", "canonical_name": "ICICIBANK", "ticker": "ICICIBANK.NS", "sector": "banking"},
            {"id": "kotakbank", "entity_type": "Company", "name": "Kotak Mahindra Bank", "canonical_name": "KOTAKBANK", "ticker": "KOTAKBANK.NS", "sector": "banking"},
            {"id": "lt", "entity_type": "Company", "name": "Larsen & Toubro", "canonical_name": "LT", "ticker": "LT.NS", "sector": "infra"},
            {"id": "sbin", "entity_type": "Company", "name": "State Bank of India", "canonical_name": "SBIN", "ticker": "SBIN.NS", "sector": "banking"},
            {"id": "bhartiartl", "entity_type": "Company", "name": "Bharti Airtel", "canonical_name": "BHARTIARTL", "ticker": "BHARTIARTL.NS", "sector": "telecom"},
            {"id": "axisbank", "entity_type": "Company", "name": "Axis Bank", "canonical_name": "AXISBANK", "ticker": "AXISBANK.NS", "sector": "banking"},
            {"id": "wipro", "entity_type": "Company", "name": "Wipro", "canonical_name": "WIPRO", "ticker": "WIPRO.NS", "sector": "it"},
            {"id": "hcltech", "entity_type": "Company", "name": "HCL Technologies", "canonical_name": "HCLTECH", "ticker": "HCLTECH.NS", "sector": "it"},
            {"id": "maruti", "entity_type": "Company", "name": "Maruti Suzuki", "canonical_name": "MARUTI", "ticker": "MARUTI.NS", "sector": "auto"},
            {"id": "tatamotors", "entity_type": "Company", "name": "Tata Motors", "canonical_name": "TATAMOTORS", "ticker": "TATAMOTORS.NS", "sector": "auto"},
            # ── Crypto ──
            {"id": "btc", "entity_type": "Product", "name": "Bitcoin", "canonical_name": "BTC", "ticker": "BTCUSDT", "sector": "crypto"},
            {"id": "eth", "entity_type": "Product", "name": "Ethereum", "canonical_name": "ETH", "ticker": "ETHUSDT", "sector": "crypto"},
            {"id": "sol", "entity_type": "Product", "name": "Solana", "canonical_name": "SOL", "ticker": "SOLUSDT", "sector": "crypto"},
            {"id": "bnb", "entity_type": "Product", "name": "BNB", "canonical_name": "BNB", "ticker": "BNBUSDT", "sector": "crypto"},
            {"id": "xrp", "entity_type": "Product", "name": "XRP", "canonical_name": "XRP", "ticker": "XRPUSDT", "sector": "crypto"},
            {"id": "ada", "entity_type": "Product", "name": "Cardano", "canonical_name": "ADA", "ticker": "ADAUSDT", "sector": "crypto"},
            {"id": "doge", "entity_type": "Product", "name": "Dogecoin", "canonical_name": "DOGE", "ticker": "DOGEUSDT", "sector": "crypto"},
            {"id": "dot", "entity_type": "Product", "name": "Polkadot", "canonical_name": "DOT", "ticker": "DOTUSDT", "sector": "crypto"},
            {"id": "avax", "entity_type": "Product", "name": "Avalanche", "canonical_name": "AVAX", "ticker": "AVAXUSDT", "sector": "crypto"},
            {"id": "pol", "entity_type": "Product", "name": "Polygon", "canonical_name": "POL", "ticker": "POLUSDT", "sector": "crypto"},
            # ── Forex ──
            {"id": "usd", "entity_type": "Country", "name": "US Dollar", "canonical_name": "USD"},
            {"id": "inr", "entity_type": "Country", "name": "Indian Rupee", "canonical_name": "INR"},
            {"id": "eur", "entity_type": "Country", "name": "Euro", "canonical_name": "EUR"},
            {"id": "gbp", "entity_type": "Country", "name": "British Pound", "canonical_name": "GBP"},
            {"id": "jpy", "entity_type": "Country", "name": "Japanese Yen", "canonical_name": "JPY"},
            {"id": "aud", "entity_type": "Country", "name": "Australian Dollar", "canonical_name": "AUD"},
            # ── Key Global Entities (supply chain context) ──
            {"id": "tsmc", "entity_type": "Company", "name": "TSMC", "canonical_name": "TSMC", "sector": "semiconductors"},
            {"id": "nvidia", "entity_type": "Company", "name": "NVIDIA", "canonical_name": "NVIDIA", "sector": "semiconductors"},
            {"id": "apple", "entity_type": "Company", "name": "Apple", "canonical_name": "APPLE", "sector": "tech"},
            {"id": "google", "entity_type": "Company", "name": "Google", "canonical_name": "GOOGLE", "sector": "tech"},
            {"id": "microsoft", "entity_type": "Company", "name": "Microsoft", "canonical_name": "MICROSOFT", "sector": "tech"},
            {"id": "suzuki", "entity_type": "Company", "name": "Suzuki Motor", "canonical_name": "SUZUKI", "sector": "auto"},
            {"id": "jlr", "entity_type": "Company", "name": "Jaguar Land Rover", "canonical_name": "JLR", "sector": "auto"},
            {"id": "rbi", "entity_type": "Regulation", "name": "Reserve Bank of India", "canonical_name": "RBI"},
            {"id": "fed", "entity_type": "Regulation", "name": "US Federal Reserve", "canonical_name": "FED"},
            {"id": "ecb", "entity_type": "Regulation", "name": "European Central Bank", "canonical_name": "ECB"},
            {"id": "binance", "entity_type": "Company", "name": "Binance", "canonical_name": "BINANCE", "sector": "crypto"},
            {"id": "coinbase", "entity_type": "Company", "name": "Coinbase", "canonical_name": "COINBASE", "sector": "crypto"},
            # ── Sectors ──
            {"id": "sec_banking", "entity_type": "Sector", "name": "Indian Banking", "canonical_name": "INDIAN_BANKING"},
            {"id": "sec_it", "entity_type": "Sector", "name": "Indian IT Services", "canonical_name": "INDIAN_IT"},
            {"id": "sec_auto", "entity_type": "Sector", "name": "Indian Auto", "canonical_name": "INDIAN_AUTO"},
            {"id": "sec_crypto", "entity_type": "Sector", "name": "Cryptocurrency", "canonical_name": "CRYPTO_SECTOR"},
            {"id": "india", "entity_type": "Country", "name": "India", "canonical_name": "INDIA"},
        ],
        "edges": [
            # ── Indian IT → Global Tech (client dependencies) ──
            {"source_id": "tcs", "target_id": "google", "relation_type": "SUPPLIES_TO", "weight": 0.40, "confidence": 0.80, "description": "IT outsourcing services"},
            {"source_id": "tcs", "target_id": "microsoft", "relation_type": "SUPPLIES_TO", "weight": 0.35, "confidence": 0.75, "description": "Cloud migration services"},
            {"source_id": "infy", "target_id": "apple", "relation_type": "SUPPLIES_TO", "weight": 0.30, "confidence": 0.70, "description": "Digital transformation"},
            {"source_id": "infy", "target_id": "google", "relation_type": "SUPPLIES_TO", "weight": 0.35, "confidence": 0.75, "description": "Cloud consulting"},
            {"source_id": "wipro", "target_id": "microsoft", "relation_type": "SUPPLIES_TO", "weight": 0.30, "confidence": 0.70, "description": "Enterprise IT services"},
            {"source_id": "hcltech", "target_id": "google", "relation_type": "SUPPLIES_TO", "weight": 0.30, "confidence": 0.70, "description": "Engineering services"},
            # ── IT Companies compete with each other ──
            {"source_id": "tcs", "target_id": "infy", "relation_type": "COMPETES_WITH", "weight": 0.85, "confidence": 0.95, "description": "Top-tier Indian IT rivals"},
            {"source_id": "wipro", "target_id": "hcltech", "relation_type": "COMPETES_WITH", "weight": 0.70, "confidence": 0.90, "description": "Mid-tier Indian IT rivals"},
            {"source_id": "tcs", "target_id": "sec_it", "relation_type": "OPERATES_IN", "weight": 0.95, "confidence": 1.0},
            {"source_id": "infy", "target_id": "sec_it", "relation_type": "OPERATES_IN", "weight": 0.95, "confidence": 1.0},
            {"source_id": "wipro", "target_id": "sec_it", "relation_type": "OPERATES_IN", "weight": 0.90, "confidence": 1.0},
            {"source_id": "hcltech", "target_id": "sec_it", "relation_type": "OPERATES_IN", "weight": 0.90, "confidence": 1.0},
            # ── Banking sector relationships ──
            {"source_id": "hdfcbank", "target_id": "icicibank", "relation_type": "COMPETES_WITH", "weight": 0.80, "confidence": 0.95, "description": "Top private banks"},
            {"source_id": "hdfcbank", "target_id": "kotakbank", "relation_type": "COMPETES_WITH", "weight": 0.65, "confidence": 0.90, "description": "Private bank competition"},
            {"source_id": "sbin", "target_id": "hdfcbank", "relation_type": "COMPETES_WITH", "weight": 0.75, "confidence": 0.90, "description": "Public vs private bank"},
            {"source_id": "axisbank", "target_id": "icicibank", "relation_type": "COMPETES_WITH", "weight": 0.70, "confidence": 0.90, "description": "Mid-large private banks"},
            {"source_id": "hdfcbank", "target_id": "sec_banking", "relation_type": "OPERATES_IN", "weight": 0.95, "confidence": 1.0},
            {"source_id": "icicibank", "target_id": "sec_banking", "relation_type": "OPERATES_IN", "weight": 0.95, "confidence": 1.0},
            {"source_id": "sbin", "target_id": "sec_banking", "relation_type": "OPERATES_IN", "weight": 0.95, "confidence": 1.0},
            {"source_id": "kotakbank", "target_id": "sec_banking", "relation_type": "OPERATES_IN", "weight": 0.90, "confidence": 1.0},
            {"source_id": "axisbank", "target_id": "sec_banking", "relation_type": "OPERATES_IN", "weight": 0.90, "confidence": 1.0},
            {"source_id": "rbi", "target_id": "sec_banking", "relation_type": "REGULATES", "weight": 0.95, "confidence": 1.0, "description": "RBI monetary policy directly impacts all banks"},
            {"source_id": "rbi", "target_id": "inr", "relation_type": "REGULATES", "weight": 0.95, "confidence": 1.0, "description": "RBI manages INR exchange rate"},
            # ── Auto sector ──
            {"source_id": "maruti", "target_id": "suzuki", "relation_type": "DEPENDS_ON", "weight": 0.90, "confidence": 0.95, "description": "Suzuki owns 58% of Maruti Suzuki"},
            {"source_id": "tatamotors", "target_id": "jlr", "relation_type": "OWNS", "weight": 0.85, "confidence": 0.95, "description": "JLR is Tata Motors' premium brand"},
            {"source_id": "maruti", "target_id": "tatamotors", "relation_type": "COMPETES_WITH", "weight": 0.70, "confidence": 0.90, "description": "Domestic auto market rivals"},
            {"source_id": "maruti", "target_id": "sec_auto", "relation_type": "OPERATES_IN", "weight": 0.95, "confidence": 1.0},
            {"source_id": "tatamotors", "target_id": "sec_auto", "relation_type": "OPERATES_IN", "weight": 0.95, "confidence": 1.0},
            # ── Conglomerates ──
            {"source_id": "reliance", "target_id": "bhartiartl", "relation_type": "COMPETES_WITH", "weight": 0.80, "confidence": 0.90, "description": "Jio vs Airtel telecom war"},
            {"source_id": "reliance", "target_id": "india", "relation_type": "OPERATES_IN", "weight": 0.95, "confidence": 1.0},
            {"source_id": "itc", "target_id": "india", "relation_type": "OPERATES_IN", "weight": 0.90, "confidence": 1.0},
            {"source_id": "lt", "target_id": "india", "relation_type": "OPERATES_IN", "weight": 0.90, "confidence": 1.0},
            # ── Crypto ecosystem ──
            {"source_id": "eth", "target_id": "btc", "relation_type": "COMPETES_WITH", "weight": 0.60, "confidence": 0.85, "description": "Alt vs BTC market correlation"},
            {"source_id": "sol", "target_id": "eth", "relation_type": "COMPETES_WITH", "weight": 0.70, "confidence": 0.85, "description": "L1 blockchain competition"},
            {"source_id": "avax", "target_id": "eth", "relation_type": "COMPETES_WITH", "weight": 0.55, "confidence": 0.80, "description": "L1 smart contract competition"},
            {"source_id": "pol", "target_id": "eth", "relation_type": "DEPENDS_ON", "weight": 0.80, "confidence": 0.90, "description": "Polygon L2 depends on Ethereum"},
            {"source_id": "bnb", "target_id": "binance", "relation_type": "DEPENDS_ON", "weight": 0.90, "confidence": 0.95, "description": "BNB value tied to Binance exchange"},
            {"source_id": "btc", "target_id": "sec_crypto", "relation_type": "OPERATES_IN", "weight": 0.95, "confidence": 1.0},
            {"source_id": "eth", "target_id": "sec_crypto", "relation_type": "OPERATES_IN", "weight": 0.95, "confidence": 1.0},
            {"source_id": "sol", "target_id": "sec_crypto", "relation_type": "OPERATES_IN", "weight": 0.90, "confidence": 1.0},
            {"source_id": "binance", "target_id": "sec_crypto", "relation_type": "OPERATES_IN", "weight": 0.90, "confidence": 1.0},
            # ── Forex: central bank regulation ──
            {"source_id": "fed", "target_id": "usd", "relation_type": "REGULATES", "weight": 0.95, "confidence": 1.0, "description": "Fed rate decisions drive USD"},
            {"source_id": "ecb", "target_id": "eur", "relation_type": "REGULATES", "weight": 0.95, "confidence": 1.0, "description": "ECB rate decisions drive EUR"},
            {"source_id": "usd", "target_id": "inr", "relation_type": "AFFECTS", "weight": 0.85, "confidence": 0.90, "description": "USD strength weakens INR"},
            {"source_id": "fed", "target_id": "sec_crypto", "relation_type": "AFFECTS", "weight": 0.70, "confidence": 0.80, "description": "Fed rate hikes reduce crypto risk appetite"},
            # ── Cross-domain: semiconductor supply chain for tech companies ──
            {"source_id": "tsmc", "target_id": "nvidia", "relation_type": "SUPPLIES_TO", "weight": 0.90, "confidence": 0.95, "description": "TSMC fabs NVIDIA GPUs"},
            {"source_id": "tsmc", "target_id": "apple", "relation_type": "SUPPLIES_TO", "weight": 0.85, "confidence": 0.95, "description": "TSMC fabs Apple silicon"},
            {"source_id": "nvidia", "target_id": "tcs", "relation_type": "SUPPLIES_TO", "weight": 0.30, "confidence": 0.65, "description": "GPU infrastructure for AI services"},
            {"source_id": "nvidia", "target_id": "infy", "relation_type": "SUPPLIES_TO", "weight": 0.25, "confidence": 0.60, "description": "AI compute for digital services"},
        ],
    }
