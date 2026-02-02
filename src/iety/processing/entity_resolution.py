"""Entity resolution using trigram fuzzy matching."""

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class EntityMatch:
    """A potential entity match."""

    canonical_id: UUID
    canonical_name: str
    entity_type: str
    similarity: float
    identifiers: list[dict] = field(default_factory=list)


@dataclass
class ResolvedEntity:
    """A resolved entity with cross-references."""

    canonical_id: UUID
    canonical_name: str
    entity_type: str
    aliases: list[str] = field(default_factory=list)
    identifiers: dict = field(default_factory=dict)  # type -> value mapping
    sources: list[dict] = field(default_factory=list)  # source records


class EntityResolver:
    """Cross-domain entity resolution using PostgreSQL trigram matching.

    Matches entities across different data sources:
    - USASpending recipients (UEI, DUNS, name)
    - SEC companies (CIK, ticker, name)
    - Legal parties (name)
    - GDELT actors (name, code)

    Uses pg_trgm for fuzzy name matching with configurable threshold.
    """

    # Default similarity threshold
    DEFAULT_THRESHOLD = 0.6

    # Entity type configurations
    ENTITY_CONFIGS = {
        "company": {
            "identifier_types": ["uei", "duns", "cik", "ticker"],
            "name_field": "name",
        },
        "person": {
            "identifier_types": ["party_id"],
            "name_field": "name",
        },
        "organization": {
            "identifier_types": ["actor_code"],
            "name_field": "name",
        },
    }

    def __init__(
        self,
        session: AsyncSession,
        similarity_threshold: float = DEFAULT_THRESHOLD,
    ):
        """Initialize entity resolver.

        Args:
            session: Database session
            similarity_threshold: Minimum trigram similarity (0-1)
        """
        self.session = session
        self.similarity_threshold = similarity_threshold

    async def find_matches(
        self,
        name: str,
        entity_type: str = "company",
        limit: int = 5,
    ) -> list[EntityMatch]:
        """Find potential matches for an entity name.

        Args:
            name: Entity name to match
            entity_type: Type of entity ("company", "person", "organization")
            limit: Maximum matches to return

        Returns:
            List of EntityMatch sorted by similarity
        """
        sql = text("""
            SELECT
                ce.id as canonical_id,
                ce.canonical_name,
                ce.entity_type,
                similarity(ce.canonical_name, :name) as sim_score
            FROM integration.canonical_entities ce
            WHERE ce.entity_type = :entity_type
              AND similarity(ce.canonical_name, :name) >= :threshold
            ORDER BY sim_score DESC
            LIMIT :limit
        """)

        result = await self.session.execute(
            sql,
            {
                "name": name,
                "entity_type": entity_type,
                "threshold": self.similarity_threshold,
                "limit": limit,
            },
        )
        rows = result.fetchall()

        matches = []
        for row in rows:
            # Get identifiers for this entity
            id_sql = text("""
                SELECT identifier_type, identifier_value, source_schema, source_table
                FROM integration.entity_identifiers
                WHERE canonical_id = :canonical_id
            """)
            id_result = await self.session.execute(
                id_sql, {"canonical_id": row.canonical_id}
            )
            identifiers = [
                {
                    "type": r.identifier_type,
                    "value": r.identifier_value,
                    "source": f"{r.source_schema}.{r.source_table}",
                }
                for r in id_result.fetchall()
            ]

            matches.append(
                EntityMatch(
                    canonical_id=row.canonical_id,
                    canonical_name=row.canonical_name,
                    entity_type=row.entity_type,
                    similarity=float(row.sim_score),
                    identifiers=identifiers,
                )
            )

        return matches

    async def find_by_identifier(
        self,
        identifier_type: str,
        identifier_value: str,
    ) -> Optional[ResolvedEntity]:
        """Find an entity by a specific identifier.

        Args:
            identifier_type: Type of identifier (uei, duns, cik, etc.)
            identifier_value: Identifier value

        Returns:
            ResolvedEntity if found, None otherwise
        """
        sql = text("""
            SELECT
                ce.id as canonical_id,
                ce.canonical_name,
                ce.entity_type,
                ce.aliases
            FROM integration.entity_identifiers ei
            JOIN integration.canonical_entities ce ON ce.id = ei.canonical_id
            WHERE ei.identifier_type = :id_type
              AND ei.identifier_value = :id_value
        """)

        result = await self.session.execute(
            sql,
            {"id_type": identifier_type, "id_value": identifier_value},
        )
        row = result.fetchone()

        if not row:
            return None

        # Get all identifiers
        id_sql = text("""
            SELECT identifier_type, identifier_value
            FROM integration.entity_identifiers
            WHERE canonical_id = :canonical_id
        """)
        id_result = await self.session.execute(
            id_sql, {"canonical_id": row.canonical_id}
        )
        identifiers = {r.identifier_type: r.identifier_value for r in id_result.fetchall()}

        return ResolvedEntity(
            canonical_id=row.canonical_id,
            canonical_name=row.canonical_name,
            entity_type=row.entity_type,
            aliases=row.aliases or [],
            identifiers=identifiers,
        )

    async def create_canonical_entity(
        self,
        name: str,
        entity_type: str,
        identifiers: dict[str, str],
        source_schema: str,
        source_table: str,
        source_id: UUID,
        aliases: Optional[list[str]] = None,
    ) -> UUID:
        """Create a new canonical entity with identifiers.

        Args:
            name: Canonical name
            entity_type: Entity type
            identifiers: Dict of identifier_type -> identifier_value
            source_schema: Source schema
            source_table: Source table
            source_id: Source record ID
            aliases: Optional list of name aliases

        Returns:
            UUID of created canonical entity
        """
        # Create canonical entity
        entity_sql = text("""
            INSERT INTO integration.canonical_entities
                (entity_type, canonical_name, aliases)
            VALUES
                (:entity_type, :name, :aliases)
            RETURNING id
        """)

        result = await self.session.execute(
            entity_sql,
            {
                "entity_type": entity_type,
                "name": name,
                "aliases": aliases or [],
            },
        )
        canonical_id = result.fetchone()[0]

        # Create identifiers
        id_sql = text("""
            INSERT INTO integration.entity_identifiers
                (canonical_id, entity_type, identifier_type, identifier_value,
                 source_schema, source_table, source_id)
            VALUES
                (:canonical_id, :entity_type, :id_type, :id_value,
                 :source_schema, :source_table, :source_id)
            ON CONFLICT (identifier_type, identifier_value) DO UPDATE SET
                canonical_id = EXCLUDED.canonical_id
        """)

        for id_type, id_value in identifiers.items():
            if id_value:  # Skip empty values
                await self.session.execute(
                    id_sql,
                    {
                        "canonical_id": canonical_id,
                        "entity_type": entity_type,
                        "id_type": id_type,
                        "id_value": id_value,
                        "source_schema": source_schema,
                        "source_table": source_table,
                        "source_id": str(source_id),
                    },
                )

        await self.session.commit()
        return canonical_id

    async def link_entity(
        self,
        canonical_id: UUID,
        identifier_type: str,
        identifier_value: str,
        source_schema: str,
        source_table: str,
        source_id: UUID,
        confidence: float = 1.0,
    ) -> None:
        """Link a source record to an existing canonical entity.

        Args:
            canonical_id: Canonical entity ID
            identifier_type: Type of identifier
            identifier_value: Identifier value
            source_schema: Source schema
            source_table: Source table
            source_id: Source record ID
            confidence: Match confidence (0-1)
        """
        sql = text("""
            INSERT INTO integration.entity_identifiers
                (canonical_id, entity_type, identifier_type, identifier_value,
                 source_schema, source_table, source_id, confidence)
            SELECT
                :canonical_id,
                ce.entity_type,
                :id_type,
                :id_value,
                :source_schema,
                :source_table,
                :source_id,
                :confidence
            FROM integration.canonical_entities ce
            WHERE ce.id = :canonical_id
            ON CONFLICT (identifier_type, identifier_value) DO UPDATE SET
                confidence = GREATEST(entity_identifiers.confidence, EXCLUDED.confidence)
        """)

        await self.session.execute(
            sql,
            {
                "canonical_id": canonical_id,
                "id_type": identifier_type,
                "id_value": identifier_value,
                "source_schema": source_schema,
                "source_table": source_table,
                "source_id": str(source_id),
                "confidence": confidence,
            },
        )
        await self.session.commit()

    async def merge_entities(
        self,
        primary_id: UUID,
        secondary_id: UUID,
    ) -> UUID:
        """Merge two canonical entities into one.

        Args:
            primary_id: ID of entity to keep
            secondary_id: ID of entity to merge into primary

        Returns:
            UUID of merged entity (primary_id)
        """
        # Update all identifiers to point to primary
        sql = text("""
            UPDATE integration.entity_identifiers
            SET canonical_id = :primary_id
            WHERE canonical_id = :secondary_id
        """)
        await self.session.execute(
            sql, {"primary_id": primary_id, "secondary_id": secondary_id}
        )

        # Merge aliases
        alias_sql = text("""
            UPDATE integration.canonical_entities
            SET
                aliases = (
                    SELECT jsonb_agg(DISTINCT elem)
                    FROM (
                        SELECT jsonb_array_elements_text(
                            COALESCE(ce1.aliases, '[]'::jsonb) ||
                            COALESCE(ce2.aliases, '[]'::jsonb) ||
                            jsonb_build_array(ce2.canonical_name)
                        ) as elem
                        FROM integration.canonical_entities ce1,
                             integration.canonical_entities ce2
                        WHERE ce1.id = :primary_id
                          AND ce2.id = :secondary_id
                    ) sub
                ),
                merged_from = COALESCE(merged_from, ARRAY[]::uuid[]) || ARRAY[:secondary_id]::uuid[]
            WHERE id = :primary_id
        """)
        await self.session.execute(
            alias_sql, {"primary_id": primary_id, "secondary_id": secondary_id}
        )

        # Delete secondary entity
        delete_sql = text("""
            DELETE FROM integration.canonical_entities
            WHERE id = :secondary_id
        """)
        await self.session.execute(delete_sql, {"secondary_id": secondary_id})

        await self.session.commit()
        return primary_id

    async def resolve_usaspending_recipient(
        self,
        recipient_name: str,
        uei: Optional[str],
        duns: Optional[str],
        source_id: UUID,
    ) -> Optional[UUID]:
        """Resolve a USASpending recipient to canonical entity.

        Args:
            recipient_name: Recipient name
            uei: Unique Entity Identifier
            duns: DUNS number (legacy)
            source_id: Award record ID

        Returns:
            Canonical entity ID if resolved/created
        """
        # Try to find by UEI first
        if uei:
            entity = await self.find_by_identifier("uei", uei)
            if entity:
                return entity.canonical_id

        # Try DUNS
        if duns:
            entity = await self.find_by_identifier("duns", duns)
            if entity:
                # Add UEI if we have it
                if uei:
                    await self.link_entity(
                        entity.canonical_id,
                        "uei",
                        uei,
                        "usaspending",
                        "awards",
                        source_id,
                    )
                return entity.canonical_id

        # Try fuzzy name match
        matches = await self.find_matches(recipient_name, entity_type="company")
        if matches and matches[0].similarity >= 0.85:
            # High confidence match - link to existing
            match = matches[0]
            identifiers = {}
            if uei:
                identifiers["uei"] = uei
            if duns:
                identifiers["duns"] = duns

            for id_type, id_value in identifiers.items():
                await self.link_entity(
                    match.canonical_id,
                    id_type,
                    id_value,
                    "usaspending",
                    "awards",
                    source_id,
                    confidence=match.similarity,
                )
            return match.canonical_id

        # Create new canonical entity
        identifiers = {}
        if uei:
            identifiers["uei"] = uei
        if duns:
            identifiers["duns"] = duns

        return await self.create_canonical_entity(
            name=recipient_name,
            entity_type="company",
            identifiers=identifiers,
            source_schema="usaspending",
            source_table="awards",
            source_id=source_id,
        )


async def create_entity_resolver(
    session: AsyncSession,
    similarity_threshold: float = 0.6,
) -> EntityResolver:
    """Factory function to create entity resolver."""
    return EntityResolver(session, similarity_threshold)
