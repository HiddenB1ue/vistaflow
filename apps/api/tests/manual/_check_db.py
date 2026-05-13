"""Quick DB check for route plans and candidates."""
import asyncio
import asyncpg


async def main() -> None:
    pool = await asyncpg.create_pool(
        dsn="postgresql://vistaflow:vistaflow@localhost:5432/vistaflow",
        min_size=1, max_size=3,
    )
    async with pool.acquire() as conn:
        # 1. Check table structures
        for tbl in ("route_plan_cache", "route_plan_candidate", "route_plan_segment"):
            cols = await conn.fetch(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = $1 ORDER BY ordinal_position", tbl
            )
            print(f"{tbl} columns: {[r['column_name'] for r in cols]}")

        # 2. Find plans with 北京/上海
        plans = await conn.fetch(
            "SELECT plan_id, from_station, to_station, search_date "
            "FROM route_plan_cache "
            "WHERE from_station LIKE '%北京%' AND to_station LIKE '%上海%' "
            "ORDER BY search_date DESC LIMIT 10"
        )
        print(f"\nFound {len(plans)} plans for 北京→上海:")
        for r in plans:
            print(f"  {r['plan_id']} | {r['from_station']}→{r['to_station']} | {r['search_date']}")

        if not plans:
            # Show all plans
            all_plans = await conn.fetch(
                "SELECT plan_id, from_station, to_station, search_date "
                "FROM route_plan_cache ORDER BY search_date DESC LIMIT 20"
            )
            print(f"\nAll plans ({len(all_plans)}):")
            for r in all_plans:
                print(f"  {r['plan_id']} | {r['from_station']}→{r['to_station']} | {r['search_date']}")

        # 3. If plans found, check candidate count and unique legs
        if plans:
            plan_id = plans[0]["plan_id"]
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM route_plan_candidate WHERE plan_id = $1", plan_id
            )
            print(f"\nCandidate count for plan {plan_id}: {count}")

            # Unique legs from segments
            legs = await conn.fetch(
                "SELECT DISTINCT from_station, to_station "
                "FROM route_plan_segment WHERE plan_id = $1 "
                "ORDER BY from_station, to_station",
                plan_id,
            )
            print(f"Unique legs: {len(legs)}")
            for leg in legs:
                print(f"  {leg['from_station']} → {leg['to_station']}")

        # 4. Check station telecodes
        telecodes = await conn.fetch(
            "SELECT name, telecode FROM stations "
            "WHERE name IN ('北京', '北京南', '北京西', '上海', '上海虹桥', '上海南') "
            "AND telecode IS NOT NULL"
        )
        print(f"\nTelecodes:")
        for r in telecodes:
            print(f"  {r['name']} = {r['telecode']}")

    await pool.close()


asyncio.run(main())
