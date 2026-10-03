from neo4j import AsyncGraphDatabase
from ..config import settings

RELATIONS = {
    ('C01','C06'):'ENABLES', ('C06','C07'):'ENABLES', ('C07','C03'):'ENABLES',
    ('C01','C02'):'COMPLEMENTS', ('C02','C03'):'ENABLES', ('C03','C10'):'ENABLES',
    ('C05','C07'):'ENABLES', ('C04','C05'):'ENABLES', ('C08','C09'):'ENABLES', ('C09','C10'):'ENABLES'
}

async def project_capability_relations():
    driver = AsyncGraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    try:
        async with driver.session() as session:
            result = await session.run('MATCH (a:CapabilityType),(b:CapabilityType) WHERE a.code IN $codes AND b.code IN $codes RETURN a,b', codes=list({c for pair in RELATIONS for c in pair}))
            nodes = {(r['a']['code'], r['b']['code']): (r['a'], r['b']) async for r in result}
            count = 0
            for (ca, cb), rel in RELATIONS.items():
                if (ca, cb) not in nodes:
                    continue
                cypher = f"MATCH (a:CapabilityType {{code:$a}}),(b:CapabilityType {{code:$b}}) MERGE (a)-[:{rel}]->(b)"
                await session.run(cypher, a=ca, b=cb)
                count += 1
            return count
    finally:
        await driver.close()
