import uuid
from backend.agents.base import BaseAgent, register_agent
from backend.models.company import Company
from backend.tools.web_search import search_companies


@register_agent("company_discovery")
class CompanyDiscoveryAgent(BaseAgent):
    """Discovers companies via SerpAPI Google search or mock dataset."""

    async def run(self, input: dict, memory, config: dict) -> dict:
        workflow_id = input.get("workflow_id")
        icp = input.get("icp", {})

        log_id = await self.log_start(workflow_id, "company_discovery", {
            "icp_industries": icp.get("industries"),
            "icp_locations": icp.get("locations"),
            "icp_countries": icp.get("countries"),
        })

        await self.emit(workflow_id, "company_discovery", "running", {
            "message": f"Searching Google for {icp.get('industries', ['companies'])} companies in {icp.get('locations') or icp.get('countries', ['US'])}..."
        })

        # Search
        raw_companies = await search_companies(icp)

        await self.emit(workflow_id, "company_discovery", "running", {
            "message": f"Found {len(raw_companies)} results. Running 3-layer deduplication..."
        })

        company_ids = []
        skipped = 0
        new_count = 0
        seen_domains_batch = set()

        for company_data in raw_companies:
            domain = (company_data.get("domain") or "").lower().strip()
            if not domain or len(domain) < 4:
                continue

            # Layer 1: Memory check (cross-workflow dedup via ChromaDB/PostgreSQL)
            if memory:
                try:
                    if memory.check_duplicate(domain):
                        skipped += 1
                        continue
                except:
                    pass

            # Layer 2: DB check — domain already in companies table (any workflow)
            existing = self.db.query(Company).filter(Company.domain == domain).first()
            if existing:
                skipped += 1
                continue

            # Layer 3: Current batch dedup
            if domain in seen_domains_batch:
                skipped += 1
                continue
            seen_domains_batch.add(domain)

            # Insert new company
            company = Company(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                name=company_data.get("name") or domain.split(".")[0].title(),
                domain=domain,
                industry=company_data.get("industry"),
                country=company_data.get("country"),
                employee_count=company_data.get("employee_count"),
                funding_stage=company_data.get("funding_stage"),
                tech_stack_json=company_data.get("tech_stack", []),
                qualification_score=None,
                status="pending",
            )
            self.db.add(company)
            company_ids.append(company.id)
            new_count += 1

            # Emit per-company discovered event for live activity feed
            await self.emit(workflow_id, "company_discovery", "company_discovered", {
                "company_name": company.name,
                "domain": company.domain,
                "industry": company.industry,
                "country": company.country,
                "employee_count": company.employee_count,
            })

        self.db.commit()

        result = {
            "company_ids": company_ids,
            "companies_found": new_count,
            "duplicates_skipped": skipped,
        }

        await self.emit(workflow_id, "company_discovery", "completed", {
            "message": f"✓ {new_count} new companies found ({skipped} duplicates skipped)",
            "companies_found": new_count,
            "duplicates_skipped": skipped,
        })

        await self.log_complete(log_id, result)
        return result
