"""
Multilingual Internationalization (i18n) module for Connected Healthcare.
Provides maintainable, extensible dictionary-based translations across:
- English (en)
- Telugu (te — తెలుగు)
- Hindi (hi — हिन्दी)
"""

from typing import Dict, Any, List

AVAILABLE_LANGUAGES = {
    "en": "English",
    "te": "తెలుగు (Telugu)",
    "hi": "हिन्दी (Hindi)",
}

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # -------------------------------------------------------------------------
    # App Header & Global Navigation
    # -------------------------------------------------------------------------
    "app_title": {
        "en": "🏥 Connected Healthcare",
        "te": "🏥 కనెక్టెడ్ హెల్త్‌కేర్",
        "hi": "🏥 कनेक्टेड हेल्थकेयर",
    },
    "app_subtitle": {
        "en": "Hospital Demand Intelligence & Public Health Surveillance",
        "te": "ఆసుపత్రి డిమాండ్ విశ్లేషణ మరియు ప్రజారోగ్య పర్యవేక్షణ",
        "hi": "अस्पताल मांग विश्लेषण एवं सार्वजनिक स्वास्थ्य निगरानी",
    },
    "language_selector": {
        "en": "Language / భాష / भाषा",
        "te": "భాష / Language / भाषा",
        "hi": "भाषा / Language / భాష",
    },
    "experience_mode": {
        "en": "Dashboard Experience",
        "te": "డాష్‌బోర్డ్ రకం",
        "hi": "डैशबोर्ड प्रकार",
    },
    "mode_public": {
        "en": "👥 Public Dashboard (Citizen View)",
        "te": "👥 ప్రజా డాష్‌బోర్డ్ (పౌరుల వీక్షణ)",
        "hi": "👥 सार्वजनिक डैशबोर्ड (नागरिक दृश्य)",
    },
    "mode_developer": {
        "en": "🛠️ Developer / Admin Intelligence",
        "te": "🛠️ డెవలపర్ / అడ్మిన్ ఇంటెలిజెన్స్",
        "hi": "🛠️ डेवलपर / एडमिन इंटेलिजेंस",
    },
    "select_location": {
        "en": "📍 Select District / Location",
        "te": "📍 జిల్లా / ప్రాంతాన్ని ఎంచుకోండి",
        "hi": "📍 जिला / क्षेत्र चुनें",
    },
    "select_hospital": {
        "en": "🏥 Select Hospital Facility",
        "te": "🏥 ఆసుపత్రిని ఎంచుకోండి",
        "hi": "🏥 अस्पताल चुनें",
    },
    "last_updated": {
        "en": "Last observation updated",
        "te": "చివరి సమాచారం అప్‌డేట్",
        "hi": "अंतिम डेटा अपडेट",
    },

    # -------------------------------------------------------------------------
    # Situation Summary & Layman Explanation
    # -------------------------------------------------------------------------
    "situation_summary_title": {
        "en": "📋 Current Situation Overview",
        "te": "📋 ప్రస్తుత పరిస్థితి సమీక్ష",
        "hi": "📋 वर्तमान स्थिति सारांश",
    },
    "summary_normal": {
        "en": "At {hospital} ({location}), operations are currently running within normal historical limits. {crowd} people are waiting with an estimated consultation wait of {wait} minutes.",
        "te": "{hospital} ({location}) లో కార్యకలాపాలు ప్రస్తుతం సాధారణ పరిమితుల్లో ఉన్నాయి. {crowd} మంది వేచి ఉన్నారు, అంచనా వేచి ఉండే సమయం {wait} నిమిషాలు.",
        "hi": "{hospital} ({location}) में परिचालन सामान्य स्थिति में है। वर्तमान में {crowd} लोग प्रतीक्षारत हैं और अनुमानित प्रतीक्षा समय {wait} मिनट है।",
    },
    "summary_unusual": {
        "en": "At {hospital} ({location}), activity is busier than usual with {crowd} people waiting (typical baseline is ~{baseline}). Estimated wait time is approximately {wait} minutes.",
        "te": "{hospital} ({location}) లో సాధారణం కంటే ఎక్కువ రద్దీ ఉంది. ప్రస్తుతం {crowd} మంది వేచి ఉన్నారు (సాధారణంగా ~{baseline}). అంచనా నిరీక్షణ సమయం {wait} నిమిషాలు.",
        "hi": "{hospital} ({location}) में सामान्य से अधिक व्यस्तता है। वर्तमान में {crowd} लोग प्रतीक्षा कर रहे हैं (सामान्य औसत ~{baseline})। अनुमानित प्रतीक्षा समय लगभग {wait} मिनट है।",
    },
    "summary_spike": {
        "en": "Attention: High operational surge detected at {hospital} ({location}). {crowd} people waiting with elevated waiting times (~{wait} min). Staff and resources may be under strain.",
        "te": "గమనిక: {hospital} ({location}) లో అత్యధిక రద్దీ నమోదైంది. {crowd} మంది వేచి ఉన్నారు, వేచి ఉండే సమయం దాదాపు {wait} నిమిషాలు. సిబ్బందిపై ఒత్తిడి ఉండవచ్చు.",
        "hi": "सावधान: {hospital} ({location}) में अत्यधिक भीड़ दर्ज की गई है। {crowd} लोग प्रतीक्षारत हैं और प्रतीक्षा समय (~{wait} मिनट) काफी अधिक है।",
    },

    # -------------------------------------------------------------------------
    # Metric Cards & Descriptions
    # -------------------------------------------------------------------------
    "metric_people_waiting": {
        "en": "People Waiting",
        "te": "వేచి ఉన్న రోగులు",
        "hi": "प्रतीक्षारत मरीज",
    },
    "metric_people_waiting_desc": {
        "en": "Number of people recorded in the waiting room",
        "te": "ప్రస్తుతం నిరీక్షణ గదిలో ఉన్న రోగుల సంఖ్య",
        "hi": "प्रतीक्षा कक्ष में मौजूद मरीजों की संख्या",
    },
    "metric_waiting_time": {
        "en": "Estimated Waiting Time",
        "te": "అంచనా నిరీక్షణ సమయం",
        "hi": "अनुमानित प्रतीक्षा समय",
    },
    "metric_waiting_time_desc": {
        "en": "Estimated wait in minutes before consultation",
        "te": "డాక్టర్ పరిశీలనకు ముందు వేచి ఉండే అంచనా సమయం",
        "hi": "परामर्श से पहले अनुमानित प्रतीक्षा मिनट",
    },
    "metric_new_patients": {
        "en": "New Patient Arrivals",
        "te": "కొత్తగా వచ్చిన రోగులు",
        "hi": "नए मरीज आगमन",
    },
    "metric_new_patients_desc": {
        "en": "New patient registrations in the past hour",
        "te": "గడిచిన గంటలో నమోదైన కొత్త రోగులు",
        "hi": "पिछले एक घंटे में नए पंजीकृत मरीज",
    },
    "metric_discharged": {
        "en": "Discharged Patients",
        "te": "డిశ్చార్జ్ అయిన రోగులు",
        "hi": "डिस्चार्ज मरीज",
    },
    "metric_discharged_desc": {
        "en": "Treated patients discharged in the past hour",
        "te": "చికిత్స పూర్తయి విడుదలైన రోగులు",
        "hi": "उपचार के बाद डिस्चार्ज किए गए मरीज",
    },
    "metric_emergency": {
        "en": "Emergency Cases",
        "te": "అత్యవసర కేసులు",
        "hi": "आपातकालीन मामले",
    },
    "metric_emergency_desc": {
        "en": "Acute emergency triage admissions",
        "te": "తక్షణ చికిత్స అవసరమైన తీవ్ర కేసులు",
        "hi": "तत्काल उपचार आवश्यक गंभीर मामले",
    },
    "metric_predicted_crowd": {
        "en": "Expected Upcoming Crowd",
        "te": "రాబోయే అంచనా రద్దీ",
        "hi": "आगामी अपेक्षित भीड़",
    },
    "metric_predicted_crowd_desc": {
        "en": "Forecasted waiting room crowd for next hour",
        "te": "తరువాతి గంటకు అంచనా వేసిన రద్దీ స్థాయి",
        "hi": "अगले घंटे के लिए अनुमानित प्रतीक्षारत भीड़",
    },
    "metric_predicted_wait": {
        "en": "Expected Upcoming Wait",
        "te": "రాబోయే అంచనా నిరీక్షణ",
        "hi": "आगामी अपेक्षित प्रतीक्षा",
    },
    "metric_predicted_wait_desc": {
        "en": "Forecasted waiting time for next hour",
        "te": "తరువాతి గంటకు అంచనా వేసిన నిరీక్షణ సమయం",
        "hi": "अगले घंटे के लिए अनुमानित प्रतीक्षा समय",
    },

    # -------------------------------------------------------------------------
    # Status Badges & Alerts
    # -------------------------------------------------------------------------
    "status_normal": {
        "en": "🟢 Normal Hospital Activity",
        "te": "🟢 సాధారణ ఆసుపత్రి కార్యకలాపాలు",
        "hi": "🟢 सामान्य अस्पताल गतिविधि",
    },
    "status_unusual": {
        "en": "🟡 Busier Than Usual",
        "te": "🟡 సాధారణం కంటే ఎక్కువ రద్దీ",
        "hi": "🟡 सामान्य से अधिक व्यस्त",
    },
    "status_spike": {
        "en": "🔴 High Hospital Activity Spike",
        "te": "🔴 అత్యధిక ఆసుపత్రి రద్దీ హెచ్చరిక",
        "hi": "🔴 अत्यधिक अस्पताल गतिविधि",
    },
    "status_why": {
        "en": "Why was this status assigned?",
        "te": "ఈ స్థితి ఎందుకు నిర్ణయించబడింది?",
        "hi": "यह स्थिति क्यों निर्धारित की गई?",
    },
    "status_normal_reason": {
        "en": "All operational indicators are within normal historical ranges.",
        "te": "అన్ని కార్యాచరణ సూచికలు సాధారణ చారిత్రక పరిమితుల్లోనే ఉన్నాయి.",
        "hi": "सभी परिचालन संकेतक सामान्य ऐतिहासिक सीमा में हैं।",
    },

    # -------------------------------------------------------------------------
    # Comparisons & Charts
    # -------------------------------------------------------------------------
    "hospital_comparison_title": {
        "en": "🏢 Hospital Activity Comparison",
        "te": "🏢 ఆసుపత్రుల కార్యకలాపాల పోలిక",
        "hi": "🏢 अस्पताल गतिविधि तुलना",
    },
    "hospital_comparison_desc": {
        "en": "Compare waiting times and crowd pressure across local hospitals in this district.",
        "te": "ఈ జిల్లాలోని ఆసుపత్రుల రద్దీ మరియు వేచి ఉండే సమయాన్ని పోల్చండి.",
        "hi": "इस जिले के अस्पतालों में भीड़ और प्रतीक्षा समय की तुलना करें।",
    },
    "trend_chart_title": {
        "en": "📈 Crowd & Waiting Time Trends",
        "te": "📈 రద్దీ మరియు వేచి ఉండే సమయ పోకడలు",
        "hi": "📈 भीड़ और प्रतीक्षा समय रुझान",
    },
    "trend_chart_desc": {
        "en": "Historical observations over the past 48 operational hours.",
        "te": "గడిచిన 48 గంటల చారిత్రక పరిశీలనలు.",
        "hi": "पिछले 48 परिचालन घंटों के ऐतिहासिक अवलोकन।",
    },
    "health_pulse_title": {
        "en": "🩺 Community Health Condition Trends",
        "te": "🩺 సమాజ ఆరోగ్య పరిస్థితుల పోకడలు",
        "hi": "🩺 सामुदायिक स्वास्थ्य स्थिति रुझान",
    },
    "health_pulse_desc": {
        "en": "Reported health condition counts over time in this district. Reported trends provide situational awareness and do not determine individual clinical diagnoses.",
        "te": "ఈ జిల్లాలో నమోదైన వ్యాధుల వివరాలు. ఇవి సమాచారం కొరకు మాత్రమే, వైద్య నిర్ధారణ కాదు.",
        "hi": "इस जिले में दर्ज बीमारियों के रुझान। यह केवल जानकारी के लिए है, कोई चिकित्सकीय निदान नहीं।",
    },

    # -------------------------------------------------------------------------
    # Buttons & Controls
    # -------------------------------------------------------------------------
    "btn_simulate_hour": {
        "en": "🎲 Simulate Next Hour",
        "te": "🎲 తరువాతి గంటను అనుకరించండి",
        "hi": "🎲 अगले घंटे का सिमुलेशन करें",
    },
    "btn_refresh": {
        "en": "🔄 Refresh Dashboard",
        "te": "🔄 డాష్‌బోర్డ్ రీఫ్రెష్ చేయండి",
        "hi": "🔄 डैशबोर्ड रीफ्रेश करें",
    },
    "btn_save_observation": {
        "en": "💾 Save Observation",
        "te": "💾 పరిశీలనను భద్రపరచండి",
        "hi": "💾 अवलोकन सहेजें",
    },

    # -------------------------------------------------------------------------
    # Disclaimers & Notices
    # -------------------------------------------------------------------------
    "disclaimer_title": {
        "en": "Medical Disclaimer & Transparency Notice",
        "te": "వైద్యపరమైన నిరాకరణ మరియు పారదర్శకత ప్రకటన",
        "hi": "चिकित्सकीय अस्वीकरण एवं पारदर्शिता सूचना",
    },
    "disclaimer_text": {
        "en": "This application is a hospital operations decision-support and planning demonstration tool. It is NOT an autonomous medical diagnostic system or a substitute for professional healthcare consultation.",
        "te": "ఈ అప్లికేషన్ కేవలం ఆసుపత్రి ప్రణాళిక మరియు నిర్ణయ సహాయక ప్రదర్శన సాధనం మాత్రమే. ఇది స్వయంప్రతిపత్త వైద్య నిర్ధారణ లేదా డాక్టర్ సలహాకు ప్రత్యామ్నాయం కాదు.",
        "hi": "यह एप्लिकेशन केवल अस्पताल योजना और निर्णय-सहायता प्रदर्शन उपकरण है। यह कोई स्वायत्त नैदानिक प्रणाली या पेशेवर चिकित्सकीय सलाह का विकल्प नहीं है।",
    },
    "synthetic_notice": {
        "en": "Demonstration Project: Current operational and public health records are simulated demonstration data.",
        "te": "ప్రదర్శన ప్రాజెక్ట్: ప్రస్తుత ఆసుపత్రి మరియు ఆరోగ్య రికార్డులు డెమో కోసం రూపొందించబడిన అనుకరణ సమాచారం.",
        "hi": "प्रदर्शन परियोजना: वर्तमान परिचालन और स्वास्थ्य रिकॉर्ड प्रदर्शन के लिए सिम्युलेटेड डेटा हैं।",
    },

    # -------------------------------------------------------------------------
    # Units & Conditions
    # -------------------------------------------------------------------------
    "unit_minutes": {
        "en": "minutes",
        "te": "నిమిషాలు",
        "hi": "मिनट",
    },
    "unit_patients": {
        "en": "patients",
        "te": "రోగులు",
        "hi": "मरीज",
    },
    "cond_fever": {
        "en": "Fever",
        "te": "జ్వరం (Fever)",
        "hi": "बुखार (Fever)",
    },
    "cond_respiratory": {
        "en": "Respiratory Infection",
        "te": "శ్వాసకోశ ఇన్ఫెక్షన్ (Respiratory)",
        "hi": "श्वसन संक्रमण (Respiratory)",
    },
    "cond_dengue": {
        "en": "Dengue",
        "te": "డెంగ్యూ (Dengue)",
        "hi": "डेंगू (Dengue)",
    },
    "cond_diabetes": {
        "en": "Diabetes",
        "te": "మధుమేహం (Diabetes)",
        "hi": "मधुमेह (Diabetes)",
    },
}


def t(key: str, lang: str = "en", **kwargs: Any) -> str:
    """
    Retrieves the translated string for the given key and language.
    Falls back gracefully to English if the key or language is not found.
    Interpolates any provided kwargs.
    """
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key

    text = entry.get(lang) or entry.get("en", key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


def get_available_languages() -> Dict[str, str]:
    """Returns mapping of language code to display name."""
    return AVAILABLE_LANGUAGES
