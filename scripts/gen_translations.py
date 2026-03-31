import json
import os

base_path = r"d:\Main_project1\final\frontend\src\locales"
schemes_json_path = r"d:\Main_project1\final\frontend\data\schemes_merged_final.json"

# Load all schemes from the master DB to ensure 100% key coverage
master_schemes = []
try:
    with open(schemes_json_path, "r", encoding="utf-8") as f:
        master_schemes = json.load(f)
except Exception as e:
    print(f"Warning: Could not load schemes JSON: {e}")

en_template = {
    "common": {
        "dashboard": "Dashboard", "discovery": "Scheme Discovery", "validation": "Document Validation", 
        "assistant": "AI Advisor", "profile": "My Profile", "logout": "Log Out", "active": "Active",
        "engine_online": "AI Engine Online", "engine_offline": "Engine Offline", "navigation": "Navigation",
        "shortlisted": "Shortlisted", "shortlist": "Shortlist", "saved_schemes": "Saved Schemes", 
        "pro_tip": "Pro Tip", "pro_subtitle": "Verified businesses get 3× higher priority in scheme matching.",
        "grounded": "Grounded Intel", "re_run": "Re-run Analysis", "view_details": "View Details", "sort": "Sort",
        "matches": "Matches", "clear_all": "Clear All Filters", "complete": "Complete"
    },
    "dashboard": {
        "title": "Intelligence Dashboard", "subtitle": "AI-powered overview", "welcome_back": "Welcome Back",
        "intel_summary": "Karios Intelligence Summary", "karios_score": "Karios Score",
        "status_optimized": "Optimized Eligibility Detected", "status_needed": "Profile Needed for Full Karios Score",
        "optimized_msg": "Your MSME profile shows high compatibility with 14+ government schemes. Complete your UDYAM document validation to increase your AI Score by 18%.",
        "needed_msg": "Build your 5-step business profile to unlock personalized scheme discovery with 94% match accuracy and see your full funding potential.",
        "priority_high": "Priority: High", "action_required": "Action Required", "profile_active": "Profile Active",
        "profile_incomplete": "Profile incomplete", "profile_incomplete_msg": "Complete your business profile for personalized scheme matching.",
        "complete_profile": "Complete Profile",
        "stats": {
            "active_schemes": "Active Schemes", "total_investment": "Total Investment", 
            "docs_verified": "Documents Verified", "ai_sessions": "AI Sessions"
        }
    },
    "discovery": {
        "title": "Scheme Discovery", "subtitle": "AI matching across 383+ schemes", "search_placeholder": "Search schemes, sectors or keywords...",
        "filter_intel": "Filter Intelligence", "apply_filters": "Apply Filters", "showing": "Showing {{count}} of {{total}} schemes",
        "no_matches": "No schemes match your current filters", "analyzing": "Analyzing...",
        "primary_sector": "Primary Sector", "state_region": "State / Region", "entity_type": "Entity Type",
        "best_match": "Best Match", "deadline": "Deadline"
    },
    "profile": {
        "title": "Build Your Intelligence Profile", "subtitle": "This data powers your personalized scheme discovery engine.",
        "phase_label": "Phase 2 — Business Intelligence Profile", "step_label": "Step {{current}} of {{total}}: {{title}}",
        "continue": "Continue", "submit": "Submit & Discover Schemes", "saving": "Saving...",
        "skip": "Skip profile setup for now (limited matching)", "back": "Back",
        "required_error": "{{field}} is required."
    },
    "modal": {
        "overview": "Strategic Overview", "eligibility": "Core Eligibility", "intel_advisor": "Scheme Detail Assistant",
        "grounded_tag": "BGE-M3 Based", "official_portal": "Access Official Portal",
        "chat_placeholder": "Ask about steps, documents, or eligibility...",
        "quick_chips": {
            "eligibility": "Eligibility", "documents": "Required documents", "apply": "How to apply", "benefits": "Benefits"
        }
    },
    "assistant": {
        "title": "AI Advisor", "subtitle": "RAG-powered conversational intelligence", "welcome": "Hello! I'm KARIOS Intelligence.",
        "error_sync": "I encountered a synchronization error. Please try again soon."
    },
    "schemes": { s["scheme_id"]: {"name": s["scheme_name"]} for s in master_schemes }
}

# Scheme-specific high-quality translations for major national programs
SCHEME_VIRTUAL_DB = {
    "SCH-151417f0": { # CGTMSE
        "hi": "सूक्ष्म और लघु उद्यमों के लिए क्रेडिट गारंटी फंड ट्रस्ट (CGTMSE)",
        "ta": "குறு மற்றும் சிறு நிறுவனங்களுக்கான கடன் உத்தரவாத நிதி அறக்கட்டளை (CGTMSE)",
        "mr": "सूक्ष्म आणि लघु उद्योगांसाठी क्रेडिट गॅरंटी फंड ट्रस्ट (CGTMSE)",
        "kn": "ಸೂಕ್ಷ್ಮ ಮತ್ತು ಸಣ್ಣ ಉದ್ಯಮಗಳಿಗೆ ಕ್ರೆಡಿಟ್ ಗ್ಯಾರಂಟಿ ಫಂಡ್ ಟ್ರಸ್ಟ್ (CGTMSE)"
    },
    "SCH-93680a06": { # MUDRA Shishu
        "hi": "प्रधानमंत्री मुद्रा योजना - शिशु श्रेणी (MUDRA)",
        "ta": "பிரதான் மந்திரி முத்ரா யோஜனா - சிஷு வகை (MUDRA)",
        "mr": "प्रधानमंत्री मुद्रा योजना - शिशू श्रेणी",
        "kn": "ಪ್ರಧಾನ ಮಂತ್ರಿ ಮುದ್ರಾ ಯೋಜನೆ - ಶಿಶು ವರ್ಗ"
    },
    "SCH-5494feec": { # MUDRA Kishor
        "hi": "प्रधानमंत्री मुद्रा योजना - किशोर श्रेणी (MUDRA)",
        "ta": "பிரதான் மந்திரி முத்ரா யோஜனா - கிஷோர் வகை (MUDRA)",
        "mr": "प्रधानमंत्री मुद्रा योजना - किशोर श्रेणी",
        "kn": "ಪ್ರಧಾನ ಮಂತ್ರಿ ಮುದ್ರಾ ಯೋಜನೆ - ಕಿಶೋರ್ ವರ್ಗ"
    },
    "SCH-35eec055": { # Startup India Seed Fund
        "hi": "स्टार्टअप इंडिया सीड फंड योजना (SISFS)",
        "ta": "ஸ்டார்ட்அப் இந்தியா விதை நிதித் திட்டம் (SISFS)",
        "mr": "स्टार्टअप इंडिया सीड फंड योजना",
        "kn": "ಸ್ಟಾರ್ಟ್ಅಪ್ ಇಂಡಿಯಾ ಸೀಡ್ ಫಂಡ್ ಯೋಜನೆ"
    },
    "SCH-6740dae4": { # NSIC Raw Material Assistance
        "hi": "NSIC कच्चा माल सहायता योजना",
        "ta": "NSIC மூலப்பொருள் உதவித் திட்டம்"
    }
}

translations = {
    "hi": { 
        "common": {
            "dashboard": "डैशबोर्ड", "discovery": "योजना खोज", "engine_online": "एआई इंजन ऑनलाइन", 
            "engine_offline": "इंजन ऑफ़लाइन", "pro_subtitle": "सत्यापित व्यवसायों को योजना मिलान में 3× उच्च प्राथमिकता मिलती है।",
            "grounded": "आधारित इंटेलिजेंस", "re_run": "पुनः विश्लेषण करें", "view_details": "विवरण देखें", "sort": "क्रमबद्ध करें",
            "matches": "मिलान", "shortlisted": "शॉर्टलिस्ट किया गया", "shortlist": "शॉर्टलिस्ट", "clear_all": "सभी फ़िल्टर साफ़ करें", "pro_tip": "प्रो टिप", "complete": "पूर्ण"
        },
        "dashboard": {
            "title": "इंटेलिजेंस डैशबोर्ड", "subtitle": "एआई-संचालित अवलोकन", "welcome_back": "वापसी पर स्वागत है",
            "intel_summary": "कारियोस इंटेलिजेंस सारांश", "karios_score": "कारियोस स्कोर",
            "status_optimized": "अनुकूलित पात्रता का पता चला", "status_needed": "पूर्ण कारियोस स्कोर के लिए प्रोफाइल आवश्यक है",
            "optimized_msg": "आपकी एमएसएमई प्रोफाइल 14+ सरकारी योजनाओं के साथ उच्च अनुकूलता दिखाती है। स्कोर बढ़ाने के लिए दस्तावेज़ सत्यापन पूरा करें।",
            "needed_msg": "94% मिलान सटीकता के साथ व्यक्तिगत योजना खोज को अनलॉक करने के लिए अपनी 5-चरणीय व्यावसायिक प्रोफ़ाइल बनाएं।",
            "priority_high": "प्राथमिकता: उच्च", "action_required": "कार्रवाई आवश्यक", "profile_active": "प्रोफाइल सक्रिय",
            "profile_incomplete": "प्रोफाइल अपूर्ण", "profile_incomplete_msg": "व्यक्तिगत योजना मिलान के लिए अपनी व्यावसायिक प्रोफ़ाइल पूरी करें।",
            "complete_profile": "प्रोफाइल पूरी करें",
            "stats": {
                "active_schemes": "सक्रिय योजनाएं", "total_investment": "कुल निवेश", 
                "docs_verified": "सत्यापित दस्तावेज़", "ai_sessions": "एआई सत्र"
            }
        },
        "discovery": {
            "title": "योजना खोज", "subtitle": "383+ योजनाओं में एआई मिलान", "search_placeholder": "योजनाएं, क्षेत्र या कीवर्ड खोजें...",
            "filter_intel": "फ़िल्टर इंटेलिजेंस", "apply_filters": "फ़िल्टर लागू करें", "showing": "{{total}} में से {{count}} योजनाएं दिखा रहा है",
            "no_matches": "आपके वर्तमान फ़िल्टर से कोई योजना मेल नहीं खाती", "analyzing": "विश्लेषण कर रहा है...",
            "primary_sector": "प्राथमिक क्षेत्र", "state_region": "राज्य / क्षेत्र", "entity_type": "संस्था का प्रकार",
            "best_match": "सबसे अच्छा मिलान", "deadline": "समय सीमा"
        },
        "profile": {
            "title": "अपनी इंटेलिजेंस प्रोफाइल बनाएं", "subtitle": "यह डेटा आपकी व्यक्तिगत योजना खोज इंजन को शक्ति प्रदान करता है।",
            "phase_label": "चरण 2 — व्यावसायिक इंटेलिजेंस प्रोफाइल", "step_label": "चरण {{total}} में से {{current}}: {{title}}",
            "continue": "जारी रखें", "submit": "जमा करें और योजनाओं की खोज करें", "saving": "सहेज रहा है...",
            "skip": "अभी के लिए प्रोफाइल सेटअप छोड़ें (सीमित मिलान)", "back": "पीछे",
            "required_error": "{{field}} आवश्यक है।"
        },
        "modal": {
            "overview": "रणनीतिक अवलोकन", "eligibility": "मुख्य पात्रता", "intel_advisor": "योजना विवरण सहायक",
            "grounded_tag": "BGE-M3 आधारित", "official_portal": "आधिकारिक पोर्टल पर जाएं",
            "chat_placeholder": "चरणों, दस्तावेजों या पात्रता के बारे में पूछें...",
            "quick_chips": {
                "eligibility": "पात्रता", "documents": "आवश्यक दस्तावेज़", "apply": "आवेदन कैसे करें", "benefits": "लाभ"
            }
        },
        "schemes": { k: {"name": v["hi"]} for k, v in SCHEME_VIRTUAL_DB.items() if "hi" in v }
    },
    "ta": {
        "common": {
            "dashboard": "டேஷ்போர்டு", "discovery": "திட்டக் கண்டுபிடிப்பு", "engine_online": "AI என்ஜின் ஆன்லைன்",
            "view_details": "விவரங்களைக் காண்க", "re_run": "மீண்டும் இயக்கவும்", "matches": "பொருத்தங்கள்", "clear_all": "அனைத்தையும் துடை"
        },
        "dashboard": {
            "intel_summary": "காரியோஸ் நுண்ணறிவுச் சுருக்கம்", "karios_score": "காரியோஸ் மதிப்பெண்",
            "complete_profile": "சுயவிவரத்தைப் பூர்த்தி செய்க",
            "stats": {
                "active_schemes": "செயலில் உள்ள திட்டங்கள்", "total_investment": "மொத்த முதலீடு"
            }
        },
        "discovery": {
            "title": "திட்டக் கண்டுபிடிப்பு", "subtitle": "383+ திட்டங்களில் AI பொருத்தம்", 
            "filter_intel": "வடிகட்டி நுண்ணறிவு", "apply_filters": "வடிகட்டிகளைப் பயன்படுத்து",
            "primary_sector": "முதன்மைத் துறை", "state_region": "மாநிலம் / பிராந்தியம்", "entity_type": "நிறுவன வகை",
            "best_match": "சிறந்த பொருத்தம்", "deadline": "காலக்கெடு"
        },
        "profile": {
            "title": "உங்கள் நுண்ணறிவு சுயவிவரத்தை உருவாக்குங்கள்", "back": "முன்பு", "continue": "தொடரவும்", "required_error": "{{field}} தேவை."
        },
        "modal": {
            "intel_advisor": "திட்ட விவர உதவியாளர்", "official_portal": "அதிகாரப்பூர்வ போர்ட்டலை அணுகவும்",
            "quick_chips": {
                "eligibility": "தகுதி", "documents": "தேவையான ஆவணங்கள்", "apply": "விண்ணப்பிப்பது எப்படி", "benefits": "நன்மைகள்"
            }
        },
        "schemes": { k: {"name": v["ta"]} for k, v in SCHEME_VIRTUAL_DB.items() if "ta" in v }
    },
    "mr": { 
        "common": {"dashboard": "डॅशबोर्ड", "engine_online": "एआय इंजिन ऑनलाइन", "engine_offline": "इंजिन ऑफलाइन", "view_details": "तपशील पहा", "matches": "सामने", "clear_all": "सर्व साफ करा"},
        "schemes": {}
    },
    "kn": { 
        "common": {"dashboard": "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್", "engine_online": "AI ಎಂಜಿನ್ ಆನ್‌ಲೈನ್", "view_details": "ವಿವರಗಳನ್ನು ನೋಡಿ", "matches": "ಪಂದ್ಯಗಳು", "clear_all": "ಎಲ್ಲವನ್ನೂ ತೆರವುಗೊಳಿಸಿ"},
        "schemes": {}
    }
}

all_langs = ["en", "hi", "mr", "kn", "ta", "te", "bn", "gu", "ml", "or", "pa", "ur", "as", "sat", "ks", "ne"]

for lang in all_langs:
    target_dir = os.path.join(base_path, lang)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    file_path = os.path.join(target_dir, "translation.json")
    custom = translations.get(lang, {})
    
    final_data = {}
    for section, keys in en_template.items():
        if section == "schemes":
            # Populate all schemes, overriding with custom translations if available
            final_data["schemes"] = {}
            for sid, sdata in keys.items():
                final_data["schemes"][sid] = sdata.copy()
                if sid in custom.get("schemes", {}):
                    final_data["schemes"][sid].update(custom["schemes"][sid])
        else:
            final_data[section] = keys.copy()
            if section in custom:
                final_data[section].update(custom[section])
            
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

print(f"Updated {len(all_langs)} translation files with {len(master_schemes)} schemes each.")
