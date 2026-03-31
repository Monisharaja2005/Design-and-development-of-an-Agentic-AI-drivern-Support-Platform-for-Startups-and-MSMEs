import asyncio
import os
import json
import logging
import httpx
from pydantic import BaseModel
from typing import List, Optional, Dict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Profile(BaseModel):
    sector: str = ""
    state: str = ""
    entityType: str = ""
    businessDescription: str = ""
    goals: str = ""
    turnover: str = ""
    projectCost: str = ""
    gender: str = "Male"
    socialCategory: str = "General"
    udyamRegistered: str = "No"
    isPhysicallyChallenged: str = "No"
    isStartupIndiaRegistered: str = "No"
    gstRegistered: str = "No"
    district: str = ""
    taluk: str = ""
    pinCode: str = ""
    businessName: str = ""
    brandName: str = ""
    yearEstablished: str = ""
    employees: str = ""
    subSector: str = ""
    techLevel: str = ""
    exportIntention: str = ""
    locationType: str = ""
    address: str = ""
    premisesType: str = ""
    womenEmployees: str = ""
    dob: str = ""
    financeMode: str = ""
    ownContrib: str = ""
    bank: str = ""
    investmentReq: str = ""
    hasLoans: str = ""
    udyamRegistered: str = ""

async def audit_precision():
    url = "http://localhost:8001/v1/recommend"
    
    # Test Case: Textile MSME in Tamil Nadu
    profile = Profile(
        sector="Textile",
        state="Tamil Nadu",
        entityType="Proprietorship",
        businessDescription="We are a small-scale textile manufacturing unit in Coimbatore specialized in cotton yarn processing and garment manufacturing.",
        goals="Modernize machinery and scale production capacity for export.",
        turnover="10 Lakh to 50 Lakh",
        projectCost="25 Lakh",
        gender="Male",
        socialCategory="General"
    )
    
    logger.info(f"--- PRECISION AUDIT START: {profile.sector} in {profile.state} ---")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(url, json=profile.dict())
            data = resp.json()
            results = data.get("schemes", [])
            
            logger.info(f"Total Elite Matches Found: {len(results)}")
            
            # Check for "Unwanted" Noise
            unwanted_sectors = ["agriculture", "food processing", "it ", "software", "dairy", "drone"]
            unwanted_found = []
            
            print("\n--- ELITE SHORTLISTING SAMPLES ---")
            for i, s in enumerate(results[:10]):
                name = s.get('scheme_name', 'Unknown')
                score = s.get('final_rank_score', 0)
                sector = s.get('sector', 'General')
                state = s.get('state', 'India')
                
                print(f"{i+1}. {name} | Score: {score:.2f} | Sector: {sector} | State: {state}")
                
                # Check for logic violations
                for u in unwanted_sectors:
                    if u in str(sector).lower() or u in str(name).lower():
                        if "all" not in str(sector).lower():
                           unwanted_found.append(f"{name} ({sector})")

            print("\n--- HARD GATE VERIFICATION ---")
            if not unwanted_found:
                print("✅ HARD SECTOR GATE: Success. No mismatched industry schemes (Agri/Food/IT) found in elite list.")
            else:
                print(f"❌ HARD SECTOR GATE: Failed. Found {len(unwanted_found)} mismatched schemes: {unwanted_found}")

            # Geographic Check
            mismatched_states = [s for s in results if s.get('state') and "Tamil Nadu" not in s.get('state') and "India" not in s.get('state') and "Central" not in s.get('state')]
            if not mismatched_states:
                print("✅ GEOGRAPHIC GATE: Success. No mismatched state schemes found.")
            else:
                print(f"❌ GEOGRAPHIC GATE: Failed. Found {len(mismatched_states)} mismatched states.")

            print("\n--- ACCURACY SUMMARY ---")
            avg_score = sum(s.get('final_rank_score', 0) for s in results) / len(results) if results else 0
            print(f"Average Elite Score: {avg_score:.2f}")
            print(f"Shortlisting Status: {'LASER CORRECT' if avg_score > 80 and not unwanted_found else 'SOFT MATCHING'}")

        except Exception as e:
            logger.error(f"Audit failed: {e}")

if __name__ == "__main__":
    asyncio.run(audit_precision())
