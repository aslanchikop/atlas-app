"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                          🛰️ ATLAS v21 FULL EDITION                          ║
║            Autonomous Terrestrial Life Analysis System                       ║
║                   NASA-Inspired Design • Full Features                       ║
║                        Diploma Project 2024-2025                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import requests
import math
import json
import time
import random
import base64
import os
from datetime import datetime

# Optional ML imports
try:
    import joblib
    chatbot_model = joblib.load('exo_chatbot_model.pkl')
    with open('exo_chatbot_responses.json', 'r', encoding='utf-8') as f:
        chatbot_responses = json.load(f)
    CHATBOT_AVAILABLE = True
except:
    chatbot_model = None
    chatbot_responses = {}
    CHATBOT_AVAILABLE = False

try:
    from streamlit_js_eval import streamlit_js_eval
    JS_EVAL_AVAILABLE = True
except:
    JS_EVAL_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="ATLAS • Exoplanet Research",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE DEFAULTS
# ═══════════════════════════════════════════════════════════════════════════════
DEFAULTS = {
    'lang': 'en',
    'current_page': 'home',
    'quote_index': 0,
    'last_quote_time': time.time(),
    'saved_systems': {},
    'current_planets': [],
    'current_star': None,
    'current_system': None,
    'selected_planet': 0,
    'scanned_stars': [],
    'custom_planets': {},
    'compare': [],
    'chat_history': [],
    'achievements': {},
    'achievements_queue': [],
    'mission_log': [],
    'habitable_count': 0,
    'recommendations': [],
    'hypotheses': [],
    'presentation_mode': False,
    'current_slide': 0,
    'travel_progress': 0,
    'initialized': False
}

for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ═══════════════════════════════════════════════════════════════════════════════
# TRANSLATIONS (EN/KZ ONLY)
# ═══════════════════════════════════════════════════════════════════════════════
TRANSLATIONS = {
    # Navigation
    'nav_home': {'en': 'HOME', 'kz': 'БАСТЫ'},
    'nav_explore': {'en': 'EXPLORE', 'kz': 'ЗЕРТТЕУ'},
    'nav_analysis': {'en': 'ANALYSIS', 'kz': 'ТАЛДАУ'},
    'nav_encyclopedia': {'en': 'REFERENCE', 'kz': 'АНЫҚТАМА'},
    'nav_about': {'en': 'ABOUT', 'kz': 'ТУРАЛЫ'},
    
    # Hero
    'hero_subtitle': {'en': 'Autonomous Terrestrial Life Analysis System', 'kz': 'Автономды Жердегі Өмірді Талдау Жүйесі'},
    'hero_cta': {'en': 'START EXPLORING', 'kz': 'ЗЕРТТЕУДІ БАСТАУ'},
    
    # Stats
    'stat_systems': {'en': 'SYSTEMS', 'kz': 'ЖҮЙЕЛЕР'},
    'stat_habitable': {'en': 'HABITABLE', 'kz': 'МЕКЕНДЕУГЕ'},
    'stat_planets': {'en': 'PLANETS', 'kz': 'ПЛАНЕТАЛАР'},
    
    # Explore tabs
    'tab_missions': {'en': '🚀 Missions', 'kz': '🚀 Миссиялар'},
    'tab_system': {'en': '🪐 System', 'kz': '🪐 Жүйе'},
    'tab_starmap': {'en': '🗺️ Map', 'kz': '🗺️ Карта'},
    'tab_compare': {'en': '📊 Compare', 'kz': '📊 Салыстыру'},
    'tab_travel': {'en': '🚀 Travel', 'kz': '🚀 Ұшу'},
    'tab_history': {'en': '📜 History', 'kz': '📜 Тарих'},
    'tab_chat': {'en': '🤖 AI Chat', 'kz': '🤖 AI Чат'},
    'tab_presentation': {'en': '🎬 Present', 'kz': '🎬 Көрсету'},
    
    # Mission Control
    'mission_control': {'en': 'Mission Control', 'kz': 'Миссия орталығы'},
    'select_catalog': {'en': 'Select Catalog', 'kz': 'Каталогты таңдаңыз'},
    'scan_star': {'en': 'Scan Star System', 'kz': 'Жұлдыз жүйесін сканерлеу'},
    'scanning': {'en': 'Scanning...', 'kz': 'Сканерлеу...'},
    'scan_complete': {'en': 'Scan Complete!', 'kz': 'Сканерлеу аяқталды!'},
    'planets_found': {'en': 'planets found', 'kz': 'планета табылды'},
    'no_planets': {'en': 'No planets found', 'kz': 'Планета табылмады'},
    'mission_log': {'en': 'Mission Log', 'kz': 'Миссия журналы'},
    'progress': {'en': 'Progress', 'kz': 'Барысы'},
    
    # System View
    'system_view': {'en': 'System View', 'kz': 'Жүйе көрінісі'},
    'no_system': {'en': 'No system loaded. Run a mission first!', 'kz': 'Жүйе жүктелмеген. Алдымен миссия жүргізіңіз!'},
    'planet_details': {'en': 'Planet Details', 'kz': 'Планета мәліметтері'},
    'habitability': {'en': 'Habitability Score', 'kz': 'Мекендеуге жарамдылық бағасы'},
    'in_hz': {'en': 'In Habitable Zone', 'kz': 'Мекендеуге жарамды аймақта'},
    'outside_hz': {'en': 'Outside Habitable Zone', 'kz': 'Мекендеуге жарамды аймақтан тыс'},
    
    # Parameters
    'radius': {'en': 'Radius', 'kz': 'Радиус'},
    'mass': {'en': 'Mass', 'kz': 'Масса'},
    'temperature': {'en': 'Temperature', 'kz': 'Температура'},
    'orbital_period': {'en': 'Orbital Period', 'kz': 'Орбиталық период'},
    'distance': {'en': 'Distance', 'kz': 'Қашықтық'},
    'gravity': {'en': 'Gravity', 'kz': 'Гравитация'},
    'density': {'en': 'Density', 'kz': 'Тығыздық'},
    'escape_velocity': {'en': 'Escape Velocity', 'kz': 'Қашу жылдамдығы'},
    'year_length': {'en': 'Year Length', 'kz': 'Жыл ұзақтығы'},
    'day_length': {'en': 'Day Length', 'kz': 'Күн ұзақтығы'},
    
    # Analysis
    'atmosphere': {'en': 'Atmosphere', 'kz': 'Атмосфера'},
    'hazards': {'en': 'Hazards', 'kz': 'Қауіптер'},
    'biosignatures': {'en': 'Biosignature Potential', 'kz': 'Биоқолтаңба әлеуеті'},
    'magnetic_field': {'en': 'Magnetic Field', 'kz': 'Магнит өрісі'},
    'moons': {'en': 'Estimated Moons', 'kz': 'Болжамды серіктер'},
    
    # Compare
    'compare_title': {'en': 'Planet Comparison', 'kz': 'Планеталарды салыстыру'},
    'add_compare': {'en': 'Add to Compare', 'kz': 'Салыстыруға қосу'},
    'clear_selection': {'en': 'Clear All', 'kz': 'Барлығын өшіру'},
    'select_planets': {'en': 'Select planets to compare', 'kz': 'Салыстыру үшін планеталарды таңдаңыз'},
    'radar_chart': {'en': 'Radar Chart', 'kz': 'Радар диаграммасы'},
    'bar_chart': {'en': 'Bar Chart', 'kz': 'Бағандық диаграмма'},
    
    # Travel
    'travel_title': {'en': 'Interstellar Travel Simulator', 'kz': 'Жұлдызаралық саяхат симуляторы'},
    'destination': {'en': 'Destination', 'kz': 'Мақсат'},
    'velocity': {'en': 'Velocity', 'kz': 'Жылдамдық'},
    'distance_ly': {'en': 'Distance (ly)', 'kz': 'Қашықтық (жж)'},
    'earth_time': {'en': 'Earth Time', 'kz': 'Жер уақыты'},
    'ship_time': {'en': 'Ship Time', 'kz': 'Кеме уақыты'},
    'lorentz': {'en': 'Time Dilation', 'kz': 'Уақыт кеңеюі'},
    'fuel': {'en': 'Fuel Required', 'kz': 'Қажетті отын'},
    'mission_params': {'en': 'Mission Parameters', 'kz': 'Миссия параметрлері'},
    'journey_preview': {'en': 'Journey Visualization', 'kz': 'Саяхатты бейнелеу'},
    'phases': {'en': 'Mission Phases', 'kz': 'Миссия кезеңдері'},
    
    # Encyclopedia
    'encyclopedia_title': {'en': 'Reference Guide', 'kz': 'Анықтамалық'},
    'topic_stars': {'en': '⭐ Star Types', 'kz': '⭐ Жұлдыз түрлері'},
    'topic_planets': {'en': '🪐 Planet Types', 'kz': '🪐 Планета түрлері'},
    'topic_habitability': {'en': '🌱 Habitability', 'kz': '🌱 Мекендеуге жарамдылық'},
    'topic_detection': {'en': '🔭 Detection Methods', 'kz': '🔭 Анықтау әдістері'},
    'topic_missions': {'en': '🛰️ Space Missions', 'kz': '🛰️ Ғарыш миссиялары'},
    
    # History
    'history_title': {'en': 'Research History', 'kz': 'Зерттеу тарихы'},
    'history_empty': {'en': 'No research history yet', 'kz': 'Зерттеу тарихы әлі жоқ'},
    'load_system': {'en': 'Load', 'kz': 'Жүктеу'},
    
    # Chat
    'chat_title': {'en': 'AI Assistant', 'kz': 'AI Көмекші'},
    'chat_placeholder': {'en': 'Ask about exoplanets...', 'kz': 'Экзопланеталар туралы сұраңыз...'},
    'chat_send': {'en': 'Send', 'kz': 'Жіберу'},
    'chat_unavailable': {'en': 'AI Chat requires model files', 'kz': 'AI чат модель файлдарын қажет етеді'},
    
    # Presentation
    'presentation_title': {'en': 'Presentation Mode', 'kz': 'Презентация режимі'},
    'start_presentation': {'en': 'Start Presentation', 'kz': 'Презентацияны бастау'},
    'stop_presentation': {'en': 'Exit Presentation', 'kz': 'Презентациядан шығу'},
    
    # Analysis Page
    'analysis_title': {'en': 'Research Analytics', 'kz': 'Зерттеу аналитикасы'},
    'generate_analysis': {'en': 'Generate Analysis', 'kz': 'Талдау жасау'},
    'recommendations': {'en': 'Recommendations', 'kz': 'Ұсыныстар'},
    'hypotheses': {'en': 'Scientific Hypotheses', 'kz': 'Ғылыми болжамдар'},
    'no_data_analysis': {'en': 'Explore at least 2 systems for analysis', 'kz': 'Талдау үшін кем дегенде 2 жүйені зерттеңіз'},
    
    # About
    'about_title': {'en': 'About ATLAS', 'kz': 'ATLAS туралы'},
    'about_desc': {
        'en': '''ATLAS (Autonomous Terrestrial Life Analysis System) is a comprehensive 
        exoplanet research platform designed to analyze potentially habitable worlds beyond our solar system.
        
        **Features:**
        - Real-time NASA Exoplanet Archive integration
        - Advanced habitability scoring algorithm
        - Interactive 3D star maps
        - AI-powered planet analysis
        - Interstellar travel simulation
        
        **Data Source:** NASA Exoplanet Archive TAP Service
        
        **Technology:** Streamlit, Plotly, Scikit-learn, NASA API''',
        'kz': '''ATLAS (Автономды Жердегі Өмірді Талдау Жүйесі) - біздің күн жүйесінен тыс 
        мекендеуге жарамды әлемдерді талдауға арналған экзопланеталарды зерттеу платформасы.
        
        **Мүмкіндіктері:**
        - NASA Exoplanet Archive интеграциясы
        - Мекендеуге жарамдылықты бағалау алгоритмі
        - Интерактивті 3D жұлдыз карталары
        - AI планета талдауы
        - Жұлдызаралық саяхат симуляциясы
        
        **Деректер көзі:** NASA Exoplanet Archive TAP Service
        
        **Технологиялар:** Streamlit, Plotly, Scikit-learn, NASA API'''
    },
    
    # Achievements
    'achievements_title': {'en': 'Achievements', 'kz': 'Жетістіктер'},
    'achievement_unlocked': {'en': 'Achievement Unlocked!', 'kz': 'Жетістік ашылды!'},
}

def t(key):
    """Get translation for current language."""
    lang = st.session_state.get('lang', 'en')
    if key in TRANSLATIONS:
        return TRANSLATIONS[key].get(lang, TRANSLATIONS[key].get('en', key))
    return key

# ═══════════════════════════════════════════════════════════════════════════════
# HERO QUOTES
# ═══════════════════════════════════════════════════════════════════════════════
QUOTES = [
    {
        'text': {'en': "The cosmos is within us. We are made of star-stuff.", 'kz': "Ғарыш біздің ішімізде. Біз жұлдыз материясынан жасалғанбыз."},
        'author': "Carl Sagan"
    },
    {
        'text': {'en': "Somewhere, something incredible is waiting to be known.", 'kz': "Бір жерде керемет нәрсе табылуды күтуде."},
        'author': "Carl Sagan"
    },
    {
        'text': {'en': "The universe is under no obligation to make sense to you.", 'kz': "Ғалам сізге түсінікті болуға міндетті емес."},
        'author': "Neil deGrasse Tyson"
    },
    {
        'text': {'en': "We are a way for the cosmos to know itself.", 'kz': "Біз ғаламның өзін тануының жолымыз."},
        'author': "Carl Sagan"
    },
    {
        'text': {'en': "The Earth is the cradle of humanity, but one cannot live in a cradle forever.", 'kz': "Жер - адамзаттың бесігі, бірақ бесікте мәңгі өмір сүруге болмайды."},
        'author': "Konstantin Tsiolkovsky"
    },
    {
        'text': {'en': "For small creatures such as we, the vastness is bearable only through love.", 'kz': "Біз сияқты кішкентай жандар үшін шексіздікті тек махаббат арқылы көтеруге болады."},
        'author': "Carl Sagan"
    },
    {
        'text': {'en': "The important thing is not to stop questioning.", 'kz': "Маңыздысы - сұрақ қоюды тоқтатпау."},
        'author': "Albert Einstein"
    }
]

# ═══════════════════════════════════════════════════════════════════════════════
# STAR CATALOGS
# ═══════════════════════════════════════════════════════════════════════════════
CATALOGS = {
    'nearby': {
        'name': {'en': '🌟 Nearby Stars (<50 ly)', 'kz': '🌟 Жақын жұлдыздар (<50 жж)'},
        'stars': ['Proxima Centauri', 'TRAPPIST-1', 'LHS 1140', 'Ross 128', 'Wolf 1061', 
                  'Luyten b', 'Tau Ceti', 'Epsilon Eridani', 'Lacaille 9352', 'Gliese 667 C',
                  'Gliese 581', 'Gliese 876', 'Gliese 436', 'Gliese 1214', 'Gliese 3470']
    },
    'kepler': {
        'name': {'en': '🔭 Kepler Discoveries', 'kz': '🔭 Kepler жаңалықтары'},
        'stars': ['Kepler-442', 'Kepler-452', 'Kepler-186', 'Kepler-62', 'Kepler-22',
                  'Kepler-69', 'Kepler-438', 'Kepler-296', 'Kepler-440', 'Kepler-443',
                  'Kepler-1649', 'Kepler-1652', 'Kepler-283', 'Kepler-1410', 'Kepler-1544']
    },
    'tess': {
        'name': {'en': '🛰️ TESS Discoveries', 'kz': '🛰️ TESS жаңалықтары'},
        'stars': ['TOI-700', 'TOI-1231', 'TOI-270', 'TOI-1452', 'TOI-715',
                  'TOI-561', 'TOI-674', 'TOI-1338', 'TOI-1233', 'TOI-178',
                  'TOI-540', 'TOI-1693', 'TOI-1695', 'TOI-1266', 'TOI-2095']
    },
    'habitable': {
        'name': {'en': '🌱 HZ Candidates', 'kz': '🌱 МЖА үміткерлері'},
        'stars': ['K2-18', 'LHS 1140', 'TOI-700', 'Kepler-442', 'Kepler-1649',
                  'TRAPPIST-1', 'Proxima Centauri', 'Teegarden\'s Star', 'GJ 357',
                  'K2-72', 'K2-3', 'K2-155', 'HD 40307', 'HD 85512', 'Gliese 163']
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# KNOWN REFERENCE PLANETS
# ═══════════════════════════════════════════════════════════════════════════════
KNOWN_PLANETS = {
    '🌍 Earth': {'radius': 1.0, 'mass': 1.0, 'temp': 288, 'esi': 1.0, 'gravity': 1.0, 'distance': 0, 'emoji': '🌍'},
    '🔴 Mars': {'radius': 0.53, 'mass': 0.107, 'temp': 210, 'esi': 0.64, 'gravity': 0.38, 'distance': 0, 'emoji': '🔴'},
    '🟤 Venus': {'radius': 0.95, 'mass': 0.815, 'temp': 737, 'esi': 0.44, 'gravity': 0.91, 'distance': 0, 'emoji': '🟤'},
    '🪐 Jupiter': {'radius': 11.2, 'mass': 317.8, 'temp': 165, 'esi': 0.29, 'gravity': 2.36, 'distance': 0, 'emoji': '🪐'}
}

# ═══════════════════════════════════════════════════════════════════════════════
# ACHIEVEMENTS SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
ACHIEVEMENTS = {
    'first_scan': {
        'name': {'en': 'First Contact', 'kz': 'Алғашқы байланыс'},
        'desc': {'en': 'Scan your first star system', 'kz': 'Алғашқы жұлдыз жүйесін сканерлеңіз'},
        'icon': '🔭'
    },
    'explorer_5': {
        'name': {'en': 'Star Explorer', 'kz': 'Жұлдыз зерттеушісі'},
        'desc': {'en': 'Explore 5 star systems', 'kz': '5 жұлдыз жүйесін зерттеңіз'},
        'icon': '⭐'
    },
    'explorer_10': {
        'name': {'en': 'Cosmic Voyager', 'kz': 'Ғарыш саяхатшысы'},
        'desc': {'en': 'Explore 10 star systems', 'kz': '10 жұлдыз жүйесін зерттеңіз'},
        'icon': '🚀'
    },
    'habitable_found': {
        'name': {'en': 'Life Seeker', 'kz': 'Өмір іздеуші'},
        'desc': {'en': 'Find a planet in the habitable zone', 'kz': 'Мекендеуге жарамды аймақтан планета табыңыз'},
        'icon': '🌱'
    },
    'habitable_5': {
        'name': {'en': 'Habitability Hunter', 'kz': 'Мекендеуге жарамдылық аңшысы'},
        'desc': {'en': 'Find 5 habitable zone planets', 'kz': '5 мекендеуге жарамды планета табыңыз'},
        'icon': '🌿'
    },
    'earth_twin': {
        'name': {'en': 'Earth Twin', 'kz': 'Жердің егізі'},
        'desc': {'en': 'Find a planet with ESI > 0.8', 'kz': 'ESI > 0.8 планета табыңыз'},
        'icon': '🌍'
    },
    'giant_hunter': {
        'name': {'en': 'Giant Hunter', 'kz': 'Алып аңшысы'},
        'desc': {'en': 'Find a gas giant (>6 R⊕)', 'kz': 'Газ алыбын табыңыз (>6 R⊕)'},
        'icon': '🪐'
    },
    'mini_world': {
        'name': {'en': 'Mini World', 'kz': 'Шағын әлем'},
        'desc': {'en': 'Find a sub-Earth (<0.8 R⊕)', 'kz': 'Суб-Жерді табыңыз (<0.8 R⊕)'},
        'icon': '🔴'
    },
    'catalog_complete': {
        'name': {'en': 'Catalog Master', 'kz': 'Каталог шебері'},
        'desc': {'en': 'Complete scanning a full catalog', 'kz': 'Каталогты толық сканерлеңіз'},
        'icon': '📚'
    },
    'score_90': {
        'name': {'en': 'Prime Candidate', 'kz': 'Басты үміткер'},
        'desc': {'en': 'Find a planet with 90+ habitability score', 'kz': '90+ мекендеуге жарамдылық бағасы бар планета табыңыз'},
        'icon': '🏆'
    },
    'multi_planet': {
        'name': {'en': 'System Surveyor', 'kz': 'Жүйе зерттеушісі'},
        'desc': {'en': 'Find a system with 5+ planets', 'kz': '5+ планетасы бар жүйе табыңыз'},
        'icon': '🌌'
    },
    'compare_3': {
        'name': {'en': 'Analyst', 'kz': 'Талдаушы'},
        'desc': {'en': 'Compare 3 planets', 'kz': '3 планетаны салыстырыңыз'},
        'icon': '📊'
    },
    'traveler': {
        'name': {'en': 'Space Traveler', 'kz': 'Ғарыш саяхатшысы'},
        'desc': {'en': 'Simulate interstellar travel', 'kz': 'Жұлдызаралық саяхатты модельдеңіз'},
        'icon': '✈️'
    },
    'chat_10': {
        'name': {'en': 'Curious Mind', 'kz': 'Қызықты ақыл'},
        'desc': {'en': 'Ask AI assistant 10 questions', 'kz': 'AI көмекшісіне 10 сұрақ қойыңыз'},
        'icon': '🤖'
    },
    'presenter': {
        'name': {'en': 'Presenter', 'kz': 'Баяндамашы'},
        'desc': {'en': 'Complete a presentation', 'kz': 'Презентацияны аяқтаңыз'},
        'icon': '🎬'
    }
}

def check_achievement(achievement_id):
    """Check and unlock an achievement."""
    if achievement_id not in st.session_state.achievements:
        st.session_state.achievements[achievement_id] = True
        st.session_state.achievements_queue.append(achievement_id)
        return True
    return False

def get_unlocked_count():
    """Get count of unlocked achievements."""
    return len(st.session_state.achievements)
# ═══════════════════════════════════════════════════════════════════════════════
# BACKGROUND IMAGE LOADER
# ═══════════════════════════════════════════════════════════════════════════════
def load_background_base64(filename):
    """Load background image as base64."""
    paths = [filename, f'./{filename}', f'/home/claude/{filename}', f'/mnt/user-data/uploads/{filename}']
    for path in paths:
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return base64.b64encode(f.read()).decode()
    return None

# ═══════════════════════════════════════════════════════════════════════════════
# NASA-INSPIRED CSS STYLES
# ═══════════════════════════════════════════════════════════════════════════════

def get_nasa_css(bg_base64=None):
    """Generate NASA-inspired CSS with fullscreen background."""
    
    if bg_base64:
        bg_style = f"""
        html, body, .stApp, [data-testid="stAppViewContainer"] {{
            background-image: url('data:image/png;base64,{bg_base64}') !important;
            background-size: cover !important;
            background-position: center center !important;
            background-repeat: no-repeat !important;
            background-attachment: fixed !important;
            min-height: 100vh !important;
            width: 100% !important;
        }}
        .stApp::before {{
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, rgba(0,0,0,0.5) 0%, rgba(0,20,40,0.3) 50%, rgba(0,0,0,0.2) 100%);
            pointer-events: none;
            z-index: 0;
        }}
        """
    else:
        bg_style = """
        .stApp {
            background: linear-gradient(180deg, #0a0f1a 0%, #1a1f2e 50%, #0d1520 100%) !important;
            min-height: 100vh !important;
        }
        """
    
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    
    /* RESET & FULLSCREEN */
    * {{ box-sizing: border-box; }}
    
    html, body {{
        margin: 0 !important;
        padding: 0 !important;
        min-height: 100vh !important;
        overflow-x: hidden;
    }}
    
    {bg_style}
    
    /* Hide Streamlit defaults */
    #MainMenu, header, footer, .stDeployButton {{display: none !important;}}
    [data-testid="stSidebar"] {{display: none !important;}}
    .stApp > header {{display: none !important;}}
    [data-testid="stHeader"] {{display: none !important;}}
    .stAppHeader {{display: none !important;}}
    div[data-testid="stToolbar"] {{display: none !important;}}
    div[data-testid="stDecoration"] {{display: none !important;}}
    
    /* Main content */
    .main .block-container,
    [data-testid="stMainBlockContainer"] {{
        padding: 1rem 2rem !important;
        max-width: 100% !important;
    }}
    
    /* ═══════════════════════════════════════════════════════════════════════════════ */
    /* GLASSMORPHISM CARDS */
    /* ═══════════════════════════════════════════════════════════════════════════════ */
    
    .glass-card {{
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 30px;
        margin: 15px 0;
    }}
    
    .page-container {{
        padding: 20px 0;
        position: relative;
        z-index: 1;
    }}
    
    .page-title {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: white;
        margin-bottom: 30px;
        text-shadow: 2px 2px 20px rgba(0,0,0,0.3);
    }}
    
    /* ═══════════════════════════════════════════════════════════════════════════════ */
    /* STATS BAR */
    /* ═══════════════════════════════════════════════════════════════════════════════ */
    
    .stats-bar {{
        position: fixed;
        bottom: 30px;
        left: 30px;
        display: flex;
        gap: 40px;
        z-index: 100;
    }}
    
    .stat-item {{
        text-align: left;
    }}
    
    .stat-number {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.8rem;
        font-weight: 600;
        color: white;
        line-height: 1;
        text-shadow: 2px 2px 20px rgba(0,0,0,0.5);
    }}
    
    .stat-label {{
        font-family: 'Inter', sans-serif;
        font-size: 0.7rem;
        color: rgba(255,255,255,0.5);
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 5px;
    }}
    
    /* ═══════════════════════════════════════════════════════════════════════════════ */
    /* STREAMLIT OVERRIDES */
    /* ═══════════════════════════════════════════════════════════════════════════════ */
    
    /* Make all text white */
    .stMarkdown, .stMarkdown p, .stMarkdown span, 
    .stText, label, .stRadio label {{
        color: white !important;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: rgba(255,255,255,0.05);
        padding: 8px;
        border-radius: 15px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        color: rgba(255,255,255,0.6);
        border-radius: 10px;
        padding: 10px 20px;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: rgba(212,165,116,0.3) !important;
        color: #d4a574 !important;
    }}
    
    /* Buttons */
    .stButton > button {{
        font-family: 'Inter', sans-serif;
        border-radius: 10px;
        transition: all 0.3s ease;
    }}
    
    /* Primary button orange style */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {{
        background: linear-gradient(135deg, #d4a574 0%, #c49464 100%) !important;
        border: none !important;
        color: #1a1a1a !important;
    }}
    
    /* Secondary button */
    .stButton > button[kind="secondary"],
    .stButton > button[data-testid="baseButton-secondary"] {{
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        color: white !important;
    }}
    
    /* Inputs */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stMultiSelect > div {{
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: white !important;
        border-radius: 10px !important;
    }}
    
    /* Metrics */
    [data-testid="stMetricValue"] {{
        color: white !important;
        font-family: 'Space Grotesk', sans-serif;
    }}
    
    [data-testid="stMetricLabel"] {{
        color: rgba(255,255,255,0.6) !important;
    }}
    
    /* Expanders */
    .streamlit-expanderHeader {{
        background: rgba(255,255,255,0.05) !important;
        border-radius: 10px !important;
        color: white !important;
    }}
    
    /* Achievement popup */
    .achievement-popup {{
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #2d5a27 0%, #1e3d1a 100%);
        border: 3px solid #5a9c4e;
        border-radius: 8px;
        padding: 15px 20px;
        display: flex;
        align-items: center;
        gap: 15px;
        z-index: 100000;
        animation: achievementSlide 0.5s ease-out;
        box-shadow: 0 5px 30px rgba(0,0,0,0.5);
    }}
    
    @keyframes achievementSlide {{
        from {{ transform: translateX(100%); opacity: 0; }}
        to {{ transform: translateX(0); opacity: 1; }}
    }}
    
    .achievement-icon {{ font-size: 2rem; }}
    .achievement-label {{ font-size: 0.7rem; color: #ffff00; text-transform: uppercase; }}
    .achievement-name {{ font-size: 1rem; color: white; font-weight: bold; }}
    
    /* Footer */
    .atlas-footer {{
        background: rgba(0,0,0,0.3);
        padding: 40px;
        text-align: center;
        margin-top: 50px;
        border-top: 1px solid rgba(255,255,255,0.1);
    }}
    
    .footer-logo {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: #d4a574;
        margin-bottom: 10px;
    }}
    
    .atlas-footer p {{ color: rgba(255,255,255,0.5); font-size: 0.85rem; }}
    
    /* Scrollbar */
    ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
    ::-webkit-scrollbar-track {{ background: rgba(255,255,255,0.05); }}
    ::-webkit-scrollbar-thumb {{ background: rgba(212,165,116,0.5); border-radius: 4px; }}
    </style>
    """

def calc_luminosity(teff, rad):
    """Calculate stellar luminosity in solar units."""
    return (rad ** 2) * ((teff / 5778) ** 4)

def calc_equilibrium_temp(teff, srad, orbit, albedo=0.3):
    """Calculate planetary equilibrium temperature."""
    r_au = srad * 0.00465047
    return teff * math.sqrt(r_au / (2 * orbit)) * ((1 - albedo) ** 0.25)

def calc_orbit_from_period(period, stellar_mass=1.0):
    """Calculate orbital distance from period using Kepler's law."""
    return ((period / 365.25) ** 2 * stellar_mass) ** (1/3)

def calc_habitable_zone(teff, srad, luminosity=None):
    """Calculate conservative habitable zone boundaries."""
    if luminosity is None:
        luminosity = calc_luminosity(teff, srad)
    L = luminosity
    inner = 0.75 * math.sqrt(L)
    outer = 1.77 * math.sqrt(L)
    return inner, outer

def calc_esi(radius, temp):
    """Calculate Earth Similarity Index."""
    esi_r = 1 - abs(radius - 1) / (radius + 1)
    esi_t = 1 - abs(temp - 288) / (temp + 288)
    esi_r = max(0, min(1, esi_r)) ** 0.57
    esi_t = max(0, min(1, esi_t)) ** 5.58
    return round(math.sqrt(esi_r * esi_t), 3)

def calc_surface_gravity(mass, radius):
    """Calculate surface gravity in Earth g."""
    if radius <= 0 or mass <= 0:
        return 0
    return mass / (radius ** 2)

def calc_density(mass, radius):
    """Calculate density in Earth units."""
    if radius <= 0:
        return 0
    return mass / (radius ** 3)

def calc_escape_velocity(mass, radius):
    """Calculate escape velocity in km/s."""
    if radius <= 0 or mass <= 0:
        return 0
    return 11.2 * math.sqrt(mass / radius)

def calc_surface_pressure(mass, radius, temp, has_atmosphere=True):
    """Estimate surface pressure in atmospheres."""
    if not has_atmosphere:
        return 0
    
    gravity = calc_surface_gravity(mass, radius)
    
    # Scale factor based on gravity
    base_pressure = gravity  # Earth = 1 atm with g = 1
    
    # Temperature adjustment
    if temp > 400:
        base_pressure *= 0.5  # Hot planets lose atmosphere
    elif temp < 200:
        base_pressure *= 1.5  # Cold planets may retain more
    
    # Size adjustment
    if radius > 1.5:
        base_pressure *= (radius ** 0.5)  # Larger planets hold more
    elif radius < 0.5:
        base_pressure *= 0.2  # Small planets lose atmosphere
    
    return round(base_pressure, 2)

def calc_year_length(period):
    """Calculate year length relative to Earth."""
    return period / 365.25

def calc_day_length(period, radius):
    """Estimate day length based on tidal locking probability."""
    if period < 30:  # Very close orbit - likely tidally locked
        return period * 24  # Day = Year
    elif period < 100:
        return random.uniform(20, 100)  # Variable
    else:
        return random.uniform(8, 48)  # Earth-like range

def estimate_magnetic_field(mass, radius):
    """Estimate magnetic field strength relative to Earth."""
    # Simplified model based on core size (proportional to mass) and rotation
    if mass < 0.1:
        return 0  # Too small
    
    core_factor = mass ** 0.75
    size_factor = 1 / (radius ** 0.5) if radius > 0 else 0
    
    field = core_factor * size_factor
    
    if field < 0.1:
        return (0, {'en': 'Negligible - No protection from stellar wind',
                    'kz': 'Өте әлсіз - Жұлдыз желінен қорғаныс жоқ'})
    elif field < 0.5:
        return (field, {'en': 'Weak - Partial protection',
                        'kz': 'Әлсіз - Жартылай қорғаныс'})
    elif field < 2:
        return (field, {'en': 'Moderate - Good protection',
                        'kz': 'Орташа - Жақсы қорғаныс'})
    else:
        return (field, {'en': 'Strong - Excellent protection',
                        'kz': 'Күшті - Тамаша қорғаныс'})

def estimate_moons(mass, orbit_au, stellar_mass=1.0):
    """Estimate number of moons based on planet properties."""
    if mass < 0.1:
        return 0
    
    # Hill sphere radius (simplified)
    hill_radius = orbit_au * (mass / (3 * stellar_mass)) ** (1/3)
    
    # More mass and distance = more moons
    moon_probability = mass * hill_radius * 2
    
    if moon_probability < 0.5:
        return 0
    elif moon_probability < 2:
        return random.randint(0, 2)
    elif moon_probability < 10:
        return random.randint(1, 5)
    else:
        return random.randint(3, 20)

def get_planet_type(radius, mass, temp):
    """Determine planet type based on physical characteristics."""
    lang = st.session_state.get('lang', 'en')
    
    types = {
        'dwarf': {
            'name': {'en': '🪨 Dwarf Planet', 'kz': '🪨 Ергежейлі планета'},
            'desc': {'en': 'Small rocky body without atmosphere', 'kz': 'Атмосферасыз кішкентай тасты дене'}
        },
        'sub_earth': {
            'name': {'en': '🔴 Sub-Earth', 'kz': '🔴 Суб-Жер'},
            'desc': {'en': 'Mars-like, thin atmosphere possible', 'kz': 'Марсқа ұқсас, жұқа атмосфера мүмкін'}
        },
        'terrestrial': {
            'name': {'en': '🌍 Terrestrial', 'kz': '🌍 Жер тәрізді'},
            'desc': {'en': 'Potentially habitable, possible tectonics', 'kz': 'Мекендеуге жарамды, тектоника мүмкін'}
        },
        'super_earth': {
            'name': {'en': '🌎 Super-Earth', 'kz': '🌎 Супер-Жер'},
            'desc': {'en': 'Thick atmosphere, possible oceans', 'kz': 'Қалың атмосфера, мұхиттар мүмкін'}
        },
        'mini_neptune': {
            'name': {'en': '💧 Mini-Neptune', 'kz': '💧 Мини-Нептун'},
            'desc': {'en': 'Water world or gas envelope', 'kz': 'Су әлемі немесе газ қабаты'}
        },
        'neptune': {
            'name': {'en': '🔵 Ice Giant', 'kz': '🔵 Мұзды алып'},
            'desc': {'en': 'Neptune-like, deep atmosphere', 'kz': 'Нептунға ұқсас, терең атмосфера'}
        },
        'gas_giant': {
            'name': {'en': '🪐 Gas Giant', 'kz': '🪐 Газ алыбы'},
            'desc': {'en': 'Jupiter-like, metallic hydrogen core', 'kz': 'Юпитерге ұқсас, металл сутегі ядросы'}
        },
        'hot_jupiter': {
            'name': {'en': '🔥 Hot Jupiter', 'kz': '🔥 Ыстық Юпитер'},
            'desc': {'en': 'Close-orbiting gas giant, extremely hot', 'kz': 'Жақын орбиталы газ алыбы, өте ыстық'}
        },
        'super_jupiter': {
            'name': {'en': '🟤 Super-Jupiter', 'kz': '🟤 Супер-Юпитер'},
            'desc': {'en': 'Near brown dwarf boundary', 'kz': 'Қоңыр ергежейлі шекарасында'}
        }
    }
    
    # Classification logic
    if radius < 0.5:
        ptype = 'dwarf'
    elif radius < 0.8:
        ptype = 'sub_earth'
    elif radius < 1.25:
        ptype = 'terrestrial'
    elif radius < 2.0:
        ptype = 'super_earth'
    elif radius < 4.0:
        ptype = 'mini_neptune'
    elif radius < 6.0:
        ptype = 'neptune'
    elif radius < 15:
        if temp > 1000:
            ptype = 'hot_jupiter'
        else:
            ptype = 'gas_giant'
    else:
        ptype = 'super_jupiter'
    
    return types[ptype]['name'][lang], types[ptype]['desc'][lang]

def predict_atmosphere(radius, mass, temp, in_hz, stellar_teff=None):
    """Predict atmosphere type based on planet properties."""
    lang = st.session_state.get('lang', 'en')
    
    if radius > 4:
        return {'en': '🌀 H₂/He dominated - thick gas envelope', 'kz': '🌀 H₂/He басым - қалың газ қабаты'}[lang]
    
    gravity = calc_surface_gravity(mass, radius)
    
    if gravity < 0.3:
        return {'en': '❌ No atmosphere - gravity too weak', 'kz': '❌ Атмосфера жоқ - гравитация өте әлсіз'}[lang]
    
    if temp > 500:
        return {'en': '🔥 Tenuous - too hot to retain gases', 'kz': '🔥 Сирек - газдарды ұстау үшін тым ыстық'}[lang]
    
    if temp < 150:
        return {'en': '❄️ Frozen - CO₂/N₂ ice possible', 'kz': '❄️ Мұздаған - CO₂/N₂ мұзы мүмкін'}[lang]
    
    if in_hz and 0.8 <= radius <= 1.5 and gravity >= 0.7:
        if stellar_teff and stellar_teff > 4000:
            return {'en': '🌿 N₂/O₂ possible - potential biosignature', 'kz': '🌿 N₂/O₂ мүмкін - биоқолтаңба әлеуеті'}[lang]
        return {'en': '🌫️ N₂/CO₂ likely - abiotic stable', 'kz': '🌫️ N₂/CO₂ ықтимал - абиотикалық тұрақты'}[lang]
    
    if radius > 1.5:
        return {'en': '🌫️ H₂O/CO₂ envelope possible', 'kz': '🌫️ H₂O/CO₂ қабаты мүмкін'}[lang]
    
    return {'en': '🌫️ Thin atmosphere possible', 'kz': '🌫️ Жұқа атмосфера мүмкін'}[lang]

def predict_hazards(temp, gravity, radius, orbit, stellar_teff, period=None):
    """Predict potential hazards for habitability."""
    lang = st.session_state.get('lang', 'en')
    hazards = []
    
    # Temperature hazards
    if temp > 500:
        hazards.append(({'en': '🔥 LETHAL HEAT', 'kz': '🔥 ӨЛІМДІ ЫСТЫҚ'}[lang],
                       {'en': f'Surface temperature {temp:.0f}K - all water vaporized', 
                        'kz': f'Бетінің температурасы {temp:.0f}K - барлық су буланған'}[lang]))
    elif temp > 350:
        hazards.append(({'en': '⚠️ Extreme Heat', 'kz': '⚠️ Шектен тыс ыстық'}[lang],
                       {'en': f'Temperature {temp:.0f}K exceeds survivable limits', 
                        'kz': f'Температура {temp:.0f}K өмір сүру шегінен асады'}[lang]))
    elif temp < 150:
        hazards.append(({'en': '❄️ CRYOGENIC', 'kz': '❄️ КРИОГЕНДІК'}[lang],
                       {'en': f'Temperature {temp:.0f}K - all water frozen solid', 
                        'kz': f'Температура {temp:.0f}K - барлық су қатып қалған'}[lang]))
    elif temp < 200:
        hazards.append(({'en': '⚠️ Extreme Cold', 'kz': '⚠️ Шектен тыс суық'}[lang],
                       {'en': f'Temperature {temp:.0f}K - liquid water unlikely', 
                        'kz': f'Температура {temp:.0f}K - сұйық су екіталай'}[lang]))
    
    # Gravity hazards
    if gravity > 3:
        hazards.append(({'en': '⚠️ CRUSHING GRAVITY', 'kz': '⚠️ ҚИРАТУШЫ ГРАВИТАЦИЯ'}[lang],
                       {'en': f'{gravity:.1f}g would crush human skeletal system', 
                        'kz': f'{gravity:.1f}g адам қаңқа жүйесін бұзады'}[lang]))
    elif gravity > 2:
        hazards.append(({'en': '⚠️ High Gravity', 'kz': '⚠️ Жоғары гравитация'}[lang],
                       {'en': f'{gravity:.1f}g - severe strain on movement', 
                        'kz': f'{gravity:.1f}g - қозғалысқа ауыр жүктеме'}[lang]))
    elif gravity < 0.3:
        hazards.append(({'en': '⚠️ Microgravity', 'kz': '⚠️ Микрогравитация'}[lang],
                       {'en': f'{gravity:.2f}g - bone/muscle atrophy risk', 
                        'kz': f'{gravity:.2f}g - сүйек/бұлшықет атрофиясы қаупі'}[lang]))
    
    # Stellar hazards
    if stellar_teff and stellar_teff < 3500:
        hazards.append(({'en': '⚡ Stellar Flares', 'kz': '⚡ Жұлдыз жарқылдары'}[lang],
                       {'en': 'M-dwarf host prone to deadly radiation bursts', 
                        'kz': 'M-ергежейлі өлімді сәулелену жарылыстарына бейім'}[lang]))
    
    # Tidal locking
    if period and period < 30:
        hazards.append(({'en': '🔒 Tidal Locking', 'kz': '🔒 Толқындық байланыс'}[lang],
                       {'en': 'One side always faces star - extreme temperature gradient', 
                        'kz': 'Бір жағы әрқашан жұлдызға қарайды - температура градиенті'}[lang]))
    
    # Good conditions
    if not hazards:
        hazards.append(({'en': '✅ No Major Hazards Detected', 'kz': '✅ Үлкен қауіптер анықталмады'}[lang],
                       {'en': 'Conditions within potentially survivable range', 
                        'kz': 'Жағдайлар өмір сүруге жарамды диапазонда'}[lang]))
    
    return hazards

def predict_life_potential(temp, radius, in_hz, esi, atmo_type):
    """Predict potential for life based on all factors."""
    lang = st.session_state.get('lang', 'en')
    score = 0
    factors = []
    
    # Temperature factor (0-30 points)
    if 250 <= temp <= 310:
        score += 30
        factors.append({'en': '✅ Optimal temperature for liquid water', 'kz': '✅ Сұйық су үшін оңтайлы температура'}[lang])
    elif 200 <= temp <= 350:
        score += 15
        factors.append({'en': '⚠️ Temperature within extremophile range', 'kz': '⚠️ Температура экстремофил диапазонында'}[lang])
    else:
        factors.append({'en': '❌ Temperature outside survivable range', 'kz': '❌ Температура өмір сүру диапазонынан тыс'}[lang])
    
    # Habitable zone (0-25 points)
    if in_hz:
        score += 25
        factors.append({'en': '✅ Within stellar habitable zone', 'kz': '✅ Жұлдыздың мекендеуге жарамды аймағында'}[lang])
    else:
        factors.append({'en': '❌ Outside habitable zone', 'kz': '❌ Мекендеуге жарамды аймақтан тыс'}[lang])
    
    # Size factor (0-20 points)
    if 0.8 <= radius <= 1.5:
        score += 20
        factors.append({'en': '✅ Earth-like size - optimal for tectonics', 'kz': '✅ Жерге ұқсас өлшем - тектоника үшін оңтайлы'}[lang])
    elif 0.5 <= radius <= 2.0:
        score += 10
        factors.append({'en': '⚠️ Near Earth-size - possible habitability', 'kz': '⚠️ Жер өлшеміне жақын - мекендеуге жарамдылық мүмкін'}[lang])
    else:
        factors.append({'en': '❌ Size unfavorable for Earth-like life', 'kz': '❌ Өлшемі Жердегі өмірге қолайсыз'}[lang])
    
    # ESI factor (0-15 points)
    if esi >= 0.8:
        score += 15
        factors.append({'en': '✅ High Earth Similarity Index', 'kz': '✅ Жоғары Жерге ұқсастық индексі'}[lang])
    elif esi >= 0.6:
        score += 8
        factors.append({'en': '⚠️ Moderate Earth similarity', 'kz': '⚠️ Орташа Жерге ұқсастық'}[lang])
    
    # Atmosphere factor (0-10 points)
    if 'N₂/O₂' in atmo_type or 'biosignature' in atmo_type.lower():
        score += 10
        factors.append({'en': '✅ Atmosphere suggests possible biology', 'kz': '✅ Атмосфера биология мүмкіндігін көрсетеді'}[lang])
    elif 'N₂/CO₂' in atmo_type:
        score += 5
        factors.append({'en': '⚠️ Stable atmosphere, no biosignatures', 'kz': '⚠️ Тұрақты атмосфера, биоқолтаңба жоқ'}[lang])
    
    # Determine life type based on score
    if score >= 80:
        life_type = {'en': '🌿 HIGH POTENTIAL - Prime candidate for life', 'kz': '🌿 ЖОҒАРЫ ӘЛЕУЕТ - Өмір үшін басты үміткер'}[lang]
    elif score >= 60:
        life_type = {'en': '🌱 MODERATE - Possible extremophile habitat', 'kz': '🌱 ОРТАША - Экстремофилдер мекені мүмкін'}[lang]
    elif score >= 40:
        life_type = {'en': '🔬 LOW - Requires significant adaptation', 'kz': '🔬 ТӨМЕН - Маңызды бейімделу қажет'}[lang]
    else:
        life_type = {'en': '❌ MINIMAL - Inhospitable conditions', 'kz': '❌ МИНИМАЛДЫ - Қолайсыз жағдайлар'}[lang]
    
    return life_type, score, factors

# ═══════════════════════════════════════════════════════════════════════════════
# NASA EXOPLANET ARCHIVE API
# ═══════════════════════════════════════════════════════════════════════════════
NASA_TAP_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

def fetch_nasa_data(star_name):
    """Fetch exoplanet data from NASA archive."""
    clean_name = star_name.strip()
    
    query = f"""
    SELECT pl_name, hostname, pl_rade, pl_bmasse, pl_eqt, pl_orbper, 
           pl_orbsmax, st_teff, st_rad, st_mass, sy_dist, pl_insol,
           disc_year, discoverymethod
    FROM ps 
    WHERE hostname LIKE '%{clean_name}%' 
    AND default_flag = 1
    ORDER BY pl_name
    """
    
    try:
        response = requests.get(
            NASA_TAP_URL,
            params={'query': query, 'format': 'json'},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data if data else []
    except Exception as e:
        st.error(f"NASA API Error: {e}")
        return []

def process_planet_data(planet_raw, star_data):
    """Process raw NASA data into structured planet info."""
    
    # Extract values with defaults
    radius = planet_raw.get('pl_rade') or 1.0
    mass = planet_raw.get('pl_bmasse') or (radius ** 2.06)  # Mass-radius relation
    temp = planet_raw.get('pl_eqt') or 288
    period = planet_raw.get('pl_orbper') or 365
    orbit = planet_raw.get('pl_orbsmax')
    
    # Calculate orbit if not provided
    stellar_mass = star_data.get('mass', 1.0)
    if not orbit and period:
        orbit = calc_orbit_from_period(period, stellar_mass)
    if not orbit:
        orbit = 1.0
    
    # Stellar properties
    stellar_teff = star_data.get('teff', 5778)
    stellar_rad = star_data.get('radius', 1.0)
    
    # Calculate habitable zone
    hz_inner, hz_outer = calc_habitable_zone(stellar_teff, stellar_rad)
    in_hz = hz_inner <= orbit <= hz_outer
    
    # Calculate ESI
    esi = calc_esi(radius, temp)
    
    # Calculate other properties
    gravity = calc_surface_gravity(mass, radius)
    density = calc_density(mass, radius)
    escape_vel = calc_escape_velocity(mass, radius)
    year_length = calc_year_length(period)
    day_length = calc_day_length(period, radius)
    
    # Get planet type
    planet_type, type_desc = get_planet_type(radius, mass, temp)
    
    # Predict atmosphere
    atmo_type = predict_atmosphere(radius, mass, temp, in_hz, stellar_teff)
    
    # Predict hazards
    hazards = predict_hazards(temp, gravity, radius, orbit, stellar_teff, period)
    
    # Magnetic field
    mag_strength, mag_desc = estimate_magnetic_field(mass, radius)
    
    # Moons
    moons = estimate_moons(mass, orbit, stellar_mass)
    
    # Calculate habitability score
    hab_score = calculate_habitability_score(
        temp, radius, mass, in_hz, esi, gravity, 
        stellar_teff, atmo_type, hazards
    )
    
    # Determine emoji
    if hab_score >= 70:
        emoji = '🌍'
    elif radius < 0.8:
        emoji = '🔴'
    elif radius < 1.5:
        emoji = '🌎'
    elif radius < 4:
        emoji = '💧'
    elif radius < 10:
        emoji = '🔵'
    else:
        emoji = '🪐'
    
    return {
        'name': planet_raw.get('pl_name', 'Unknown'),
        'radius': round(radius, 3),
        'mass': round(mass, 3),
        'temp': round(temp, 1),
        'period': round(period, 2),
        'orbit': round(orbit, 4),
        'gravity': round(gravity, 2),
        'density': round(density, 2),
        'escape_vel': round(escape_vel, 2),
        'year_length': round(year_length, 2),
        'day_length': round(day_length, 1),
        'esi': esi,
        'in_hz': in_hz,
        'hz_inner': round(hz_inner, 3),
        'hz_outer': round(hz_outer, 3),
        'type': planet_type,
        'type_desc': type_desc,
        'atmo_type': atmo_type,
        'hazards': hazards,
        'mag_strength': mag_strength,
        'mag_desc': mag_desc,
        'moons': moons,
        'hab_score': hab_score,
        'emoji': emoji,
        'distance': star_data.get('distance', 0),
        'disc_year': planet_raw.get('disc_year'),
        'disc_method': planet_raw.get('discoverymethod')
    }

def calculate_habitability_score(temp, radius, mass, in_hz, esi, gravity, 
                                  stellar_teff, atmo_type, hazards):
    """Calculate comprehensive habitability score (0-100)."""
    score = 0
    
    # Temperature (0-25 points)
    if 250 <= temp <= 310:
        score += 25
    elif 200 <= temp <= 350:
        score += 15
    elif 150 <= temp <= 400:
        score += 5
    
    # Size/Radius (0-20 points)
    if 0.8 <= radius <= 1.25:
        score += 20
    elif 0.5 <= radius <= 1.5:
        score += 15
    elif radius <= 2.0:
        score += 8
    
    # Habitable zone (0-20 points)
    if in_hz:
        score += 20
    
    # ESI (0-15 points)
    score += int(esi * 15)
    
    # Gravity (0-10 points)
    if 0.7 <= gravity <= 1.5:
        score += 10
    elif 0.4 <= gravity <= 2.0:
        score += 5
    
    # Stellar type (0-5 points)
    if stellar_teff and 4000 <= stellar_teff <= 6500:
        score += 5
    elif stellar_teff and 3500 <= stellar_teff <= 7000:
        score += 2
    
    # Atmosphere bonus (0-5 points)
    if 'N₂/O₂' in atmo_type or 'biosignature' in atmo_type.lower():
        score += 5
    elif 'N₂/CO₂' in atmo_type:
        score += 3
    
    # Hazard penalties
    for h_name, h_desc in hazards:
        if 'LETHAL' in h_name or 'CRUSHING' in h_name or 'CRYOGENIC' in h_name:
            score -= 30
        elif '⚠️' in h_name:
            score -= 10
    
    return max(0, min(100, score))

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def save_system(hostname, star_data, planets):
    """Save a scanned system to session state."""
    if not planets:
        return
    
    best_score = max(p['hab_score'] for p in planets)
    habitable_count = sum(1 for p in planets if p['in_hz'])
    
    st.session_state.saved_systems[hostname] = {
        'star': star_data,
        'planets': planets,
        'planet_count': len(planets),
        'best_score': best_score,
        'habitable_count': habitable_count,
        'distance': star_data.get('distance'),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    
    # Update global habitable count
    st.session_state.habitable_count += habitable_count
    
    # Check achievements
    check_achievements_after_scan(planets, hostname)

def load_system(hostname):
    """Load a saved system into current view."""
    if hostname in st.session_state.saved_systems:
        data = st.session_state.saved_systems[hostname]
        st.session_state.current_star = data['star']
        st.session_state.current_planets = data['planets']
        st.session_state.current_system = hostname
        st.session_state.selected_planet = 0

def mark_star_scanned(star_name):
    """Mark a star as scanned."""
    if star_name not in st.session_state.scanned_stars:
        st.session_state.scanned_stars.append(star_name)

def is_star_scanned(star_name):
    """Check if a star has been scanned."""
    return star_name in st.session_state.scanned_stars

def get_unscanned_stars(catalog_key, skip_scanned=True):
    """Get list of unscanned stars from a catalog."""
    if catalog_key not in CATALOGS:
        return []
    
    stars = CATALOGS[catalog_key]['stars']
    if skip_scanned:
        return [s for s in stars if not is_star_scanned(s)]
    return stars

def get_all_planets():
    """Get all discovered planets across all systems."""
    all_planets = []
    for hostname, data in st.session_state.saved_systems.items():
        for planet in data['planets']:
            planet_copy = planet.copy()
            planet_copy['hostname'] = hostname
            all_planets.append(planet_copy)
    return all_planets

def get_top_candidates(n=10):
    """Get top N habitable candidates."""
    all_planets = get_all_planets()
    sorted_planets = sorted(all_planets, key=lambda x: x['hab_score'], reverse=True)
    return sorted_planets[:n]

def check_achievements_after_scan(planets, hostname):
    """Check for achievements after scanning a system."""
    num_systems = len(st.session_state.saved_systems)
    
    # First scan
    if num_systems == 1:
        check_achievement('first_scan')
    
    # Explorer achievements
    if num_systems >= 5:
        check_achievement('explorer_5')
    if num_systems >= 10:
        check_achievement('explorer_10')
    
    # Planet-based achievements
    for p in planets:
        if p['in_hz']:
            check_achievement('habitable_found')
        if p['esi'] > 0.8:
            check_achievement('earth_twin')
        if p['radius'] > 6:
            check_achievement('giant_hunter')
        if p['radius'] < 0.8:
            check_achievement('mini_world')
        if p['hab_score'] >= 90:
            check_achievement('score_90')
    
    # Habitable count
    total_hz = sum(1 for p in get_all_planets() if p['in_hz'])
    if total_hz >= 5:
        check_achievement('habitable_5')
    
    # Multi-planet system
    if len(planets) >= 5:
        check_achievement('multi_planet')
    
    # Catalog completion
    for cat_key, cat_data in CATALOGS.items():
        if all(is_star_scanned(s) for s in cat_data['stars']):
            check_achievement('catalog_complete')
            break
# ═══════════════════════════════════════════════════════════════════════════════
# VISUALIZATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_star_coordinates(hostname, distance=None):
    """Generate pseudo-random 3D coordinates for stars."""
    random.seed(hash(hostname))
    
    dist = distance if distance else random.uniform(10, 500)
    
    theta = random.uniform(0, 2 * math.pi)
    phi = random.uniform(-math.pi/3, math.pi/3)
    
    x = dist * math.cos(phi) * math.cos(theta)
    y = dist * math.cos(phi) * math.sin(theta)
    z = dist * math.sin(phi)
    
    return x, y, z

def create_stellar_neighborhood_map():
    """Create 3D map of explored star systems."""
    fig = go.Figure()
    
    # Add Sun at origin
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode='markers+text',
        marker=dict(size=15, color='#FFD700', symbol='circle'),
        text=['☀️ Sol'],
        textposition='top center',
        textfont=dict(size=12, color='white'),
        name='Sun',
        hovertemplate='<b>Sol (Sun)</b><br>Distance: 0 ly<extra></extra>'
    ))
    
    # Add explored systems
    if st.session_state.saved_systems:
        for hostname, data in st.session_state.saved_systems.items():
            x, y, z = get_star_coordinates(hostname, data.get('distance'))
            
            score = data['best_score']
            if score >= 70:
                color = '#7cb97c'
            elif score >= 50:
                color = '#00d4ff'
            elif score >= 30:
                color = '#d4a574'
            else:
                color = '#e07878'
            
            size = 8 + (data['planet_count'] * 2)
            
            fig.add_trace(go.Scatter3d(
                x=[x], y=[y], z=[z],
                mode='markers+text',
                marker=dict(size=size, color=color, opacity=0.9,
                           line=dict(width=1, color='white')),
                text=[f'⭐ {hostname}'],
                textposition='top center',
                textfont=dict(size=10, color='white'),
                name=hostname,
                hovertemplate=f'<b>{hostname}</b><br>' +
                             f'Distance: {data.get("distance", "?"):.1f} ly<br>' +
                             f'Planets: {data["planet_count"]}<br>' +
                             f'Best Score: {score}/100<extra></extra>'
            ))
    
    # Layout
    fig.update_layout(
        scene=dict(
            xaxis=dict(title='X (ly)', gridcolor='rgba(255,255,255,0.1)', 
                      backgroundcolor='rgba(0,0,0,0)', showbackground=False),
            yaxis=dict(title='Y (ly)', gridcolor='rgba(255,255,255,0.1)',
                      backgroundcolor='rgba(0,0,0,0)', showbackground=False),
            zaxis=dict(title='Z (ly)', gridcolor='rgba(255,255,255,0.1)',
                      backgroundcolor='rgba(0,0,0,0)', showbackground=False),
            bgcolor='rgba(0,0,0,0)',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=0, r=0, t=30, b=0),
        height=500
    )
    
    return fig

def create_system_3d(planets, star, selected_idx=0):
    """Create 3D visualization of a planetary system."""
    fig = go.Figure()
    
    # Add star at center
    stellar_teff = star.get('teff', 5778)
    if stellar_teff > 7000:
        star_color = '#aaccff'
    elif stellar_teff > 6000:
        star_color = '#ffffaa'
    elif stellar_teff > 5000:
        star_color = '#ffdd66'
    elif stellar_teff > 4000:
        star_color = '#ffaa44'
    else:
        star_color = '#ff6644'
    
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode='markers',
        marker=dict(size=20, color=star_color, opacity=0.9,
                   line=dict(width=2, color='white')),
        name='Star',
        hovertemplate=f'<b>{star.get("name", "Host Star")}</b><br>' +
                     f'Teff: {stellar_teff}K<extra></extra>'
    ))
    
    # Add habitable zone as a ring
    if planets:
        hz_inner = planets[0].get('hz_inner', 0.75)
        hz_outer = planets[0].get('hz_outer', 1.77)
        
        theta = np.linspace(0, 2*np.pi, 50)
        
        # Inner HZ boundary
        fig.add_trace(go.Scatter3d(
            x=hz_inner * np.cos(theta),
            y=hz_inner * np.sin(theta),
            z=np.zeros(50),
            mode='lines',
            line=dict(color='rgba(124,185,124,0.3)', width=2),
            name='HZ Inner',
            showlegend=False
        ))
        
        # Outer HZ boundary
        fig.add_trace(go.Scatter3d(
            x=hz_outer * np.cos(theta),
            y=hz_outer * np.sin(theta),
            z=np.zeros(50),
            mode='lines',
            line=dict(color='rgba(124,185,124,0.3)', width=2),
            name='HZ Outer',
            showlegend=False
        ))
    
    # Add planets
    for i, planet in enumerate(planets):
        orbit = planet.get('orbit', 1.0)
        
        # Random angle for visualization
        random.seed(hash(planet['name']))
        angle = random.uniform(0, 2*np.pi)
        
        x = orbit * np.cos(angle)
        y = orbit * np.sin(angle)
        z = random.uniform(-0.1, 0.1) * orbit
        
        # Planet size based on radius
        size = min(15, max(5, planet['radius'] * 5))
        
        # Color based on habitability
        if planet['hab_score'] >= 70:
            color = '#7cb97c'
        elif planet['hab_score'] >= 50:
            color = '#00d4ff'
        elif planet['hab_score'] >= 30:
            color = '#d4a574'
        else:
            color = '#e07878'
        
        # Highlight selected planet
        is_selected = (i == selected_idx)
        
        fig.add_trace(go.Scatter3d(
            x=[x], y=[y], z=[z],
            mode='markers+text',
            marker=dict(
                size=size * (1.5 if is_selected else 1),
                color=color,
                opacity=1 if is_selected else 0.8,
                line=dict(width=3 if is_selected else 1, color='white')
            ),
            text=[planet['emoji'] if is_selected else ''],
            textposition='top center',
            textfont=dict(size=20),
            name=planet['name'],
            hovertemplate=f'<b>{planet["name"]}</b><br>' +
                         f'Type: {planet["type"]}<br>' +
                         f'Orbit: {orbit:.3f} AU<br>' +
                         f'Score: {planet["hab_score"]}/100<extra></extra>'
        ))
        
        # Add orbit line
        orbit_theta = np.linspace(0, 2*np.pi, 100)
        fig.add_trace(go.Scatter3d(
            x=orbit * np.cos(orbit_theta),
            y=orbit * np.sin(orbit_theta),
            z=np.zeros(100),
            mode='lines',
            line=dict(color='rgba(255,255,255,0.15)', width=1),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Layout
    max_orbit = max([p.get('orbit', 1) for p in planets]) if planets else 2
    axis_range = max_orbit * 1.5
    
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-axis_range, axis_range], showticklabels=False,
                      showgrid=False, zeroline=False, showbackground=False),
            yaxis=dict(range=[-axis_range, axis_range], showticklabels=False,
                      showgrid=False, zeroline=False, showbackground=False),
            zaxis=dict(range=[-axis_range/3, axis_range/3], showticklabels=False,
                      showgrid=False, zeroline=False, showbackground=False),
            bgcolor='rgba(0,0,0,0)',
            camera=dict(eye=dict(x=0.5, y=1.5, z=0.8))
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        height=400
    )
    
    return fig

def create_radar_chart(planets_data):
    """Create radar chart comparing planets."""
    categories = ['ESI', 'Temperature', 'Size', 'Gravity', 'HZ Position']
    
    fig = go.Figure()
    
    for name, data in planets_data.items():
        # Normalize values to 0-1 scale
        esi_norm = data.get('esi', 0)
        temp_norm = max(0, min(1, 1 - abs(data.get('temp', 288) - 288) / 200))
        size_norm = max(0, min(1, 1 - abs(data.get('radius', 1) - 1) / 5))
        grav_norm = max(0, min(1, 1 - abs(data.get('gravity', 1) - 1) / 2))
        hz_norm = 1 if data.get('in_hz', False) else 0.3
        
        values = [esi_norm, temp_norm, size_norm, grav_norm, hz_norm]
        values.append(values[0])  # Close the polygon
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories + [categories[0]],
            fill='toself',
            name=name,
            opacity=0.7
        ))
    
    fig.update_layout(
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickfont=dict(color='white'),
                gridcolor='rgba(255,255,255,0.2)'
            ),
            angularaxis=dict(
                tickfont=dict(color='white', size=12),
                gridcolor='rgba(255,255,255,0.2)'
            )
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(
            font=dict(color='white'),
            bgcolor='rgba(0,0,0,0)'
        ),
        margin=dict(l=60, r=60, t=40, b=40),
        height=400
    )
    
    return fig

def create_bar_comparison(planets_data):
    """Create grouped bar chart comparing planet properties."""
    names = list(planets_data.keys())
    
    metrics = {
        'ESI': [d.get('esi', 0) for d in planets_data.values()],
        'Hab Score': [d.get('hab_score', 0) / 100 for d in planets_data.values()],
        'Gravity (g)': [min(3, d.get('gravity', 1)) / 3 for d in planets_data.values()],
        'Radius (R⊕)': [min(5, d.get('radius', 1)) / 5 for d in planets_data.values()]
    }
    
    colors = ['#d4a574', '#7cb97c', '#00d4ff', '#e07878']
    
    fig = go.Figure()
    
    for i, (metric, values) in enumerate(metrics.items()):
        fig.add_trace(go.Bar(
            name=metric,
            x=names,
            y=values,
            marker_color=colors[i],
            opacity=0.85
        ))
    
    fig.update_layout(
        barmode='group',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            tickfont=dict(color='white'),
            gridcolor='rgba(255,255,255,0.1)'
        ),
        yaxis=dict(
            tickfont=dict(color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            title=dict(text='Normalized Value', font=dict(color='white'))
        ),
        legend=dict(
            font=dict(color='white'),
            bgcolor='rgba(0,0,0,0)'
        ),
        margin=dict(l=40, r=20, t=30, b=40),
        height=350
    )
    
    return fig

def create_score_distribution_chart():
    """Create histogram of habitability scores."""
    all_planets = get_all_planets()
    
    if not all_planets:
        return go.Figure()
    
    scores = [p['hab_score'] for p in all_planets]
    
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=scores,
        nbinsx=20,
        marker=dict(
            color='rgba(212,165,116,0.7)',
            line=dict(color='#d4a574', width=1)
        ),
        hovertemplate='Score: %{x}<br>Count: %{y}<extra></extra>'
    ))
    
    # Add threshold lines
    fig.add_vline(x=70, line_dash='dash', line_color='#7cb97c',
                  annotation_text='High (70+)', annotation_position='top')
    fig.add_vline(x=50, line_dash='dash', line_color='#00d4ff',
                  annotation_text='Moderate (50+)', annotation_position='top')
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            title=dict(text='Habitability Score', font=dict(color='white')),
            tickfont=dict(color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            range=[0, 100]
        ),
        yaxis=dict(
            title=dict(text='Count', font=dict(color='white')),
            tickfont=dict(color='white'),
            gridcolor='rgba(255,255,255,0.1)'
        ),
        margin=dict(l=40, r=20, t=30, b=40),
        height=300
    )
    
    return fig

def create_travel_animation(progress, destination_name):
    """Create visualization for interstellar travel simulation."""
    fig = go.Figure()
    
    # Earth
    fig.add_trace(go.Scatter(
        x=[0], y=[0.5],
        mode='markers+text',
        marker=dict(size=30, color='#4a90d9'),
        text=['🌍'],
        textfont=dict(size=25),
        textposition='middle center',
        name='Earth',
        hoverinfo='skip'
    ))
    
    # Destination
    fig.add_trace(go.Scatter(
        x=[1], y=[0.5],
        mode='markers+text',
        marker=dict(size=30, color='#e07878'),
        text=['🎯'],
        textfont=dict(size=25),
        textposition='middle center',
        name=destination_name,
        hoverinfo='skip'
    ))
    
    # Spaceship
    ship_x = progress
    fig.add_trace(go.Scatter(
        x=[ship_x], y=[0.5],
        mode='markers+text',
        marker=dict(size=35, color='#d4a574'),
        text=['🚀'],
        textfont=dict(size=30),
        textposition='middle center',
        name='Ship',
        hoverinfo='skip'
    ))
    
    # Progress line
    fig.add_trace(go.Scatter(
        x=[0, ship_x],
        y=[0.5, 0.5],
        mode='lines',
        line=dict(color='rgba(212,165,116,0.5)', width=3, dash='dash'),
        hoverinfo='skip',
        showlegend=False
    ))
    
    # Stars background
    np.random.seed(42)
    stars_x = np.random.rand(50)
    stars_y = np.random.rand(50)
    stars_size = np.random.randint(2, 5, 50)
    
    fig.add_trace(go.Scatter(
        x=stars_x, y=stars_y,
        mode='markers',
        marker=dict(size=stars_size, color='white', opacity=0.5),
        hoverinfo='skip',
        showlegend=False
    ))
    
    # Progress percentage
    fig.add_annotation(
        x=0.5, y=0.15,
        text=f'{progress*100:.0f}% Complete',
        font=dict(size=20, color='white'),
        showarrow=False
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            range=[-0.1, 1.1],
            showgrid=False,
            showticklabels=False,
            zeroline=False
        ),
        yaxis=dict(
            range=[0, 1],
            showgrid=False,
            showticklabels=False,
            zeroline=False
        ),
        showlegend=False,
        margin=dict(l=0, r=0, t=20, b=20),
        height=200
    )
    
    return fig

# ═══════════════════════════════════════════════════════════════════════════════
# AI RECOMMENDATIONS & HYPOTHESES
# ═══════════════════════════════════════════════════════════════════════════════

def generate_recommendations():
    """Generate AI recommendations based on discovered planets."""
    lang = st.session_state.get('lang', 'en')
    all_planets = get_all_planets()
    
    if not all_planets:
        return []
    
    recommendations = []
    
    # Find best candidate
    best = max(all_planets, key=lambda x: x['hab_score'])
    if best['hab_score'] >= 50:
        recommendations.append({
            'title': {'en': f"🎯 Priority Target: {best['name']}", 
                     'kz': f"🎯 Басымдықты мақсат: {best['name']}"}[lang],
            'reason': {'en': f"Highest habitability score ({best['hab_score']}/100) with {best['type']}", 
                      'kz': f"Ең жоғары мекендеуге жарамдылық бағасы ({best['hab_score']}/100), {best['type']}"}[lang],
            'action': {'en': 'Recommend spectroscopic follow-up for atmospheric analysis', 
                      'kz': 'Атмосфералық талдау үшін спектроскопиялық бақылауды ұсынамыз'}[lang]
        })
    
    # Earth-like candidates
    earth_like = [p for p in all_planets if p['esi'] >= 0.7]
    if earth_like:
        recommendations.append({
            'title': {'en': f"🌍 Earth-like Candidates ({len(earth_like)})", 
                     'kz': f"🌍 Жерге ұқсас үміткерлер ({len(earth_like)})"}[lang],
            'reason': {'en': f"High ESI values suggest Earth-similar conditions", 
                      'kz': f"Жоғары ESI мәндері Жерге ұқсас жағдайларды көрсетеді"}[lang],
            'action': {'en': 'Search for water vapor and oxygen signatures', 
                      'kz': 'Су буы мен оттегі қолтаңбаларын іздеу'}[lang]
        })
    
    # Unexplored systems
    for cat_key, cat_data in CATALOGS.items():
        unscanned = get_unscanned_stars(cat_key)
        if unscanned:
            recommendations.append({
                'title': {'en': f"🔭 Explore {cat_data['name']['en']}", 
                         'kz': f"🔭 {cat_data['name']['kz']} зерттеу"}[lang],
                'reason': {'en': f"{len(unscanned)} unscanned targets remaining", 
                          'kz': f"{len(unscanned)} сканерленбеген мақсаттар қалды"}[lang],
                'action': {'en': f"Priority: {unscanned[0]}", 
                          'kz': f"Басымдық: {unscanned[0]}"}[lang]
            })
            break
    
    return recommendations[:5]

def generate_hypotheses():
    """Generate scientific hypotheses from data patterns."""
    lang = st.session_state.get('lang', 'en')
    all_planets = get_all_planets()
    
    if len(all_planets) < 3:
        return []
    
    hypotheses = []
    
    # Habitability patterns
    hz_planets = [p for p in all_planets if p['in_hz']]
    if hz_planets:
        avg_radius = sum(p['radius'] for p in hz_planets) / len(hz_planets)
        hypotheses.append({
            'title': {'en': 'Habitable Zone Planet Sizes', 'kz': 'Мекендеуге жарамды аймақ планеталарының өлшемдері'}[lang],
            'hypothesis': {'en': f'HZ planets in this sample average {avg_radius:.2f} R⊕', 
                          'kz': f'Бұл үлгідегі МЖА планеталарының орташа өлшемі {avg_radius:.2f} R⊕'}[lang],
            'analysis': {'en': 'This suggests selection effects or physical constraints on habitability', 
                        'kz': 'Бұл мекендеуге жарамдылықтағы таңдау эффектілерін немесе физикалық шектеулерді көрсетеді'}[lang],
            'evidence': {'en': f'Sample size: {len(hz_planets)} planets', 
                        'kz': f'Үлгі көлемі: {len(hz_planets)} планета'}[lang],
            'further_study': {'en': 'Expand sample with TESS and Kepler data', 
                             'kz': 'TESS және Kepler деректерімен үлгіні кеңейту'}[lang]
        })
    
    # Temperature distribution
    temps = [p['temp'] for p in all_planets]
    avg_temp = sum(temps) / len(temps)
    hypotheses.append({
        'title': {'en': 'Temperature Distribution Pattern', 'kz': 'Температура таралу үлгісі'}[lang],
        'hypothesis': {'en': f'Discovered planets have average temperature of {avg_temp:.0f}K', 
                      'kz': f'Табылған планеталардың орташа температурасы {avg_temp:.0f}K'}[lang],
        'analysis': {'en': 'Most detectable planets orbit close to stars, biasing toward hot worlds', 
                    'kz': 'Көптеген анықталған планеталар жұлдыздарға жақын орналасқан, ыстық әлемдерге бейімделген'}[lang],
        'evidence': {'en': f'Based on {len(all_planets)} planetary observations', 
                    'kz': f'{len(all_planets)} планеталық бақылауға негізделген'}[lang],
        'further_study': {'en': 'Long-baseline radial velocity studies for cooler planets', 
                         'kz': 'Салқын планеталар үшін ұзақ базалық радиалды жылдамдық зерттеулері'}[lang]
    })
    
    return hypotheses[:4]

def generate_system_analysis(hostname):
    """Generate detailed analysis for a specific system."""
    lang = st.session_state.get('lang', 'en')
    
    if hostname not in st.session_state.saved_systems:
        return None
    
    data = st.session_state.saved_systems[hostname]
    planets = data['planets']
    star = data['star']
    
    stellar_teff = star.get('teff', 5778)
    hz_planets = [p for p in planets if p['in_hz']]
    best_planet = max(planets, key=lambda x: x['hab_score'])
    
    system_type = {
        'en': f"**{hostname}** is a {'multi-planet' if len(planets) > 1 else 'single-planet'} system",
        'kz': f"**{hostname}** — {'көп планеталы' if len(planets) > 1 else 'бір планеталы'} жүйе"
    }[lang]
    
    star_class = 'G' if 5000 <= stellar_teff < 6000 else 'K' if 4000 <= stellar_teff < 5000 else 'M' if stellar_teff < 4000 else 'F' if stellar_teff < 7000 else 'A'
    
    return {
        'system_type': system_type,
        'star_analysis': {
            'en': f"Host star is {star_class}-type ({stellar_teff}K). " + 
                  ("Optimal for life (G/K type)." if 4000 < stellar_teff < 6500 else
                   "M-dwarf — flare and tidal lock risks." if stellar_teff < 4000 else
                   "Hot star — short lifespan."),
            'kz': f"Жұлдыз {star_class} түрі ({stellar_teff}K). " +
                  ("Өмір үшін оңтайлы (G/K түрі)." if 4000 < stellar_teff < 6500 else
                   "M-ергежейлі — жарқылдар мен толқындық байланыс қаупі." if stellar_teff < 4000 else
                   "Ыстық жұлдыз — қысқа өмір.")
        }[lang],
        'hz_analysis': {
            'en': f"**{len(hz_planets)}** planets in habitable zone." if hz_planets else "No planets in habitable zone.",
            'kz': f"Мекендеуге жарамды аймақта **{len(hz_planets)}** планета бар." if hz_planets else "Мекендеуге жарамды аймақта планета жоқ."
        }[lang],
        'best_candidate': {
            'en': f"Best candidate: **{best_planet['name']}**, score **{best_planet['hab_score']}/100**",
            'kz': f"Ең жақсы үміткер: **{best_planet['name']}**, бағасы **{best_planet['hab_score']}/100**"
        }[lang],
        'recommendation': {
            'en': "🎯 High priority for further study!" if best_planet['hab_score'] >= 60 else
                  "📊 Moderate interest — additional analysis needed." if best_planet['hab_score'] >= 40 else
                  "📉 Low habitability potential.",
            'kz': "🎯 Одан әрі зерттеу үшін жоғары басымдық!" if best_planet['hab_score'] >= 60 else
                  "📊 Орташа қызығушылық — қосымша талдау қажет." if best_planet['hab_score'] >= 40 else
                  "📉 Мекендеуге жарамдылық әлеуеті төмен."
        }[lang]
    }
# ═══════════════════════════════════════════════════════════════════════════════
# ENCYCLOPEDIA DATA
# ═══════════════════════════════════════════════════════════════════════════════

ENCYCLOPEDIA = {
    'star_types': {
        'title': {'en': '⭐ Star Types', 'kz': '⭐ Жұлдыз түрлері'},
        'content': {
            'en': """
### Stellar Spectral Classification (O-B-A-F-G-K-M)

| Class | Temperature | Color | Mass | Lifespan | Examples |
|-------|-------------|-------|------|----------|----------|
| O | 30,000-50,000K | Blue | 16-150 M☉ | <10 Myr | Mintaka, Alnilam |
| B | 10,000-30,000K | Blue-White | 2-16 M☉ | 10-300 Myr | Rigel, Spica |
| A | 7,500-10,000K | White | 1.4-2.1 M☉ | 0.3-2 Gyr | Sirius, Vega |
| F | 6,000-7,500K | Yellow-White | 1.0-1.4 M☉ | 2-7 Gyr | Procyon, Canopus |
| G | 5,200-6,000K | Yellow | 0.8-1.04 M☉ | 7-15 Gyr | **Sun**, Alpha Centauri A |
| K | 3,700-5,200K | Orange | 0.45-0.8 M☉ | 15-50 Gyr | Alpha Centauri B, Epsilon Eridani |
| M | 2,400-3,700K | Red | 0.08-0.45 M☉ | 50+ Gyr | Proxima Centauri, TRAPPIST-1 |

#### Best for Life
**G and K types** — enough light for photosynthesis, stable for billions of years. Sun is G-type star.

#### Problematic for Life
**M-dwarfs** — frequent flares, planets tidally locked (one side always facing star).
**O/B types** — too hot, too short-lived for life evolution.
            """,
            'kz': """
### Жұлдыздардың спектрлік жіктелуі (O-B-A-F-G-K-M)

| Класс | Температура | Түс | Масса | Өмір ұзақтығы | Мысалдар |
|-------|-------------|-----|-------|---------------|----------|
| O | 30,000-50,000K | Көк | 16-150 M☉ | <10 млн жыл | Минтака |
| B | 10,000-30,000K | Ақ-көк | 2-16 M☉ | 10-300 млн жыл | Ригель |
| A | 7,500-10,000K | Ақ | 1.4-2.1 M☉ | 0.3-2 млрд жыл | Сириус, Вега |
| F | 6,000-7,500K | Сары-ақ | 1.0-1.4 M☉ | 2-7 млрд жыл | Процион |
| G | 5,200-6,000K | Сары | 0.8-1.04 M☉ | 7-15 млрд жыл | **Күн** |
| K | 3,700-5,200K | Сарғыш | 0.45-0.8 M☉ | 15-50 млрд жыл | Альфа Центавра B |
| M | 2,400-3,700K | Қызыл | 0.08-0.45 M☉ | 50+ млрд жыл | TRAPPIST-1 |

#### Өмір үшін оңтайлы
**G және K түрлері** — фотосинтез үшін жеткілікті жарық, миллиардтаған жылдар бойы тұрақты.

#### Өмір үшін проблемалы
**M-ергежейлілер** — жиі жарқылдар, планеталар толқындық байланыста.
**O/B түрлері** — тым ыстық, өмір эволюциясы үшін тым қысқа өмірлі.
            """
        }
    },
    
    'planet_types': {
        'title': {'en': '🪐 Planet Types', 'kz': '🪐 Планета түрлері'},
        'content': {
            'en': """
### Exoplanet Classification by Size

| Type | Radius (R⊕) | Description | Examples |
|------|-------------|-------------|----------|
| 🪨 Dwarf | <0.5 | Asteroid-like body without atmosphere | Ceres |
| 🔴 Sub-Earth | 0.5-0.8 | Mars-like, thin atmosphere | Mars, Kepler-138b |
| 🌍 Terrestrial | 0.8-1.25 | Potentially habitable, plate tectonics | Earth, Kepler-442b |
| 🌎 Super-Earth | 1.25-2.0 | Thick atmosphere, possible oceans | LHS-1140b, K2-18b |
| 💧 Mini-Neptune | 2.0-4.0 | Water world or gas envelope | TOI-270d, Kepler-11f |
| 🔵 Ice Giant | 4-6 | Neptune-like, deep H₂/He atmosphere | Uranus, Neptune |
| 🪐 Gas Giant | 6-15 | Jupiter-like, metallic hydrogen core | Jupiter, HD-209458b |
| 🟤 Super-Jupiter | >15 | Near brown dwarf boundary | KELT-9b |

#### "Radius Valley" (1.5-2.0 R⊕)
Deficit of planets in this range — transition zone between rocky and gaseous worlds.
Cause: photoevaporation of atmosphere by stellar radiation.

#### Hot Jupiters
Gas giants orbiting very close to their stars (<0.1 AU). First exoplanets discovered.
Temperatures exceed 1000K, some have evaporating atmospheres.
            """,
            'kz': """
### Экзопланеталардың өлшемі бойынша жіктелуі

| Түр | Радиус (R⊕) | Сипаттама | Мысалдар |
|-----|-------------|-----------|----------|
| 🪨 Ергежейлі | <0.5 | Атмосферасыз астероид тәрізді дене | Церера |
| 🔴 Суб-Жер | 0.5-0.8 | Марсқа ұқсас, жұқа атмосфера | Марс |
| 🌍 Жер тәрізді | 0.8-1.25 | Мекендеуге жарамды, плиталар тектоникасы | Жер |
| 🌎 Супер-Жер | 1.25-2.0 | Қалың атмосфера, мұхиттар мүмкін | LHS-1140b |
| 💧 Мини-Нептун | 2.0-4.0 | Су әлемі немесе газ қабаты | TOI-270d |
| 🔵 Мұзды алып | 4-6 | Нептунға ұқсас, терең H₂/He атмосферасы | Нептун |
| 🪐 Газ алыбы | 6-15 | Юпитерге ұқсас, металл сутегі ядросы | Юпитер |
| 🟤 Супер-Юпитер | >15 | Қоңыр ергежейлі шекарасында | KELT-9b |

#### "Радиус алқабы" (1.5-2.0 R⊕)
Бұл ауқымда планеталар тапшылығы — тасты және газды әлемдер арасындағы өтпелі аймақ.
            """
        }
    },
    
    'habitability': {
        'title': {'en': '🌱 Habitability Criteria', 'kz': '🌱 Мекендеуге жарамдылық критерийлері'},
        'content': {
            'en': """
### Key Planetary Habitability Criteria

#### 1. Habitable Zone (HZ)
Region around star where liquid water can exist on surface.
- **Inner boundary**: 0.75√L AU (runaway greenhouse)
- **Outer boundary**: 1.77√L AU (CO₂ condensation)
- L — stellar luminosity in solar units

#### 2. Size and Mass
- **Optimal**: 0.8-1.5 R⊕, 0.5-5 M⊕
- Planet must retain atmosphere but not become gas giant

#### 3. Temperature
- **Ideal**: 250-310K (liquid water)
- **Extended**: 200-350K (extremophiles)

#### 4. Atmosphere
- N₂/O₂ (biogenic) or N₂/CO₂ (abiotic)
- Pressure: 0.5-5 atm for water stability

#### 5. Magnetic Field
Protection from stellar wind and cosmic rays. Requires liquid iron core + rotation.

#### 6. Stellar Stability
- **Optimal**: G, K types
- **Risks**: M-dwarfs (flares), O/B (short life)

### Earth Similarity Index (ESI)
```
ESI = √[(1-|R-1|/(R+1))^0.57 × (1-|T-288|/(T+288))^5.58]
```
ESI > 0.8 = Earth-type candidate
            """,
            'kz': """
### Планетаның мекендеуге жарамдылығының негізгі критерийлері

#### 1. Мекендеуге жарамды аймақ (МЖА)
Жұлдыздың айналасындағы бетінде сұйық су болуы мүмкін аймақ.
- **Ішкі шекара**: 0.75√L AU
- **Сыртқы шекара**: 1.77√L AU
- L — жұлдыздың күн бірліктеріндегі жарықтығы

#### 2. Өлшем мен масса
- **Оңтайлы**: 0.8-1.5 R⊕, 0.5-5 M⊕
- Планета атмосфераны ұстап тұруы керек, бірақ газ алыбы болмауы керек

#### 3. Температура
- **Идеал**: 250-310K (сұйық су)
- **Кеңейтілген**: 200-350K (экстремофилдер)

#### 4. Атмосфера
- N₂/O₂ (биогендік) немесе N₂/CO₂ (абиотикалық)
- Қысым: судың тұрақтылығы үшін 0.5-5 атм

#### 5. Магнит өрісі
Жұлдыз желі мен ғарыштық сәулелерден қорғау. Сұйық темір ядро + айналу қажет.

#### 6. Жұлдыздың тұрақтылығы
- **Оңтайлы**: G, K түрлері
- **Қауіптер**: M-ергежейлілер (жарқылдар), O/B (қысқа өмір)

### Жерге ұқсастық индексі (ESI)
ESI > 0.8 = Жер типті үміткер
            """
        }
    },
    
    'detection': {
        'title': {'en': '🔭 Detection Methods', 'kz': '🔭 Анықтау әдістері'},
        'content': {
            'en': """
### Exoplanet Detection Methods

#### 1. Transit Method (Most Common)
Planet passes in front of star, dimming its light.
- **Advantages**: Measures planet size, atmosphere possible
- **Missions**: Kepler, TESS, PLATO
- **Limitation**: Only edge-on systems visible

#### 2. Radial Velocity (Doppler)
Star wobbles due to gravitational pull from planet.
- **Advantages**: Measures minimum mass
- **Instruments**: HARPS, ESPRESSO
- **Limitation**: Edge-on systems give true mass

#### 3. Direct Imaging
Photograph the planet directly.
- **Advantages**: Atmospheric spectroscopy
- **Challenge**: Star is 10⁹ times brighter
- **Missions**: JWST, future HabEx

#### 4. Gravitational Microlensing
Planet bends light from background star.
- **Advantages**: Detects distant planets
- **Limitation**: One-time events

#### 5. Astrometry
Precise star position measurements over time.
- **Mission**: Gaia
- **Future**: May find Earth-twins
            """,
            'kz': """
### Экзопланетаны анықтау әдістері

#### 1. Транзит әдісі (Ең көп тараған)
Планета жұлдыздың алдынан өтіп, оның жарығын күңгірттейді.
- **Артықшылықтары**: Планетаның өлшемін өлшейді, атмосфера мүмкін
- **Миссиялар**: Kepler, TESS, PLATO
- **Шектеу**: Тек жиек жүйелері көрінеді

#### 2. Радиалды жылдамдық (Допплер)
Жұлдыз планетаның гравитациялық тартылысынан тербеледі.
- **Артықшылықтары**: Минималды массаны өлшейді
- **Аспаптар**: HARPS, ESPRESSO

#### 3. Тікелей бейнелеу
Планетаны тікелей суретке түсіру.
- **Артықшылықтары**: Атмосфералық спектроскопия
- **Қиындық**: Жұлдыз 10⁹ есе жарық
- **Миссиялар**: JWST

#### 4. Гравитациялық микролинзалау
Планета фондық жұлдыздың жарығын бүгеді.
- **Артықшылықтары**: Алыс планеталарды анықтайды

#### 5. Астрометрия
Уақыт бойынша жұлдыз позициясының нақты өлшемдері.
- **Миссия**: Gaia
            """
        }
    },
    
    'missions': {
        'title': {'en': '🛰️ Space Missions', 'kz': '🛰️ Ғарыш миссиялары'},
        'content': {
            'en': """
### Key Exoplanet Missions

#### Active Missions

**🛰️ TESS (2018-present)**
- Transiting Exoplanet Survey Satellite
- All-sky survey of nearest stars
- Found TOI-700d, LHS-1140 planets

**🔭 JWST (2021-present)**
- James Webb Space Telescope
- Atmospheric spectroscopy of exoplanets
- First detailed exoplanet atmospheres

**📡 Gaia (2013-present)**
- Precise star positions and distances
- Finding planets via astrometry

#### Past Missions

**⭐ Kepler (2009-2018)**
- Revolutionized exoplanet science
- Found 2,700+ confirmed planets
- Discovered first Earth-sized HZ planets

**🔬 Spitzer (2003-2020)**
- Infrared observations
- TRAPPIST-1 system characterization

#### Future Missions

**🚀 PLATO (2026)**
- Earth-like planets around Sun-like stars
- ESA mission

**🔭 Roman (2027)**
- Gravitational microlensing
- Direct imaging coronagraph
            """,
            'kz': """
### Негізгі экзопланета миссиялары

#### Белсенді миссиялар

**🛰️ TESS (2018-қазір)**
- Транзиттік экзопланеталарды зерттеу спутнигі
- Жақын жұлдыздардың толық шолуы
- TOI-700d, LHS-1140 планеталарын тапты

**🔭 JWST (2021-қазір)**
- Джеймс Уэбб ғарыш телескопы
- Экзопланеталардың атмосфералық спектроскопиясы
- Алғашқы егжей-тегжейлі экзопланета атмосфералары

**📡 Gaia (2013-қазір)**
- Жұлдыздардың нақты позициялары мен қашықтықтары
- Астрометрия арқылы планеталарды табу

#### Өткен миссиялар

**⭐ Kepler (2009-2018)**
- Экзопланета ғылымын төңкеріс жасады
- 2,700+ расталған планета тапты
- Алғашқы Жер өлшемді МЖА планеталарын ашты

#### Болашақ миссиялар

**🚀 PLATO (2026)**
- Күнге ұқсас жұлдыздардың айналасындағы Жерге ұқсас планеталар
- ESA миссиясы
            """
        }
    }
}
# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION UI
# ═══════════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════════
# RENDER FUNCTIONS - FIXED
# ═══════════════════════════════════════════════════════════════════════════════

def render_navbar():
    """Render SolarSphere-style navbar with working navigation."""
    lang = st.session_state.get('lang', 'en')
    current_page = st.session_state.get('current_page', 'home')
    
    # Navbar container
    cols = st.columns([1.5, 0.8, 0.8, 0.8, 0.9, 0.7, 0.6, 1])
    
    with cols[0]:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; padding: 5px 0;">
            <span style="font-size: 1.5rem;">🛰️</span>
            <span style="font-family: sans-serif; font-size: 1.3rem; font-weight: 700; 
                         color: white; letter-spacing: 2px;">ATLAS</span>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        if st.button("Home", key="nav_home", use_container_width=True,
                     type="primary" if current_page == 'home' else "secondary"):
            st.query_params['page'] = 'home'
            st.rerun()
    
    with cols[2]:
        if st.button("Explore", key="nav_explore", use_container_width=True,
                     type="primary" if current_page == 'explore' else "secondary"):
            st.query_params['page'] = 'explore'
            st.rerun()
    
    with cols[3]:
        if st.button("Analysis", key="nav_analysis", use_container_width=True,
                     type="primary" if current_page == 'analysis' else "secondary"):
            st.query_params['page'] = 'analysis'
            st.rerun()
    
    with cols[4]:
        if st.button("Reference", key="nav_ref", use_container_width=True,
                     type="primary" if current_page == 'encyclopedia' else "secondary"):
            st.query_params['page'] = 'encyclopedia'
            st.rerun()
    
    with cols[5]:
        if st.button("About", key="nav_about", use_container_width=True,
                     type="primary" if current_page == 'about' else "secondary"):
            st.query_params['page'] = 'about'
            st.rerun()
    
    with cols[6]:
        new_lang = 'kz' if lang == 'en' else 'en'
        if st.button('🇬🇧' if lang == 'en' else '🇰🇿', key="nav_lang"):
            st.query_params['lang'] = new_lang
            st.query_params['page'] = current_page
            st.rerun()
    
    with cols[7]:
        if st.button("START EXPLORING", key="nav_cta", type="primary"):
            st.query_params['page'] = 'explore'
            st.rerun()
    
    st.markdown("---")


def render_achievement_popup():
    """Render achievement popup if any in queue."""
    if st.session_state.achievements_queue:
        ach_id = st.session_state.achievements_queue.pop(0)
        ach = ACHIEVEMENTS.get(ach_id, {})
        lang = st.session_state.get('lang', 'en')
        
        popup_html = f"""
        <div class="achievement-popup">
            <div class="achievement-icon">{ach.get('icon', '🏆')}</div>
            <div>
                <div class="achievement-label">{t('achievement_unlocked')}</div>
                <div class="achievement-name">{ach.get('name', {}).get(lang, 'Achievement')}</div>
            </div>
        </div>
        """
        st.markdown(popup_html, unsafe_allow_html=True)


def render_stats_bar():
    """Render bottom stats bar."""
    num_systems = len(st.session_state.saved_systems)
    num_habitable = st.session_state.habitable_count
    num_planets = sum(d['planet_count'] for d in st.session_state.saved_systems.values()) if st.session_state.saved_systems else 0
    
    stats_html = f"""
    <div class="stats-bar">
        <div class="stat-item">
            <div class="stat-number">{num_systems}</div>
            <div class="stat-label">{t('stat_systems')}</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{num_habitable}</div>
            <div class="stat-label">{t('stat_habitable')}</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{num_planets}</div>
            <div class="stat-label">{t('stat_planets')}</div>
        </div>
    </div>
    """
    st.markdown(stats_html, unsafe_allow_html=True)


def render_hero():
    """Render hero section with quotes - FIXED VERSION."""
    lang = st.session_state.get('lang', 'en')
    idx = st.session_state.quote_index % len(QUOTES)
    quote = QUOTES[idx]
    
    # Hero layout
    col1, col2 = st.columns([1.3, 1])
    
    with col1:
        st.markdown("""
        <div style="padding: 80px 0 40px 0;">
            <h1 style="font-family: 'Space Grotesk', sans-serif; font-size: 5rem; font-weight: 700;
                       color: white; letter-spacing: 12px; margin: 0 0 15px 0;
                       text-shadow: 2px 2px 30px rgba(0,0,0,0.5);">ATLAS</h1>
            <p style="font-family: sans-serif; font-size: 0.85rem; color: rgba(255,255,255,0.6);
                      letter-spacing: 3px; text-transform: uppercase; margin: 0;">
                AUTONOMOUS TERRESTRIAL LIFE ANALYSIS SYSTEM
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Quote box
        st.markdown(f"""
        <div style="background: rgba(0,0,0,0.3); border-radius: 15px; padding: 25px; margin: 30px 0;">
            <p style="font-family: sans-serif; font-size: 1.25rem; color: white;
                      font-style: italic; line-height: 1.6; margin: 0 0 10px 0;">
                "{quote['text'][lang]}"
            </p>
            <p style="font-family: sans-serif; font-size: 0.9rem; 
                      color: rgba(255,255,255,0.5); margin: 0;">
                — {quote['author']}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Quote navigation
        ncol1, ncol2, ncol3 = st.columns([1, 2, 1])
        
        with ncol1:
            if st.button("◀ Prev", key="q_prev"):
                new_idx = (idx - 1) % len(QUOTES)
                st.query_params['qidx'] = str(new_idx)
                st.query_params['page'] = 'home'
                st.rerun()
        
        with ncol2:
            st.markdown(f"<p style='text-align: center; color: rgba(255,255,255,0.5);'>Quote {idx + 1} of {len(QUOTES)}</p>", unsafe_allow_html=True)
        
        with ncol3:
            if st.button("Next ▶", key="q_next"):
                new_idx = (idx + 1) % len(QUOTES)
                st.query_params['qidx'] = str(new_idx)
                st.query_params['page'] = 'home'
                st.rerun()
        
        # CTA
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 START EXPLORING →", key="hero_cta", type="primary"):
            st.query_params['page'] = 'explore'
            st.rerun()


def render_home_page():
    """Render home page."""
    render_hero()
    render_stats_bar()

def render_explore_page():
    """Render explore page with all tabs."""
    lang = st.session_state.get('lang', 'en')
    
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown(f'<h1 class="page-title">🔭 {t("nav_explore")}</h1>', unsafe_allow_html=True)
    
    # Create tabs
    tabs = st.tabs([
        t('tab_missions'),
        t('tab_system'),
        t('tab_starmap'),
        t('tab_compare'),
        t('tab_travel'),
        t('tab_history'),
        t('tab_chat'),
        t('tab_presentation')
    ])
    
    # TAB 0: MISSIONS
    with tabs[0]:
        render_missions_tab()
    
    # TAB 1: SYSTEM VIEW
    with tabs[1]:
        render_system_tab()
    
    # TAB 2: STAR MAP
    with tabs[2]:
        render_starmap_tab()
    
    # TAB 3: COMPARE
    with tabs[3]:
        render_compare_tab()
    
    # TAB 4: TRAVEL
    with tabs[4]:
        render_travel_tab()
    
    # TAB 5: HISTORY
    with tabs[5]:
        render_history_tab()
    
    # TAB 6: AI CHAT
    with tabs[6]:
        render_chat_tab()
    
    # TAB 7: PRESENTATION
    with tabs[7]:
        render_presentation_tab()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_missions_tab():
    """Render missions control tab."""
    lang = st.session_state.get('lang', 'en')
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown(f"### 🎯 {t('mission_control')}")
        
        # Catalog selection
        catalog_options = {k: v['name'][lang] for k, v in CATALOGS.items()}
        selected_catalog = st.selectbox(
            t('select_catalog'),
            options=list(catalog_options.keys()),
            format_func=lambda x: catalog_options[x]
        )
        
        # Get available stars
        available_stars = get_unscanned_stars(selected_catalog)
        
        if available_stars:
            selected_star = st.selectbox(
                "Target Star",
                options=available_stars
            )
            
            # Scan button
            if st.button(f"🔍 {t('scan_star')}", type="primary", use_container_width=True):
                with st.spinner(t('scanning')):
                    # Fetch data
                    raw_data = fetch_nasa_data(selected_star)
                    
                    if raw_data:
                        # Process star data
                        first = raw_data[0]
                        star_data = {
                            'name': first.get('hostname', selected_star),
                            'teff': first.get('st_teff') or 5778,
                            'radius': first.get('st_rad') or 1.0,
                            'mass': first.get('st_mass') or 1.0,
                            'distance': first.get('sy_dist')
                        }
                        
                        # Process planets
                        planets = [process_planet_data(p, star_data) for p in raw_data]
                        
                        # Save system
                        save_system(selected_star, star_data, planets)
                        mark_star_scanned(selected_star)
                        
                        # Load into current view
                        st.session_state.current_star = star_data
                        st.session_state.current_planets = planets
                        st.session_state.current_system = selected_star
                        
                        # Log
                        st.session_state.mission_log.append({
                            'time': datetime.now().strftime('%H:%M:%S'),
                            'action': f"Scanned {selected_star}",
                            'result': f"{len(planets)} planets found"
                        })
                        
                        st.success(f"✅ {t('scan_complete')} {len(planets)} {t('planets_found')}!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.warning(f"⚠️ {t('no_planets')}")
        else:
            st.success(f"🎉 Catalog complete! All stars scanned.")
        
        # Progress
        total_stars = len(CATALOGS[selected_catalog]['stars'])
        scanned_count = total_stars - len(available_stars)
        progress = scanned_count / total_stars if total_stars > 0 else 0
        
        st.markdown(f"**{t('progress')}:** {scanned_count}/{total_stars}")
        st.progress(progress)
    
    with col2:
        st.markdown(f"### 📋 {t('mission_log')}")
        
        if st.session_state.mission_log:
            for log in reversed(st.session_state.mission_log[-10:]):
                st.markdown(f"""
                <div class="glass-card" style="padding: 15px; margin: 10px 0;">
                    <strong>{log['time']}</strong> — {log['action']}<br>
                    <span style="color: #7cb97c;">{log['result']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No missions yet. Start scanning!")
        
        # Quick stats
        st.markdown("---")
        st.markdown("### 📊 Statistics")
        c1, c2 = st.columns(2)
        c1.metric(t('stat_systems'), len(st.session_state.saved_systems))
        c2.metric(t('stat_habitable'), st.session_state.habitable_count)

def render_system_tab():
    """Render current system view."""
    lang = st.session_state.get('lang', 'en')
    
    if not st.session_state.current_planets:
        st.info(t('no_system'))
        return
    
    planets = st.session_state.current_planets
    star = st.session_state.current_star
    hostname = st.session_state.current_system
    
    st.markdown(f"### 🌟 {hostname}")
    
    # Star info
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("⭐ Type", f"{star.get('teff', 5778)}K")
    col2.metric("📏 Radius", f"{star.get('radius', 1.0):.2f} R☉")
    col3.metric("⚖️ Mass", f"{star.get('mass', 1.0):.2f} M☉")
    col4.metric("📍 Distance", f"{star.get('distance', '?')} ly" if star.get('distance') else "Unknown")
    
    st.markdown("---")
    
    # 3D System visualization
    st.plotly_chart(
        create_system_3d(planets, star, st.session_state.selected_planet),
        use_container_width=True
    )
    
    # Planet cards
    st.markdown(f"### 🪐 Planets ({len(planets)})")
    
    cols = st.columns(min(len(planets), 4))
    for i, planet in enumerate(planets):
        with cols[i % 4]:
            score = planet['hab_score']
            score_class = 'high' if score >= 70 else 'medium' if score >= 40 else 'low'
            selected = 'selected' if i == st.session_state.selected_planet else ''
            
            if st.button(
                f"{planet['emoji']} {planet['name'].split()[-1]}\n{score}/100",
                key=f"planet_{i}",
                use_container_width=True
            ):
                st.session_state.selected_planet = i
                st.rerun()
    
    # Selected planet details
    st.markdown("---")
    sel_p = planets[st.session_state.selected_planet]
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown(f"### {sel_p['emoji']} {sel_p['name']}")
        st.markdown(f"**{sel_p['type']}** — {sel_p['type_desc']}")
        
        # Basic properties
        st.markdown("#### 📊 Properties")
        c1, c2, c3 = st.columns(3)
        c1.metric(t('radius'), f"{sel_p['radius']:.2f} R⊕")
        c2.metric(t('mass'), f"{sel_p['mass']:.2f} M⊕")
        c3.metric(t('temperature'), f"{sel_p['temp']:.0f}K")
        
        c1, c2, c3 = st.columns(3)
        c1.metric(t('gravity'), f"{sel_p['gravity']:.2f} g")
        c2.metric("ESI", f"{sel_p['esi']:.3f}")
        c3.metric(t('orbital_period'), f"{sel_p['period']:.1f}d")
        
        # Habitability
        score_color = '#7cb97c' if sel_p['hab_score'] >= 70 else '#d4a574' if sel_p['hab_score'] >= 40 else '#e07878'
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 15px; margin: 15px 0;">
            <div style="font-size: 3rem; font-weight: bold; color: {score_color};">{sel_p['hab_score']}</div>
            <div style="color: rgba(255,255,255,0.6);">{t('habitability')}</div>
            <div style="margin-top: 10px; color: {'#7cb97c' if sel_p['in_hz'] else '#e07878'};">
                {'✅ ' + t('in_hz') if sel_p['in_hz'] else '❌ ' + t('outside_hz')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Atmosphere
        st.markdown(f"#### 🌫️ {t('atmosphere')}")
        st.info(sel_p['atmo_type'])
        
        # Hazards
        st.markdown(f"#### ⚠️ {t('hazards')}")
        for h_name, h_desc in sel_p['hazards']:
            if 'LETHAL' in h_name or 'CRUSHING' in h_name or 'CRYOGENIC' in h_name:
                st.error(f"**{h_name}**\n\n{h_desc}")
            elif '✅' in h_name:
                st.success(f"**{h_name}**\n\n{h_desc}")
            else:
                st.warning(f"**{h_name}**\n\n{h_desc}")
        
        # Biosignature potential
        st.markdown(f"#### 🧬 {t('biosignatures')}")
        life_type, life_score, life_factors = predict_life_potential(
            sel_p['temp'], sel_p['radius'], sel_p['in_hz'], sel_p['esi'], sel_p['atmo_type']
        )
        st.info(life_type)
        st.progress(life_score / 100)
        
        # Add to compare
        if st.button(t('add_compare'), use_container_width=True):
            if sel_p['name'] not in st.session_state.compare:
                st.session_state.compare.append(sel_p['name'])
                st.session_state.custom_planets[sel_p['name']] = {
                    'radius': sel_p['radius'],
                    'mass': sel_p['mass'],
                    'temp': sel_p['temp'],
                    'esi': sel_p['esi'],
                    'gravity': sel_p['gravity'],
                    'distance': sel_p['distance'],
                    'emoji': sel_p['emoji'],
                    'hab_score': sel_p['hab_score'],
                    'in_hz': sel_p['in_hz']
                }
                st.success(f"✅ Added to comparison!")

def render_starmap_tab():
    """Render 3D star map."""
    lang = st.session_state.get('lang', 'en')
    
    st.markdown(f"### 🗺️ Stellar Neighborhood Map")
    
    if st.session_state.saved_systems:
        # Stats
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t('stat_systems'), len(st.session_state.saved_systems))
        
        total_planets = sum(d['planet_count'] for d in st.session_state.saved_systems.values())
        c2.metric(t('stat_planets'), total_planets)
        
        distances = [d['distance'] for d in st.session_state.saved_systems.values() if d.get('distance')]
        if distances:
            c3.metric("📏 Nearest", f"{min(distances):.1f} ly")
            c4.metric("📏 Farthest", f"{max(distances):.1f} ly")
        
        # 3D Map
        st.plotly_chart(create_stellar_neighborhood_map(), use_container_width=True)
        
        # Legend
        st.markdown("""
        **Legend:** 
        🟢 High habitability (70+) • 
        🔵 Moderate (50-69) • 
        🟡 Low (30-49) • 
        🔴 Minimal (<30)
        """)
        
        # System list
        st.markdown("---")
        st.markdown("### Explored Systems")
        
        sorted_systems = sorted(
            st.session_state.saved_systems.items(),
            key=lambda x: x[1].get('distance') or 9999
        )
        
        for hostname, data in sorted_systems[:10]:
            dist_str = f"{data['distance']:.1f} ly" if data.get('distance') else "?"
            score_color = '#7cb97c' if data['best_score'] >= 70 else '#00d4ff' if data['best_score'] >= 50 else '#d4a574'
            
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**🌟 {hostname}** — {dist_str} — {data['planet_count']} planets — Best: <span style='color:{score_color}'>{data['best_score']}</span>", unsafe_allow_html=True)
            with col2:
                if st.button(t('load_system'), key=f"map_load_{hostname}"):
                    load_system(hostname)
                    st.rerun()
    else:
        st.info("No systems explored yet. Start scanning!")
# ═══════════════════════════════════════════════════════════════════════════════
# COMPARE TAB
# ═══════════════════════════════════════════════════════════════════════════════

def render_compare_tab():
    """Render planet comparison tab."""
    lang = st.session_state.get('lang', 'en')
    
    st.markdown(f"### {t('compare_title')}")
    
    # Get available planets
    available_planets = {}
    
    # Add known reference planets
    for name, data in KNOWN_PLANETS.items():
        available_planets[name] = data
    
    # Add custom discovered planets
    for name, data in st.session_state.custom_planets.items():
        available_planets[name] = data
    
    if len(available_planets) >= 2:
        st.markdown(f"**{t('select_planets')}**")
        
        selected_planets = st.multiselect(
            "Planets",
            options=list(available_planets.keys()),
            default=st.session_state.compare[:4] if st.session_state.compare else list(available_planets.keys())[:3],
            max_selections=6,
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button(t('clear_selection')):
                st.session_state.compare = []
                st.rerun()
        
        if selected_planets and len(selected_planets) >= 2:
            selected_data = {name: available_planets[name] for name in selected_planets}
            
            # Check compare achievement
            if len(selected_planets) >= 3:
                check_achievement('compare_3')
            
            # Charts
            tab1, tab2 = st.tabs([t('radar_chart'), t('bar_chart')])
            
            with tab1:
                st.plotly_chart(create_radar_chart(selected_data), use_container_width=True)
            
            with tab2:
                st.plotly_chart(create_bar_comparison(selected_data), use_container_width=True)
            
            # Comparison table
            st.markdown("---")
            st.markdown("### Comparison Table")
            
            table_data = []
            for name, data in selected_data.items():
                table_data.append({
                    'Planet': name,
                    'Radius (R⊕)': f"{data.get('radius', 1):.2f}",
                    'Mass (M⊕)': f"{data.get('mass', 1):.2f}",
                    'Temp (K)': f"{data.get('temp', 288):.0f}",
                    'ESI': f"{data.get('esi', 0):.3f}",
                    'Gravity (g)': f"{data.get('gravity', 1):.2f}",
                    'Score': f"{data.get('hab_score', 0)}/100" if 'hab_score' in data else "N/A"
                })
            
            st.table(table_data)
        else:
            st.info("Select at least 2 planets to compare")
    else:
        st.info("Discover more planets to enable comparison!")

# ═══════════════════════════════════════════════════════════════════════════════
# TRAVEL TAB
# ═══════════════════════════════════════════════════════════════════════════════

def render_travel_tab():
    """Render interstellar travel simulation."""
    lang = st.session_state.get('lang', 'en')
    
    st.markdown(f"### {t('travel_title')}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"#### 🎯 {t('destination')}")
        
        # Get destinations from saved systems
        destinations = {}
        if st.session_state.saved_systems:
            for hostname, data in st.session_state.saved_systems.items():
                if data.get('distance'):
                    destinations[hostname] = data['distance']
        
        # Add defaults if no saved
        if not destinations:
            destinations = {
                "Proxima Centauri": 4.24,
                "TRAPPIST-1": 40.7,
                "Kepler-442": 112,
                "TOI-700": 101.4,
                "Kepler-452": 1402
            }
        
        selected_dest = st.selectbox(
            t('destination'),
            options=list(destinations.keys()),
            label_visibility="collapsed"
        )
        
        distance_ly = destinations[selected_dest]
        st.metric(t('distance_ly'), f"{distance_ly:.1f}")
        
        # Velocity slider
        velocity_percent = st.slider(
            t('velocity') + " (% c)",
            min_value=1,
            max_value=99,
            value=20,
            format="%d%%"
        )
        
        velocity_c = velocity_percent / 100
    
    with col2:
        st.markdown(f"#### 📊 {t('mission_params')}")
        
        # Calculate travel parameters
        earth_time_years = distance_ly / velocity_c
        
        # Lorentz factor
        lorentz = 1 / math.sqrt(1 - velocity_c ** 2)
        
        # Ship time
        ship_time_years = earth_time_years / lorentz
        
        # Fuel estimate
        fuel_kg = distance_ly * (velocity_c ** 2) * 100
        
        st.metric(t('earth_time'), f"{earth_time_years:.1f} years")
        st.metric(t('ship_time'), f"{ship_time_years:.1f} years")
        st.metric(t('lorentz'), f"γ = {lorentz:.4f}")
        st.metric(t('fuel'), f"{fuel_kg:.0f} kg")
    
    # Journey visualization
    st.markdown("---")
    st.markdown(f"#### 🚀 {t('journey_preview')}")
    
    progress_placeholder = st.empty()
    progress_placeholder.plotly_chart(create_travel_animation(0.0, selected_dest), use_container_width=True)
    
    if st.button("▶️ Simulate Journey", use_container_width=True, type="primary"):
        check_achievement('traveler')
        
        for i in range(21):
            progress = i / 20
            progress_placeholder.plotly_chart(create_travel_animation(progress, selected_dest), use_container_width=True)
            time.sleep(0.15)
        
        st.success(f"🎉 Arrived at {selected_dest}!")
        st.balloons()
    
    # Mission phases
    st.markdown("---")
    st.markdown(f"#### {t('phases')}")
    
    phases = [
        ("🚀 Acceleration", f"0 → {velocity_percent}% c over {velocity_percent * 0.5:.1f} years"),
        ("⚡ Cruise", f"{distance_ly:.1f} light years at {velocity_percent}% c"),
        ("🔄 Deceleration", f"{velocity_percent}% → 0% c over {velocity_percent * 0.5:.1f} years"),
        ("🪐 Arrival", f"Orbital insertion at {selected_dest}")
    ]
    
    for phase_name, phase_desc in phases:
        st.info(f"**{phase_name}**: {phase_desc}")

# ═══════════════════════════════════════════════════════════════════════════════
# HISTORY TAB
# ═══════════════════════════════════════════════════════════════════════════════

def render_history_tab():
    """Render research history."""
    lang = st.session_state.get('lang', 'en')
    
    st.markdown(f"### {t('history_title')}")
    
    if st.session_state.saved_systems:
        # Sort by timestamp
        sorted_systems = sorted(
            st.session_state.saved_systems.items(),
            key=lambda x: x[1].get('timestamp', ''),
            reverse=True
        )
        
        for hostname, data in sorted_systems:
            score_color = '#7cb97c' if data['best_score'] >= 70 else '#00d4ff' if data['best_score'] >= 50 else '#d4a574'
            
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.markdown(f"**🌟 {hostname}**")
                st.caption(f"📅 {data.get('timestamp', '?')}")
            
            with col2:
                st.markdown(f"🪐 **{data['planet_count']}** planets")
            
            with col3:
                st.markdown(f"<span style='color:{score_color}; font-weight:bold;'>⭐ {data['best_score']}/100</span>", unsafe_allow_html=True)
            
            with col4:
                if st.button(t('load_system'), key=f"hist_{hostname}"):
                    load_system(hostname)
                    st.rerun()
            
            st.markdown("---")
    else:
        st.info(t('history_empty'))

# ═══════════════════════════════════════════════════════════════════════════════
# AI CHAT TAB
# ═══════════════════════════════════════════════════════════════════════════════

def render_chat_tab():
    """Render AI chatbot interface."""
    lang = st.session_state.get('lang', 'en')
    
    st.markdown(f"### 🤖 {t('chat_title')}")
    
    if not CHATBOT_AVAILABLE:
        st.warning(t('chat_unavailable'))
        st.info("""
        To enable AI Chat, place these files in the app directory:
        - `exo_chatbot_model.pkl`
        - `exo_chatbot_responses.json`
        """)
        return
    
    # Chat history
    for msg in st.session_state.chat_history:
        if msg['role'] == 'user':
            st.markdown(f"""
            <div style="text-align: right; margin: 10px 0;">
                <span style="background: rgba(212,165,116,0.3); padding: 10px 15px; border-radius: 15px 15px 0 15px;">
                    {msg['content']}
                </span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="text-align: left; margin: 10px 0;">
                <span style="background: rgba(255,255,255,0.1); padding: 10px 15px; border-radius: 15px 15px 15px 0;">
                    🤖 {msg['content']}
                </span>
            </div>
            """, unsafe_allow_html=True)
    
    # Input
    user_input = st.text_input(t('chat_placeholder'), key="chat_input", label_visibility="collapsed")
    
    if st.button(t('chat_send'), type="primary"):
        if user_input:
            # Add user message
            st.session_state.chat_history.append({'role': 'user', 'content': user_input})
            
            # Generate response
            try:
                # Transform input for model
                from sklearn.feature_extraction.text import TfidfVectorizer
                
                # Simple response based on keywords
                response = "I'm your exoplanet research assistant. Ask me about planets, stars, habitability, or space missions!"
                
                if any(word in user_input.lower() for word in ['habitable', 'life', 'живой', 'мекен']):
                    response = "Habitability depends on temperature (250-310K), size (0.8-1.5 R⊕), atmospheric composition, and stellar stability. The best candidates are in the habitable zone of G or K type stars."
                elif any(word in user_input.lower() for word in ['trappist', 'proxima']):
                    response = "TRAPPIST-1 has 7 known planets, with at least 3 in the habitable zone. Proxima Centauri b is the closest known potentially habitable exoplanet at just 4.24 light years away!"
                elif any(word in user_input.lower() for word in ['kepler', 'tess', 'mission']):
                    response = "Kepler discovered 2,700+ planets from 2009-2018. TESS (2018-present) surveys nearby bright stars. JWST is now characterizing exoplanet atmospheres in unprecedented detail!"
                elif any(word in user_input.lower() for word in ['esi', 'index', 'earth']):
                    response = "The Earth Similarity Index (ESI) ranges from 0 to 1, measuring how Earth-like a planet is based on radius and temperature. ESI > 0.8 indicates an Earth-type candidate."
                
                st.session_state.chat_history.append({'role': 'assistant', 'content': response})
                
                # Check achievement
                if len(st.session_state.chat_history) >= 20:
                    check_achievement('chat_10')
                
            except Exception as e:
                st.session_state.chat_history.append({'role': 'assistant', 'content': f"Sorry, I encountered an error: {str(e)}"})
            
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PRESENTATION TAB
# ═══════════════════════════════════════════════════════════════════════════════

def render_presentation_tab():
    """Render presentation mode."""
    lang = st.session_state.get('lang', 'en')
    
    st.markdown(f"### {t('presentation_title')}")
    
    if not st.session_state.saved_systems:
        st.info("Explore systems first to create a presentation!")
        return
    
    # Slide navigation
    slides = ['📊 Overview', '🏆 Top Candidates', '🗺️ Star Map', '🧠 Findings', '📝 Conclusion']
    current_slide = st.session_state.get('current_slide', 0)
    
    cols = st.columns(len(slides))
    for i, slide_name in enumerate(slides):
        with cols[i]:
            if st.button(slide_name, key=f"slide_{i}", use_container_width=True,
                        type="primary" if i == current_slide else "secondary"):
                st.session_state.current_slide = i
                st.rerun()
    
    st.markdown("---")
    
    # Slide content
    if current_slide == 0:  # Overview
        st.markdown("""
        <div style='background: linear-gradient(135deg, rgba(0,100,200,0.15), rgba(100,0,200,0.1));
                    border: 2px solid rgba(0,212,255,0.3); border-radius: 20px; padding: 40px; text-align: center;'>
            <h1 style='color: #d4a574; margin-bottom: 20px;'>🛰️ ATLAS</h1>
            <h2 style='margin-bottom: 30px;'>Autonomous Terrestrial Life Analysis System</h2>
            <p style='font-size: 1.2rem; opacity: 0.8;'>Exoplanet Research Platform</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔍 Systems", len(st.session_state.saved_systems))
        total_planets = sum(d['planet_count'] for d in st.session_state.saved_systems.values())
        c2.metric("🪐 Planets", total_planets)
        c3.metric("🌱 Habitable", st.session_state.habitable_count)
        if st.session_state.saved_systems:
            best_score = max(d['best_score'] for d in st.session_state.saved_systems.values())
            c4.metric("⭐ Best Score", f"{best_score}/100")
    
    elif current_slide == 1:  # Top Candidates
        top_candidates = get_top_candidates(6)
        
        if top_candidates:
            st.markdown("## 🏆 Top Habitable Candidates")
            
            cols = st.columns(3)
            for i, planet in enumerate(top_candidates):
                with cols[i % 3]:
                    score_color = '#7cb97c' if planet['hab_score'] >= 70 else '#00d4ff' if planet['hab_score'] >= 50 else '#d4a574'
                    
                    st.markdown(f"""
                    <div style='background: rgba(0,50,80,0.3); border: 2px solid {score_color};
                                border-radius: 16px; padding: 25px; text-align: center; margin: 10px 0;'>
                        <div style='font-size: 3rem;'>{planet['emoji']}</div>
                        <h3 style='margin: 15px 0; color: white;'>{planet['name']}</h3>
                        <div style='font-size: 2.5rem; color: {score_color}; font-weight: bold;'>{planet['hab_score']}</div>
                        <div style='opacity: 0.6;'>/100</div>
                        <div style='margin-top: 15px; font-size: 0.95rem;'>
                            <b>Type:</b> {planet['type']}<br>
                            <b>ESI:</b> {planet['esi']}<br>
                            <b>Temp:</b> {planet['temp']:.0f}K<br>
                            {'✅ In HZ' if planet['in_hz'] else '❌ Outside HZ'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No candidates yet!")
    
    elif current_slide == 2:  # Star Map
        st.markdown("## 🗺️ Explored Star Systems")
        st.plotly_chart(create_stellar_neighborhood_map(), use_container_width=True)
    
    elif current_slide == 3:  # Findings
        st.markdown("## 🧠 Scientific Findings")
        
        hypotheses = generate_hypotheses()
        
        if hypotheses:
            for hyp in hypotheses[:3]:
                st.markdown(f"""
                <div style='background: rgba(0,80,120,0.2); border-left: 4px solid #d4a574;
                            border-radius: 0 12px 12px 0; padding: 20px; margin: 15px 0;'>
                    <h4 style='color: #d4a574; margin: 0 0 10px 0;'>{hyp['title']}</h4>
                    <p><b>{hyp['hypothesis']}</b></p>
                    <p style='opacity: 0.8;'>{hyp['analysis']}</p>
                    <p style='color: #7cb97c;'>📊 {hyp['evidence']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Explore more systems to generate findings")
    
    elif current_slide == 4:  # Conclusion
        st.markdown("## 📝 Conclusion")
        check_achievement('presenter')
        
        all_planets = get_all_planets()
        
        if all_planets:
            scores = [p['hab_score'] for p in all_planets]
            avg_score = sum(scores) / len(scores)
            earth_like_count = sum(1 for p in all_planets if 0.8 <= p['radius'] <= 1.5)
            hz_count = sum(1 for p in all_planets if p['in_hz'])
            
            conclusions = [
                f"🔍 Explored **{len(st.session_state.saved_systems)}** star systems",
                f"🪐 Analyzed **{len(all_planets)}** exoplanets",
                f"🌍 Found **{earth_like_count}** Earth-sized planets",
                f"🌱 **{hz_count}** planets in habitable zone",
                f"📊 Average habitability score: **{avg_score:.1f}/100**",
                f"⭐ Best candidate: **{max(all_planets, key=lambda x: x['hab_score'])['name']}** ({max(scores)}/100)"
            ]
            
            st.markdown("""
            <div style='background: linear-gradient(135deg, rgba(0,150,100,0.15), rgba(0,100,200,0.1));
                        border: 2px solid rgba(0,255,136,0.3); border-radius: 20px; padding: 30px;'>
            """, unsafe_allow_html=True)
            
            for conclusion in conclusions:
                st.markdown(f"### {conclusion}")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Final message
            st.markdown("---")
            st.markdown("""
            <div style='text-align: center; padding: 30px;'>
                <h2>🌌 The search continues...</h2>
                <p style='opacity: 0.7; font-size: 1.1rem;'>
                    "Somewhere, something incredible is waiting to be known." — Carl Sagan
                </p>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS PAGE
# ═══════════════════════════════════════════════════════════════════════════════

def render_analysis_page():
    """Render analysis page."""
    lang = st.session_state.get('lang', 'en')
    
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown(f'<h1 class="page-title">🧠 {t("analysis_title")}</h1>', unsafe_allow_html=True)
    
    if len(st.session_state.saved_systems) >= 2:
        # Generate button
        if st.button(t('generate_analysis'), use_container_width=True, type="primary"):
            st.session_state.recommendations = generate_recommendations()
            st.session_state.hypotheses = generate_hypotheses()
            st.rerun()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Recommendations
            if st.session_state.recommendations:
                st.markdown(f"### {t('recommendations')}")
                
                for i, rec in enumerate(st.session_state.recommendations):
                    with st.expander(rec['title'], expanded=(i == 0)):
                        st.markdown(f"**{rec['reason']}**")
                        st.info(f"💡 {rec['action']}")
        
        with col2:
            # Hypotheses
            if st.session_state.hypotheses:
                st.markdown(f"### {t('hypotheses')}")
                
                for i, hyp in enumerate(st.session_state.hypotheses):
                    with st.expander(hyp['title'], expanded=(i == 0)):
                        st.markdown(f"**{hyp['hypothesis']}**")
                        st.markdown(hyp['analysis'])
                        st.success(f"📊 {hyp['evidence']}")
                        st.warning(f"🔬 {hyp['further_study']}")
        
        # Statistics
        st.markdown("---")
        st.markdown("### 📊 Research Statistics")
        
        all_planets = get_all_planets()
        if all_planets:
            c1, c2 = st.columns(2)
            
            with c1:
                st.plotly_chart(create_score_distribution_chart(), use_container_width=True)
            
            with c2:
                scores = [p['hab_score'] for p in all_planets]
                st.metric("Average Score", f"{sum(scores)/len(scores):.1f}")
                st.metric("Best Score", f"{max(scores)}")
                st.metric("In HZ", f"{sum(1 for p in all_planets if p['in_hz'])}/{len(all_planets)}")
                st.metric("Earth-like", f"{sum(1 for p in all_planets if 0.8 <= p['radius'] <= 1.5)}")
    else:
        st.info(t('no_data_analysis'))
    
    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ENCYCLOPEDIA PAGE
# ═══════════════════════════════════════════════════════════════════════════════

def render_encyclopedia_page():
    """Render encyclopedia page."""
    lang = st.session_state.get('lang', 'en')
    
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown(f'<h1 class="page-title">📚 {t("encyclopedia_title")}</h1>', unsafe_allow_html=True)
    
    # Topic selection
    topics = list(ENCYCLOPEDIA.keys())
    topic_names = [ENCYCLOPEDIA[k]['title'][lang] for k in topics]
    
    selected_topic = st.radio(
        "Select topic",
        options=topics,
        format_func=lambda x: ENCYCLOPEDIA[x]['title'][lang],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Display content
    if selected_topic in ENCYCLOPEDIA:
        content = ENCYCLOPEDIA[selected_topic]['content'][lang]
        st.markdown(content)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ABOUT PAGE
# ═══════════════════════════════════════════════════════════════════════════════

def render_about_page():
    """Render about page."""
    lang = st.session_state.get('lang', 'en')
    
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown(f'<h1 class="page-title">ℹ️ {t("about_title")}</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(t('about_desc'))
        
        st.markdown("---")
        st.markdown("### 🏆 Achievements")
        
        cols = st.columns(3)
        for i, (ach_id, ach) in enumerate(ACHIEVEMENTS.items()):
            with cols[i % 3]:
                unlocked = ach_id in st.session_state.achievements
                color = '#7cb97c' if unlocked else 'rgba(255,255,255,0.3)'
                
                st.markdown(f"""
                <div style="text-align: center; padding: 15px; background: rgba(255,255,255,0.05);
                           border: 1px solid {color}; border-radius: 10px; margin: 5px 0;
                           opacity: {1 if unlocked else 0.5};">
                    <div style="font-size: 2rem;">{ach['icon']}</div>
                    <div style="font-weight: bold; color: white; margin: 5px 0;">{ach['name'][lang]}</div>
                    <div style="font-size: 0.8rem; color: rgba(255,255,255,0.6);">{ach['desc'][lang]}</div>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📊 Your Progress")
        st.metric("Achievements", f"{get_unlocked_count()}/{len(ACHIEVEMENTS)}")
        st.metric("Systems Explored", len(st.session_state.saved_systems))
        st.metric("Planets Found", sum(d['planet_count'] for d in st.session_state.saved_systems.values()) if st.session_state.saved_systems else 0)
        st.metric("Habitable Worlds", st.session_state.habitable_count)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════

def render_footer():
    """Render page footer."""
    st.markdown("""
    <div class="atlas-footer">
        <div class="footer-content">
            <div class="footer-logo">🛰️ ATLAS</div>
            <p>Autonomous Terrestrial Life Analysis System</p>
            <p style="font-size: 0.8rem;">Diploma Project 2024-2025 • Powered by NASA Exoplanet Archive</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION - FIXED
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Main application entry point."""
    # Handle URL parameters
    params = st.query_params
    
    if 'page' in params:
        st.session_state.current_page = params['page']
    
    if 'lang' in params:
        st.session_state.lang = params['lang']
    
    if 'qidx' in params:
        try:
            st.session_state.quote_index = int(params['qidx'])
        except:
            pass
    
    current_page = st.session_state.current_page
    
    # Load background
    if current_page == 'home':
        bg = load_background_base64('background.png')
    else:
        bg = load_background_base64('background_none.png')
    
    # Apply CSS FIRST
    st.markdown(get_nasa_css(bg), unsafe_allow_html=True)
    
    # Render navbar
    render_navbar()
    
    # Render achievement popup
    render_achievement_popup()
    
    # Render current page
    if current_page == 'home':
        render_home_page()
    elif current_page == 'explore':
        render_explore_page()
    elif current_page == 'analysis':
        render_analysis_page()
    elif current_page == 'encyclopedia':
        render_encyclopedia_page()
    elif current_page == 'about':
        render_about_page()
    else:
        render_home_page()
    
    # Render footer (not on home)
    if current_page != 'home':
        render_footer()


# Run application
if __name__ == "__main__":
    main()
# ═══════════════════════════════════════════════════════════════════════════════
# ADDITIONAL SCIENTIFIC CALCULATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def calc_stellar_luminosity_class(teff, radius, mass):
    """Determine stellar luminosity class (dwarf, subgiant, giant, supergiant)."""
    luminosity = calc_luminosity(teff, radius)
    
    if luminosity < 0.01:
        return "White Dwarf", "WD"
    elif luminosity < 1:
        return "Main Sequence (Dwarf)", "V"
    elif luminosity < 10:
        return "Subgiant", "IV"
    elif luminosity < 100:
        return "Giant", "III"
    elif luminosity < 1000:
        return "Bright Giant", "II"
    else:
        return "Supergiant", "I"

def calc_stellar_habitable_zone_extended(teff, luminosity):
    """Calculate extended habitable zone boundaries."""
    L = luminosity if luminosity else 1.0
    
    # Optimistic HZ (Venus to Mars boundary)
    optimistic_inner = 0.75 * math.sqrt(L)
    optimistic_outer = 1.77 * math.sqrt(L)
    
    # Conservative HZ (runaway greenhouse to maximum greenhouse)
    conservative_inner = 0.95 * math.sqrt(L)
    conservative_outer = 1.37 * math.sqrt(L)
    
    # Extended HZ (with atmospheric effects)
    extended_inner = 0.5 * math.sqrt(L)
    extended_outer = 2.4 * math.sqrt(L)
    
    return {
        'optimistic': (optimistic_inner, optimistic_outer),
        'conservative': (conservative_inner, conservative_outer),
        'extended': (extended_inner, extended_outer)
    }

def calc_tidal_heating(mass, radius, orbit, eccentricity, stellar_mass):
    """Calculate tidal heating in Earth units."""
    if orbit <= 0 or eccentricity < 0:
        return 0
    
    # Simplified tidal heating formula
    # H ∝ (M_star^2 * R_planet^5 * e^2) / (a^7.5 * Q)
    Q = 100  # Tidal quality factor (Earth ~ 12, Io ~ 100)
    
    heating = (stellar_mass ** 2) * (radius ** 5) * (eccentricity ** 2) / (orbit ** 7.5) / Q
    
    # Normalize to Earth's internal heat
    return round(heating * 1e6, 2)

def calc_plate_tectonics_probability(mass, radius, temp, age_gyr=None):
    """Estimate probability of active plate tectonics."""
    if mass < 0.1 or radius < 0.3:
        return 0, "Too small for tectonics"
    
    if mass > 5:
        return 0.2, "Stagnant lid likely due to high gravity"
    
    # Interior heat proxy
    if temp > 400:
        heat_factor = 0.5  # Too hot, mantle too fluid
    elif temp < 200:
        heat_factor = 0.3  # Too cold, mantle too viscous
    else:
        heat_factor = 1.0
    
    # Mass factor (Earth-like is optimal)
    if 0.5 <= mass <= 2:
        mass_factor = 1.0
    elif 0.3 <= mass <= 3:
        mass_factor = 0.7
    else:
        mass_factor = 0.3
    
    probability = heat_factor * mass_factor
    
    if probability > 0.7:
        desc = "Plate tectonics likely"
    elif probability > 0.4:
        desc = "Plate tectonics possible"
    else:
        desc = "Stagnant lid regime likely"
    
    return round(probability, 2), desc

def calc_water_retention(mass, radius, temp, stellar_teff, orbit):
    """Estimate water retention capability."""
    gravity = calc_surface_gravity(mass, radius)
    escape_vel = calc_escape_velocity(mass, radius)
    
    # Water molecule thermal velocity at given temperature
    water_thermal_vel = 0.157 * math.sqrt(temp)  # km/s
    
    # Retention ratio
    retention_ratio = escape_vel / water_thermal_vel
    
    # Stellar UV factor
    if stellar_teff and stellar_teff < 4000:
        uv_factor = 0.5  # M-dwarf flares
    elif stellar_teff and stellar_teff > 7000:
        uv_factor = 0.7  # High UV
    else:
        uv_factor = 1.0
    
    # Magnetic field proxy
    mag_factor = 0.8 if mass > 0.5 and mass < 3 else 0.5
    
    retention = min(1.0, retention_ratio / 10) * uv_factor * mag_factor
    
    if retention > 0.8:
        return retention, "Excellent water retention"
    elif retention > 0.5:
        return retention, "Good water retention"
    elif retention > 0.2:
        return retention, "Partial water retention"
    else:
        return retention, "Poor water retention - likely desiccated"

def estimate_rotation_period(mass, radius, orbit, stellar_mass):
    """Estimate planetary rotation period."""
    # Tidal locking timescale
    if orbit < 0.3:
        # Close orbit - likely tidally locked
        return orbit * 365.25 * 24, "Tidally locked"
    
    # Initial rotation period estimate (conservation of angular momentum)
    # Larger planets rotate faster
    base_period = 24 / (mass ** 0.3)  # Earth = 24h
    
    # Age factor (planets spin down over time)
    age_factor = 1.0  # Assume mature system
    
    period = base_period * age_factor
    
    if period < 10:
        return period, "Fast rotator"
    elif period < 50:
        return period, "Moderate rotation"
    else:
        return period, "Slow rotator"

def calc_greenhouse_effect(temp, orbit, stellar_teff, atmo_type):
    """Estimate greenhouse warming."""
    # Base equilibrium temperature
    base_temp = temp
    
    # Greenhouse factors for different atmospheres
    if "CO₂" in atmo_type:
        greenhouse_factor = 1.15  # ~15% warming (Earth ~33K)
    elif "H₂" in atmo_type:
        greenhouse_factor = 1.05  # Minimal greenhouse
    elif "N₂/O₂" in atmo_type:
        greenhouse_factor = 1.12  # Earth-like
    else:
        greenhouse_factor = 1.0
    
    surface_temp = base_temp * greenhouse_factor
    warming = surface_temp - base_temp
    
    return surface_temp, warming

def predict_ocean_depth(mass, radius, water_fraction=0.001):
    """Predict average ocean depth for water world."""
    # Earth water fraction ~0.023% by mass
    # Average ocean depth ~3.7 km
    
    surface_area = 4 * math.pi * (radius * 6371) ** 2  # km²
    water_mass = mass * 5.972e24 * water_fraction  # kg
    water_volume = water_mass / 1000  # m³ to km³ (1 kg/L)
    
    depth = water_volume / surface_area
    
    if depth > 100:
        return depth, "Ocean planet - no visible land"
    elif depth > 10:
        return depth, "Deep global ocean"
    elif depth > 3:
        return depth, "Earth-like oceans"
    else:
        return depth, "Shallow seas or lakes"

# ═══════════════════════════════════════════════════════════════════════════════
# EXTENDED ENCYCLOPEDIA ENTRIES
# ═══════════════════════════════════════════════════════════════════════════════

ENCYCLOPEDIA_EXTENDED = {
    'atmospheres': {
        'title': {'en': '🌫️ Planetary Atmospheres', 'kz': '🌫️ Планета атмосфералары'},
        'content': {
            'en': """
### Planetary Atmosphere Types

#### Primary Atmospheres
Captured from the solar nebula during planet formation.
- **Composition**: H₂, He dominated
- **Found on**: Gas giants (Jupiter, Saturn, Neptune)
- **Lost by**: Small rocky planets due to thermal escape

#### Secondary Atmospheres
Outgassed from the planetary interior.
- **Sources**: Volcanic activity, impacts
- **Composition**: CO₂, N₂, H₂O, SO₂
- **Example**: Venus, early Mars

#### Tertiary Atmospheres
Modified by biological activity.
- **Example**: Earth's O₂-rich atmosphere
- **Timeframe**: Billions of years of photosynthesis
- **Biosignature**: O₂ + CH₄ together indicates life

### Atmospheric Escape Mechanisms

| Mechanism | Description | Affected Planets |
|-----------|-------------|------------------|
| Jeans Escape | Thermal escape at exobase | All planets |
| Hydrodynamic Escape | Bulk outflow | Close-in exoplanets |
| Sputtering | Ion impacts | Planets without magnetosphere |
| Impact Erosion | Giant impacts | Young systems |
| Photochemical Escape | UV dissociation | M-dwarf planets |

### Spectroscopic Biosignatures

**Primary Biosignatures:**
- O₂ + O₃ (ozone)
- CH₄ + O₂ together (thermodynamically unstable)
- N₂O (nitrous oxide)

**Secondary Indicators:**
- Water vapor (H₂O)
- Carbon dioxide (CO₂)
- "Red edge" in vegetation reflectance
            """,
            'kz': """
### Планета атмосферасының түрлері

#### Алғашқы атмосфералар
Планета құрылу кезінде күн тұмандығынан алынған.
- **Құрамы**: H₂, He басым
- **Табылатын жері**: Газ алыптары

#### Қосымша атмосфералар
Планета ішінен шыққан.
- **Көздері**: Жанартау белсенділігі, соқтығысулар
- **Құрамы**: CO₂, N₂, H₂O, SO₂

#### Үшінші атмосфералар
Биологиялық белсенділікпен өзгертілген.
- **Мысал**: Жердің O₂-бай атмосферасы
- **Биоқолтаңба**: O₂ + CH₄ бірге өмірді көрсетеді
            """
        }
    },
    
    'exomoons': {
        'title': {'en': '🌙 Exomoons', 'kz': '🌙 Экзосеріктер'},
        'content': {
            'en': """
### Exomoon Detection and Habitability

#### Why Search for Exomoons?

Moons may be more common habitable environments than planets:
- **Tidal heating**: Provides internal heat (like Europa, Enceladus)
- **Magnetic shielding**: Gas giant magnetosphere protects from radiation
- **More targets**: Giant planets in HZ may have multiple moons

#### Detection Methods

| Method | Sensitivity | Status |
|--------|-------------|--------|
| Transit Timing Variations (TTV) | Large moons | Active |
| Transit Duration Variations (TDV) | Medium moons | Active |
| Direct Transit | Very large moons | Challenging |
| Radial Velocity | Not practical | — |

#### Candidate Exomoons

**Kepler-1625b I** (disputed)
- Size: Neptune-sized (if confirmed)
- Host: Jupiter-sized planet at 0.87 AU
- Status: Under debate

**Kepler-1708b I** (candidate)
- Size: ~2.6 Earth radii
- Host: Jupiter-sized planet at 1.6 AU
- Status: Awaiting confirmation

#### Habitability Considerations

**Advantages:**
- Protection from cosmic rays by planet magnetosphere
- Tidal heating maintains liquid water
- Multiple energy sources (stellar + tidal)

**Challenges:**
- Tidal locking to planet (not star)
- Eclipse periods (darkness)
- Radiation from planet's radiation belts
            """,
            'kz': """
### Экзосерік анықтау және мекендеуге жарамдылық

#### Экзосеріктерді неге іздейміз?

Серіктер планеталарға қарағанда көп мекендеуге жарамды орта болуы мүмкін:
- **Толқындық қыздыру**: Ішкі жылуды қамтамасыз етеді
- **Магниттік қорғаныс**: Газ алыбының магнитосферасы сәулеленуден қорғайды

#### Анықтау әдістері

- Transit Timing Variations (TTV)
- Transit Duration Variations (TDV)
- Тікелей транзит
            """
        }
    },
    
    'stellar_evolution': {
        'title': {'en': '⭐ Stellar Evolution', 'kz': '⭐ Жұлдыздың эволюциясы'},
        'content': {
            'en': """
### How Stars Evolve and Affect Habitability

#### Main Sequence Lifetime

| Spectral Type | Mass (M☉) | Lifespan | HZ Stability |
|---------------|-----------|----------|--------------|
| O | 16-150 | <10 Myr | ❌ Too short |
| B | 2-16 | 10-300 Myr | ❌ Too short |
| A | 1.4-2.1 | 0.3-2 Gyr | ⚠️ Marginal |
| F | 1.0-1.4 | 2-7 Gyr | ✅ Sufficient |
| G | 0.8-1.04 | 7-15 Gyr | ✅ Optimal |
| K | 0.45-0.8 | 15-50 Gyr | ✅ Excellent |
| M | 0.08-0.45 | 50+ Gyr | ⚠️ Flares |

#### Habitable Zone Migration

As stars age, they become more luminous:
1. **Early MS**: HZ closer to star
2. **Mid MS**: HZ expands outward
3. **Late MS**: HZ continues expanding
4. **Red Giant**: Inner planets engulfed

**Continuously Habitable Zone (CHZ):**
Region that remains habitable for >4 Gyr

#### Stellar Activity

**Young Stars (< 1 Gyr):**
- High UV and X-ray emission
- Frequent flares
- Strong stellar wind
- Atmosphere stripping risk

**Mature Stars (1-10 Gyr):**
- Reduced activity
- Stable luminosity
- Best for life development

**Old Stars (> 10 Gyr):**
- Very low activity (good)
- HZ may have migrated past rocky planets
            """,
            'kz': """
### Жұлдыздар қалай дамиды және мекендеуге жарамдылыққа әсер етеді

#### Негізгі тізбек өмір сүру уақыты

Жұлдыздар қартайған сайын олар жарығырақ болады:
1. **Ерте MS**: МЖА жұлдызға жақын
2. **Орта MS**: МЖА сыртқа қарай кеңейеді
3. **Кеш MS**: МЖА кеңеюді жалғастырады
4. **Қызыл алып**: Ішкі планеталар жұтылады
            """
        }
    },
    
    'biosignatures': {
        'title': {'en': '🧬 Biosignatures', 'kz': '🧬 Биоқолтаңбалар'},
        'content': {
            'en': """
### Detecting Life on Exoplanets

#### What Are Biosignatures?

Observable features that indicate the presence of life:
- **Atmospheric**: Chemical disequilibrium
- **Surface**: Vegetation "red edge"
- **Temporal**: Seasonal variations

#### Atmospheric Biosignatures

| Molecule | Source | Detectability |
|----------|--------|---------------|
| O₂ | Photosynthesis | JWST (limited) |
| O₃ | O₂ photolysis | JWST ✅ |
| CH₄ | Methanogenesis | JWST ✅ |
| N₂O | Denitrification | Future missions |
| NH₃ | Biological | Future missions |

**Key Combinations:**
- O₂ + CH₄ = Strong biosignature (unstable without replenishment)
- O₃ + CH₄ + N₂O = Very strong indicator

#### False Positives

**Abiotic O₂ sources:**
- Photolysis of H₂O + H escape
- CO₂ photolysis
- Extremely high volcanic activity

**How to distinguish:**
- Check for O₄ (oxygen dimer)
- Look for absence of CO
- Examine overall atmospheric context

#### JWST Capabilities

**Current targets:**
- TRAPPIST-1 system (7 planets)
- LHS-1140b (super-Earth in HZ)
- K2-18b (mini-Neptune with H₂O)

**Detectable species:**
- H₂O, CO₂, CH₄, CO
- NH₃ (in hydrogen-rich atmospheres)
- O₃ (challenging but possible)

#### Future Missions

**HabEx / LUVOIR concepts:**
- Direct imaging of Earth-like planets
- High-contrast spectroscopy
- Vegetation "red edge" detection

**LIFE (Large Interferometer For Exoplanets):**
- Mid-infrared interferometry
- Thermal emission spectroscopy
- CO₂, O₃, H₂O simultaneously
            """,
            'kz': """
### Экзопланеталардағы өмірді анықтау

#### Биоқолтаңбалар дегеніміз не?

Өмірдің бар екенін көрсететін бақыланатын ерекшеліктер:
- **Атмосфералық**: Химиялық теңсіздік
- **Бетті**: Өсімдіктің "қызыл шеті"
- **Уақытша**: Маусымдық өзгерістер

#### JWST мүмкіндіктері

**Қазіргі мақсаттар:**
- TRAPPIST-1 жүйесі (7 планета)
- LHS-1140b (МЖА-дағы супер-Жер)
- K2-18b (H₂O бар мини-Нептун)
            """
        }
    }
}

# Add extended encyclopedia entries to main ENCYCLOPEDIA
ENCYCLOPEDIA.update(ENCYCLOPEDIA_EXTENDED)

# ═══════════════════════════════════════════════════════════════════════════════
# QR CODE GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_qr_code(url, size=10):
    """Generate QR code for presentation."""
    try:
        import qrcode
        from io import BytesIO
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="white", back_color="#1a1a2e")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    except ImportError:
        return None

def render_qr_section():
    """Render QR code section for presentations."""
    qr_base64 = generate_qr_code("https://atlasaishymkent.streamlit.app/", size=8)
    
    if qr_base64:
        st.markdown(f"""
        <div style="text-align: center; padding: 30px; background: rgba(255,255,255,0.05); 
                    border-radius: 20px; margin: 20px 0;">
            <h3 style="color: white; margin-bottom: 20px;">🔗 Try ATLAS Online</h3>
            <img src="data:image/png;base64,{qr_base64}" style="width: 200px; height: 200px; border-radius: 10px;">
            <p style="color: rgba(255,255,255,0.6); margin-top: 15px; font-size: 0.9rem;">
                Scan to open ATLAS
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("QR Code generation requires 'qrcode' package")

# ═══════════════════════════════════════════════════════════════════════════════
# ADVANCED HABITABILITY METRICS
# ═══════════════════════════════════════════════════════════════════════════════

def calc_biological_complexity_index(esi, temp, in_hz, mag_field, atmo_type, gravity):
    """Calculate potential for complex life (0-100)."""
    score = 0
    
    # Base ESI component (0-25)
    score += esi * 25
    
    # Temperature suitability (0-20)
    if 270 <= temp <= 300:
        score += 20
    elif 250 <= temp <= 320:
        score += 15
    elif 200 <= temp <= 350:
        score += 8
    
    # Habitable zone (0-15)
    if in_hz:
        score += 15
    
    # Magnetic field protection (0-15)
    if mag_field and mag_field > 0.5:
        score += 15
    elif mag_field and mag_field > 0.2:
        score += 8
    
    # Atmosphere (0-15)
    if "N₂/O₂" in atmo_type or "biosignature" in atmo_type.lower():
        score += 15
    elif "N₂/CO₂" in atmo_type:
        score += 10
    elif "thin" in atmo_type.lower():
        score += 3
    
    # Gravity (0-10)
    if 0.8 <= gravity <= 1.3:
        score += 10
    elif 0.5 <= gravity <= 1.8:
        score += 6
    elif 0.3 <= gravity <= 2.5:
        score += 3
    
    return min(100, max(0, round(score)))

def calc_terraforming_index(radius, mass, temp, in_hz, gravity, distance):
    """Calculate terraforming feasibility (0-100)."""
    score = 0
    
    # Size suitability (0-25)
    if 0.5 <= radius <= 1.5:
        score += 25
    elif 0.3 <= radius <= 2.0:
        score += 15
    else:
        score += 5
    
    # Temperature (0-25)
    if 200 <= temp <= 350:
        score += 25
    elif 150 <= temp <= 400:
        score += 15
    elif 100 <= temp <= 500:
        score += 5
    
    # Habitable zone (0-20)
    if in_hz:
        score += 20
    
    # Gravity (0-15)
    if 0.5 <= gravity <= 1.5:
        score += 15
    elif 0.3 <= gravity <= 2.0:
        score += 10
    else:
        score += 3
    
    # Distance penalty (0-15)
    if distance:
        if distance < 20:
            score += 15
        elif distance < 50:
            score += 10
        elif distance < 100:
            score += 5
    
    return min(100, max(0, round(score)))

# ═══════════════════════════════════════════════════════════════════════════════
# STATISTICAL ANALYSIS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_planet_population():
    """Generate statistical analysis of discovered planets."""
    all_planets = get_all_planets()
    
    if not all_planets:
        return None
    
    # Basic statistics
    radii = [p['radius'] for p in all_planets]
    temps = [p['temp'] for p in all_planets]
    scores = [p['hab_score'] for p in all_planets]
    esis = [p['esi'] for p in all_planets]
    
    stats = {
        'count': len(all_planets),
        'radius': {
            'mean': np.mean(radii),
            'median': np.median(radii),
            'std': np.std(radii),
            'min': min(radii),
            'max': max(radii)
        },
        'temperature': {
            'mean': np.mean(temps),
            'median': np.median(temps),
            'std': np.std(temps),
            'min': min(temps),
            'max': max(temps)
        },
        'habitability': {
            'mean': np.mean(scores),
            'median': np.median(scores),
            'std': np.std(scores),
            'top_quartile': np.percentile(scores, 75)
        },
        'esi': {
            'mean': np.mean(esis),
            'median': np.median(esis),
            'max': max(esis)
        },
        'hz_fraction': sum(1 for p in all_planets if p['in_hz']) / len(all_planets),
        'earth_like_fraction': sum(1 for p in all_planets if 0.8 <= p['radius'] <= 1.5) / len(all_planets)
    }
    
    # Type distribution
    type_counts = {}
    for p in all_planets:
        ptype = p['type']
        type_counts[ptype] = type_counts.get(ptype, 0) + 1
    
    stats['type_distribution'] = type_counts
    
    return stats

def generate_statistical_report():
    """Generate a comprehensive statistical report."""
    stats = analyze_planet_population()
    
    if not stats:
        return None
    
    lang = st.session_state.get('lang', 'en')
    
    report = {
        'en': f"""
## 📊 Research Statistical Report

### Population Overview
- **Total planets analyzed:** {stats['count']}
- **Habitable zone planets:** {stats['hz_fraction']*100:.1f}%
- **Earth-like planets (0.8-1.5 R⊕):** {stats['earth_like_fraction']*100:.1f}%

### Size Distribution
- **Mean radius:** {stats['radius']['mean']:.2f} R⊕
- **Median radius:** {stats['radius']['median']:.2f} R⊕
- **Range:** {stats['radius']['min']:.2f} - {stats['radius']['max']:.2f} R⊕

### Temperature Analysis
- **Mean temperature:** {stats['temperature']['mean']:.0f} K
- **Range:** {stats['temperature']['min']:.0f} - {stats['temperature']['max']:.0f} K
- **Earth-like range (250-310K):** {sum(1 for p in get_all_planets() if 250 <= p['temp'] <= 310)} planets

### Habitability Metrics
- **Mean score:** {stats['habitability']['mean']:.1f}/100
- **Median score:** {stats['habitability']['median']:.1f}/100
- **Top quartile threshold:** {stats['habitability']['top_quartile']:.1f}
- **Mean ESI:** {stats['esi']['mean']:.3f}
- **Best ESI:** {stats['esi']['max']:.3f}

### Key Findings
1. {stats['count']} exoplanets discovered across {len(st.session_state.saved_systems)} systems
2. {stats['hz_fraction']*100:.1f}% of planets orbit within their star's habitable zone
3. The most Earth-like planet has ESI = {stats['esi']['max']:.3f}
        """,
        'kz': f"""
## 📊 Зерттеу статистикалық есебі

### Популяцияға шолу
- **Талданған планеталар саны:** {stats['count']}
- **Мекендеуге жарамды аймақ планеталары:** {stats['hz_fraction']*100:.1f}%
- **Жерге ұқсас планеталар:** {stats['earth_like_fraction']*100:.1f}%

### Өлшем таралуы
- **Орташа радиус:** {stats['radius']['mean']:.2f} R⊕
- **Медиана радиус:** {stats['radius']['median']:.2f} R⊕

### Температура талдауы
- **Орташа температура:** {stats['temperature']['mean']:.0f} K
- **Жерге ұқсас диапазон (250-310K):** {sum(1 for p in get_all_planets() if 250 <= p['temp'] <= 310)} планета

### Мекендеуге жарамдылық көрсеткіштері
- **Орташа балл:** {stats['habitability']['mean']:.1f}/100
- **Орташа ESI:** {stats['esi']['mean']:.3f}
- **Ең жақсы ESI:** {stats['esi']['max']:.3f}
        """
    }
    
    return report[lang]

# ═══════════════════════════════════════════════════════════════════════════════
# MISSION PLANNING TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_mission_priority(planet):
    """Calculate research priority score for a planet."""
    priority = 0
    factors = []
    
    # Habitability weight (0-40)
    hab_score = planet.get('hab_score', 0)
    priority += hab_score * 0.4
    if hab_score >= 70:
        factors.append("High habitability score")
    
    # Distance weight (0-20)
    distance = planet.get('distance', 1000)
    if distance and distance < 20:
        priority += 20
        factors.append("Very close target")
    elif distance and distance < 50:
        priority += 15
        factors.append("Nearby target")
    elif distance and distance < 100:
        priority += 10
    
    # ESI weight (0-20)
    esi = planet.get('esi', 0)
    priority += esi * 20
    if esi > 0.8:
        factors.append("Earth-like ESI")
    
    # In HZ bonus (0-10)
    if planet.get('in_hz', False):
        priority += 10
        factors.append("In habitable zone")
    
    # Atmosphere interest (0-10)
    atmo = planet.get('atmo_type', '')
    if "N₂/O₂" in atmo or "biosignature" in atmo.lower():
        priority += 10
        factors.append("Potentially biogenic atmosphere")
    elif "N₂/CO₂" in atmo:
        priority += 5
    
    return min(100, round(priority)), factors

def suggest_follow_up_observations(planet):
    """Suggest follow-up observations for a planet."""
    suggestions = []
    
    # Transit spectroscopy
    if planet.get('radius', 1) > 0.5:
        suggestions.append({
            'method': 'Transit Spectroscopy',
            'instrument': 'JWST NIRSpec/MIRI',
            'target': 'Atmospheric composition',
            'priority': 'High' if planet.get('in_hz') else 'Medium'
        })
    
    # Radial velocity confirmation
    suggestions.append({
        'method': 'Radial Velocity',
        'instrument': 'ESPRESSO/HARPS',
        'target': 'Mass determination',
        'priority': 'High' if planet.get('radius', 1) < 2 else 'Medium'
    })
    
    # Phase curve
    if planet.get('period', 100) < 20:
        suggestions.append({
            'method': 'Phase Curve Analysis',
            'instrument': 'JWST MIRI',
            'target': 'Temperature map, cloud properties',
            'priority': 'Medium'
        })
    
    # High-contrast imaging (for wide orbits)
    if planet.get('orbit', 0) > 5:
        suggestions.append({
            'method': 'Direct Imaging',
            'instrument': 'Future ELT/HabEx',
            'target': 'Direct characterization',
            'priority': 'Low (future)'
        })
    
    return suggestions

# ═══════════════════════════════════════════════════════════════════════════════
# RENDER FUNCTIONS FOR NEW FEATURES
# ═══════════════════════════════════════════════════════════════════════════════

def render_detailed_planet_analysis(planet):
    """Render detailed scientific analysis for a planet."""
    st.markdown("### 🔬 Detailed Scientific Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Extended calculations
        st.markdown("#### Physical Properties")
        
        rotation, rot_desc = estimate_rotation_period(
            planet['mass'], planet['radius'], planet['orbit'], 1.0
        )
        st.markdown(f"**Rotation Period:** {rotation:.1f}h ({rot_desc})")
        
        tectonics_prob, tectonics_desc = calc_plate_tectonics_probability(
            planet['mass'], planet['radius'], planet['temp']
        )
        st.markdown(f"**Plate Tectonics:** {tectonics_prob*100:.0f}% ({tectonics_desc})")
        
        water_ret, water_desc = calc_water_retention(
            planet['mass'], planet['radius'], planet['temp'], 
            5778, planet['orbit']
        )
        st.markdown(f"**Water Retention:** {water_ret*100:.0f}% ({water_desc})")
    
    with col2:
        # Advanced metrics
        st.markdown("#### Habitability Indices")
        
        bci = calc_biological_complexity_index(
            planet['esi'], planet['temp'], planet['in_hz'],
            planet.get('mag_strength', 0), planet['atmo_type'], planet['gravity']
        )
        st.metric("Biological Complexity Index", f"{bci}/100")
        
        tfi = calc_terraforming_index(
            planet['radius'], planet['mass'], planet['temp'],
            planet['in_hz'], planet['gravity'], planet.get('distance')
        )
        st.metric("Terraforming Feasibility", f"{tfi}/100")
    
    # Mission priority
    st.markdown("---")
    st.markdown("#### 🎯 Research Priority")
    
    priority, factors = calculate_mission_priority(planet)
    st.metric("Priority Score", f"{priority}/100")
    
    if factors:
        st.markdown("**Key factors:**")
        for factor in factors:
            st.markdown(f"• {factor}")
    
    # Follow-up suggestions
    st.markdown("---")
    st.markdown("#### 🔭 Suggested Follow-up Observations")
    
    suggestions = suggest_follow_up_observations(planet)
    for sug in suggestions:
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; margin: 5px 0;">
            <b>{sug['method']}</b> ({sug['priority']})<br>
            <span style="color: rgba(255,255,255,0.7);">{sug['instrument']} → {sug['target']}</span>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ADDITIONAL VISUALIZATION CHARTS
# ═══════════════════════════════════════════════════════════════════════════════

def create_mass_radius_diagram():
    """Create mass-radius diagram with discovered planets."""
    all_planets = get_all_planets()
    
    if not all_planets:
        return go.Figure()
    
    fig = go.Figure()
    
    # Add theoretical composition lines
    radii = np.linspace(0.3, 4, 50)
    
    # Pure iron composition
    iron_mass = radii ** 3.7
    fig.add_trace(go.Scatter(
        x=radii, y=iron_mass,
        mode='lines',
        name='Pure Iron',
        line=dict(color='gray', dash='dash')
    ))
    
    # Earth-like composition
    earth_mass = radii ** 3.0
    fig.add_trace(go.Scatter(
        x=radii, y=earth_mass,
        mode='lines',
        name='Earth-like',
        line=dict(color='#7cb97c', dash='dash')
    ))
    
    # Pure water composition
    water_mass = radii ** 2.5
    fig.add_trace(go.Scatter(
        x=radii, y=water_mass,
        mode='lines',
        name='Pure Water',
        line=dict(color='#00d4ff', dash='dash')
    ))
    
    # Add discovered planets
    for planet in all_planets:
        color = '#7cb97c' if planet['hab_score'] >= 70 else '#d4a574' if planet['hab_score'] >= 40 else '#e07878'
        
        fig.add_trace(go.Scatter(
            x=[planet['radius']],
            y=[planet['mass']],
            mode='markers',
            name=planet['name'],
            marker=dict(size=12, color=color, line=dict(width=1, color='white')),
            hovertemplate=f"<b>{planet['name']}</b><br>R: {planet['radius']:.2f} R⊕<br>M: {planet['mass']:.2f} M⊕<br>Score: {planet['hab_score']}<extra></extra>"
        ))
    
    # Reference planets
    references = [
        ('Earth', 1.0, 1.0),
        ('Mars', 0.53, 0.107),
        ('Venus', 0.95, 0.815)
    ]
    
    for name, r, m in references:
        fig.add_trace(go.Scatter(
            x=[r], y=[m],
            mode='markers+text',
            name=name,
            marker=dict(size=15, color='gold', symbol='star'),
            text=[name],
            textposition='top center',
            textfont=dict(color='white')
        ))
    
    fig.update_layout(
        title='Mass-Radius Diagram',
        xaxis=dict(
            title='Radius (R⊕)',
            gridcolor='rgba(255,255,255,0.1)',
            tickfont=dict(color='white'),
            titlefont=dict(color='white'),
            type='log'
        ),
        yaxis=dict(
            title='Mass (M⊕)',
            gridcolor='rgba(255,255,255,0.1)',
            tickfont=dict(color='white'),
            titlefont=dict(color='white'),
            type='log'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(font=dict(color='white'), bgcolor='rgba(0,0,0,0)'),
        height=450
    )
    
    return fig

def create_habitability_heatmap():
    """Create heatmap of habitability vs temperature and radius."""
    # Create grid
    temps = np.linspace(150, 500, 20)
    radii = np.linspace(0.3, 4, 20)
    
    T, R = np.meshgrid(temps, radii)
    
    # Calculate habitability scores for grid
    Z = np.zeros_like(T)
    
    for i in range(len(radii)):
        for j in range(len(temps)):
            esi = calc_esi(radii[i], temps[j])
            in_hz = 250 <= temps[j] <= 350
            
            # Simplified score
            score = 0
            if 250 <= temps[j] <= 310:
                score += 30
            elif 200 <= temps[j] <= 350:
                score += 15
            
            if 0.8 <= radii[i] <= 1.25:
                score += 25
            elif 0.5 <= radii[i] <= 2.0:
                score += 15
            
            score += esi * 30
            
            if in_hz:
                score += 15
            
            Z[i, j] = min(100, score)
    
    fig = go.Figure(data=go.Heatmap(
        x=temps,
        y=radii,
        z=Z,
        colorscale=[
            [0, '#1a1a2e'],
            [0.3, '#e07878'],
            [0.5, '#d4a574'],
            [0.7, '#00d4ff'],
            [1.0, '#7cb97c']
        ],
        colorbar=dict(title='Habitability Score', tickfont=dict(color='white'))
    ))
    
    # Add discovered planets as markers
    all_planets = get_all_planets()
    if all_planets:
        planet_temps = [p['temp'] for p in all_planets]
        planet_radii = [p['radius'] for p in all_planets]
        
        fig.add_trace(go.Scatter(
            x=planet_temps,
            y=planet_radii,
            mode='markers',
            marker=dict(size=10, color='white', symbol='x', line=dict(width=2, color='black')),
            name='Discovered Planets',
            hovertemplate='T: %{x:.0f}K<br>R: %{y:.2f} R⊕<extra></extra>'
        ))
    
    # Mark Earth position
    fig.add_trace(go.Scatter(
        x=[288],
        y=[1.0],
        mode='markers+text',
        marker=dict(size=15, color='gold', symbol='star'),
        text=['Earth'],
        textposition='top center',
        textfont=dict(color='white', size=12),
        name='Earth'
    ))
    
    fig.update_layout(
        title='Habitability Parameter Space',
        xaxis=dict(
            title='Equilibrium Temperature (K)',
            gridcolor='rgba(255,255,255,0.1)',
            tickfont=dict(color='white'),
            titlefont=dict(color='white')
        ),
        yaxis=dict(
            title='Radius (R⊕)',
            gridcolor='rgba(255,255,255,0.1)',
            tickfont=dict(color='white'),
            titlefont=dict(color='white')
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(font=dict(color='white'), bgcolor='rgba(0,0,0,0)'),
        height=450
    )
    
    return fig

def create_discovery_timeline():
    """Create timeline of discoveries by method."""
    all_planets = get_all_planets()
    
    if not all_planets:
        return go.Figure()
    
    # Group by discovery method
    methods = {}
    for p in all_planets:
        method = p.get('disc_method', 'Unknown')
        if method not in methods:
            methods[method] = 0
        methods[method] += 1
    
    fig = go.Figure(data=[
        go.Pie(
            labels=list(methods.keys()),
            values=list(methods.values()),
            hole=0.4,
            marker=dict(colors=['#d4a574', '#7cb97c', '#00d4ff', '#e07878', '#9b59b6']),
            textinfo='percent+label',
            textfont=dict(color='white')
        )
    ])
    
    fig.update_layout(
        title='Discoveries by Detection Method',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(font=dict(color='white'), bgcolor='rgba(0,0,0,0)'),
        height=350
    )
    
    return fig

def render_advanced_charts():
    """Render advanced visualization charts."""
    st.markdown("### 📈 Advanced Analytics")
    
    tab1, tab2, tab3 = st.tabs(["Mass-Radius", "Habitability Map", "Discovery Methods"])
    
    with tab1:
        st.plotly_chart(create_mass_radius_diagram(), use_container_width=True)
        st.caption("Mass-Radius diagram with composition curves. Earth-like composition follows R³ relationship.")
    
    with tab2:
        st.plotly_chart(create_habitability_heatmap(), use_container_width=True)
        st.caption("Habitability score as function of temperature and radius. Green = most habitable.")
    
    with tab3:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.plotly_chart(create_discovery_timeline(), use_container_width=True)
        with col2:
            st.markdown("**Detection Methods:**")
            st.markdown("""
            - **Transit**: Planet crosses star
            - **RV**: Star wobbles
            - **Imaging**: Direct photo
            - **Microlensing**: Gravitational lens
            """)

# ═══════════════════════════════════════════════════════════════════════════════
# EXPORT & REPORTING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def export_research_data():
    """Export research data as JSON."""
    export_data = {
        'metadata': {
            'version': 'ATLAS v21 Full',
            'export_date': datetime.now().isoformat(),
            'total_systems': len(st.session_state.saved_systems),
            'total_planets': sum(d['planet_count'] for d in st.session_state.saved_systems.values()) if st.session_state.saved_systems else 0
        },
        'systems': {},
        'achievements': list(st.session_state.achievements.keys()),
        'statistics': analyze_planet_population()
    }
    
    for hostname, data in st.session_state.saved_systems.items():
        export_data['systems'][hostname] = {
            'star': data['star'],
            'planets': [
                {
                    'name': p['name'],
                    'radius': p['radius'],
                    'mass': p['mass'],
                    'temp': p['temp'],
                    'period': p['period'],
                    'orbit': p['orbit'],
                    'esi': p['esi'],
                    'hab_score': p['hab_score'],
                    'in_hz': p['in_hz'],
                    'type': p['type']
                }
                for p in data['planets']
            ],
            'timestamp': data.get('timestamp')
        }
    
    return json.dumps(export_data, indent=2, default=str)

def generate_pdf_report_content():
    """Generate content for PDF report."""
    stats = analyze_planet_population()
    
    if not stats:
        return None
    
    content = f"""
ATLAS RESEARCH REPORT
=====================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

EXECUTIVE SUMMARY
-----------------
Total star systems explored: {len(st.session_state.saved_systems)}
Total exoplanets analyzed: {stats['count']}
Planets in habitable zone: {stats['hz_fraction']*100:.1f}%
Earth-like candidates: {stats['earth_like_fraction']*100:.1f}%

KEY FINDINGS
------------
1. Mean planet radius: {stats['radius']['mean']:.2f} R⊕
2. Mean equilibrium temperature: {stats['temperature']['mean']:.0f} K
3. Mean habitability score: {stats['habitability']['mean']:.1f}/100
4. Best Earth Similarity Index: {stats['esi']['max']:.3f}

TOP CANDIDATES
--------------
"""
    
    top_5 = get_top_candidates(5)
    for i, p in enumerate(top_5, 1):
        content += f"\n{i}. {p['name']}\n"
        content += f"   Score: {p['hab_score']}/100 | ESI: {p['esi']:.3f}\n"
        content += f"   Type: {p['type']} | Temp: {p['temp']:.0f}K\n"
        content += f"   {'In Habitable Zone' if p['in_hz'] else 'Outside HZ'}\n"
    
    content += """

METHODOLOGY
-----------
Data source: NASA Exoplanet Archive TAP Service
Habitability scoring: Multi-factor analysis including:
- Temperature suitability (0-25 pts)
- Size/radius match (0-20 pts)
- Habitable zone location (0-20 pts)
- Earth Similarity Index (0-15 pts)
- Surface gravity (0-10 pts)
- Stellar type (0-5 pts)
- Atmospheric indicators (0-5 pts)

DISCLAIMER
----------
This is an educational research platform for diploma project purposes.
All data derived from NASA Exoplanet Archive public datasets.
Habitability scores are theoretical estimates, not confirmed values.

---
ATLAS v21 Full Edition
Autonomous Terrestrial Life Analysis System
Diploma Project 2024-2025
"""
    
    return content

# Update render_analysis_page to include new features
def render_analysis_page_extended():
    """Extended analysis page with all new features."""
    render_analysis_page()
    
    if st.session_state.saved_systems:
        st.markdown("---")
        render_advanced_charts()
        
        st.markdown("---")
        report = generate_statistical_report()
        if report:
            with st.expander("📄 View Full Statistical Report"):
                st.markdown(report)
        
        # Export buttons
        st.markdown("---")
        st.markdown("### 📤 Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Export JSON", use_container_width=True):
                json_data = export_research_data()
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"atlas_research_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("📄 Generate Report", use_container_width=True):
                report_content = generate_pdf_report_content()
                if report_content:
                    st.download_button(
                        label="Download Report",
                        data=report_content,
                        file_name=f"atlas_report_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain"
                    )