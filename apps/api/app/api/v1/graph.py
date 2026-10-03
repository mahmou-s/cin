from fastapi import APIRouter, HTTPException
from neo4j import AsyncGraphDatabase
from ...config import settings

router = APIRouter()

QUERY = """
MATCH (c:Community)-[:HAS_CAPABILITY]->(a:CapabilityAssertion)-[:INSTANCE_OF]->(t:CapabilityType)
RETURN c, a, t
LIMIT $limit
"""

@router.get("/graph/capabilities")
async def graph_capabilities(limit: int = 500):
    limit = max(1, min(limit, 2000))
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        nodes = {}
        links = []
        async with driver.session() as session:
            result = await session.run(QUERY, limit=limit)
            async for record in result:
                community = record["c"]
                assertion = record["a"]
                capability = record["t"]

                node_specs = [
                    (community, "Community", community.get("name")),
                    (assertion, "CapabilityAssertion", assertion.get("id")),
                    (capability, "CapabilityType", capability.get("name")),
                ]
                for node, node_type, label in node_specs:
                    node_id = str(node.get("id"))
                    nodes[node_id] = {
                        "id": node_id,
                        "label": label or node_id,
                        "type": node_type,
                        "code": capability.get("code") if node_type == "CapabilityType" else None,
                        "confidence": assertion.get("confidence_score") if node_type == "CapabilityAssertion" else None,
                    }

                links.extend([
                    {
                        "id": f"{community['id']}-HAS_CAPABILITY-{assertion['id']}",
                        "source": str(community["id"]),
                        "target": str(assertion["id"]),
                        "type": "HAS_CAPABILITY",
                    },
                    {
                        "id": f"{assertion['id']}-INSTANCE_OF-{capability['id']}",
                        "source": str(assertion["id"]),
                        "target": str(capability["id"]),
                        "type": "INSTANCE_OF",
                    },
                ])

        return {"nodes": list(nodes.values()), "links": links}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="KNOWLEDGE_GRAPH_UNAVAILABLE") from exc
    finally:
        await driver.close()
