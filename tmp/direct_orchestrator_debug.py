import asyncio
from ai_scheme_server import AgentOrchestrator, Profile

async def main():
    profile = Profile(sector="Food Processing", state="Tamil Nadu", entityType="Proprietorship", turnover="₹50 Lakh", investment="₹10 Lakh", businessAge="2 years", isExporting=True, fundingRequirement="₹20 Lakh", purpose="Expansion", language="en")
    print("Running orchestrate_discovery directly...")
    try:
        res = await AgentOrchestrator.orchestrate_discovery(profile)
        print(f"Success! {len(res)} results.")
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
