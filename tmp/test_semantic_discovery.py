import asyncio
import sys
import os

# Add parent dir to sys.path to import from ai_scheme_server
sys.path.append(os.getcwd())

from ai_scheme_server import Profile, AgentOrchestrator

async def main():
    print("--- 🧠 TESTING DEEP SEMANTIC DISCOVERY ---")
    
    # Mocking a Textile MSME in Tamil Nadu
    profile = Profile(
        entityType="Proprietorship",
        sector="Textile",
        state="Tamil Nadu",
        businessName="Sri Vinayaka Textiles",
        businessDescription="We focus on modernization of handloom and powerloom units in Coimbatore, Tamil Nadu. Seeking credit-linked subsidies and capital grants.",
        goals="Modernization and expansion of manufacturing capacity.",
        language="ta"
    )

    print(f"User Narrative Target: Textile | Tamil Nadu | Proprietorship")
    
    results = await AgentOrchestrator.orchestrate_discovery(profile)
    
    print(f"\nTop 5 Results for Deep Semantic Matching:")
    for i, s in enumerate(results[:5]):
        print(f"{i+1}. {s.get('scheme_name')} (Score: {s.get('final_rank_score', 0):.2f})")
        print(f"   Matches: {', '.join(s.get('match_reasons', []))}")
        print(f"   Sector: {s.get('sector')}")
        print("-" * 40)

    if results:
        top_scheme = results[0]
        # Check if rank is sensible
        if top_scheme.get('final_rank_score', 0) > 70:
            print("\n✅ SUCCESS: Strong semantic alignment detected.")
        else:
            print("\n⚠️ WARNING: Score is lower than expected. Check weighting.")
    else:
        print("\n❌ FAILED: No results returned.")

if __name__ == "__main__":
    asyncio.run(main())
