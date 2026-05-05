"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                              ATLAS v21                                        ║
║          Autonomous Terrestrial Life Analysis System                          ║
║                                                                               ║
║  Дипломный проект: Платформа исследования экзопланет                         ║
║                                                                               ║
║  Features:                                                                    ║
║  - NASA Exoplanet Archive integration                                         ║
║  - 3D stellar neighborhood map                                                ║
║  - Smart AI analysis & hypothesis generation                                  ║
║  - Achievement system                                                         ║
║  - LocalStorage persistence                                                   ║
║  - Multilingual (RU/EN/KZ)                                                    ║
║  - Dark/Light adaptive themes                                                 ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import math
import numpy as np
import requests
import time
import random
import json
import base64
from datetime import datetime
from pathlib import Path
import streamlit.components.v1 as components

# ═══════════════════════════════════════════════════════════════════════════════
# LOCAL STORAGE (Browser persistence)
# ═══════════════════════════════════════════════════════════════════════════════
try:
    from streamlit_js_eval import streamlit_js_eval
    LOCAL_STORAGE_AVAILABLE = True
except ImportError:
    LOCAL_STORAGE_AVAILABLE = False


def save_to_local_storage():
    """Save session data to browser localStorage."""
    if not LOCAL_STORAGE_AVAILABLE:
        return
    
    try:
        # Prepare data for saving (convert sets to lists)
        data = {
            'saved_systems': st.session_state.get('saved_systems', {}),
            'scanned_stars': list(st.session_state.get('scanned_stars', set())),
            'achievements_unlocked': st.session_state.get('achievements_unlocked', []),
            'total_planets_found': st.session_state.get('total_planets_found', 0),
            'habitable_count': st.session_state.get('habitable_count', 0),
            'weather_views': list(st.session_state.get('weather_views', set())),
            'catalogs_explored': list(st.session_state.get('catalogs_explored', set())),
            'compare': st.session_state.get('compare', []),
            'theme': st.session_state.get('theme', 'dark'),
            'lang': st.session_state.get('lang', 'ru'),
        }
        
        json_data = json.dumps(data, ensure_ascii=False)
        # Escape for JavaScript
        json_data = json_data.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
        
        streamlit_js_eval(js_expressions=f"localStorage.setItem('atlas_v21_data', '{json_data}')", key="save_ls")
    except Exception as e:
        pass  # Silently fail


def load_from_local_storage():
    """Load session data from browser localStorage."""
    if not LOCAL_STORAGE_AVAILABLE:
        return False
    
    try:
        raw_data = streamlit_js_eval(js_expressions="localStorage.getItem('atlas_v21_data')", key="load_ls")
        
        if raw_data and raw_data != 'null':
            data = json.loads(raw_data)
            
            # Restore data to session state
            if 'saved_systems' in data:
                st.session_state.saved_systems = data['saved_systems']
            if 'scanned_stars' in data:
                st.session_state.scanned_stars = set(data['scanned_stars'])
            if 'achievements_unlocked' in data:
                st.session_state.achievements_unlocked = data['achievements_unlocked']
            if 'total_planets_found' in data:
                st.session_state.total_planets_found = data['total_planets_found']
            if 'habitable_count' in data:
                st.session_state.habitable_count = data['habitable_count']
            if 'weather_views' in data:
                st.session_state.weather_views = set(data['weather_views'])
            if 'catalogs_explored' in data:
                st.session_state.catalogs_explored = set(data['catalogs_explored'])
            if 'compare' in data:
                st.session_state.compare = data['compare']
            if 'theme' in data:
                st.session_state.theme = data['theme']
            if 'lang' in data:
                st.session_state.lang = data['lang']
            
            return True
    except Exception as e:
        pass
    
    return False


def clear_local_storage():
    """Clear all saved data from localStorage."""
    if LOCAL_STORAGE_AVAILABLE:
        try:
            streamlit_js_eval(js_expressions="localStorage.removeItem('atlas_v21_data')", key="clear_ls")
        except:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# ML MODELS
# ═══════════════════════════════════════════════════════════════════════════════
try:
    import joblib
    # Chatbot model
    chatbot_model = joblib.load('exo_chatbot_model.pkl')
    with open('exo_chatbot_responses.json', 'r', encoding='utf-8') as f:
        chatbot_responses = json.load(f)
    CHATBOT_AVAILABLE = True
except:
    chatbot_model = None
    chatbot_responses = {}
    CHATBOT_AVAILABLE = False

# Exoplanet habitability prediction model
try:
    import joblib
    exoplanet_model = joblib.load('exoplanet_model.pkl')
    exoplanet_features = joblib.load('features.pkl')
    EXOPLANET_MODEL_AVAILABLE = True
except:
    exoplanet_model = None
    exoplanet_features = None
    EXOPLANET_MODEL_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="ATLAS — Exoplanet Research Platform",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════════
DEFAULTS = {
    'lang': 'en',
    'theme': 'dark',
    'current_page': 'missions',
    'scan_count': 0,
    'habitable_count': 0,
    'selected_idx': 0,
    'compare': [],
    'chat_history': [],
    'custom_planets': {},
    'atlas_results': [],
    'saved_systems': {},
    'scanned_stars': set(),
    'current_system': None,
    'selected_catalog': 'nearby',
    'presentation_mode': False,
    'hypotheses': [],
    'recommendations': [],
    'achievements_unlocked': [],
    'achievement_popup': None,
    'total_planets_found': 0,
    'ai_uses': 0,
    'catalogs_explored': set(),
    'weather_views': set(),
    'local_storage_loaded': False,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Load data from localStorage on first run
if not st.session_state.get('local_storage_loaded', False):
    if load_from_local_storage():
        st.session_state.local_storage_loaded = True
    else:
        st.session_state.local_storage_loaded = True

if isinstance(st.session_state.scanned_stars, list):
    st.session_state.scanned_stars = set(st.session_state.scanned_stars)
if isinstance(st.session_state.get('catalogs_explored'), list):
    st.session_state.catalogs_explored = set(st.session_state.catalogs_explored)
if isinstance(st.session_state.get('weather_views'), list):
    st.session_state.weather_views = set(st.session_state.weather_views)

if st.session_state.get('lang') not in ('en', 'kz'):
    st.session_state.lang = 'en'

st.session_state.theme = 'dark'

# ═══════════════════════════════════════════════════════════════════════════════
# ACHIEVEMENTS SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
ACHIEVEMENTS = {
    # EASY (Bronze)
    'first_contact': {
        'icon': '🌟', 'tier': 'bronze',
        'ru': 'Первый контакт', 'en': 'First Contact', 'kz': 'Алғашқы байланыс',
        'desc_ru': 'Изучить первую звёздную систему',
        'desc_en': 'Study your first star system',
        'desc_kz': 'Алғашқы жұлдыз жүйесін зерттеу',
    },
    'observer': {
        'icon': '🔭', 'tier': 'bronze',
        'ru': 'Наблюдатель', 'en': 'Observer', 'kz': 'Бақылаушы',
        'desc_ru': 'Изучить 5 звёздных систем',
        'desc_en': 'Study 5 star systems',
        'desc_kz': '5 жұлдыз жүйесін зерттеу',
    },
    'earth_twin': {
        'icon': '🌍', 'tier': 'bronze',
        'ru': 'Земной близнец', 'en': 'Earth Twin', 'kz': 'Жер егізі',
        'desc_ru': 'Найти планету с ESI > 0.8',
        'desc_en': 'Find a planet with ESI > 0.8',
        'desc_kz': 'ESI > 0.8 болатын планетаны табу',
    },
    'trappist_fan': {
        'icon': '⭐', 'tier': 'bronze',
        'ru': 'Фанат TRAPPIST', 'en': 'TRAPPIST Fan', 'kz': 'TRAPPIST жанкүйері',
        'desc_ru': 'Изучить систему TRAPPIST-1',
        'desc_en': 'Study the TRAPPIST-1 system',
        'desc_kz': 'TRAPPIST-1 жүйесін зерттеу',
    },
    'comparator': {
        'icon': '⚖️', 'tier': 'bronze',
        'ru': 'Сравниватель', 'en': 'Comparator', 'kz': 'Салыстырушы',
        'desc_ru': 'Сравнить 3 планеты',
        'desc_en': 'Compare 3 planets',
        'desc_kz': '3 планетаны салыстыру',
    },
    # MEDIUM (Silver)
    'world_hunter': {
        'icon': '🏆', 'tier': 'silver',
        'ru': 'Охотник за мирами', 'en': 'World Hunter', 'kz': 'Әлем аңшысы',
        'desc_ru': 'Изучить 15 звёздных систем',
        'desc_en': 'Study 15 star systems',
        'desc_kz': '15 жұлдыз жүйесін зерттеу',
    },
    'life_zone': {
        'icon': '🌱', 'tier': 'silver',
        'ru': 'Зона жизни', 'en': 'Life Zone', 'kz': 'Өмір аймағы',
        'desc_ru': 'Найти 5 планет в обитаемой зоне',
        'desc_en': 'Find 5 planets in habitable zone',
        'desc_kz': 'Мекендеуге жарамды аймақта 5 планета табу',
    },
    'scientist': {
        'icon': '🔬', 'tier': 'silver',
        'ru': 'Учёный', 'en': 'Scientist', 'kz': 'Ғалым',
        'desc_ru': 'Использовать AI анализ 10 раз',
        'desc_en': 'Use AI analysis 10 times',
        'desc_kz': 'AI талдауын 10 рет қолдану',
    },
    'catalog_master': {
        'icon': '📚', 'tier': 'silver',
        'ru': 'Мастер каталогов', 'en': 'Catalog Master', 'kz': 'Каталог шебері',
        'desc_ru': 'Исследовать все каталоги',
        'desc_en': 'Explore all catalogs',
        'desc_kz': 'Барлық каталогтарды зерттеу',
    },
    'night_owl': {
        'icon': '🦉', 'tier': 'silver',
        'ru': 'Ночная сова', 'en': 'Night Owl', 'kz': 'Түнгі жапалақ',
        'desc_ru': 'Провести сессию после полуночи',
        'desc_en': 'Have a session after midnight',
        'desc_kz': 'Түн ортасынан кейін сеанс өткізу',
    },
    # HARD (Gold)
    'rare_find': {
        'icon': '💎', 'tier': 'gold',
        'ru': 'Редкая находка', 'en': 'Rare Find', 'kz': 'Сирек табыс',
        'desc_ru': 'Найти планету с hab_score > 85',
        'desc_en': 'Find a planet with hab_score > 85',
        'desc_kz': 'hab_score > 85 болатын планета табу',
    },
    'galaxy_cartographer': {
        'icon': '🗺️', 'tier': 'gold',
        'ru': 'Картограф галактики', 'en': 'Galaxy Cartographer', 'kz': 'Галактика картографы',
        'desc_ru': 'Изучить 30 звёздных систем',
        'desc_en': 'Study 30 star systems',
        'desc_kz': '30 жұлдыз жүйесін зерттеу',
    },
    'kepler_legacy': {
        'icon': '🔭', 'tier': 'gold',
        'ru': 'Наследие Кеплера', 'en': 'Kepler Legacy', 'kz': 'Кеплер мұрасы',
        'desc_ru': 'Найти 50 планет',
        'desc_en': 'Find 50 planets',
        'desc_kz': '50 планета табу',
    },
    'weather_watcher': {
        'icon': '🌤️', 'tier': 'gold',
        'ru': 'Метеоролог', 'en': 'Weather Watcher', 'kz': 'Метеоролог',
        'desc_ru': 'Просмотреть прогноз погоды 10 планет',
        'desc_en': 'View weather forecast for 10 planets',
        'desc_kz': '10 планетаның ауа райын көру',
    },
    # LEGENDARY (Diamond)
    'atlas_master': {
        'icon': '👑', 'tier': 'diamond',
        'ru': 'Мастер ATLAS', 'en': 'ATLAS Master', 'kz': 'ATLAS шебері',
        'desc_ru': 'Получить все достижения',
        'desc_en': 'Unlock all achievements',
        'desc_kz': 'Барлық жетістіктерді ашу',
    },
    'pioneer': {
        'icon': '🚀', 'tier': 'diamond',
        'ru': 'Пионер', 'en': 'Pioneer', 'kz': 'Пионер',
        'desc_ru': 'Найти 100 планет',
        'desc_en': 'Find 100 planets',
        'desc_kz': '100 планета табу',
    },
}

TIER_COLORS = {
    'bronze': '#cd7f32',
    'silver': '#c0c0c0',
    'gold': '#ffd700',
    'diamond': '#b9f2ff',
}

def check_achievement(achievement_id):
    """Check and unlock an achievement."""
    if achievement_id not in st.session_state.achievements_unlocked:
        st.session_state.achievements_unlocked.append(achievement_id)
        st.session_state.achievement_popup = achievement_id
        return True
    return False

def check_all_achievements():
    """Check all achievement conditions."""
    systems_count = len(st.session_state.saved_systems)
    
    # First Contact
    if systems_count >= 1:
        check_achievement('first_contact')
    
    # Observer
    if systems_count >= 5:
        check_achievement('observer')
    
    # World Hunter
    if systems_count >= 15:
        check_achievement('world_hunter')
    
    # Galaxy Cartographer
    if systems_count >= 30:
        check_achievement('galaxy_cartographer')
    
    # TRAPPIST Fan
    if any('trappist' in s.lower() for s in st.session_state.saved_systems.keys()):
        check_achievement('trappist_fan')
    
    # Comparator
    if len(st.session_state.compare) >= 3:
        check_achievement('comparator')
    
    # Scientist
    if st.session_state.get('ai_uses', 0) >= 10:
        check_achievement('scientist')
    
    # Catalog Master
    if len(st.session_state.get('catalogs_explored', set())) >= 4:
        check_achievement('catalog_master')
    
    # Night Owl
    current_hour = datetime.now().hour
    if current_hour >= 0 and current_hour < 5:
        check_achievement('night_owl')
    
    # Kepler Legacy
    if st.session_state.get('total_planets_found', 0) >= 50:
        check_achievement('kepler_legacy')
    
    # Pioneer
    if st.session_state.get('total_planets_found', 0) >= 100:
        check_achievement('pioneer')


def render_achievement_popup():
    """Render achievement popup like Minecraft."""
    if st.session_state.achievement_popup:
        ach_id = st.session_state.achievement_popup
        ach = ACHIEVEMENTS.get(ach_id, {})
        lang = st.session_state.lang
        
        title = ach.get(lang, ach.get('en', 'Achievement'))
        desc = ach.get(f'desc_{lang}', ach.get('desc_en', ''))
        icon = ach.get('icon', '🏆')
        tier = ach.get('tier', 'bronze')
        color = TIER_COLORS.get(tier, '#ffd700')
        
        popup_text = {
            'ru': 'Достижение получено!',
            'en': 'Achievement Unlocked!',
            'kz': 'Жетістік ашылды!'
        }
        
        st.markdown(f"""
        <div id="achievement-popup" style="
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, rgba(20,20,30,0.95), rgba(40,40,60,0.95));
            border: 2px solid {color};
            border-radius: 16px;
            padding: 20px 25px;
            z-index: 9999;
            animation: slideIn 0.5s ease-out, fadeOut 0.5s ease-in 4.5s forwards;
            box-shadow: 0 0 30px {color}40, 0 10px 40px rgba(0,0,0,0.5);
            min-width: 300px;
        ">
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="font-size: 2.5rem; filter: drop-shadow(0 0 10px {color});">{icon}</div>
                <div>
                    <div style="font-size: 0.75rem; color: {color}; text-transform: uppercase; letter-spacing: 2px;">
                        {popup_text.get(lang, popup_text['en'])}
                    </div>
                    <div style="font-size: 1.2rem; font-weight: bold; color: white; margin: 5px 0;">{title}</div>
                    <div style="font-size: 0.85rem; color: rgba(255,255,255,0.7);">{desc}</div>
                </div>
            </div>
        </div>
        
        <style>
        @keyframes slideIn {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        @keyframes fadeOut {{
            from {{ opacity: 1; }}
            to {{ opacity: 0; visibility: hidden; }}
        }}
        </style>
        """, unsafe_allow_html=True)
        
        # Clear popup after showing
        st.session_state.achievement_popup = None

# ═══════════════════════════════════════════════════════════════════════════════
# TRANSLATIONS (100+ keys, 3 languages)
# ═══════════════════════════════════════════════════════════════════════════════
TR = {
    'app_title': {'ru': '🛰️ ATLAS', 'en': '🛰️ ATLAS', 'kz': '🛰️ ATLAS'},
    'app_subtitle': {'ru': 'Autonomous Terrestrial Life Analysis System', 'en': 'Autonomous Terrestrial Life Analysis System', 'kz': 'Жерлік өмірді автономды талдау жүйесі'},
    'tab_missions': {'ru': '🚀 Миссии', 'en': '🚀 Missions', 'kz': '🚀 Миссиялар'},
    'tab_system': {'ru': '🪐 Система', 'en': '🪐 System', 'kz': '🪐 Жүйе'},
    'tab_starmap': {'ru': '🗺️ Карта', 'en': '🗺️ Map', 'kz': '🗺️ Карта'},
    'tab_analysis': {'ru': '🧠 Анализ', 'en': '🧠 Analysis', 'kz': '🧠 Талдау'},
    'tab_compare': {'ru': '📊 Сравнение', 'en': '📊 Compare', 'kz': '📊 Салыстыру'},
    'tab_encyclopedia': {'ru': '📚 Справка', 'en': '📚 Reference', 'kz': '📚 Анықтама'},
    'tab_history': {'ru': '📜 История', 'en': '📜 History', 'kz': '📜 Тарих'},
    'tab_travel': {'ru': '🚀 Полёт', 'en': '🚀 Travel', 'kz': '🚀 Ұшу'},
    'tab_presentation': {'ru': '🎬 Презентация', 'en': '🎬 Presentation', 'kz': '🎬 Презентация'},
    'sidebar_lang': {'ru': '🌐 Язык', 'en': '🌐 Language', 'kz': '🌐 Тіл'},
    'sidebar_theme': {'ru': '🎨 Тема', 'en': '🎨 Theme', 'kz': '🎨 Тақырып'},
    'sidebar_stats': {'ru': '📊 Статистика', 'en': '📊 Statistics', 'kz': '📊 Статистика'},
    'sidebar_search': {'ru': '⚡ Поиск', 'en': '⚡ Search', 'kz': '⚡ Іздеу'},
    'theme_dark': {'ru': '🌙 Тёмная', 'en': '🌙 Dark', 'kz': '🌙 Қараңғы'},
    'theme_light': {'ru': '☀️ Светлая', 'en': '☀️ Light', 'kz': '☀️ Жарық'},
    'stat_systems': {'ru': 'Систем', 'en': 'Systems', 'kz': 'Жүйелер'},
    'stat_habitable': {'ru': 'Обитаемых', 'en': 'Habitable', 'kz': 'Мекендеуге жарамды'},
    'stat_skipped': {'ru': 'Пропущено', 'en': 'Skipped', 'kz': 'Өткізілді'},
    'mission_control': {'ru': '🤖 Центр управления миссиями', 'en': '🤖 Mission Control', 'kz': '🤖 Миссия басқару орталығы'},
    'select_catalog': {'ru': '🗂️ Каталог', 'en': '🗂️ Catalog', 'kz': '🗂️ Каталог'},
    'stars_available': {'ru': 'звёзд доступно', 'en': 'stars available', 'kz': 'жұлдыз қолжетімді'},
    'skip_scanned': {'ru': 'Пропускать изученные', 'en': 'Skip scanned', 'kz': 'Зерттелгенді өткізу'},
    'targets': {'ru': '🎯 Целей', 'en': '🎯 Targets', 'kz': '🎯 Мақсаттар'},
    'start_mission': {'ru': '🚀 Запустить', 'en': '🚀 Start', 'kz': '🚀 Бастау'},
    'clear_scanned': {'ru': '🔄 Сбросить', 'en': '🔄 Reset', 'kz': '🔄 Қалпына келтіру'},
    'mission_complete': {'ru': '✅ Миссия завершена', 'en': '✅ Mission complete', 'kz': '✅ Миссия аяқталды'},
    'candidates_found': {'ru': 'кандидатов', 'en': 'candidates', 'kz': 'үміткер'},
    'load_best': {'ru': '📂 Загрузить лучшую', 'en': '📂 Load best', 'kz': '📂 Үздікті жүктеу'},
    'system_view': {'ru': '🌟 Звёздная система', 'en': '🌟 Star System', 'kz': '🌟 Жұлдыз жүйесі'},
    'select_planet': {'ru': '🪐 Выберите планету', 'en': '🪐 Select planet', 'kz': '🪐 Планета таңдаңыз'},
    'detailed_analysis': {'ru': '🔬 Детальный анализ', 'en': '🔬 Detailed Analysis', 'kz': '🔬 Толық талдау'},
    'physical': {'ru': '⚙️ Физические', 'en': '⚙️ Physical', 'kz': '⚙️ Физикалық'},
    'orbital': {'ru': '🌀 Орбитальные', 'en': '🌀 Orbital', 'kz': '🌀 Орбиталық'},
    'habitability': {'ru': '🌱 Обитаемость', 'en': '🌱 Habitability', 'kz': '🌱 Мекендеуге жарамдылық'},
    'star_params': {'ru': '⭐ Звезда', 'en': '⭐ Star', 'kz': '⭐ Жұлдыз'},
    'atmosphere': {'ru': '🌫️ Атмосфера', 'en': '🌫️ Atmosphere', 'kz': '🌫️ Атмосфера'},
    'hazards': {'ru': '⚠️ Угрозы', 'en': '⚠️ Hazards', 'kz': '⚠️ Қауіптер'},
    'biosignatures': {'ru': '🧬 Биосигнатуры', 'en': '🧬 Biosignatures', 'kz': '🧬 Биосигнатуралар'},
    'add_compare': {'ru': '➕ В сравнение', 'en': '➕ Add to compare', 'kz': '➕ Салыстыруға'},
    'no_system': {'ru': '🔭 Нет данных. Запустите миссию!', 'en': '🔭 No data. Run a mission!', 'kz': '🔭 Деректер жоқ. Миссия іске қосыңыз!'},
    'starmap_title': {'ru': '🗺️ Карта звёздного окружения', 'en': '🗺️ Stellar Neighborhood Map', 'kz': '🗺️ Жұлдыздық аймақ картасы'},
    'starmap_desc': {'ru': '3D карта исследованных систем относительно Солнца', 'en': '3D map of explored systems relative to the Sun', 'kz': 'Күнге қатысты зерттелген жүйелердің 3D картасы'},
    'starmap_empty': {'ru': 'Карта пуста. Исследуйте системы!', 'en': 'Map empty. Explore systems!', 'kz': 'Карта бос. Жүйелерді зерттеңіз!'},
    'analysis_title': {'ru': '🧠 Интеллектуальный анализ ATLAS', 'en': '🧠 ATLAS Intelligent Analysis', 'kz': '🧠 ATLAS интеллектуалды талдау'},
    'recommendations': {'ru': '💡 Рекомендации', 'en': '💡 Recommendations', 'kz': '💡 Ұсыныстар'},
    'hypotheses': {'ru': '🔬 Научные гипотезы', 'en': '🔬 Scientific Hypotheses', 'kz': '🔬 Ғылыми болжамдар'},
    'generate_analysis': {'ru': '🧠 Сгенерировать анализ', 'en': '🧠 Generate analysis', 'kz': '🧠 Талдау жасау'},
    'no_data_analysis': {'ru': 'Мало данных. Исследуйте больше систем.', 'en': 'Not enough data. Explore more.', 'kz': 'Деректер аз. Көбірек зерттеңіз.'},
    'compare_title': {'ru': '📊 Сравнение планет', 'en': '📊 Planet Comparison', 'kz': '📊 Планеталарды салыстыру'},
    'select_planets': {'ru': 'Выберите планеты:', 'en': 'Select planets:', 'kz': 'Планеталарды таңдаңыз:'},
    'radar_chart': {'ru': '🕸️ Радар', 'en': '🕸️ Radar', 'kz': '🕸️ Радар'},
    'bar_chart': {'ru': '📊 Гистограмма', 'en': '📊 Bar Chart', 'kz': '📊 Гистограмма'},
    'comparison_table': {'ru': '📋 Таблица', 'en': '📋 Table', 'kz': '📋 Кесте'},
    'clear_selection': {'ru': '🗑️ Очистить', 'en': '🗑️ Clear', 'kz': '🗑️ Тазалау'},
    'encyclopedia_title': {'ru': '📚 Справочник', 'en': '📚 Reference Guide', 'kz': '📚 Анықтамалық'},
    'history_title': {'ru': '📜 История исследований', 'en': '📜 Research History', 'kz': '📜 Зерттеу тарихы'},
    'saved_systems': {'ru': '📂 Сохранённые системы', 'en': '📂 Saved Systems', 'kz': '📂 Сақталған жүйелер'},
    'load_system': {'ru': 'Загрузить', 'en': 'Load', 'kz': 'Жүктеу'},
    'clear_history': {'ru': '🗑️ Очистить', 'en': '🗑️ Clear', 'kz': '🗑️ Тазалау'},
    'history_empty': {'ru': '📭 История пуста', 'en': '📭 History empty', 'kz': '📭 Тарих бос'},
    'travel_title': {'ru': '🚀 Межзвёздный калькулятор', 'en': '🚀 Interstellar Calculator', 'kz': '🚀 Жұлдызаралық калькулятор'},
    'destination': {'ru': '📍 Цель', 'en': '📍 Destination', 'kz': '📍 Мақсат'},
    'distance_ly': {'ru': 'Расстояние (св.лет)', 'en': 'Distance (ly)', 'kz': 'Қашықтық (ж.ж.)'},
    'velocity': {'ru': '⚡ Скорость', 'en': '⚡ Velocity', 'kz': '⚡ Жылдамдық'},
    'earth_time': {'ru': '⏱️ Время Земли', 'en': '⏱️ Earth Time', 'kz': '⏱️ Жер уақыты'},
    'ship_time': {'ru': '🧑‍🚀 Время корабля', 'en': '🧑‍🚀 Ship Time', 'kz': '🧑‍🚀 Кеме уақыты'},
    'lorentz': {'ru': '⚡ Фактор Лоренца', 'en': '⚡ Lorentz Factor', 'kz': '⚡ Лоренц факторы'},
    'fuel': {'ru': '⚛️ Антиматерия', 'en': '⚛️ Antimatter', 'kz': '⚛️ Антиматерия'},
    'journey_preview': {'ru': '🎬 Превью', 'en': '🎬 Preview', 'kz': '🎬 Алдын ала көру'},
    'phases': {'ru': '📅 Фазы', 'en': '📅 Phases', 'kz': '📅 Фазалар'},
    'presentation_title': {'ru': '🎬 Режим презентации', 'en': '🎬 Presentation Mode', 'kz': '🎬 Презентация режимі'},
    'start_presentation': {'ru': '▶️ Начать', 'en': '▶️ Start', 'kz': '▶️ Бастау'},
    'stop_presentation': {'ru': '⏹️ Завершить', 'en': '⏹️ End', 'kz': '⏹️ Аяқтау'},
    'slide_overview': {'ru': '📊 Обзор', 'en': '📊 Overview', 'kz': '📊 Шолу'},
    'slide_top': {'ru': '🏆 Лучшие', 'en': '🏆 Top', 'kz': '🏆 Үздік'},
    'slide_conclusions': {'ru': '📝 Выводы', 'en': '📝 Conclusions', 'kz': '📝 Қорытынды'},
    'loading': {'ru': 'Загрузка...', 'en': 'Loading...', 'kz': 'Жүктелуде...'},
    'found': {'ru': '✅ Найдено', 'en': '✅ Found', 'kz': '✅ Табылды'},
    'not_found': {'ru': '❌ Не найдено', 'en': '❌ Not found', 'kz': '❌ Табылмады'},
    'planets': {'ru': 'планет', 'en': 'planets', 'kz': 'планета'},
    'best': {'ru': 'Лучший', 'en': 'Best', 'kz': 'Үздік'},
    'unknown': {'ru': 'Неизв.', 'en': 'Unknown', 'kz': 'Белгісіз'},
    'yes': {'ru': 'Да', 'en': 'Yes', 'kz': 'Иә'},
    'no': {'ru': 'Нет', 'en': 'No', 'kz': 'Жоқ'},
    'radius': {'ru': 'Радиус', 'en': 'Radius', 'kz': 'Радиус'},
    'mass': {'ru': 'Масса', 'en': 'Mass', 'kz': 'Масса'},
    'temp': {'ru': 'Температура', 'en': 'Temperature', 'kz': 'Температура'},
    'density': {'ru': 'Плотность', 'en': 'Density', 'kz': 'Тығыздық'},
    'gravity': {'ru': 'Гравитация', 'en': 'Gravity', 'kz': 'Гравитация'},
    'orbit': {'ru': 'Орбита', 'en': 'Orbit', 'kz': 'Орбита'},
    'period': {'ru': 'Период', 'en': 'Period', 'kz': 'Кезең'},
    'distance': {'ru': 'Расстояние', 'en': 'Distance', 'kz': 'Қашықтық'},
    'score': {'ru': 'Оценка', 'en': 'Score', 'kz': 'Баға'},
    'esi': {'ru': 'ESI', 'en': 'ESI', 'kz': 'ESI'},
    'in_hz': {'ru': 'В зоне HZ', 'en': 'In HZ', 'kz': 'HZ аймағында'},
    'escape_v': {'ru': 'Убегания', 'en': 'Escape', 'kz': 'Қашу'},
    'pressure': {'ru': 'Давление', 'en': 'Pressure', 'kz': 'Қысым'},
    'year_len': {'ru': 'Год', 'en': 'Year', 'kz': 'Жыл'},
    'mag_field': {'ru': 'Магн.поле', 'en': 'Mag.Field', 'kz': 'Магн.өріс'},
    'moons': {'ru': 'Спутники', 'en': 'Moons', 'kz': 'Серіктер'},
}

def t(key):
    """Get translation for current language"""
    lang = st.session_state.get('lang', 'ru')
    return TR.get(key, {}).get(lang, key)

# ═══════════════════════════════════════════════════════════════════════════════
# CATALOGS
# ═══════════════════════════════════════════════════════════════════════════════
CATALOGS = {
    'nearby': {
        'name': {'ru': '🌟 Ближайшие (<50 св.лет)', 'en': '🌟 Nearby (<50 ly)', 'kz': '🌟 Жақын (<50 ж.ж.)'},
        'stars': ["Proxima", "TRAPPIST-1", "Ross-128", "Luyten", "Wolf-1061", "GJ-1061", "Teegarden", "YZ-Ceti", "GJ-273", "Kapteyn"]
    },
    'kepler': {
        'name': {'ru': '🔭 Kepler', 'en': '🔭 Kepler', 'kz': '🔭 Kepler'},
        'stars': ["Kepler-442", "Kepler-62", "Kepler-186", "Kepler-452", "Kepler-22", "Kepler-69", "Kepler-438", "Kepler-296", "Kepler-1649", "Kepler-1652"]
    },
    'tess': {
        'name': {'ru': '🛰️ TESS', 'en': '🛰️ TESS', 'kz': '🛰️ TESS'},
        'stars': ["TOI-700", "TOI-1452", "TOI-715", "LHS-1140", "LP-890-9", "TOI-1235", "TOI-270", "TOI-540", "K2-18", "GJ-357"]
    },
    'habitable': {
        'name': {'ru': '🌱 Обитаемые', 'en': '🌱 Habitable', 'kz': '🌱 Мекендеуге жарамды'},
        'stars': ["TRAPPIST-1", "Proxima", "TOI-700", "Kepler-442", "Kepler-62", "LHS-1140", "K2-18", "Kepler-186", "GJ-667C", "HD-40307"]
    },
    'giants': {
        'name': {'ru': '🪐 Гиганты', 'en': '🪐 Giants', 'kz': '🪐 Алыптар'},
        'stars': ["HD-209458", "51-Peg", "HD-189733", "WASP-12", "WASP-17", "HAT-P-7", "TrES-2", "HD-149026", "WASP-79", "KELT-9"]
    },
    'multiplanet': {
        'name': {'ru': '🌐 Многопланетные', 'en': '🌐 Multi-planet', 'kz': '🌐 Көппланеталы'},
        'stars': ["TRAPPIST-1", "Kepler-90", "HD-10180", "Kepler-11", "HR-8799", "55-Cnc", "GJ-876", "Kepler-80", "TOI-178", "HD-219134"]
    }
}

KNOWN_PLANETS = {
    "Earth": {"radius": 1.0, "mass": 1.0, "temp": 288, "distance": 0, "esi": 1.0, "emoji": "🌍", "gravity": 1.0},
    "TRAPPIST-1e": {"radius": 0.92, "mass": 0.77, "temp": 251, "distance": 40.7, "esi": 0.85, "emoji": "🔵", "gravity": 0.93},
    "Proxima b": {"radius": 1.08, "mass": 1.27, "temp": 234, "distance": 4.24, "esi": 0.87, "emoji": "🔴", "gravity": 1.08},
    "Kepler-442b": {"radius": 1.34, "mass": 2.34, "temp": 233, "distance": 1206, "esi": 0.84, "emoji": "🟢", "gravity": 1.3},
    "TOI-700 d": {"radius": 1.19, "mass": 1.72, "temp": 268, "distance": 101.4, "esi": 0.93, "emoji": "🌎", "gravity": 1.21},
}
# ═══════════════════════════════════════════════════════════════════════════════
# CSS THEMES - GoVista/Trabu Style
# ═══════════════════════════════════════════════════════════════════════════════

def get_css():
    """Return the single ATLAS theme used across the whole app."""
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Cormorant+Garamond:wght@500;600&display=swap');

:root {
    --atlas-bg: #0f1014;
    --atlas-panel: rgba(31, 29, 28, 0.9);
    --atlas-panel-soft: rgba(53, 49, 46, 0.84);
    --atlas-border: rgba(255,255,255,0.12);
    --atlas-border-strong: rgba(213, 161, 79, 0.42);
    --atlas-text: #f4eee5;
    --atlas-text-soft: rgba(244, 238, 229, 0.72);
    --atlas-text-dim: rgba(244, 238, 229, 0.48);
    --atlas-accent: #d5a14f;
    --atlas-cream: #ece1cf;
    --atlas-shadow: 0 22px 60px rgba(0, 0, 0, 0.28);
}

html, body, [class*="css"] {
    font-family: 'Manrope', sans-serif !important;
}

body {
    color: var(--atlas-text);
}

.stApp {
    background:
        radial-gradient(circle at top, rgba(228, 217, 197, 0.08), transparent 26%),
        linear-gradient(180deg, #121317 0%, #0d0f13 55%, #0c0d11 100%) !important;
    color: var(--atlas-text);
}

[data-testid="stAppViewContainer"] {
    background: transparent !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

[data-testid="collapsedControl"],
[data-testid="stSidebar"] {
    display: none !important;
}

.block-container {
    max-width: 1480px !important;
    padding-top: 0.7rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    padding-bottom: 2rem !important;
}

h1, h2, h3, h4, h5 {
    color: var(--atlas-text) !important;
    letter-spacing: -0.03em;
}

p, label, .stCaption, .stMarkdown, .stText, li {
    color: var(--atlas-text-soft) !important;
}

a {
    color: inherit !important;
    text-decoration: none !important;
}

.atlas-nav-shell {
    position: sticky;
    top: 0.9rem;
    z-index: 1000;
    margin-bottom: 1.25rem;
}

.atlas-nav-bar {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 18px;
    padding: 14px 18px;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,0.45);
    background: rgba(245, 242, 236, 0.78);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    box-shadow: 0 16px 42px rgba(0,0,0,0.16);
}

.atlas-brand {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    color: #171515 !important;
    font-size: 0.98rem;
    font-weight: 800;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    white-space: nowrap;
}

.atlas-brand-dot {
    width: 11px;
    height: 11px;
    border-radius: 50%;
    background: radial-gradient(circle at 35% 35%, #f4ebde 0%, #d8aa60 42%, #181818 100%);
    box-shadow: 0 0 0 1px rgba(23,21,21,0.12);
}

.atlas-nav-links {
    display: flex;
    justify-content: center;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
}

.atlas-nav-link,
.atlas-nav-ghost,
.atlas-nav-lang {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 40px;
    padding: 0 18px;
    border-radius: 999px;
    font-size: 0.86rem;
    font-weight: 700;
    color: #181716 !important;
    transition: all 0.22s ease;
    white-space: nowrap;
}

.atlas-nav-link:hover,
.atlas-nav-ghost:hover,
.atlas-nav-lang:hover {
    background: rgba(20, 18, 17, 0.09);
}

.atlas-nav-link.active {
    background: #1f1d1c;
    color: #fff8ee !important;
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.12);
}

.atlas-nav-right {
    display: inline-flex;
    align-items: center;
    gap: 10px;
}

.atlas-nav-lang-group {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px;
    border-radius: 999px;
    background: rgba(18, 17, 17, 0.08);
}

.atlas-nav-lang.active {
    background: #1f1d1c;
    color: #fff8ee !important;
}

.atlas-more {
    position: relative;
}

.atlas-more summary {
    list-style: none;
    cursor: pointer;
}

.atlas-more summary::-webkit-details-marker {
    display: none;
}

.atlas-more-menu {
    position: absolute;
    right: 0;
    top: calc(100% + 10px);
    min-width: 210px;
    padding: 10px;
    border-radius: 20px;
    background: rgba(245, 242, 236, 0.94);
    border: 1px solid rgba(17, 15, 14, 0.08);
    box-shadow: 0 20px 48px rgba(0,0,0,0.22);
}

.atlas-more-menu a {
    display: block;
    padding: 10px 12px;
    border-radius: 12px;
    color: #171515 !important;
    font-size: 0.86rem;
    font-weight: 700;
}

.atlas-more-menu a:hover,
.atlas-more-menu a.active {
    background: rgba(17, 15, 14, 0.08);
}

.atlas-stage-caption {
    margin: 0.2rem 0 0.95rem;
    font-size: 0.76rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--atlas-text-dim);
}

.atlas-page-wrap {
    margin-top: 1.2rem;
}

.atlas-page-title {
    margin: 0.1rem 0 0.4rem;
    font-size: 2rem !important;
    font-weight: 700 !important;
}

.atlas-page-subtitle {
    margin: 0 0 1.25rem;
    max-width: 720px;
    color: var(--atlas-text-soft);
}

.stAlert,
.stCodeBlock,
.stDataFrame,
.js-plotly-plot,
[data-testid="stMetric"],
.element-container .stPlotlyChart {
    border-radius: 24px !important;
}

.stAlert,
[data-testid="stMetric"],
.stCodeBlock > div,
.element-container .stPlotlyChart,
.stDataFrame,
.stTextArea,
.stTextInput,
.stNumberInput,
.stSelectbox,
.stMultiSelect {
    background: var(--atlas-panel-soft) !important;
    border: 1px solid var(--atlas-border) !important;
    box-shadow: var(--atlas-shadow) !important;
}

[data-testid="stMetric"] {
    padding: 14px 16px !important;
}

[data-testid="stMetricLabel"] p {
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-size: 0.68rem !important;
    color: var(--atlas-text-dim) !important;
}

[data-testid="stMetricValue"] {
    color: var(--atlas-text) !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}

.stButton > button {
    min-height: 46px !important;
    border-radius: 999px !important;
    border: 1px solid var(--atlas-border) !important;
    background: rgba(36, 34, 33, 0.94) !important;
    color: var(--atlas-text) !important;
    font-weight: 700 !important;
    box-shadow: none !important;
}

.stButton > button:hover {
    border-color: var(--atlas-border-strong) !important;
    color: var(--atlas-cream) !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(180deg, rgba(213,161,79,0.28) 0%, rgba(123,89,40,0.22) 100%) !important;
    border: 1px solid var(--atlas-border-strong) !important;
}

.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div {
    background: rgba(25, 23, 22, 0.92) !important;
    color: var(--atlas-text) !important;
    border: 1px solid var(--atlas-border) !important;
    border-radius: 18px !important;
}

.stCheckbox label,
.stRadio label {
    color: var(--atlas-text-soft) !important;
}

.stSlider [data-baseweb="slider"] > div div {
    background-color: var(--atlas-accent) !important;
}

.streamlit-expanderHeader {
    border-radius: 18px !important;
    border: 1px solid var(--atlas-border) !important;
    background: rgba(29, 27, 26, 0.94) !important;
}

.streamlit-expanderContent {
    border: 1px solid var(--atlas-border) !important;
    border-top: none !important;
    border-radius: 0 0 18px 18px !important;
    background: rgba(24, 22, 21, 0.88) !important;
}

.news-card {
    background: rgba(27, 25, 24, 0.94);
    border: 1px solid var(--atlas-border);
    border-radius: 22px;
    padding: 18px;
    margin-bottom: 12px;
    box-shadow: var(--atlas-shadow);
}

.news-tag {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    background: rgba(213, 161, 79, 0.14);
    border: 1px solid rgba(213, 161, 79, 0.34);
    color: var(--atlas-cream);
    font-size: 0.67rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.atlas-divider {
    width: 100%;
    height: 1px;
    margin: 1.3rem 0 1.1rem;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
}

.atlas-chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin: 0.5rem 0 1rem;
}

.atlas-chip {
    padding: 9px 14px;
    border-radius: 999px;
    background: rgba(31, 29, 28, 0.88);
    border: 1px solid var(--atlas-border);
    color: var(--atlas-text-soft) !important;
    font-size: 0.82rem;
    font-weight: 700;
}

[data-testid="stToast"] {
    right: 18px !important;
    top: 18px !important;
    left: auto !important;
    background: rgba(246, 241, 234, 0.96) !important;
    color: #171515 !important;
    border-radius: 18px !important;
    border: 1px solid rgba(213, 161, 79, 0.32) !important;
}

::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-thumb {
    background: rgba(213, 161, 79, 0.35);
    border-radius: 999px;
}

::-webkit-scrollbar-track {
    background: transparent;
}

@media (max-width: 1100px) {
    .atlas-nav-bar {
        grid-template-columns: 1fr;
        border-radius: 28px;
        padding: 16px;
    }

    .atlas-nav-links,
    .atlas-nav-right {
        justify-content: flex-start;
    }
}
</style>
"""

def calc_luminosity(teff, rad):
    """Calculate stellar luminosity in solar units using Stefan-Boltzmann law.
    L = R² × (T/T☉)⁴ where T☉ = 5778K
    """
    if not teff or not rad or teff <= 0 or rad <= 0:
        return 1.0
    return (rad ** 2) * ((teff / 5778) ** 4)


def calc_equilibrium_temp(teff, srad, orbit, albedo=0.3):
    """Calculate planetary equilibrium temperature.
    Teq = T★ × √(R★/(2a)) × (1-A)^0.25
    Where A = albedo, a = orbital distance in AU
    """
    if not teff or not srad or not orbit or orbit <= 0:
        return None
    r_au = srad * 0.00465047  # Solar radii to AU
    return teff * math.sqrt(r_au / (2 * orbit)) * ((1 - albedo) ** 0.25)


def calc_orbit_from_period(period, stellar_mass=1.0):
    """Calculate semi-major axis from orbital period using Kepler's 3rd law.
    a = (P²/365.25² × M★)^(1/3) [AU]
    """
    if not period or period <= 0:
        return None
    return ((period / 365.25) ** 2 * (stellar_mass or 1)) ** (1/3)


def calc_habitable_zone(teff, srad, luminosity=None):
    """Calculate conservative habitable zone boundaries.
    Inner: 0.75√L AU (runaway greenhouse limit)
    Outer: 1.77√L AU (CO₂ condensation limit)
    """
    L = luminosity if luminosity and luminosity > 0 else calc_luminosity(teff, srad)
    inner = 0.75 * math.sqrt(L)
    outer = 1.77 * math.sqrt(L)
    return inner, outer, L


def calc_esi(radius, temp):
    """Calculate Earth Similarity Index (ESI).
    ESI = √[(1-|R-1|/(R+1))^0.57 × (1-|T-288|/(T+288))^5.58]
    Where R = radius in Earth radii, T = temperature in Kelvin
    ESI = 1.0 means identical to Earth
    """
    if not radius or not temp or radius <= 0 or temp <= 0:
        return 0
    esi_r = (1 - abs((radius - 1) / (radius + 1))) ** 0.57
    esi_t = (1 - abs((temp - 288) / (temp + 288))) ** 5.58
    return round(math.sqrt(esi_r * esi_t), 3)


def calc_surface_gravity(mass, radius):
    """Calculate surface gravity relative to Earth.
    g = M/R² where M and R are in Earth units
    """
    if not mass or not radius or radius <= 0:
        return None
    return mass / (radius ** 2)


def calc_density(mass, radius):
    """Calculate mean density relative to Earth.
    ρ = M/R³ where M and R are in Earth units
    Earth density = 5.51 g/cm³
    """
    if not mass or not radius or radius <= 0:
        return None
    return mass / (radius ** 3)


def calc_escape_velocity(mass, radius):
    """Calculate escape velocity in km/s.
    v_esc = 11.2 × √(M/R) where Earth's v_esc = 11.2 km/s
    """
    if not mass or not radius or radius <= 0:
        return None
    return 11.2 * math.sqrt(mass / radius)


def calc_surface_pressure(mass, radius, temp, has_atmosphere=True):
    """Estimate surface atmospheric pressure relative to Earth.
    Based on mass, radius, and temperature considerations.
    """
    if not mass or not radius:
        return None
    if not has_atmosphere:
        return 0
    
    g = mass / (radius ** 2)  # Surface gravity
    
    # Small planets can't retain atmosphere
    if radius < 0.5:
        return 0
    # Hot planets lose atmosphere
    if temp and temp > 1000:
        return 0
    # Gas giants have extreme pressure
    if radius > 4:
        return 100 + (radius - 4) * 50
    
    # Rocky planets - rough estimate
    base_pressure = g * radius
    if temp and temp > 500:
        base_pressure *= 0.3
    
    return round(max(0.01, min(base_pressure, 1000)), 2)


def calc_year_length(period):
    """Convert orbital period (days) to Earth years."""
    if not period:
        return None
    return period / 365.25


def calc_day_length(period, radius):
    """Estimate day length in hours.
    Close-in planets are likely tidally locked.
    """
    if not period or not radius:
        return None
    # Tidally locked if period < 20 days
    if period < 20:
        return None  # Tidally locked
    # Rough estimate based on size
    return 24 * (1 / (radius ** 0.5))


def estimate_magnetic_field(mass, radius):
    """Estimate presence and strength of magnetic field.
    Based on mass, radius, and implied internal structure.
    """
    if not mass or not radius:
        return t('unknown')
    
    density = mass / (radius ** 3)
    lang = st.session_state.get('lang', 'ru')
    
    responses = {
        'likely': {
            'ru': 'Вероятно (железное ядро)',
            'en': 'Likely (iron core dynamo)',
            'kz': 'Ықтимал (темір ядросы)'
        },
        'strong': {
            'ru': 'Сильное (металлический H)',
            'en': 'Strong (metallic hydrogen)',
            'kz': 'Күшті (металл сутегі)'
        },
        'uncertain': {
            'ru': 'Неопределённо',
            'en': 'Uncertain',
            'kz': 'Белгісіз'
        },
        'weak': {
            'ru': 'Слабое или отсутствует',
            'en': 'Weak or absent',
            'kz': 'Әлсіз немесе жоқ'
        },
        'unlikely': {
            'ru': 'Маловероятно',
            'en': 'Unlikely',
            'kz': 'Екіталай'
        }
    }
    
    if radius <= 2 and density >= 0.7:
        if mass >= 0.5:
            return responses['likely'][lang]
        return responses['weak'][lang]
    if radius > 4:
        return responses['strong'][lang]
    if 2 < radius <= 4:
        return responses['uncertain'][lang]
    return responses['unlikely'][lang]


def estimate_moons(mass, orbit_au, stellar_mass=1.0):
    """Estimate moon count based on Hill sphere size.
    Hill sphere = a × (m/(3M★))^(1/3)
    """
    if not mass or not orbit_au:
        return t('unknown'), 0
    
    hill_radius = orbit_au * (mass / (3 * stellar_mass)) ** (1/3)
    lang = st.session_state.get('lang', 'ru')
    
    responses = {
        'unlikely': {'ru': 'Маловероятно', 'en': 'Unlikely', 'kz': 'Екіталай'},
        'many': {'ru': 'Много (10-80)', 'en': 'Many (10-80)', 'kz': 'Көп (10-80)'},
        'possible_many': {'ru': 'Возможно (1-5)', 'en': 'Possible (1-5)', 'kz': 'Мүмкін (1-5)'},
        'possible_few': {'ru': 'Возможно (0-2)', 'en': 'Possible (0-2)', 'kz': 'Мүмкін (0-2)'}
    }
    
    if hill_radius < 0.001:
        return responses['unlikely'][lang], 0
    elif mass > 10:
        return responses['many'][lang], random.randint(10, 80)
    elif mass > 1:
        return responses['possible_many'][lang], random.randint(0, 5)
    else:
        return responses['possible_few'][lang], random.randint(0, 2)


def get_planet_type(radius, mass, temp):
    """Determine planet type based on physical parameters.
    Returns: (type_name, description, emoji)
    """
    lang = st.session_state.get('lang', 'ru')
    
    types = {
        'dwarf': {
            'name': {'ru': 'Карликовая', 'en': 'Dwarf', 'kz': 'Ергежейлі'},
            'desc': {'ru': 'Субпланетный объект без атмосферы', 'en': 'Sub-planetary body, no atmosphere', 'kz': 'Атмосферасыз субпланеталық дене'},
            'emoji': '🪨'
        },
        'sub_earth': {
            'name': {'ru': 'Суб-Земля', 'en': 'Sub-Earth', 'kz': 'Суб-Жер'},
            'desc': {'ru': 'Марсоподобный, тонкая атмосфера', 'en': 'Mars-like, thin atmosphere', 'kz': 'Марсқа ұқсас, жұқа атмосфера'},
            'emoji': '🔴'
        },
        'earth_like': {
            'name': {'ru': 'Землеподобная', 'en': 'Earth-like', 'kz': 'Жерге ұқсас'},
            'desc': {'ru': 'Потенциально обитаемая, возможна тектоника', 'en': 'Potentially habitable, possible tectonics', 'kz': 'Мекендеуге жарамды, тектоника мүмкін'},
            'emoji': '🌍'
        },
        'super_earth': {
            'name': {'ru': 'Супер-Земля', 'en': 'Super-Earth', 'kz': 'Супер-Жер'},
            'desc': {'ru': 'Крупная каменистая планета, плотная атмосфера', 'en': 'Large rocky world, thick atmosphere', 'kz': 'Үлкен тасты әлем, қалың атмосфера'},
            'emoji': '🌎'
        },
        'mini_neptune': {
            'name': {'ru': 'Мини-Нептун', 'en': 'Mini-Neptune', 'kz': 'Мини-Нептун'},
            'desc': {'ru': 'Водный мир или газовая оболочка', 'en': 'Water world or gas envelope', 'kz': 'Су әлемі немесе газ қабаты'},
            'emoji': '💧'
        },
        'neptune_like': {
            'name': {'ru': 'Нептуноподобная', 'en': 'Neptune-like', 'kz': 'Нептунға ұқсас'},
            'desc': {'ru': 'Ледяной гигант с глубокой атмосферой', 'en': 'Ice giant with deep atmosphere', 'kz': 'Терең атмосферасы бар мұзды алып'},
            'emoji': '🔵'
        },
        'gas_giant': {
            'name': {'ru': 'Газовый гигант', 'en': 'Gas Giant', 'kz': 'Газ алыбы'},
            'desc': {'ru': 'Юпитероподобная, H₂/He атмосфера', 'en': 'Jupiter-like, H₂/He atmosphere', 'kz': 'Юпитерге ұқсас, H₂/He атмосферасы'},
            'emoji': '🪐'
        },
        'super_jupiter': {
            'name': {'ru': 'Супер-Юпитер', 'en': 'Super-Jupiter', 'kz': 'Супер-Юпитер'},
            'desc': {'ru': 'Массивный гигант, близко к коричневому карлику', 'en': 'Massive giant, near brown dwarf', 'kz': 'Үлкен алып, қоңыр ергежейліге жақын'},
            'emoji': '🟤'
        },
        'unknown': {
            'name': {'ru': 'Неизвестно', 'en': 'Unknown', 'kz': 'Белгісіз'},
            'desc': {'ru': 'Недостаточно данных', 'en': 'Insufficient data', 'kz': 'Деректер жеткіліксіз'},
            'emoji': '❓'
        }
    }
    
    if radius is None:
        ptype = 'unknown'
    elif radius < 0.5:
        ptype = 'dwarf'
    elif radius < 0.8:
        ptype = 'sub_earth'
    elif radius <= 1.25:
        ptype = 'earth_like'
    elif radius <= 1.75:
        ptype = 'super_earth'
    elif radius <= 2.5:
        ptype = 'mini_neptune'
    elif radius <= 6:
        ptype = 'neptune_like'
    elif radius <= 15:
        ptype = 'gas_giant'
    else:
        ptype = 'super_jupiter'
    
    t_data = types[ptype]
    return t_data['name'][lang], t_data['desc'][lang], t_data['emoji']


def predict_atmosphere(radius, mass, temp, in_hz, stellar_teff=None):
    """Predict atmospheric composition based on planetary parameters."""
    lang = st.session_state.get('lang', 'ru')
    
    if not radius:
        return t('unknown'), []
    
    if radius > 6:  # Gas giant
        atmo_type = {'ru': 'H₂/He доминирует', 'en': 'H₂/He dominated', 'kz': 'H₂/He басым'}
        components = ["H₂ (90%)", "He (10%)", "CH₄", "NH₃", "H₂O"]
    elif radius > 2.5:  # Mini-Neptune/Neptune
        atmo_type = {'ru': 'H₂/He с летучими веществами', 'en': 'H₂/He with volatiles', 'kz': 'H₂/He ұшқыш заттармен'}
        components = ["H₂", "He", "H₂O", "CH₄", "NH₃"]
    elif radius > 1.75:  # Super-Earth
        if temp and temp > 500:
            atmo_type = {'ru': 'Горячая, вулканическая', 'en': 'Hot, volcanic', 'kz': 'Ыстық, вулкандық'}
            components = ["CO₂", "SO₂", "N₂"]
        else:
            atmo_type = {'ru': 'Плотная N₂/CO₂', 'en': 'Dense N₂/CO₂', 'kz': 'Тығыз N₂/CO₂'}
            components = ["N₂", "CO₂", "H₂O", "Ar"]
    elif radius >= 0.8:  # Earth-like
        if in_hz and temp and 220 <= temp <= 320:
            atmo_type = {'ru': 'Потенциально земная', 'en': 'Potentially Earth-like', 'kz': 'Жерге ұқсас мүмкін'}
            components = ["N₂", "O₂ (при жизни)", "H₂O", "CO₂", "Ar"]
        elif temp and temp > 400:
            atmo_type = {'ru': 'Плотная CO₂ (Венера)', 'en': 'Dense CO₂ (Venus-like)', 'kz': 'Тығыз CO₂ (Шолпанға ұқсас)'}
            components = ["CO₂ (96%)", "N₂", "SO₂", "H₂SO₄"]
        elif temp and temp < 200:
            atmo_type = {'ru': 'Холодная, тонкая', 'en': 'Cold, thin', 'kz': 'Суық, жұқа'}
            components = ["CO₂", "N₂", "Ar", "CO₂ лёд"]
        else:
            atmo_type = {'ru': 'CO₂/N₂ смесь', 'en': 'CO₂/N₂ mix', 'kz': 'CO₂/N₂ қоспасы'}
            components = ["CO₂", "N₂", "Ar"]
    else:  # Sub-Earth
        atmo_type = {'ru': 'Тонкая или отсутствует', 'en': 'Thin or none', 'kz': 'Жұқа немесе жоқ'}
        components = ["CO₂ (тонкий)", "N₂", "Ar"]
    
    # M-dwarf warning
    if stellar_teff and stellar_teff < 4000:
        warning = {'ru': '⚠️ Риск UV/рентген эрозии', 'en': '⚠️ UV/X-ray stripping risk', 'kz': '⚠️ UV/рентген эрозия қаупі'}
        components.append(warning[lang])
    
    return atmo_type[lang], components


def predict_hazards(temp, gravity, radius, orbit, stellar_teff, period=None):
    """Comprehensive hazard assessment with translations."""
    hazards = []
    lang = st.session_state.get('lang', 'ru')
    
    # Temperature hazards
    if temp:
        if temp > 700:
            hazards.append({
                'ru': ('🔥 СМЕРТЕЛЬНЫЙ ЖАР', f'{temp:.0f}K — поверхность расплавлена'),
                'en': ('🔥 LETHAL HEAT', f'{temp:.0f}K — surface molten'),
                'kz': ('🔥 ӨЛІМДІ ЫСТЫҚ', f'{temp:.0f}K — бет балқыған')
            })
        elif temp > 450:
            hazards.append({
                'ru': ('🌡️ Экстремальная жара', f'{temp:.0f}K — свинец плавится'),
                'en': ('🌡️ Extreme Heat', f'{temp:.0f}K — lead melts'),
                'kz': ('🌡️ Экстремалды ыстық', f'{temp:.0f}K — қорғасын ериді')
            })
        elif temp > 350:
            hazards.append({
                'ru': ('🌡️ Сильная жара', f'{temp:.0f}K — вода кипит'),
                'en': ('🌡️ Severe Heat', f'{temp:.0f}K — water boils'),
                'kz': ('🌡️ Қатты ыстық', f'{temp:.0f}K — су қайнайды')
            })
        elif temp < 100:
            hazards.append({
                'ru': ('🧊 КРИОГЕННЫЙ ХОЛОД', f'{temp:.0f}K — кислород жидкий'),
                'en': ('🧊 CRYOGENIC', f'{temp:.0f}K — oxygen liquefies'),
                'kz': ('🧊 КРИОГЕНДІК', f'{temp:.0f}K — оттегі сұйық')
            })
        elif temp < 180:
            hazards.append({
                'ru': ('❄️ Экстремальный холод', f'{temp:.0f}K — CO₂ замерзает'),
                'en': ('❄️ Extreme Cold', f'{temp:.0f}K — CO₂ freezes'),
                'kz': ('❄️ Экстремалды суық', f'{temp:.0f}K — CO₂ қатады')
            })
    
    # Gravity hazards
    if gravity:
        if gravity > 5:
            hazards.append({
                'ru': ('⚖️ ДАВЯЩАЯ ГРАВИТАЦИЯ', f'{gravity:.1f}g — движение невозможно'),
                'en': ('⚖️ CRUSHING GRAVITY', f'{gravity:.1f}g — movement impossible'),
                'kz': ('⚖️ БАСЫП ТҰРҒАН ГРАВИТАЦИЯ', f'{gravity:.1f}g — қозғалу мүмкін емес')
            })
        elif gravity > 2:
            hazards.append({
                'ru': ('🏋️ Высокая гравитация', f'{gravity:.1f}g — утомительно'),
                'en': ('🏋️ High Gravity', f'{gravity:.1f}g — exhausting'),
                'kz': ('🏋️ Жоғары гравитация', f'{gravity:.1f}g — шаршататын')
            })
        elif gravity < 0.3:
            hazards.append({
                'ru': ('🪶 Низкая гравитация', f'{gravity:.2f}g — проблемы со здоровьем'),
                'en': ('🪶 Low Gravity', f'{gravity:.2f}g — health issues'),
                'kz': ('🪶 Төмен гравитация', f'{gravity:.2f}g — денсаулық мәселелері')
            })
    
    # Radiation hazards
    if orbit and stellar_teff:
        if orbit < 0.1 and stellar_teff < 4000:
            hazards.append({
                'ru': ('☢️ Звёздные вспышки', 'M-карлик — частые UV/рентген вспышки'),
                'en': ('☢️ Stellar Flares', 'M-dwarf — frequent UV/X-ray flares'),
                'kz': ('☢️ Жұлдыздық жарқылдар', 'M-ергежейлі — жиі UV/рентген жарқылдары')
            })
        if orbit < 0.05:
            hazards.append({
                'ru': ('💫 Экстремальная радиация', f'{orbit:.3f} AU — сильный звёздный ветер'),
                'en': ('💫 Extreme Radiation', f'{orbit:.3f} AU — intense stellar wind'),
                'kz': ('💫 Экстремалды радиация', f'{orbit:.3f} AU — қарқынды жұлдыз желі')
            })
    
    # Tidal locking
    if period and period < 10:
        hazards.append({
            'ru': ('🌊 Приливной захват', f'P={period:.1f}d — одна сторона всегда к звезде'),
            'en': ('🌊 Tidal Locking', f'P={period:.1f}d — one side always facing star'),
            'kz': ('🌊 Толқындық байланыс', f'P={period:.1f}d — бір жағы әрқашан жұлдызға')
        })
    
    # No hazards
    if not hazards:
        hazards.append({
            'ru': ('✅ Нет серьёзных угроз', 'Параметры в пределах нормы'),
            'en': ('✅ No Major Hazards', 'Parameters within survivable range'),
            'kz': ('✅ Қауіпті қатер жоқ', 'Параметрлер қалыпты шегінде')
        })
    
    return [(h[lang][0], h[lang][1]) for h in hazards]


def predict_life_potential(temp, radius, in_hz, esi, atmo_type):
    """Assess potential for life with scoring and explanations."""
    lang = st.session_state.get('lang', 'ru')
    
    if not temp or not radius:
        return t('unknown'), 0, []
    
    score = 0
    factors = []
    
    # Temperature assessment
    if 260 <= temp <= 310:
        score += 30
        factors.append({'ru': '✅ Идеальная температура для воды', 'en': '✅ Ideal temperature for liquid water', 'kz': '✅ Су үшін тамаша температура'})
    elif 220 <= temp <= 350:
        score += 15
        factors.append({'ru': '⚠️ Пограничная температура', 'en': '⚠️ Marginal temperature', 'kz': '⚠️ Шекаралық температура'})
    else:
        factors.append({'ru': '❌ Температура вне диапазона воды', 'en': '❌ Temperature outside water range', 'kz': '❌ Су ауқымынан тыс температура'})
    
    # Size assessment
    if 0.8 <= radius <= 1.5:
        score += 25
        factors.append({'ru': '✅ Земной размер', 'en': '✅ Earth-like size', 'kz': '✅ Жер өлшемі'})
    elif 0.5 <= radius <= 2:
        score += 10
        factors.append({'ru': '⚠️ Пограничный размер', 'en': '⚠️ Marginal size', 'kz': '⚠️ Шекаралық өлшем'})
    else:
        factors.append({'ru': '❌ Размер неподходящий', 'en': '❌ Size unsuitable', 'kz': '❌ Өлшем жарамсыз'})
    
    # Habitable zone
    if in_hz:
        score += 25
        factors.append({'ru': '✅ В обитаемой зоне', 'en': '✅ In habitable zone', 'kz': '✅ Мекендеуге жарамды аймақта'})
    else:
        factors.append({'ru': '❌ Вне обитаемой зоны', 'en': '❌ Outside habitable zone', 'kz': '❌ Мекендеуге жарамды аймақтан тыс'})
    
    # ESI
    if esi and esi >= 0.8:
        score += 15
        factors.append({'ru': f'✅ Высокий ESI ({esi})', 'en': f'✅ High ESI ({esi})', 'kz': f'✅ Жоғары ESI ({esi})'})
    elif esi and esi >= 0.6:
        score += 8
        factors.append({'ru': f'⚠️ Средний ESI ({esi})', 'en': f'⚠️ Moderate ESI ({esi})', 'kz': f'⚠️ Орташа ESI ({esi})'})
    
    # Atmosphere
    if atmo_type and ('земн' in atmo_type.lower() or 'earth' in atmo_type.lower()):
        score += 5
        factors.append({'ru': '✅ Благоприятная атмосфера', 'en': '✅ Favorable atmosphere', 'kz': '✅ Қолайлы атмосфера'})
    
    # Life type determination
    if score >= 70:
        life_type = {'ru': '🌱 Углеродная жизнь ВЕРОЯТНА', 'en': '🌱 Carbon-based life LIKELY', 'kz': '🌱 Көміртегі негізіндегі өмір ЫҚТИМАЛ'}
    elif score >= 50:
        life_type = {'ru': '🦠 Микробная жизнь возможна', 'en': '🦠 Microbial life possible', 'kz': '🦠 Микробты өмір мүмкін'}
    elif score >= 30:
        life_type = {'ru': '🧫 Экзотическая жизнь гипотетична', 'en': '🧫 Exotic life speculative', 'kz': '🧫 Экзотикалық өмір болжамды'}
    else:
        life_type = {'ru': '❌ Жизнь маловероятна', 'en': '❌ Life unlikely', 'kz': '❌ Өмір екіталай'}
    
    return life_type[lang], min(score, 100), [f[lang] for f in factors]


def predict_habitability_ml(planet_data, star_data):
    """
    Use trained ML model to predict planet habitability.
    
    Required features (Kepler KOI format):
    - koi_period: Orbital period (days)
    - koi_duration: Transit duration (hours)
    - koi_depth: Transit depth (ppm)
    - koi_prad: Planet radius (Earth radii)
    - koi_teq: Equilibrium temperature (K)
    - koi_insol: Insolation flux (Earth flux)
    - koi_steff: Stellar effective temperature (K)
    - koi_slogg: Stellar surface gravity (log10 cm/s²)
    - koi_srad: Stellar radius (solar radii)
    
    Returns: (is_habitable, probability, confidence_text)
    """
    if not EXOPLANET_MODEL_AVAILABLE or exoplanet_model is None:
        return None, None, "Model not loaded"
    
    try:
        import numpy as np
        
        # Extract features from planet and star data
        period = planet_data.get('pl_orbper') or planet_data.get('period') or 365.0
        radius = planet_data.get('pl_rade') or planet_data.get('radius') or 1.0
        temp = planet_data.get('pl_eqt') or planet_data.get('temp') or 288
        
        st_teff = star_data.get('st_teff') or 5778
        st_rad = star_data.get('st_rad') or 1.0
        st_logg = star_data.get('st_logg') or 4.44
        
        # Calculate derived features
        # Transit duration estimate: ~13 hours for Earth-like
        duration = 13.0 * (period / 365.0) ** (1/3) * radius ** 0.5
        
        # Transit depth in ppm: (Rp/Rs)² × 10⁶
        depth = ((radius * 0.00916) / st_rad) ** 2 * 1e6  # Earth radius in solar radii
        
        # Insolation flux: (Teff/5778)⁴ × (Rstar)² / (orbit)²
        orbit = calc_orbit_from_period(period, star_data.get('st_mass', 1.0))
        if orbit and orbit > 0:
            insol = (st_teff / 5778) ** 4 * st_rad ** 2 / orbit ** 2
        else:
            insol = 1.0
        
        # Build feature array in correct order
        # ['koi_period', 'koi_duration', 'koi_depth', 'koi_prad', 'koi_teq', 'koi_insol', 'koi_steff', 'koi_slogg', 'koi_srad']
        features = np.array([[
            period,      # koi_period
            duration,    # koi_duration
            depth,       # koi_depth
            radius,      # koi_prad
            temp,        # koi_teq
            insol,       # koi_insol
            st_teff,     # koi_steff
            st_logg,     # koi_slogg
            st_rad       # koi_srad
        ]])
        
        # Get prediction
        prediction = exoplanet_model.predict(features)[0]
        
        # Get probability if available
        if hasattr(exoplanet_model, 'predict_proba'):
            proba = exoplanet_model.predict_proba(features)[0]
            probability = proba[1] if len(proba) > 1 else proba[0]  # Probability of class 1 (habitable)
        else:
            probability = 1.0 if prediction == 1 else 0.0
        
        # Confidence text
        lang = st.session_state.get('lang', 'ru')
        if probability >= 0.8:
            confidence = {'ru': '🧠 AI: Высокая вероятность обитаемости', 'en': '🧠 AI: High habitability probability', 'kz': '🧠 AI: Мекендеуге жарамдылық жоғары'}
        elif probability >= 0.5:
            confidence = {'ru': '🧠 AI: Умеренная вероятность', 'en': '🧠 AI: Moderate probability', 'kz': '🧠 AI: Орташа ықтималдық'}
        elif probability >= 0.3:
            confidence = {'ru': '🧠 AI: Низкая вероятность', 'en': '🧠 AI: Low probability', 'kz': '🧠 AI: Төмен ықтималдық'}
        else:
            confidence = {'ru': '🧠 AI: Маловероятно обитаема', 'en': '🧠 AI: Unlikely habitable', 'kz': '🧠 AI: Мекендеуге жарамсыз'}
        
        return bool(prediction), probability, confidence[lang]
        
    except Exception as e:
        return None, None, f"Prediction error: {str(e)[:50]}"
# ═══════════════════════════════════════════════════════════════════════════════
# NASA EXOPLANET ARCHIVE API
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_nasa_data(star_name):
    """
    Fetch exoplanet data from NASA Exoplanet Archive TAP service.
    
    The query retrieves all planets in a system along with stellar parameters.
    Uses the Planetary Systems (ps) table with default_flag=1 for primary data.
    """
    try:
        # Build TAP query URL
        base_url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
        
        # Query for exact hostname match
        query = f"""
        select pl_name, pl_orbper, pl_rade, pl_eqt, pl_bmasse, pl_orbsmax,
               hostname, st_spectype, st_teff, st_rad, st_lum, st_mass, 
               st_met, st_age, sy_dist
        from ps 
        where hostname='{star_name}' and default_flag=1
        """
        
        url = f"{base_url}?query={query.replace(' ', '+')}&format=json"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200 and response.json():
            return response.json()
        
        # Try LIKE query for partial match
        query_like = f"""
        select pl_name, pl_orbper, pl_rade, pl_eqt, pl_bmasse, pl_orbsmax,
               hostname, st_spectype, st_teff, st_rad, st_lum, st_mass,
               st_met, st_age, sy_dist
        from ps 
        where hostname like '{star_name}%' and default_flag=1
        """
        
        url_like = f"{base_url}?query={query_like.replace(' ', '+')}&format=json"
        response_like = requests.get(url_like, timeout=15)
        
        if response_like.status_code == 200 and response_like.json():
            data = response_like.json()
            # Filter to single system
            if data:
                hostname = data[0].get('hostname')
                return [p for p in data if p.get('hostname') == hostname]
        
        return None
        
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.RequestException:
        return None
    except Exception:
        return None


def process_planet_data(planet_raw, star_data):
    """
    Process raw NASA data into a comprehensive analyzed planet dictionary.
    
    This function applies all physics calculations and generates predictions
    for atmospheric composition, hazards, and life potential.
    """
    # Extract basic parameters
    radius = planet_raw.get('pl_rade') or 1.0
    mass = planet_raw.get('pl_bmasse')
    period = planet_raw.get('pl_orbper')
    orbit = planet_raw.get('pl_orbsmax')
    temp_measured = planet_raw.get('pl_eqt')
    distance = planet_raw.get('sy_dist')
    
    # Extract stellar parameters
    stellar_teff = star_data.get('st_teff')
    stellar_rad = star_data.get('st_rad')
    stellar_lum = star_data.get('st_lum')
    stellar_mass = star_data.get('st_mass', 1.0) or 1.0
    
    # Calculate luminosity if not provided
    if not stellar_lum and stellar_teff and stellar_rad:
        stellar_lum = calc_luminosity(stellar_teff, stellar_rad)
    
    # Calculate orbit from period if not provided
    if not orbit and period:
        orbit = calc_orbit_from_period(period, stellar_mass)
    
    # Calculate habitable zone
    hz_inner, hz_outer, luminosity = calc_habitable_zone(
        stellar_teff, stellar_rad, stellar_lum
    ) if stellar_teff and stellar_rad else (0.75, 1.77, 1.0)
    
    # Determine if in habitable zone
    in_hz = hz_inner <= (orbit or 0) <= hz_outer if orbit else False
    
    # Calculate temperature (use measured or calculate)
    if temp_measured:
        temp = temp_measured
        temp_source = {'ru': '📡 Измерено', 'en': '📡 Measured', 'kz': '📡 Өлшенген'}
    else:
        temp = calc_equilibrium_temp(stellar_teff, stellar_rad, orbit) if stellar_teff and stellar_rad and orbit else 300
        temp_source = {'ru': '📐 Вычислено', 'en': '📐 Calculated', 'kz': '📐 Есептелген'}
    
    # Calculate ESI
    esi = calc_esi(radius, temp)
    
    # Calculate derived parameters
    gravity = calc_surface_gravity(mass, radius)
    density = calc_density(mass, radius)
    escape_velocity = calc_escape_velocity(mass, radius)
    pressure = calc_surface_pressure(mass, radius, temp)
    year_length = calc_year_length(period)
    day_length = calc_day_length(period, radius)
    mag_field = estimate_magnetic_field(mass, radius)
    moon_desc, moon_count = estimate_moons(mass or 1, orbit or 1, stellar_mass)
    
    # Get planet type
    planet_type, type_desc, emoji = get_planet_type(radius, mass, temp)
    
    # Predict atmosphere
    atmo_type, atmo_components = predict_atmosphere(radius, mass, temp, in_hz, stellar_teff)
    
    # Calculate habitability score
    hab_score = 0
    if temp:
        if 230 <= temp <= 310:
            hab_score += 40
        elif 200 <= temp <= 350:
            hab_score += 20
        elif 180 <= temp <= 400:
            hab_score += 10
    
    if 0.8 <= radius <= 1.5:
        hab_score += 25
    elif 0.5 <= radius <= 2.0:
        hab_score += 15
    elif radius <= 4:
        hab_score += 5
    
    if in_hz:
        hab_score += 25
    
    if esi and esi >= 0.8:
        hab_score += 10
    elif esi and esi >= 0.6:
        hab_score += 5
    
    hab_score = min(hab_score, 100)
    
    # ML Prediction (if model available)
    ml_prediction = None
    ml_probability = None
    ml_confidence = None
    
    if EXOPLANET_MODEL_AVAILABLE:
        ml_prediction, ml_probability, ml_confidence = predict_habitability_ml(planet_raw, star_data)
    
    # Build comprehensive planet dictionary
    lang = st.session_state.get('lang', 'ru')
    
    return {
        # Identity
        'name': planet_raw.get('pl_name', '?'),
        'emoji': emoji,
        'type': planet_type,
        'type_desc': type_desc,
        
        # Physical parameters
        'radius': radius,
        'mass': mass,
        'density': density,
        'gravity': gravity,
        'escape_v': escape_velocity,
        'pressure': pressure,
        
        # Orbital parameters
        'orbit_au': orbit,
        'period': period,
        'year_len': year_length,
        'day_len': day_length,
        
        # Temperature
        'temp': temp,
        'temp_source': temp_source[lang],
        
        # Habitability
        'esi': esi,
        'in_hz': in_hz,
        'hab_score': hab_score,
        'hz_inner': hz_inner,
        'hz_outer': hz_outer,
        
        # AI Prediction
        'ml_prediction': ml_prediction,
        'ml_probability': ml_probability,
        'ml_confidence': ml_confidence,
        
        # Predictions
        'atmo_type': atmo_type,
        'atmo_comp': atmo_components,
        'mag_field': mag_field,
        'moon_desc': moon_desc,
        'moon_count': moon_count,
        
        # System data
        'distance': distance,
        'hostname': planet_raw.get('hostname'),
        
        # Raw data for reference
        'raw': planet_raw
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def save_system(hostname, star_data, planets):
    """
    Save a star system to research history.
    
    Prevents duplicates and updates statistics.
    """
    if hostname not in st.session_state.saved_systems:
        st.session_state.saved_systems[hostname] = {
            'star': star_data,
            'planets': planets,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'best_score': max((p['hab_score'] for p in planets), default=0),
            'planet_count': len(planets),
            'distance': planets[0].get('distance') if planets else None
        }
        st.session_state.scan_count += 1
        st.session_state.habitable_count += sum(1 for p in planets if p['hab_score'] >= 50)
        return True
    return False


def load_system(hostname):
    """
    Load a saved system for viewing.
    
    Sets the current system state for display.
    """
    if hostname in st.session_state.saved_systems:
        data = st.session_state.saved_systems[hostname]
        st.session_state['planets'] = data['planets']
        st.session_state['star'] = data['star']
        st.session_state['selected_idx'] = 0
        st.session_state['current_system'] = hostname
        return True
    return False


def mark_star_scanned(star_name):
    """Mark a star as scanned to avoid re-scanning."""
    st.session_state.scanned_stars.add(star_name)


def is_star_scanned(star_name):
    """Check if a star has been scanned."""
    return star_name in st.session_state.scanned_stars


def get_unscanned_stars(catalog_key, skip_scanned=True):
    """Get list of unscanned stars from a catalog."""
    catalog = CATALOGS.get(catalog_key, CATALOGS['nearby'])
    stars = catalog['stars']
    if skip_scanned:
        return [s for s in stars if not is_star_scanned(s)]
    return stars


def get_all_planets():
    """Get all planets from all saved systems for analysis."""
    all_planets = []
    for hostname, data in st.session_state.saved_systems.items():
        for planet in data['planets']:
            planet_copy = planet.copy()
            planet_copy['hostname'] = hostname
            planet_copy['star'] = data['star']
            all_planets.append(planet_copy)
    return all_planets


def get_top_candidates(n=10):
    """Get top N habitable candidates across all systems."""
    all_planets = get_all_planets()
    sorted_planets = sorted(all_planets, key=lambda x: x['hab_score'], reverse=True)
    return sorted_planets[:n]


# ═══════════════════════════════════════════════════════════════════════════════
# STELLAR COORDINATES (for star map)
# ═══════════════════════════════════════════════════════════════════════════════

# Approximate 3D coordinates of known star systems (in light-years from Sun)
STELLAR_COORDINATES = {
    'Sun': (0, 0, 0),
    'Proxima Centauri': (1.3, -0.9, -3.8),
    'TRAPPIST-1': (-12.1, 38.4, -6.9),
    'Ross 128': (-5.8, -10.1, -1.1),
    'Luyten': (-4.5, 7.2, -9.3),
    'Wolf 1061': (-4.3, -11.8, 5.0),
    'GJ 1061': (-3.7, -11.0, -0.6),
    'Teegarden': (8.0, -9.5, 3.3),
    'YZ Ceti': (-1.7, -11.8, -3.2),
    'GJ 273': (-4.4, -9.0, 7.1),
    "Kapteyn's Star": (3.8, 1.2, -12.6),
    'TOI-700': (-30, 85, 40),
    'LHS 1140': (-25, 35, 15),
    'K2-18': (-45, 100, 50),
    'Kepler-442': (400, 800, 600),
    'Kepler-62': (350, 900, 450),
    'Kepler-186': (250, 450, 300),
    'Kepler-452': (450, 1200, 700),
    'HD-209458': (50, 100, 80),
    '51 Pegasi': (-15, 48, 12),
    'GJ 357': (-20, 25, 15),
}

def get_star_coordinates(hostname, distance=None):
    """
    Get 3D coordinates for a star system.
    
    Uses known coordinates if available, otherwise generates
    pseudo-random coordinates based on distance.
    """
    # Check known coordinates (normalize hostname)
    for known_name, coords in STELLAR_COORDINATES.items():
        if known_name.lower().replace(' ', '').replace('-', '') in hostname.lower().replace(' ', '').replace('-', ''):
            return coords
    
    # Generate coordinates based on distance
    if distance:
        # Use hostname as seed for reproducibility
        seed = sum(ord(c) for c in hostname)
        np.random.seed(seed)
        
        # Random spherical coordinates
        phi = np.random.uniform(0, 2 * np.pi)
        theta = np.arccos(np.random.uniform(-1, 1))
        
        x = distance * np.sin(theta) * np.cos(phi)
        y = distance * np.sin(theta) * np.sin(phi)
        z = distance * np.cos(theta)
        
        return (x, y, z)
    
    # Default: random position at ~100 ly
    seed = sum(ord(c) for c in hostname)
    np.random.seed(seed)
    return (
        np.random.uniform(-100, 100),
        np.random.uniform(-100, 100),
        np.random.uniform(-50, 50)
    )


# ═══════════════════════════════════════════════════════════════════════════════
# NASA NEWS (RSS)
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_nasa_news():
    """Fetch latest exoplanet news from NASA RSS feed."""
    try:
        import xml.etree.ElementTree as ET
        
        rss_url = "https://www.nasa.gov/rss/dyn/lg_image_of_the_day.rss"
        response = requests.get(rss_url, timeout=5)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            news = []
            
            for item in root.findall('.//item')[:5]:  # Get top 5 news
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                
                if title is not None:
                    news.append({
                        'title': title.text[:80] + '...' if len(title.text) > 80 else title.text,
                        'link': link.text if link is not None else '#',
                        'date': pub_date.text[:16] if pub_date is not None else ''
                    })
            
            return news
    except:
        pass
    
    # Fallback: generate news from session data
    return generate_atlas_news()


def generate_atlas_news():
    """Generate ATLAS-specific news based on discoveries."""
    lang = st.session_state.get('lang', 'ru')
    news = []
    
    # Get recent discoveries
    if st.session_state.saved_systems:
        systems = list(st.session_state.saved_systems.keys())[-3:]
        for sys_name in systems:
            if lang == 'ru':
                news.append({
                    'title': f"🌟 Система {sys_name} добавлена в базу ATLAS",
                    'link': '#',
                    'date': 'Сегодня'
                })
            else:
                news.append({
                    'title': f"🌟 System {sys_name} added to ATLAS database",
                    'link': '#',
                    'date': 'Today'
                })
    
    # Default news
    default_news = {
        'ru': [
            {'title': '🔭 JWST обнаружил признаки атмосферы на K2-18 b', 'link': '#', 'date': ''},
            {'title': '📊 NASA обновило Exoplanet Archive до 5600+ планет', 'link': '#', 'date': ''},
            {'title': '🚀 TESS продолжает сканирование южного неба', 'link': '#', 'date': ''},
        ],
        'en': [
            {'title': '🔭 JWST detected atmospheric signs on K2-18 b', 'link': '#', 'date': ''},
            {'title': '📊 NASA updated Exoplanet Archive to 5600+ planets', 'link': '#', 'date': ''},
            {'title': '🚀 TESS continues southern sky survey', 'link': '#', 'date': ''},
        ]
    }
    
    news.extend(default_news.get(lang, default_news['en']))
    return news[:5]


# ═══════════════════════════════════════════════════════════════════════════════
# QR CODE GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════
def generate_planet_qr(planet_name):
    """Generate QR code for planet sharing via Streamlit Cloud."""
    try:
        import qrcode
        import io
        import base64
        
        # Build URL for the planet
        base_url = "https://atlasaishymkent.streamlit.app"
        planet_url = f"{base_url}?planet={planet_name.replace(' ', '%20')}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(planet_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="#d5a14f", back_color="#0a1628")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return img_str, planet_url
    except ImportError:
        return None, None


# ═══════════════════════════════════════════════════════════════════════════════
# SPACE WEATHER FORECAST
# ═══════════════════════════════════════════════════════════════════════════════
def generate_space_weather(planet_data, star_data, lang='ru'):
    """Generate humorous but scientifically-based weather forecast for exoplanet."""
    
    temp = planet_data.get('temp', 300)
    temp_c = temp - 273.15
    radius = planet_data.get('radius', 1)
    period = planet_data.get('period', 365)
    in_hz = planet_data.get('in_hz', False)
    planet_type = planet_data.get('type', 'Unknown')
    gravity = planet_data.get('gravity', 1)
    
    st_teff = star_data.get('st_teff', 5778)
    
    # Determine weather type based on planet characteristics
    forecasts = []
    
    # Day names
    days = {
        'ru': ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница'],
        'en': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    }
    
    for i, day in enumerate(days.get(lang, days['en'])):
        # Temperature variation (±5-15% per day)
        import random
        random.seed(hash(planet_data.get('name', '')) + i)
        temp_var = temp_c * random.uniform(-0.15, 0.15)
        day_temp = temp_c + temp_var
        
        # Weather conditions based on planet type
        if temp_c > 500:  # Extreme hot
            conditions = {
                'ru': ['☀️ Ясно, лавовые дожди', '🌋 Вулканическая активность', '💨 Сверхзвуковые ветры', 
                       '🔥 Расплавленное железо в облаках', '⚡ Электрические бури'],
                'en': ['☀️ Clear, lava rain', '🌋 Volcanic activity', '💨 Supersonic winds',
                       '🔥 Molten iron clouds', '⚡ Electric storms']
            }
            wind = random.randint(500, 3000)
        elif temp_c > 100:  # Hot
            conditions = {
                'ru': ['🌤️ Жарко, кислотные облака', '☁️ Серные осадки', '🌪️ Пылевые бури',
                       '💨 Горячие ветры', '☀️ Палящее излучение'],
                'en': ['🌤️ Hot, acid clouds', '☁️ Sulfur precipitation', '🌪️ Dust storms',
                       '💨 Hot winds', '☀️ Scorching radiation']
            }
            wind = random.randint(100, 500)
        elif temp_c > 0:  # Temperate
            conditions = {
                'ru': ['🌤️ Переменная облачность', '🌧️ Возможны осадки', '☀️ Ясно',
                       '⛅ Облачно', '🌈 После дождя радуга'],
                'en': ['🌤️ Partly cloudy', '🌧️ Possible precipitation', '☀️ Clear',
                       '⛅ Cloudy', '🌈 Rainbow after rain']
            }
            wind = random.randint(10, 100)
        elif temp_c > -100:  # Cold
            conditions = {
                'ru': ['❄️ Снегопад', '🌨️ Метель', '☁️ Облачно, холодно',
                       '🧊 Ледяной туман', '💨 Арктические ветры'],
                'en': ['❄️ Snowfall', '🌨️ Blizzard', '☁️ Cloudy, cold',
                       '🧊 Ice fog', '💨 Arctic winds']
            }
            wind = random.randint(50, 200)
        else:  # Extreme cold
            conditions = {
                'ru': ['🥶 Криогенный мороз', '🧊 Азотные осадки', '💨 Ледяные ураганы',
                       '❄️ Метановый снег', '☁️ Замёрзшая атмосфера'],
                'en': ['🥶 Cryogenic frost', '🧊 Nitrogen precipitation', '💨 Ice hurricanes',
                       '❄️ Methane snow', '☁️ Frozen atmosphere']
            }
            wind = random.randint(100, 800)
        
        condition = random.choice(conditions.get(lang, conditions['en']))
        
        forecasts.append({
            'day': day,
            'temp': day_temp,
            'condition': condition,
            'wind': wind
        })
    
    return forecasts


def get_planet_day_info(period, radius, is_tidally_locked=False):
    """Calculate local time information for planet."""
    
    # If tidally locked (common for close-in planets)
    if is_tidally_locked or (period and period < 10):
        return {
            'day_length': None,
            'tidally_locked': True,
            'description': {
                'ru': 'Планета приливно захвачена. Одна сторона всегда обращена к звезде.',
                'en': 'Planet is tidally locked. One side always faces the star.',
                'kz': 'Планета бекітілген. Бір жағы әрқашан жұлдызға қарайды.'
            }
        }
    
    # Estimate day length based on radius (larger planets rotate faster, like Jupiter)
    if period:
        # Simple model: day length scales with period and radius
        # Earth: period=365d, radius=1, day=24h
        # Jupiter: period=4333d, radius=11, day=10h
        estimated_day = 24 * (radius ** 0.5) * (period / 365) ** 0.1
        estimated_day = max(5, min(estimated_day, 200))  # Clamp between 5-200 hours
    else:
        estimated_day = 24  # Default to Earth-like
    
    return {
        'day_length': estimated_day,
        'tidally_locked': False,
        'description': {
            'ru': f'Предполагаемая длина дня: {estimated_day:.1f} часов',
            'en': f'Estimated day length: {estimated_day:.1f} hours',
            'kz': f'Болжамды күн ұзақтығы: {estimated_day:.1f} сағат'
        }
    }
# ═══════════════════════════════════════════════════════════════════════════════
# VISUALIZATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def create_system_3d(planets, star, selected_idx):
    """
    Create an interactive 3D visualization of a planetary system.
    
    Features:
    - Central star with color based on temperature
    - Planetary orbits as rings
    - Habitable zone visualization
    - Color-coded planets by habitability score
    - Interactive selection
    """
    fig = go.Figure()
    
    # Stellar parameters
    stellar_teff = star.get('st_teff', 5500)
    stellar_rad = star.get('st_rad', 1) or 1
    
    # Determine star color from temperature
    if stellar_teff > 7500:
        star_color = '#aabfff'  # Blue-white
    elif stellar_teff > 6000:
        star_color = '#fff4ea'  # Yellow-white
    elif stellar_teff > 5000:
        star_color = '#ffd2a1'  # Yellow
    elif stellar_teff > 3500:
        star_color = '#ffaa77'  # Orange
    else:
        star_color = '#ff6b6b'  # Red
    
    # Calculate scale for visualization
    hz_inner = planets[0]['hz_inner'] if planets else 0.75
    hz_outer = planets[0]['hz_outer'] if planets else 1.77
    max_orbit = max([p['orbit_au'] or 0.05 for p in planets] + [hz_outer * 1.2])
    scale = 14 / max_orbit
    
    # Add star at center
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode='markers',
        marker=dict(
            size=max(15, min(stellar_rad * 18, 30)),
            color=star_color,
            line=dict(width=2, color='rgba(255,255,255,0.3)')
        ),
        name=f"⭐ {star.get('st_spectype', 'G')} • {stellar_teff}K",
        hovertemplate=(
            f"<b>Host Star</b><br>"
            f"Type: {star.get('st_spectype', '?')}<br>"
            f"Temp: {stellar_teff}K<br>"
            f"Radius: {stellar_rad:.2f} R☉<extra></extra>"
        )
    ))
    
    # Habitable zone boundaries
    n_points = 80
    theta = np.linspace(0, 2 * np.pi, n_points)
    
    # Inner HZ boundary
    x_inner = hz_inner * scale * np.cos(theta)
    y_inner = hz_inner * scale * np.sin(theta)
    fig.add_trace(go.Scatter3d(
        x=x_inner, y=y_inner, z=np.zeros(n_points),
        mode='lines',
        line=dict(color='rgba(0,255,100,0.5)', width=3),
        name=f"🌿 HZ Inner ({hz_inner:.2f} AU)",
        showlegend=True
    ))
    
    # Outer HZ boundary
    x_outer = hz_outer * scale * np.cos(theta)
    y_outer = hz_outer * scale * np.sin(theta)
    fig.add_trace(go.Scatter3d(
        x=x_outer, y=y_outer, z=np.zeros(n_points),
        mode='lines',
        line=dict(color='rgba(0,255,100,0.3)', width=2),
        name=f"🌿 HZ Outer ({hz_outer:.2f} AU)",
        showlegend=True
    ))
    
    # Add planets
    orbit_points = np.linspace(0, 2 * np.pi, 60)
    
    for idx, planet in enumerate(planets):
        orbit_scaled = (planet['orbit_au'] or 0.05) * scale
        angle = idx * (2 * np.pi / max(len(planets), 1)) + 0.5
        px, py = orbit_scaled * np.cos(angle), orbit_scaled * np.sin(angle)
        
        # Color by habitability score
        score = planet['hab_score']
        if score >= 70:
            color = '#ece1cf'
        elif score >= 50:
            color = '#d5a14f'
        elif score >= 30:
            color = '#ffbb00'
        else:
            color = '#ff6666'
        
        # Size based on radius
        size = max(8, min(planet['radius'] * 4 + 5, 18))
        
        # Highlight selected planet
        if idx == selected_idx:
            size += 5
            color = '#ff00ff'
        
        # Orbit ring
        fig.add_trace(go.Scatter3d(
            x=orbit_scaled * np.cos(orbit_points),
            y=orbit_scaled * np.sin(orbit_points),
            z=np.zeros(60),
            mode='lines',
            line=dict(color='rgba(255,255,255,0.12)', width=1),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Planet marker
        hz_marker = "★ " if planet['in_hz'] else ""
        fig.add_trace(go.Scatter3d(
            x=[px], y=[py], z=[0],
            mode='markers',
            marker=dict(
                size=size,
                color=color,
                line=dict(width=3 if idx == selected_idx else 1, color='white')
            ),
            name=f"{hz_marker}{planet['name']} ({score})",
            hovertemplate=(
                f"<b>{planet['name']}</b><br>"
                f"Score: {score}/100<br>"
                f"R: {planet['radius']:.2f} R⊕<br>"
                f"T: {planet['temp']:.0f}K<br>"
                f"Orbit: {planet['orbit_au']:.4f} AU<extra></extra>"
            )
        ))
    
    # Layout
    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False, range=[-16, 16]),
            yaxis=dict(visible=False, range=[-16, 16]),
            zaxis=dict(visible=False, range=[-8, 8]),
            aspectmode='cube',
            bgcolor='rgba(0,0,0,0)',
            camera=dict(eye=dict(x=0, y=-1.5, z=0.8))
        ),
        margin=dict(l=0, r=0, t=10, b=0),
        height=450,
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            y=0.95,
            x=1.0,
            bgcolor='rgba(15,15,30,0.9)',
            font=dict(color='white', size=11),
            bordercolor='rgba(0,212,255,0.3)',
            borderwidth=1
        )
    )
    
    return fig


def create_stellar_neighborhood_map():
    """
    Create a 3D map of all explored star systems relative to the Sun.
    
    This visualization shows the spatial distribution of explored systems
    with color coding by best habitability score.
    """
    fig = go.Figure()
    
    # Add Sun at center
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode='markers+text',
        marker=dict(size=15, color='#fff4ea', symbol='circle'),
        text=['☀️ Sun'],
        textposition='top center',
        textfont=dict(size=12, color='white'),
        name='☀️ Sun',
        hovertemplate="<b>Sun</b><br>Our home<extra></extra>"
    ))
    
    # Add explored systems
    if st.session_state.saved_systems:
        for hostname, data in st.session_state.saved_systems.items():
            distance = data.get('distance')
            coords = get_star_coordinates(hostname, distance)
            
            best_score = data['best_score']
            planet_count = data['planet_count']
            
            # Color by best habitability score
            if best_score >= 70:
                color = '#ece1cf'
            elif best_score >= 50:
                color = '#d5a14f'
            elif best_score >= 30:
                color = '#ffbb00'
            else:
                color = '#ff6666'
            
            # Size by planet count
            size = 8 + planet_count * 2
            
            fig.add_trace(go.Scatter3d(
                x=[coords[0]],
                y=[coords[1]],
                z=[coords[2]],
                mode='markers+text',
                marker=dict(size=size, color=color, opacity=0.8),
                text=[hostname],
                textposition='top center',
                textfont=dict(size=10, color='white'),
                name=hostname,
                hovertemplate=(
                    f"<b>{hostname}</b><br>"
                    f"Distance: {distance:.1f} ly<br>" if distance else f"<b>{hostname}</b><br>"
                    f"Planets: {planet_count}<br>"
                    f"Best score: {best_score}<extra></extra>"
                )
            ))
            
            # Connection line to Sun
            fig.add_trace(go.Scatter3d(
                x=[0, coords[0]],
                y=[0, coords[1]],
                z=[0, coords[2]],
                mode='lines',
                line=dict(color='rgba(255,255,255,0.1)', width=1),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Layout
    fig.update_layout(
        scene=dict(
            xaxis=dict(
                title='X (ly)',
                gridcolor='rgba(255,255,255,0.1)',
                color='rgba(255,255,255,0.5)'
            ),
            yaxis=dict(
                title='Y (ly)',
                gridcolor='rgba(255,255,255,0.1)',
                color='rgba(255,255,255,0.5)'
            ),
            zaxis=dict(
                title='Z (ly)',
                gridcolor='rgba(255,255,255,0.1)',
                color='rgba(255,255,255,0.5)'
            ),
            bgcolor='rgba(5,5,15,1)',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        height=550,
        paper_bgcolor='rgba(0,0,0,0)',
        title=dict(
            text='',
            font=dict(color='white')
        ),
        showlegend=False
    )
    
    return fig


def create_radar_chart(planets_data):
    """
    Create a radar chart comparing multiple planets across key metrics.
    """
    if not planets_data:
        return go.Figure()
    
    categories = ['Radius', 'Mass', 'Temp', 'ESI', 'Gravity', 'Distance']
    colors = ['#d5a14f', '#ece1cf', '#ff6b9d', '#ffd93d', '#9d4edd', '#ff8c42']
    
    fig = go.Figure()
    
    for idx, (name, data) in enumerate(planets_data.items()):
        # Normalize values to 0-1 scale
        values = [
            min(data.get('radius', 1) / 3, 1),
            min(data.get('mass', 1) / 10, 1) if data.get('mass') else 0.5,
            1 - abs(data.get('temp', 288) - 288) / 500 if data.get('temp') else 0.5,
            data.get('esi', 0.5),
            min(data.get('gravity', 1) / 3, 1) if data.get('gravity') else 0.5,
            1 - min(data.get('distance', 100) / 1000, 1) if data.get('distance') else 0.5
        ]
        values.append(values[0])  # Close the radar
        
        color = colors[idx % len(colors)]
        rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories + [categories[0]],
            fill='toself',
            fillcolor=f'rgba({rgb[0]},{rgb[1]},{rgb[2]},0.2)',
            line=dict(color=color, width=2),
            name=name
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], showticklabels=False),
            bgcolor='rgba(0,0,0,0)'
        ),
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=380,
        margin=dict(l=60, r=60, t=40, b=40)
    )
    
    return fig


def create_bar_comparison(planets_data):
    """
    Create a bar chart comparing ESI and temperature scores.
    """
    if not planets_data:
        return go.Figure()
    
    names = list(planets_data.keys())
    esi_values = [planets_data[n].get('esi', 0) for n in names]
    temp_scores = [
        1 - abs(planets_data[n].get('temp', 288) - 288) / 500
        for n in names
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='ESI',
        x=names,
        y=esi_values,
        marker_color='#d5a14f'
    ))
    
    fig.add_trace(go.Bar(
        name='Temp Score',
        x=names,
        y=temp_scores,
        marker_color='#ece1cf'
    ))
    
    fig.update_layout(
        barmode='group',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=380,
        margin=dict(l=40, r=20, t=40, b=60),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)', range=[0, 1]),
        legend=dict(orientation='h', y=1.1)
    )
    
    return fig


def create_travel_animation(progress, destination_name):
    """
    Create an animated visualization of interstellar travel.
    """
    fig = go.Figure()
    
    # Stars background
    np.random.seed(42)
    n_stars = 100
    star_x = np.random.uniform(-10, 10, n_stars)
    star_y = np.random.uniform(-5, 5, n_stars)
    star_sizes = np.random.uniform(1, 4, n_stars)
    
    # Parallax effect
    star_x_moved = star_x - progress * 2
    star_x_moved = np.where(star_x_moved < -10, star_x_moved + 20, star_x_moved)
    
    fig.add_trace(go.Scatter(
        x=star_x_moved,
        y=star_y,
        mode='markers',
        marker=dict(size=star_sizes, color='white', opacity=0.7),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Ship position
    ship_x = -8 + progress * 14
    
    # Engine trail
    if progress > 0:
        trail_x = np.linspace(ship_x - 2, ship_x - 0.3, 8)
        trail_sizes = np.linspace(15, 3, 8)
        trail_opacities = np.linspace(0.8, 0.1, 8)
        
        for i in range(len(trail_x)):
            fig.add_trace(go.Scatter(
                x=[trail_x[i]],
                y=[0],
                mode='markers',
                marker=dict(
                    size=trail_sizes[i],
                    color=f'rgba(0,212,255,{trail_opacities[i]})'
                ),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Ship
    fig.add_trace(go.Scatter(
        x=[ship_x],
        y=[0],
        mode='markers+text',
        marker=dict(size=25, symbol='triangle-right', color='#d5a14f'),
        text=['🚀'],
        textposition='middle center',
        textfont=dict(size=30),
        showlegend=False
    ))
    
    # Destination planet
    fig.add_trace(go.Scatter(
        x=[8],
        y=[0],
        mode='markers+text',
        marker=dict(size=40, color='#ece1cf'),
        text=['🪐'],
        textposition='middle center',
        textfont=dict(size=40),
        name=destination_name,
        showlegend=False
    ))
    
    fig.update_layout(
        xaxis=dict(visible=False, range=[-12, 12]),
        yaxis=dict(visible=False, range=[-6, 6]),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(10,10,30,1)',
        height=200,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    return fig


def create_score_distribution_chart():
    """
    Create a histogram showing distribution of habitability scores.
    """
    all_planets = get_all_planets()
    
    if not all_planets:
        return go.Figure()
    
    scores = [p['hab_score'] for p in all_planets]
    
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=scores,
        nbinsx=10,
        marker_color='#d5a14f',
        opacity=0.7
    ))
    
    fig.update_layout(
        title=dict(
            text=t('score') + ' Distribution',
            font=dict(color='white')
        ),
        xaxis=dict(
            title=t('score'),
            gridcolor='rgba(255,255,255,0.1)',
            color='white'
        ),
        yaxis=dict(
            title='Count',
            gridcolor='rgba(255,255,255,0.1)',
            color='white'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(l=50, r=20, t=50, b=50)
    )
    
    return fig


def create_planet_types_pie():
    """Create pie chart of planet types distribution."""
    all_planets = get_all_planets()
    if not all_planets:
        return go.Figure()
    
    types = {}
    for p in all_planets:
        ptype = p.get('type', 'Unknown')
        types[ptype] = types.get(ptype, 0) + 1
    
    colors = ['#d5a14f', '#ece1cf', '#ff6b9d', '#ffd93d', '#9d4edd', '#ff8c42', '#4ecdc4']
    
    fig = go.Figure(data=[go.Pie(
        labels=list(types.keys()),
        values=list(types.values()),
        hole=0.4,
        marker_colors=colors[:len(types)]
    )])
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=300,
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=True,
        legend=dict(font=dict(size=10))
    )
    
    return fig


def create_temp_vs_radius_scatter():
    """Create scatter plot of temperature vs radius with habitability coloring."""
    all_planets = get_all_planets()
    if not all_planets:
        return go.Figure()
    
    fig = go.Figure()
    
    # Add habitable zone reference
    fig.add_shape(
        type="rect",
        x0=0.8, x1=1.5, y0=250, y1=310,
        fillcolor="rgba(0,255,136,0.1)",
        line=dict(color="rgba(0,255,136,0.3)", width=2),
    )
    
    # Color by habitability score
    colors = [p['hab_score'] for p in all_planets]
    
    fig.add_trace(go.Scatter(
        x=[p['radius'] for p in all_planets],
        y=[p['temp'] for p in all_planets],
        mode='markers',
        marker=dict(
            size=12,
            color=colors,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title='Score')
        ),
        text=[p['name'] for p in all_planets],
        hovertemplate="<b>%{text}</b><br>R: %{x:.2f} R⊕<br>T: %{y:.0f}K<extra></extra>"
    ))
    
    # Add Earth reference
    fig.add_trace(go.Scatter(
        x=[1.0], y=[288],
        mode='markers+text',
        marker=dict(size=15, color='#ece1cf', symbol='star'),
        text=['🌍 Earth'],
        textposition='top center',
        showlegend=False
    ))
    
    fig.update_layout(
        xaxis=dict(title='Radius (R⊕)', gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(title='Temperature (K)', gridcolor='rgba(255,255,255,0.1)'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=350,
        margin=dict(l=50, r=20, t=30, b=50)
    )
    
    return fig


def create_distance_histogram():
    """Create histogram of system distances."""
    all_planets = get_all_planets()
    if not all_planets:
        return go.Figure()
    
    distances = [p['distance'] for p in all_planets if p.get('distance')]
    
    if not distances:
        return go.Figure()
    
    fig = go.Figure(data=[go.Histogram(
        x=distances,
        nbinsx=15,
        marker_color='#d5a14f',
        opacity=0.7
    )])
    
    fig.update_layout(
        xaxis=dict(title='Distance (ly)', gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(title='Count', gridcolor='rgba(255,255,255,0.1)'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=280,
        margin=dict(l=50, r=20, t=20, b=50)
    )
    
    return fig
# ═══════════════════════════════════════════════════════════════════════════════
# SMART ATLAS - AI ANALYSIS & HYPOTHESIS GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_recommendations():
    """
    Analyze all explored systems and generate research recommendations.
    
    The recommendation engine considers:
    - Which catalogs haven't been explored
    - Similar systems to successful finds
    - Gaps in the research coverage
    """
    lang = st.session_state.get('lang', 'ru')
    recommendations = []
    
    saved = st.session_state.saved_systems
    scanned = st.session_state.scanned_stars
    
    # Recommendation 1: Unexplored catalogs
    for cat_key, cat_data in CATALOGS.items():
        unscanned = [s for s in cat_data['stars'] if s not in scanned]
        if len(unscanned) >= len(cat_data['stars']) * 0.7:  # 70%+ unexplored
            rec = {
                'ru': {
                    'title': f"📁 Исследуйте каталог: {cat_data['name']['ru']}",
                    'reason': f"{len(unscanned)} из {len(cat_data['stars'])} звёзд не изучены",
                    'action': f"Запустите миссию с каталогом '{cat_key}'"
                },
                'en': {
                    'title': f"📁 Explore catalog: {cat_data['name']['en']}",
                    'reason': f"{len(unscanned)} of {len(cat_data['stars'])} stars unexplored",
                    'action': f"Run mission with catalog '{cat_key}'"
                },
                'kz': {
                    'title': f"📁 Каталогты зерттеңіз: {cat_data['name']['kz']}",
                    'reason': f"{len(cat_data['stars'])} жұлдыздан {len(unscanned)} зерттелмеген",
                    'action': f"'{cat_key}' каталогымен миссия іске қосыңыз"
                }
            }
            recommendations.append(rec[lang])
    
    # Recommendation 2: Follow up on high-score systems
    if saved:
        top_systems = sorted(
            saved.items(), 
            key=lambda x: x[1]['best_score'], 
            reverse=True
        )[:3]
        
        for hostname, data in top_systems:
            if data['best_score'] >= 60:
                rec = {
                    'ru': {
                        'title': f"🎯 Приоритетная цель: {hostname}",
                        'reason': f"Балл обитаемости {data['best_score']}/100 — один из лучших результатов",
                        'action': "Загрузите систему для детального анализа планет"
                    },
                    'en': {
                        'title': f"🎯 Priority target: {hostname}",
                        'reason': f"Habitability score {data['best_score']}/100 — one of best results",
                        'action': "Load system for detailed planet analysis"
                    },
                    'kz': {
                        'title': f"🎯 Басым мақсат: {hostname}",
                        'reason': f"Мекендеуге жарамдылық бағасы {data['best_score']}/100 — ең жақсы нәтижелердің бірі",
                        'action': "Планеталарды егжей-тегжейлі талдау үшін жүйені жүктеңіз"
                    }
                }
                recommendations.append(rec[lang])
    
    # Recommendation 3: Nearby stars priority
    nearby_scanned = sum(1 for s in CATALOGS['nearby']['stars'] if s in scanned)
    if nearby_scanned < 5:
        rec = {
            'ru': {
                'title': "🌟 Приоритет: ближайшие звёзды",
                'reason': "Только " + str(nearby_scanned) + " из 10 ближайших звёзд изучены",
                'action': "Ближайшие системы — приоритет для будущих миссий"
            },
            'en': {
                'title': "🌟 Priority: nearby stars",
                'reason': f"Only {nearby_scanned} of 10 nearest stars explored",
                'action': "Nearby systems should be priority for future missions"
            },
            'kz': {
                'title': "🌟 Басымдық: жақын жұлдыздар",
                'reason': f"10 жақын жұлдыздың тек {nearby_scanned} зерттелген",
                'action': "Жақын жүйелер болашақ миссиялар үшін басымдық болуы керек"
            }
        }
        recommendations.append(rec[lang])
    
    # Recommendation 4: Multi-planet systems
    multiplanet_count = sum(1 for h, d in saved.items() if d['planet_count'] >= 3)
    if multiplanet_count < 3:
        rec = {
            'ru': {
                'title': "🌐 Ищите многопланетные системы",
                'reason': f"Найдено только {multiplanet_count} систем с 3+ планетами",
                'action': "Используйте каталог 'multiplanet' для целенаправленного поиска"
            },
            'en': {
                'title': "🌐 Search for multi-planet systems",
                'reason': f"Only {multiplanet_count} systems with 3+ planets found",
                'action': "Use 'multiplanet' catalog for targeted search"
            },
            'kz': {
                'title': "🌐 Көппланеталы жүйелерді іздеңіз",
                'reason': f"3+ планетасы бар тек {multiplanet_count} жүйе табылды",
                'action': "Мақсатты іздеу үшін 'multiplanet' каталогын пайдаланыңыз"
            }
        }
        recommendations.append(rec[lang])
    
    # Recommendation 5: Research strategy
    if len(saved) >= 5:
        avg_score = sum(d['best_score'] for d in saved.values()) / len(saved)
        
        if avg_score < 40:
            rec = {
                'ru': {
                    'title': "📊 Смените стратегию поиска",
                    'reason': f"Средний балл {avg_score:.1f}/100 — низкий результат",
                    'action': "Сфокусируйтесь на каталоге 'habitable' для лучших результатов"
                },
                'en': {
                    'title': "📊 Change search strategy",
                    'reason': f"Average score {avg_score:.1f}/100 — low result",
                    'action': "Focus on 'habitable' catalog for better results"
                },
                'kz': {
                    'title': "📊 Іздеу стратегиясын өзгертіңіз",
                    'reason': f"Орташа балл {avg_score:.1f}/100 — төмен нәтиже",
                    'action': "Жақсы нәтиже үшін 'habitable' каталогына назар аударыңыз"
                }
            }
            recommendations.append(rec[lang])
    
    return recommendations[:5]  # Return top 5 recommendations


def generate_hypotheses():
    """
    Generate scientific hypotheses based on discovered data.
    
    The hypothesis engine analyzes patterns in the data and generates
    scientifically plausible hypotheses that could be investigated further.
    """
    lang = st.session_state.get('lang', 'ru')
    hypotheses = []
    
    all_planets = get_all_planets()
    
    if len(all_planets) < 3:
        return []
    
    # Analyze data patterns
    habitable_planets = [p for p in all_planets if p['hab_score'] >= 50]
    m_dwarf_planets = [p for p in all_planets if p.get('star', {}).get('st_teff', 5500) < 4000]
    earth_like = [p for p in all_planets if 0.8 <= p['radius'] <= 1.5]
    in_hz = [p for p in all_planets if p['in_hz']]
    
    # Hypothesis 1: M-dwarf habitability
    if m_dwarf_planets:
        m_dwarf_habitable = len([p for p in m_dwarf_planets if p['hab_score'] >= 50])
        ratio = m_dwarf_habitable / len(m_dwarf_planets) if m_dwarf_planets else 0
        
        hyp = {
            'ru': {
                'title': "🔴 Обитаемость вокруг красных карликов",
                'hypothesis': f"Из {len(m_dwarf_planets)} планет у M-карликов {m_dwarf_habitable} ({ratio*100:.0f}%) потенциально обитаемы.",
                'analysis': "Несмотря на риск приливного захвата и звёздных вспышек, планеты у M-карликов могут поддерживать жизнь в терминаторной зоне между дневной и ночной сторонами.",
                'evidence': f"Найдено {m_dwarf_habitable} кандидатов с благоприятными условиями",
                'further_study': "Требуется анализ атмосферной эрозии и магнитной защиты"
            },
            'en': {
                'title': "🔴 Habitability around red dwarfs",
                'hypothesis': f"Of {len(m_dwarf_planets)} M-dwarf planets, {m_dwarf_habitable} ({ratio*100:.0f}%) are potentially habitable.",
                'analysis': "Despite risks of tidal locking and stellar flares, M-dwarf planets may support life in the terminator zone between day and night sides.",
                'evidence': f"Found {m_dwarf_habitable} candidates with favorable conditions",
                'further_study': "Atmospheric erosion and magnetic protection analysis required"
            },
            'kz': {
                'title': "🔴 Қызыл ергежейлілер айналасындағы мекендеуге жарамдылық",
                'hypothesis': f"{len(m_dwarf_planets)} M-ергежейлі планетасынан {m_dwarf_habitable} ({ratio*100:.0f}%) мекендеуге жарамды болуы мүмкін.",
                'analysis': "Толқындық байланыс пен жұлдыздық жарқылдар қаупіне қарамастан, M-ергежейлі планеталары күндізгі және түнгі жақтар арасындағы терминатор аймағында өмірді қолдай алады.",
                'evidence': f"Қолайлы жағдайлары бар {m_dwarf_habitable} үміткер табылды",
                'further_study': "Атмосфералық эрозия мен магниттік қорғаныс талдауы қажет"
            }
        }
        hypotheses.append(hyp[lang])
    
    # Hypothesis 2: Super-Earth water worlds
    super_earths = [p for p in all_planets if 1.25 < p['radius'] <= 2.0]
    if super_earths:
        water_candidates = len([p for p in super_earths if p['in_hz']])
        
        hyp = {
            'ru': {
                'title': "💧 Супер-Земли как водные миры",
                'hypothesis': f"Обнаружено {len(super_earths)} супер-Земель, из них {water_candidates} в обитаемой зоне.",
                'analysis': "Супер-Земли с радиусом 1.25-2 R⊕ могут содержать глобальные океаны глубиной сотни километров. Высокое давление на дне может создать слой льда-VII, изолирующий каменистое ядро.",
                'evidence': f"{water_candidates} планет находятся в зоне жидкой воды",
                'further_study': "Спектроскопия атмосферы для поиска водяного пара необходима"
            },
            'en': {
                'title': "💧 Super-Earths as water worlds",
                'hypothesis': f"Found {len(super_earths)} super-Earths, {water_candidates} in habitable zone.",
                'analysis': "Super-Earths with radius 1.25-2 R⊕ may contain global oceans hundreds of kilometers deep. High pressure at bottom may create ice-VII layer, insulating rocky core.",
                'evidence': f"{water_candidates} planets are in liquid water zone",
                'further_study': "Atmospheric spectroscopy for water vapor detection needed"
            },
            'kz': {
                'title': "💧 Супер-Жер су әлемдері ретінде",
                'hypothesis': f"{len(super_earths)} супер-Жер табылды, {water_candidates} мекендеуге жарамды аймақта.",
                'analysis': "1.25-2 R⊕ радиусы бар супер-Жерлер жүздеген километр тереңдіктегі ғаламдық мұхиттарды қамтуы мүмкін. Түбіндегі жоғары қысым тасты ядроны оқшаулайтын мұз-VII қабатын жасай алады.",
                'evidence': f"{water_candidates} планета сұйық су аймағында",
                'further_study': "Су буын анықтау үшін атмосфералық спектроскопия қажет"
            }
        }
        hypotheses.append(hyp[lang])
    
    # Hypothesis 3: Earth-like planet frequency
    if earth_like:
        hz_earth_like = len([p for p in earth_like if p['in_hz']])
        
        hyp = {
            'ru': {
                'title': "🌍 Частота землеподобных планет",
                'hypothesis': f"Из {len(all_planets)} изученных планет {len(earth_like)} ({len(earth_like)/len(all_planets)*100:.1f}%) имеют земной размер.",
                'analysis': f"Из них {hz_earth_like} находятся в обитаемой зоне. Это указывает на высокую частоту потенциально обитаемых миров в галактике.",
                'evidence': f"ESI > 0.8 у {len([p for p in earth_like if p['esi'] >= 0.8])} планет",
                'further_study': "Статистический анализ на большей выборке для уточнения η⊕"
            },
            'en': {
                'title': "🌍 Earth-like planet frequency",
                'hypothesis': f"Of {len(all_planets)} studied planets, {len(earth_like)} ({len(earth_like)/len(all_planets)*100:.1f}%) are Earth-sized.",
                'analysis': f"Of these, {hz_earth_like} are in habitable zone. This indicates high frequency of potentially habitable worlds in galaxy.",
                'evidence': f"ESI > 0.8 for {len([p for p in earth_like if p['esi'] >= 0.8])} planets",
                'further_study': "Statistical analysis on larger sample needed to refine η⊕"
            },
            'kz': {
                'title': "🌍 Жерге ұқсас планеталар жиілігі",
                'hypothesis': f"{len(all_planets)} зерттелген планетадан {len(earth_like)} ({len(earth_like)/len(all_planets)*100:.1f}%) Жер өлшемінде.",
                'analysis': f"Олардың {hz_earth_like} мекендеуге жарамды аймақта. Бұл галактикадағы мекендеуге жарамды әлемдердің жоғары жиілігін көрсетеді.",
                'evidence': f"{len([p for p in earth_like if p['esi'] >= 0.8])} планетада ESI > 0.8",
                'further_study': "η⊕ нақтылау үшін үлкен іріктемеде статистикалық талдау қажет"
            }
        }
        hypotheses.append(hyp[lang])
    
    # Hypothesis 4: Temperature-habitability correlation
    if habitable_planets:
        temps = [p['temp'] for p in habitable_planets if p['temp']]
        if temps:
            avg_temp = sum(temps) / len(temps)
            
            hyp = {
                'ru': {
                    'title': "🌡️ Температурный оптимум обитаемости",
                    'hypothesis': f"Средняя температура обитаемых кандидатов: {avg_temp:.0f}K (Земля: 288K).",
                    'analysis': f"Планеты с температурой 250-310K показывают наибольший потенциал. Отклонение от земной температуры не исключает жизнь — экстремофилы расширяют диапазон.",
                    'evidence': f"Найдено {len(habitable_planets)} планет с благоприятной температурой",
                    'further_study': "Моделирование климата для оценки стабильности температуры"
                },
                'en': {
                    'title': "🌡️ Temperature optimum for habitability",
                    'hypothesis': f"Average temperature of habitable candidates: {avg_temp:.0f}K (Earth: 288K).",
                    'analysis': f"Planets with temperature 250-310K show highest potential. Deviation from Earth temperature doesn't exclude life — extremophiles extend the range.",
                    'evidence': f"Found {len(habitable_planets)} planets with favorable temperature",
                    'further_study': "Climate modeling to assess temperature stability"
                },
                'kz': {
                    'title': "🌡️ Мекендеуге жарамдылықтың температуралық оптимумы",
                    'hypothesis': f"Мекендеуге жарамды үміткерлердің орташа температурасы: {avg_temp:.0f}K (Жер: 288K).",
                    'analysis': f"250-310K температурасы бар планеталар ең жоғары әлеуетті көрсетеді. Жер температурасынан ауытқу өмірді жоққа шығармайды — экстремофилдер ауқымды кеңейтеді.",
                    'evidence': f"Қолайлы температурасы бар {len(habitable_planets)} планета табылды",
                    'further_study': "Температура тұрақтылығын бағалау үшін климаттық модельдеу"
                }
            }
            hypotheses.append(hyp[lang])
    
    # Hypothesis 5: Radius valley and habitability
    valley_planets = [p for p in all_planets if 1.5 <= p['radius'] <= 2.0]
    if len(valley_planets) >= 2:
        hyp = {
            'ru': {
                'title': "📊 'Долина радиусов' и эволюция атмосфер",
                'hypothesis': f"Обнаружено {len(valley_planets)} планет в 'долине радиусов' (1.5-2 R⊕).",
                'analysis': "Это переходная зона между суперземлями и мини-нептунами. Планеты здесь либо потеряли водородную оболочку, либо сохранили её — критический фактор обитаемости.",
                'evidence': "Дефицит планет в этом диапазоне подтверждает теорию фотоиспарения",
                'further_study': "Анализ возраста систем для проверки временной эволюции"
            },
            'en': {
                'title': "📊 Radius valley and atmospheric evolution",
                'hypothesis': f"Found {len(valley_planets)} planets in 'radius valley' (1.5-2 R⊕).",
                'analysis': "This is transition zone between super-Earths and mini-Neptunes. Planets here either lost hydrogen envelope or retained it — critical for habitability.",
                'evidence': "Deficit of planets in this range confirms photoevaporation theory",
                'further_study': "System age analysis to verify temporal evolution"
            },
            'kz': {
                'title': "📊 'Радиус алқабы' және атмосфера эволюциясы",
                'hypothesis': f"'Радиус алқабында' (1.5-2 R⊕) {len(valley_planets)} планета табылды.",
                'analysis': "Бұл супер-Жерлер мен мини-Нептундар арасындағы өтпелі аймақ. Мұндағы планеталар не сутегі қабатын жоғалтты, не сақтады — мекендеуге жарамдылық үшін маңызды.",
                'evidence': "Бұл ауқымдағы планеталар тапшылығы фотобулану теориясын растайды",
                'further_study': "Уақыттық эволюцияны тексеру үшін жүйе жасын талдау"
            }
        }
        hypotheses.append(hyp[lang])
    
    return hypotheses[:5]  # Return top 5 hypotheses


def generate_system_analysis(hostname):
    """
    Generate detailed AI analysis for a specific star system.
    """
    lang = st.session_state.get('lang', 'ru')
    
    if hostname not in st.session_state.saved_systems:
        return None
    
    data = st.session_state.saved_systems[hostname]
    planets = data['planets']
    star = data['star']
    
    # Analyze system characteristics
    planet_count = len(planets)
    best_planet = max(planets, key=lambda x: x['hab_score'])
    hz_planets = [p for p in planets if p['in_hz']]
    stellar_type = star.get('st_spectype', 'G')
    stellar_teff = star.get('st_teff', 5500)
    
    # Generate analysis text
    analyses = {
        'ru': {
            'system_type': f"🌟 **{hostname}** — {'многопланетная система' if planet_count > 2 else 'система'} с {planet_count} {'планетами' if planet_count > 1 else 'планетой'}",
            'star_analysis': f"Звезда класса **{stellar_type}** с температурой **{stellar_teff}K**. " + 
                ("Оптимальна для жизни (G/K тип)." if 4000 < stellar_teff < 6500 else 
                 "M-карлик — риск вспышек и приливного захвата." if stellar_teff < 4000 else
                 "Горячая звезда — короткий срок жизни."),
            'hz_analysis': f"В обитаемой зоне находится **{len(hz_planets)}** {'планета' if len(hz_planets) == 1 else 'планет'}." if hz_planets else "Нет планет в обитаемой зоне.",
            'best_candidate': f"Лучший кандидат: **{best_planet['name']}** с баллом **{best_planet['hab_score']}/100**",
            'recommendation': "🎯 Высокий приоритет для дальнейшего исследования!" if best_planet['hab_score'] >= 60 else 
                            "📊 Умеренный интерес — требуется дополнительный анализ." if best_planet['hab_score'] >= 40 else
                            "📉 Низкий потенциал обитаемости."
        },
        'en': {
            'system_type': f"🌟 **{hostname}** — {'multi-planet system' if planet_count > 2 else 'system'} with {planet_count} {'planets' if planet_count > 1 else 'planet'}",
            'star_analysis': f"Star class **{stellar_type}** with temperature **{stellar_teff}K**. " +
                ("Optimal for life (G/K type)." if 4000 < stellar_teff < 6500 else
                 "M-dwarf — flare and tidal locking risks." if stellar_teff < 4000 else
                 "Hot star — short lifespan."),
            'hz_analysis': f"**{len(hz_planets)}** {'planet' if len(hz_planets) == 1 else 'planets'} in habitable zone." if hz_planets else "No planets in habitable zone.",
            'best_candidate': f"Best candidate: **{best_planet['name']}** with score **{best_planet['hab_score']}/100**",
            'recommendation': "🎯 High priority for further study!" if best_planet['hab_score'] >= 60 else
                            "📊 Moderate interest — additional analysis required." if best_planet['hab_score'] >= 40 else
                            "📉 Low habitability potential."
        },
        'kz': {
            'system_type': f"🌟 **{hostname}** — {planet_count} {'планетасы' if planet_count > 1 else 'планетасы'} бар {'көппланеталы жүйе' if planet_count > 2 else 'жүйе'}",
            'star_analysis': f"**{stellar_type}** класты жұлдыз, температурасы **{stellar_teff}K**. " +
                ("Өмір үшін оңтайлы (G/K түрі)." if 4000 < stellar_teff < 6500 else
                 "M-ергежейлі — жарқылдар мен толқындық байланыс қаупі." if stellar_teff < 4000 else
                 "Ыстық жұлдыз — қысқа өмір сүру."),
            'hz_analysis': f"Мекендеуге жарамды аймақта **{len(hz_planets)}** планета бар." if hz_planets else "Мекендеуге жарамды аймақта планета жоқ.",
            'best_candidate': f"Ең жақсы үміткер: **{best_planet['name']}**, бағасы **{best_planet['hab_score']}/100**",
            'recommendation': "🎯 Одан әрі зерттеу үшін жоғары басымдық!" if best_planet['hab_score'] >= 60 else
                            "📊 Орташа қызығушылық — қосымша талдау қажет." if best_planet['hab_score'] >= 40 else
                            "📉 Мекендеуге жарамдылық әлеуеті төмен."
        }
    }
    
    return analyses[lang]


def get_ai_response(question, context_planets=None):
    """
    Smart AI response system that analyzes user's discoveries.
    Features: comparisons, filters, recommendations, statistics, explanations.
    """
    lang = st.session_state.get('lang', 'ru')
    q_lower = question.lower()
    
    # Get all data
    all_planets = get_all_planets() if context_planets is None else context_planets
    saved_systems = st.session_state.get('saved_systems', {})
    current_system = st.session_state.get('current_system')
    
    # Compute statistics
    stats = {
        'total': len(all_planets),
        'systems': len(saved_systems),
        'habitable': len([p for p in all_planets if p['hab_score'] >= 50]),
        'earth_like': len([p for p in all_planets if 0.8 <= p['radius'] <= 1.5]),
        'super_earth': len([p for p in all_planets if 1.25 < p['radius'] <= 2.0]),
        'gas_giants': len([p for p in all_planets if p['radius'] > 6]),
        'in_hz': len([p for p in all_planets if p['in_hz']]),
        'avg_score': sum(p['hab_score'] for p in all_planets) / len(all_planets) if all_planets else 0,
        'best': max(all_planets, key=lambda x: x['hab_score']) if all_planets else None,
        'worst': min(all_planets, key=lambda x: x['hab_score']) if all_planets else None,
        'nearest': min(all_planets, key=lambda x: x.get('distance') or 9999) if all_planets else None,
        'hottest': max(all_planets, key=lambda x: x.get('temp') or 0) if all_planets else None,
        'coldest': min(all_planets, key=lambda x: x.get('temp') or 9999) if all_planets else None,
    }
    
    # ═══════════════════════════════════════════════════════════════════════
    # COMPARISON DETECTION: "сравни X и Y", "compare X and Y"
    # ═══════════════════════════════════════════════════════════════════════
    compare_words = ['сравни', 'сравнить', 'compare', 'vs', 'versus', 'салыстыр']
    if any(w in q_lower for w in compare_words):
        # Find planet names in question
        found_planets = []
        for p in all_planets:
            if p['name'].lower() in q_lower:
                found_planets.append(p)
        
        # Also check known planets
        for name in KNOWN_PLANETS:
            if name.lower() in q_lower and name not in [p['name'] for p in found_planets]:
                found_planets.append({'name': name, **KNOWN_PLANETS[name], 'hab_score': int(KNOWN_PLANETS[name].get('esi', 0.5) * 100)})
        
        if len(found_planets) >= 2:
            p1, p2 = found_planets[0], found_planets[1]
            comparison = {
                'ru': f"""## ⚖️ Сравнение: {p1['name']} vs {p2['name']}

| Параметр | {p1['name']} | {p2['name']} | Лучше |
|----------|-------------|-------------|-------|
| **Радиус** | {p1.get('radius', '?'):.2f} R⊕ | {p2.get('radius', '?'):.2f} R⊕ | {'🌍' if abs(p1.get('radius',1)-1) < abs(p2.get('radius',1)-1) else '🔵'} |
| **Температура** | {p1.get('temp', '?'):.0f}K | {p2.get('temp', '?'):.0f}K | {'🌍' if abs(p1.get('temp',288)-288) < abs(p2.get('temp',288)-288) else '🔵'} |
| **ESI** | {p1.get('esi', '?')} | {p2.get('esi', '?')} | {'🌍' if (p1.get('esi',0) or 0) > (p2.get('esi',0) or 0) else '🔵'} |
| **Балл** | {p1.get('hab_score', '?')}/100 | {p2.get('hab_score', '?')}/100 | {'🌍' if p1.get('hab_score',0) > p2.get('hab_score',0) else '🔵'} |

**Вывод:** {'**' + p1['name'] + '** более перспективна' if p1.get('hab_score',0) > p2.get('hab_score',0) else '**' + p2['name'] + '** более перспективна'} для поиска жизни.""",
                'en': f"""## ⚖️ Comparison: {p1['name']} vs {p2['name']}

| Parameter | {p1['name']} | {p2['name']} | Better |
|-----------|-------------|-------------|--------|
| **Radius** | {p1.get('radius', '?'):.2f} R⊕ | {p2.get('radius', '?'):.2f} R⊕ | {'🌍' if abs(p1.get('radius',1)-1) < abs(p2.get('radius',1)-1) else '🔵'} |
| **Temperature** | {p1.get('temp', '?'):.0f}K | {p2.get('temp', '?'):.0f}K | {'🌍' if abs(p1.get('temp',288)-288) < abs(p2.get('temp',288)-288) else '🔵'} |
| **ESI** | {p1.get('esi', '?')} | {p2.get('esi', '?')} | {'🌍' if (p1.get('esi',0) or 0) > (p2.get('esi',0) or 0) else '🔵'} |
| **Score** | {p1.get('hab_score', '?')}/100 | {p2.get('hab_score', '?')}/100 | {'🌍' if p1.get('hab_score',0) > p2.get('hab_score',0) else '🔵'} |

**Conclusion:** {'**' + p1['name'] + '** is more promising' if p1.get('hab_score',0) > p2.get('hab_score',0) else '**' + p2['name'] + '** is more promising'} for life search.""",
                'kz': f"""## ⚖️ Салыстыру: {p1['name']} vs {p2['name']}

**Қорытынды:** {'**' + p1['name'] + '**' if p1.get('hab_score',0) > p2.get('hab_score',0) else '**' + p2['name'] + '**'} өмір іздеу үшін перспективті."""
            }
            return comparison[lang]
    
    # ═══════════════════════════════════════════════════════════════════════
    # FILTER/SEARCH: "найди планеты с температурой > 250K"
    # ═══════════════════════════════════════════════════════════════════════
    filter_words = ['найди', 'покажи', 'какие', 'find', 'show', 'which', 'filter', 'список', 'list', 'тап', 'көрсет']
    if any(w in q_lower for w in filter_words) and all_planets:
        results = all_planets.copy()
        filter_applied = False
        filter_desc = ""
        
        # Temperature filters
        if 'тепл' in q_lower or 'warm' in q_lower or 'hot' in q_lower or 'горяч' in q_lower:
            results = [p for p in results if p.get('temp', 0) > 280]
            filter_desc = "температура > 280K"
            filter_applied = True
        elif 'холод' in q_lower or 'cold' in q_lower:
            results = [p for p in results if p.get('temp', 999) < 260]
            filter_desc = "температура < 260K"
            filter_applied = True
        
        # Size filters
        if 'земн' in q_lower or 'earth' in q_lower:
            results = [p for p in results if 0.8 <= p.get('radius', 0) <= 1.5]
            filter_desc = "земной размер (0.8-1.5 R⊕)"
            filter_applied = True
        elif 'супер' in q_lower or 'super' in q_lower:
            results = [p for p in results if 1.25 < p.get('radius', 0) <= 2.0]
            filter_desc = "супер-Земли (1.25-2 R⊕)"
            filter_applied = True
        elif 'гигант' in q_lower or 'giant' in q_lower:
            results = [p for p in results if p.get('radius', 0) > 6]
            filter_desc = "газовые гиганты (>6 R⊕)"
            filter_applied = True
        
        # HZ filter
        if 'hz' in q_lower or 'обитаем' in q_lower or 'habitable' in q_lower:
            results = [p for p in results if p.get('in_hz')]
            filter_desc = "в зоне обитаемости"
            filter_applied = True
        
        # High score filter
        if 'лучш' in q_lower or 'best' in q_lower or 'топ' in q_lower or 'top' in q_lower:
            results = sorted(results, key=lambda x: x['hab_score'], reverse=True)[:5]
            filter_desc = "топ-5 по баллу"
            filter_applied = True
        
        if filter_applied and results:
            planet_list = "\n".join([f"• **{p['name']}** — {p['hab_score']}/100, {p.get('temp',0):.0f}K, {p.get('radius',0):.2f} R⊕" for p in results[:8]])
            response = {
                'ru': f"🔍 **Найдено {len(results)} планет** ({filter_desc}):\n\n{planet_list}",
                'en': f"🔍 **Found {len(results)} planets** ({filter_desc}):\n\n{planet_list}",
                'kz': f"🔍 **{len(results)} планета табылды** ({filter_desc}):\n\n{planet_list}"
            }
            return response[lang]
    
    # ═══════════════════════════════════════════════════════════════════════
    # CURRENT SYSTEM ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════
    system_words = ['систем', 'system', 'текущ', 'current', 'загружен', 'loaded', 'жүйе']
    if any(w in q_lower for w in system_words) and current_system:
        data = saved_systems.get(current_system, {})
        planets = data.get('planets', [])
        star = data.get('star', {})
        
        if planets:
            best = max(planets, key=lambda x: x['hab_score'])
            hz_count = len([p for p in planets if p['in_hz']])
            
            analysis = {
                'ru': f"""## 🌟 Система: {current_system}

**Звезда:** {star.get('st_spectype', '?')} типа, {star.get('st_teff', '?')}K

**Планеты:** {len(planets)} шт.
{chr(10).join([f"• {p['name']} — {p['hab_score']}/100 {'✅ HZ' if p['in_hz'] else ''}" for p in planets])}

**Анализ:**
• В зоне обитаемости: {hz_count} планет
• Лучший кандидат: **{best['name']}** (ESI: {best['esi']}, {best['temp']:.0f}K)
• {'⭐ Высокий потенциал!' if best['hab_score'] >= 60 else '📊 Умеренный интерес' if best['hab_score'] >= 40 else '📉 Низкий потенциал'}""",
                'en': f"""## 🌟 System: {current_system}

**Star:** {star.get('st_spectype', '?')} type, {star.get('st_teff', '?')}K

**Planets:** {len(planets)}
{chr(10).join([f"• {p['name']} — {p['hab_score']}/100 {'✅ HZ' if p['in_hz'] else ''}" for p in planets])}

**Analysis:**
• In habitable zone: {hz_count} planets
• Best candidate: **{best['name']}** (ESI: {best['esi']}, {best['temp']:.0f}K)
• {'⭐ High potential!' if best['hab_score'] >= 60 else '📊 Moderate interest' if best['hab_score'] >= 40 else '📉 Low potential'}""",
                'kz': f"""## 🌟 Жүйе: {current_system}

**Жұлдыз:** {star.get('st_spectype', '?')} түрі, {star.get('st_teff', '?')}K
**Планеталар:** {len(planets)}
**Үздік:** {best['name']} ({best['hab_score']}/100)"""
            }
            return analysis[lang]
    
    # ═══════════════════════════════════════════════════════════════════════
    # RECOMMENDATIONS
    # ═══════════════════════════════════════════════════════════════════════
    rec_words = ['рекоменд', 'совет', 'recommend', 'suggest', 'что исслед', 'what to', 'куда', 'where', 'ұсын']
    if any(w in q_lower for w in rec_words):
        recs = []
        
        # Check unexplored catalogs
        for cat_key, cat_data in CATALOGS.items():
            scanned = st.session_state.get('scanned_stars', set())
            unscanned = [s for s in cat_data['stars'] if s not in scanned]
            if len(unscanned) >= 5:
                recs.append(f"📁 Каталог **{cat_key}**: {len(unscanned)} неисследованных звёзд")
        
        # Check for patterns
        if stats['in_hz'] < 3:
            recs.append("🌱 Сфокусируйтесь на каталоге **habitable** для поиска планет в HZ")
        
        if stats['avg_score'] < 40:
            recs.append("📊 Средний балл низкий — попробуйте каталог **nearby** (ближайшие звёзды)")
        
        if not recs:
            recs.append("✅ Вы на правильном пути! Продолжайте исследования.")
        
        response = {
            'ru': "## 💡 Рекомендации:\n\n" + "\n".join(recs[:5]),
            'en': "## 💡 Recommendations:\n\n" + "\n".join(recs[:5]),
            'kz': "## 💡 Ұсыныстар:\n\n" + "\n".join(recs[:5])
        }
        return response[lang]
    
    # ═══════════════════════════════════════════════════════════════════════
    # STATISTICS (detailed)
    # ═══════════════════════════════════════════════════════════════════════
    stat_words = ['статистик', 'statistic', 'сколько', 'how many', 'итог', 'summary', 'қанша', 'результат', 'result']
    if any(w in q_lower for w in stat_words):
        if not all_planets:
            return {'ru': "📭 Пока нет данных. Запустите миссию!", 'en': "📭 No data yet. Run a mission!", 'kz': "📭 Деректер жоқ. Миссия іске қосыңыз!"}[lang]
        
        response = {
            'ru': f"""## 📊 Полная статистика исследований

**Общие данные:**
• Систем изучено: **{stats['systems']}**
• Планет найдено: **{stats['total']}**
• Средний балл: **{stats['avg_score']:.1f}/100**

**По типам:**
• 🌍 Земного размера: **{stats['earth_like']}**
• 🌎 Супер-Земли: **{stats['super_earth']}**
• 🪐 Газовые гиганты: **{stats['gas_giants']}**

**Обитаемость:**
• В зоне HZ: **{stats['in_hz']}**
• Потенциально обитаемых (>50): **{stats['habitable']}**

**Рекорды:**
• 🏆 Лучшая: **{stats['best']['name']}** ({stats['best']['hab_score']}/100)
• 📍 Ближайшая: **{stats['nearest']['name']}** ({stats['nearest'].get('distance', '?'):.1f} св.лет)
• 🔥 Горячая: **{stats['hottest']['name']}** ({stats['hottest'].get('temp', '?'):.0f}K)
• 🧊 Холодная: **{stats['coldest']['name']}** ({stats['coldest'].get('temp', '?'):.0f}K)""" if stats['best'] else "📭 Нет данных",
            'en': f"""## 📊 Full Research Statistics

**Overview:**
• Systems explored: **{stats['systems']}**
• Planets found: **{stats['total']}**
• Average score: **{stats['avg_score']:.1f}/100**

**By type:**
• 🌍 Earth-sized: **{stats['earth_like']}**
• 🌎 Super-Earths: **{stats['super_earth']}**
• 🪐 Gas giants: **{stats['gas_giants']}**

**Habitability:**
• In HZ: **{stats['in_hz']}**
• Potentially habitable (>50): **{stats['habitable']}**

**Records:**
• 🏆 Best: **{stats['best']['name']}** ({stats['best']['hab_score']}/100)
• 📍 Nearest: **{stats['nearest']['name']}** ({stats['nearest'].get('distance', '?'):.1f} ly)""" if stats['best'] else "📭 No data",
            'kz': f"""## 📊 Зерттеу статистикасы

• Жүйелер: **{stats['systems']}**
• Планеталар: **{stats['total']}**
• Орташа балл: **{stats['avg_score']:.1f}/100**
• HZ-да: **{stats['in_hz']}**
• Үздік: **{stats['best']['name']}** ({stats['best']['hab_score']}/100)""" if stats['best'] else "📭 Деректер жоқ"
        }
        return response[lang]
    
    # ═══════════════════════════════════════════════════════════════════════
    # SCIENTIFIC EXPLANATIONS
    # ═══════════════════════════════════════════════════════════════════════
    explanations = {
        'esi': {
            'ru': """## 🌍 ESI (Earth Similarity Index)

**Что это:** Индекс подобия Земле от 0 до 1.

**Формула:**
```
ESI = √[(1-|R-1|/(R+1))^0.57 × (1-|T-288|/(T+288))^5.58]
```

**Интерпретация:**
• **ESI > 0.9** — почти близнец Земли (очень редко!)
• **ESI 0.8-0.9** — отличный кандидат для жизни
• **ESI 0.6-0.8** — условия отличаются, но жизнь возможна
• **ESI < 0.6** — значительные отличия от Земли

**Важно:** ESI учитывает только размер и температуру. Атмосфера, вода, магнитное поле — не учитываются!""",
            'en': """## 🌍 ESI (Earth Similarity Index)

**What it is:** Earth similarity from 0 to 1.

**Formula:**
```
ESI = √[(1-|R-1|/(R+1))^0.57 × (1-|T-288|/(T+288))^5.58]
```

**Interpretation:**
• **ESI > 0.9** — almost Earth twin (very rare!)
• **ESI 0.8-0.9** — excellent life candidate
• **ESI 0.6-0.8** — different conditions, but life possible
• **ESI < 0.6** — significant differences from Earth"""
        },
        'hz': {
            'ru': """## 🌱 Зона обитаемости (Habitable Zone)

**Что это:** Область вокруг звезды, где возможна жидкая вода на поверхности планеты.

**Границы:**
• **Внутренняя:** 0.75 × √L AU (убегающий парниковый эффект)
• **Внешняя:** 1.77 × √L AU (замерзание CO₂)

где L — светимость звезды в солнечных единицах.

**Для разных звёзд:**
• ☀️ Солнце (G): 0.95 - 1.37 AU
• 🔴 M-карлик: 0.1 - 0.4 AU (очень близко!)
• 🔵 F-звезда: 1.5 - 2.5 AU

**Важно:** Нахождение в HZ не гарантирует обитаемость! Нужна атмосфера, магнитное поле, и многое другое.""",
            'en': """## 🌱 Habitable Zone (HZ)

**What it is:** Region around a star where liquid water can exist on a planet's surface.

**Boundaries:**
• **Inner:** 0.75 × √L AU (runaway greenhouse)
• **Outer:** 1.77 × √L AU (CO₂ freezing)

where L = stellar luminosity in solar units."""
        },
        'trappist': {
            'ru': """## 🔴 Система TRAPPIST-1

**Звезда:** Ультрахолодный красный карлик (M8V)
• Расстояние: **40.7 световых лет**
• Температура: ~2,566K (в 2 раза холоднее Солнца)
• Размер: 12% от Солнца

**7 планет земного размера!**
• TRAPPIST-1b, c — слишком горячие
• **TRAPPIST-1d, e, f** — в зоне обитаемости! ⭐
• TRAPPIST-1g, h — возможно слишком холодные

**Почему важна:**
• Все 7 планет можно изучать транзитным методом
• 3-4 планеты потенциально обитаемы
• Ближайшая система с таким количеством землеподобных планет

**Риски:**
• ⚠️ Приливной захват (одна сторона всегда к звезде)
• ⚠️ Звёздные вспышки (M-карлики активны)
• ⚠️ Возможная потеря атмосферы""",
            'en': """## 🔴 TRAPPIST-1 System

**Star:** Ultracool red dwarf (M8V)
• Distance: **40.7 light years**
• Temperature: ~2,566K

**7 Earth-sized planets!**
• **TRAPPIST-1d, e, f** — in habitable zone! ⭐

**Risks:**
• ⚠️ Tidal locking
• ⚠️ Stellar flares"""
        }
    }
    
    # Check for explanation keywords
    if 'esi' in q_lower or 'индекс' in q_lower:
        return explanations['esi'].get(lang, explanations['esi']['en'])
    if 'hz' in q_lower or 'обитаем' in q_lower or 'habitable' in q_lower or 'зона' in q_lower:
        return explanations['hz'].get(lang, explanations['hz']['en'])
    if 'trappist' in q_lower:
        return explanations['trappist'].get(lang, explanations['trappist']['en'])
    
    # ═══════════════════════════════════════════════════════════════════════
    # GREETING
    # ═══════════════════════════════════════════════════════════════════════
    greet_words = ['привет', 'hello', 'hi', 'здравств', 'сәлем', 'хай', 'hey']
    if any(w in q_lower for w in greet_words):
        response = {
            'ru': f"""👋 Привет! Я ИИ-ассистент ATLAS.

{'📊 У вас уже есть данные: ' + str(stats["total"]) + ' планет в ' + str(stats["systems"]) + ' системах.' if stats["total"] > 0 else '🚀 Запустите миссию, чтобы начать исследования!'}

**Что я умею:**
• 📊 Статистика — "покажи статистику"
• 🔍 Поиск — "найди планеты в HZ"
• ⚖️ Сравнение — "сравни TRAPPIST-1e и Proxima b"
• 💡 Рекомендации — "что исследовать?"
• 🌟 Анализ — "расскажи про текущую систему"
• 📚 Объяснения — "что такое ESI?"

Спрашивайте!""",
            'en': f"""👋 Hello! I'm the ATLAS AI assistant.

{'📊 You have data: ' + str(stats["total"]) + ' planets in ' + str(stats["systems"]) + ' systems.' if stats["total"] > 0 else '🚀 Run a mission to start exploring!'}

**What I can do:**
• 📊 Statistics — "show statistics"
• 🔍 Search — "find planets in HZ"
• ⚖️ Compare — "compare TRAPPIST-1e and Proxima b"
• 💡 Recommendations — "what to explore?"
• 📚 Explanations — "what is ESI?"

Ask me anything!""",
            'kz': f"""👋 Сәлем! Мен ATLAS AI көмекшісімін.

{'📊 Деректер бар: ' + str(stats["total"]) + ' планета.' if stats["total"] > 0 else '🚀 Зерттеуді бастау үшін миссия іске қосыңыз!'}

Сұрақтарыңызды қойыңыз!"""
        }
        return response[lang]
    
    # ═══════════════════════════════════════════════════════════════════════
    # SPECIFIC PLANET QUERY
    # ═══════════════════════════════════════════════════════════════════════
    for p in all_planets:
        if p['name'].lower() in q_lower:
            return {
                'ru': f"""## 🪐 {p['name']}

**Тип:** {p.get('type', '?')} {p.get('emoji', '')}

**Физические параметры:**
• Радиус: **{p.get('radius', '?'):.2f} R⊕**
• Температура: **{p.get('temp', '?'):.0f}K**
• ESI: **{p.get('esi', '?')}**
• Гравитация: **{p.get('gravity', '?'):.2f}g**

**Обитаемость:**
• Балл: **{p['hab_score']}/100**
• В зоне HZ: **{'Да ✅' if p.get('in_hz') else 'Нет ❌'}**
• Атмосфера: {p.get('atmo_type', '?')}

**Оценка:** {'🌱 Отличный кандидат для жизни!' if p['hab_score'] >= 70 else '📊 Умеренный потенциал' if p['hab_score'] >= 50 else '❄️ Низкий потенциал'}""",
                'en': f"""## 🪐 {p['name']}

**Type:** {p.get('type', '?')} {p.get('emoji', '')}

**Physical:**
• Radius: **{p.get('radius', '?'):.2f} R⊕**
• Temperature: **{p.get('temp', '?'):.0f}K**
• ESI: **{p.get('esi', '?')}**

**Habitability:**
• Score: **{p['hab_score']}/100**
• In HZ: **{'Yes ✅' if p.get('in_hz') else 'No ❌'}**"""
            }[lang]
    
    # ═══════════════════════════════════════════════════════════════════════
    # DEFAULT RESPONSE
    # ═══════════════════════════════════════════════════════════════════════
    default = {
        'ru': f"""🤔 Интересный вопрос! Вот что я могу:

**Попробуйте спросить:**
• "Покажи статистику"
• "Найди планеты в зоне обитаемости"
• "Сравни Earth и TRAPPIST-1e"
• "Что такое ESI?"
• "Расскажи про систему TRAPPIST-1"
• "Какая планета лучшая?"
• "Что исследовать дальше?"

{'📊 У вас ' + str(stats["total"]) + ' планет для анализа!' if stats["total"] > 0 else '🚀 Запустите миссию для начала!'}""",
        'en': f"""🤔 Interesting question! Here's what I can do:

**Try asking:**
• "Show statistics"
• "Find planets in habitable zone"
• "Compare Earth and TRAPPIST-1e"
• "What is ESI?"
• "What to explore next?"

{'📊 You have ' + str(stats["total"]) + ' planets to analyze!' if stats["total"] > 0 else '🚀 Run a mission to start!'}""",
        'kz': """🤔 Қызықты сұрақ! Мен көмектесе аламын:

• "Статистиканы көрсет"
• "HZ-дағы планеталарды тап"
• "ESI дегеніміз не?"

🚀 Миссия іске қосыңыз!"""
    }
    return default[lang]


def get_smart_response(question):
    """
    Main function to get AI response using ML model or pattern matching.
    Always returns a string, never a dict.
    """
    lang = st.session_state.get('lang', 'ru')
    
    # Try ML model first if available
    if CHATBOT_AVAILABLE and chatbot_model is not None:
        try:
            # Predict category
            category = chatbot_model.predict([question])[0]
            
            # Get base response from trained data
            base_response = chatbot_responses.get(category, None)
            
            if base_response and isinstance(base_response, str):
                # Enhance with user's discovery data
                all_planets = get_all_planets()
                stats_info = ""
                
                if all_planets:
                    best = max(all_planets, key=lambda x: x['hab_score'])
                    stats_info = f"\n\n📊 *Из ваших данных: {len(all_planets)} планет, лучшая — {best['name']} ({best['hab_score']}/100)*"
                
                return f"🧠 **ATLAS AI** анализирует запрос...\n\n**Категория:** `{category}`\n\n{base_response}{stats_info}", "🧠"
        except Exception as e:
            pass
    
    # Fallback to pattern matching
    response = get_ai_response(question)
    
    # Ensure response is a string, not a dict
    if isinstance(response, dict):
        response = response.get(lang, response.get('ru', response.get('en', str(response))))
    
    return response, "⚡"
# ═══════════════════════════════════════════════════════════════════════════════
# ENCYCLOPEDIA DATA (Multilingual)
# ═══════════════════════════════════════════════════════════════════════════════

ENCYCLOPEDIA = {
    'star_types': {
        'title': {'ru': '⭐ Типы звёзд', 'en': '⭐ Star Types', 'kz': '⭐ Жұлдыз түрлері'},
        'content': {
            'ru': """
### Спектральная классификация звёзд (O-B-A-F-G-K-M)

| Класс | Температура | Цвет | Масса | Время жизни | Примеры |
|-------|-------------|------|-------|-------------|---------|
| O | 30,000-50,000K | Голубой | 16-150 M☉ | <10 млн лет | Минтака, Алнилам |
| B | 10,000-30,000K | Бело-голубой | 2-16 M☉ | 10-300 млн лет | Ригель, Спика |
| A | 7,500-10,000K | Белый | 1.4-2.1 M☉ | 0.3-2 млрд лет | Сириус, Вега |
| F | 6,000-7,500K | Жёлто-белый | 1.0-1.4 M☉ | 2-7 млрд лет | Процион, Канопус |
| G | 5,200-6,000K | Жёлтый | 0.8-1.04 M☉ | 7-15 млрд лет | **Солнце**, Альфа Центавра A |
| K | 3,700-5,200K | Оранжевый | 0.45-0.8 M☉ | 15-50 млрд лет | Альфа Центавра B, Эпсилон Эридана |
| M | 2,400-3,700K | Красный | 0.08-0.45 M☉ | 50+ млрд лет | Проксима Центавра, TRAPPIST-1 |

#### Оптимальные для жизни
**G и K типы** — достаточно света для фотосинтеза, стабильны миллиарды лет. Солнце — звезда G-типа.

#### Проблемные для жизни
**M-карлики** — частые вспышки, планеты в приливном захвате (одна сторона всегда к звезде).
**O/B типы** — слишком горячие, слишком недолговечные для эволюции жизни.
            """,
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
| O | 30,000-50,000K | Көк | 16-150 M☉ | <10 млн жыл | Минтака, Алнилам |
| B | 10,000-30,000K | Ақ-көк | 2-16 M☉ | 10-300 млн жыл | Ригель, Спика |
| A | 7,500-10,000K | Ақ | 1.4-2.1 M☉ | 0.3-2 млрд жыл | Сириус, Вега |
| F | 6,000-7,500K | Сары-ақ | 1.0-1.4 M☉ | 2-7 млрд жыл | Процион |
| G | 5,200-6,000K | Сары | 0.8-1.04 M☉ | 7-15 млрд жыл | **Күн**, Альфа Центавра A |
| K | 3,700-5,200K | Сарғыш | 0.45-0.8 M☉ | 15-50 млрд жыл | Альфа Центавра B |
| M | 2,400-3,700K | Қызыл | 0.08-0.45 M☉ | 50+ млрд жыл | Проксима Центавра, TRAPPIST-1 |

#### Өмір үшін оңтайлы
**G және K түрлері** — фотосинтез үшін жеткілікті жарық, миллиардтаған жылдар бойы тұрақты.

#### Өмір үшін проблемалы
**M-ергежейлілер** — жиі жарқылдар, планеталар толқындық байланыста.
**O/B түрлері** — тым ыстық, өмір эволюциясы үшін тым қысқа өмірлі.
            """
        }
    },
    
    'planet_types': {
        'title': {'ru': '🪐 Типы планет', 'en': '🪐 Planet Types', 'kz': '🪐 Планета түрлері'},
        'content': {
            'ru': """
### Классификация экзопланет по размеру

| Тип | Радиус (R⊕) | Описание | Примеры |
|-----|-------------|----------|---------|
| 🪨 Карликовая | <0.5 | Астероидоподобное тело без атмосферы | Церера |
| 🔴 Суб-Земля | 0.5-0.8 | Марсоподобная, тонкая атмосфера | Марс, Kepler-138b |
| 🌍 Земная | 0.8-1.25 | Потенциально обитаемая, тектоника плит | Земля, Kepler-442b |
| 🌎 Супер-Земля | 1.25-2.0 | Толстая атмосфера, возможны океаны | LHS-1140b, K2-18b |
| 💧 Мини-Нептун | 2.0-4.0 | Водяной мир или газовая оболочка | TOI-270d, Kepler-11f |
| 🔵 Нептуноподобная | 4-6 | Ледяной гигант, глубокая H₂/He атмосфера | Уран, Нептун |
| 🪐 Газовый гигант | 6-15 | Юпитероподобная, металлический водород | Юпитер, HD-209458b |
| 🟤 Супер-Юпитер | >15 | Грань коричневого карлика | KELT-9b |

#### "Долина радиусов" (1.5-2.0 R⊕)
В этом диапазоне наблюдается дефицит планет — переходная зона между каменистыми и газовыми мирами. 
Причина: фотоиспарение атмосферы под действием звёздного излучения.
            """,
            'en': """
### Exoplanet Classification by Size

| Type | Radius (R⊕) | Description | Examples |
|------|-------------|-------------|----------|
| 🪨 Dwarf | <0.5 | Asteroid-like body without atmosphere | Ceres |
| 🔴 Sub-Earth | 0.5-0.8 | Mars-like, thin atmosphere | Mars, Kepler-138b |
| 🌍 Terrestrial | 0.8-1.25 | Potentially habitable, plate tectonics | Earth, Kepler-442b |
| 🌎 Super-Earth | 1.25-2.0 | Thick atmosphere, possible oceans | LHS-1140b, K2-18b |
| 💧 Mini-Neptune | 2.0-4.0 | Water world or gas envelope | TOI-270d, Kepler-11f |
| 🔵 Neptune-like | 4-6 | Ice giant, deep H₂/He atmosphere | Uranus, Neptune |
| 🪐 Gas Giant | 6-15 | Jupiter-like, metallic hydrogen | Jupiter, HD-209458b |
| 🟤 Super-Jupiter | >15 | Near brown dwarf boundary | KELT-9b |

#### "Radius Valley" (1.5-2.0 R⊕)
Deficit of planets in this range — transition zone between rocky and gaseous worlds.
Cause: photoevaporation of atmosphere by stellar radiation.
            """,
            'kz': """
### Экзопланеталардың өлшемі бойынша жіктелуі

| Түр | Радиус (R⊕) | Сипаттама | Мысалдар |
|-----|-------------|-----------|----------|
| 🪨 Ергежейлі | <0.5 | Атмосферасыз астероид тәрізді дене | Церера |
| 🔴 Суб-Жер | 0.5-0.8 | Марсқа ұқсас, жұқа атмосфера | Марс, Kepler-138b |
| 🌍 Жер тәрізді | 0.8-1.25 | Мекендеуге жарамды, плиталар тектоникасы | Жер, Kepler-442b |
| 🌎 Супер-Жер | 1.25-2.0 | Қалың атмосфера, мұхиттар мүмкін | LHS-1140b, K2-18b |
| 💧 Мини-Нептун | 2.0-4.0 | Су әлемі немесе газ қабаты | TOI-270d |
| 🔵 Нептунға ұқсас | 4-6 | Мұзды алып, терең H₂/He атмосферасы | Уран, Нептун |
| 🪐 Газ алыбы | 6-15 | Юпитерге ұқсас, металл сутегі | Юпитер, HD-209458b |
| 🟤 Супер-Юпитер | >15 | Қоңыр ергежейлі шекарасында | KELT-9b |

#### "Радиус алқабы" (1.5-2.0 R⊕)
Бұл ауқымда планеталар тапшылығы — тасты және газды әлемдер арасындағы өтпелі аймақ.
            """
        }
    },
    
    'habitability': {
        'title': {'ru': '🌱 Критерии обитаемости', 'en': '🌱 Habitability Criteria', 'kz': '🌱 Мекендеуге жарамдылық критерийлері'},
        'content': {
            'ru': """
### Основные критерии обитаемости планеты

#### 1. Зона обитаемости (HZ)
Область вокруг звезды, где возможна жидкая вода на поверхности.
- **Внутренняя граница**: 0.75√L AU (парниковый эффект)
- **Внешняя граница**: 1.77√L AU (конденсация CO₂)
- L — светимость звезды в солнечных единицах

#### 2. Размер и масса
- **Оптимально**: 0.8-1.5 R⊕, 0.5-5 M⊕
- Планета должна удержать атмосферу, но не стать газовым гигантом

#### 3. Температура
- **Идеально**: 250-310K (жидкая вода)
- **Расширенно**: 200-350K (экстремофилы)

#### 4. Атмосфера
- N₂/O₂ (биогенная) или N₂/CO₂ (абиотическая)
- Давление: 0.5-5 атм для стабильности воды

#### 5. Магнитное поле
Защита от звёздного ветра и космических лучей. Требуется жидкое железное ядро + вращение.

#### 6. Стабильность звезды
- **Оптимально**: G, K типы
- **Риски**: M-карлики (вспышки), O/B (короткая жизнь)

### Индекс подобия Земле (ESI)
```
ESI = √[(1-|R-1|/(R+1))^0.57 × (1-|T-288|/(T+288))^5.58]
```
ESI > 0.8 = кандидат типа Земли
            """,
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
- **Risks**: M-dwarfs (flares), O/B (short-lived)

### Earth Similarity Index (ESI)
```
ESI = √[(1-|R-1|/(R+1))^0.57 × (1-|T-288|/(T+288))^5.58]
```
ESI > 0.8 = Earth-like candidate
            """,
            'kz': """
### Планетаның мекендеуге жарамдылығының негізгі критерийлері

#### 1. Мекендеуге жарамды аймақ (HZ)
Жұлдыз айналасындағы бетінде сұйық су болуы мүмкін аймақ.
- **Ішкі шекара**: 0.75√L AU (жүгірмелі парник)
- **Сыртқы шекара**: 1.77√L AU (CO₂ конденсациясы)

#### 2. Өлшем және масса
- **Оңтайлы**: 0.8-1.5 R⊕, 0.5-5 M⊕
- Планета атмосфераны ұстап тұруы керек

#### 3. Температура
- **Идеал**: 250-310K (сұйық су)
- **Кеңейтілген**: 200-350K (экстремофилдер)

#### 4. Атмосфера
- N₂/O₂ (биогендік) немесе N₂/CO₂ (абиотикалық)
- Қысым: 0.5-5 атм

#### 5. Магнит өрісі
Жұлдыз желі мен ғарыштық сәулелерден қорғау.

#### 6. Жұлдыз тұрақтылығы
- **Оңтайлы**: G, K түрлері
- **Қауіптер**: M-ергежейлілер (жарқылдар)

### Жерге ұқсастық индексі (ESI)
```
ESI = √[(1-|R-1|/(R+1))^0.57 × (1-|T-288|/(T+288))^5.58]
```
ESI > 0.8 = Жер тәрізді үміткер
            """
        }
    },
    
    'detection': {
        'title': {'ru': '🔭 Методы обнаружения', 'en': '🔭 Detection Methods', 'kz': '🔭 Анықтау әдістері'},
        'content': {
            'ru': """
### Методы обнаружения экзопланет

#### 1. Транзитный метод (Kepler, TESS) — 76% открытий
Планета проходит перед звездой → падение яркости 0.01-1%
- **Даёт**: радиус, период, наклон орбиты
- **Требует**: орбита "ребром" к наблюдателю

#### 2. Метод радиальных скоростей (RV) — 19% открытий
Звезда "качается" под действием гравитации планеты → допплеровский сдвиг спектра
- **Даёт**: минимальную массу (M·sin i), период
- **Точность**: до 1 м/с (планеты типа Земли)

#### 3. Прямое наблюдение — 2% открытий
Блокирование звезды коронографом → свет от планеты
- **Даёт**: атмосферу, температуру, орбиту
- **Ограничение**: только далёкие гиганты

#### 4. Микролинзирование
Гравитация планеты искривляет свет фоновой звезды
- **Одноразовое** событие, нет повтора
- Открывает далёкие планеты

#### 5. Астрометрия (Gaia)
Точное измерение покачивания звезды на небе
- **Даёт**: массу и орбиту
- **Требует**: высокую точность

### Статистика открытий (2024)
- **5,500+** подтверждённых экзопланет
- **70+** потенциально обитаемых
- **Kepler**: 2,700+ планет
- **TESS**: 500+ планет
            """,
            'en': """
### Exoplanet Detection Methods

#### 1. Transit Method (Kepler, TESS) — 76% of discoveries
Planet passes in front of star → brightness dip 0.01-1%
- **Provides**: radius, period, orbital inclination
- **Requires**: edge-on orbit

#### 2. Radial Velocity (RV) — 19% of discoveries
Star "wobbles" due to planet's gravity → Doppler shift in spectrum
- **Provides**: minimum mass (M·sin i), period
- **Precision**: down to 1 m/s (Earth-like planets)

#### 3. Direct Imaging — 2% of discoveries
Block star with coronagraph → light from planet
- **Provides**: atmosphere, temperature, orbit
- **Limitation**: only distant giants

#### 4. Microlensing
Planet's gravity bends background star light
- **One-time** event, no repeat
- Discovers distant planets

#### 5. Astrometry (Gaia)
Precise measurement of star wobble on sky
- **Provides**: mass and orbit
- **Requires**: high precision

### Discovery Statistics (2024)
- **5,500+** confirmed exoplanets
- **70+** potentially habitable
- **Kepler**: 2,700+ planets
- **TESS**: 500+ planets
            """,
            'kz': """
### Экзопланеталарды анықтау әдістері

#### 1. Транзит әдісі (Kepler, TESS) — ашылымдардың 76%
Планета жұлдыздың алдынан өтеді → жарықтық 0.01-1% төмендеуі
- **Береді**: радиус, период, орбита көлбеуі

#### 2. Радиалды жылдамдық (RV) — ашылымдардың 19%
Жұлдыз планета гравитациясынан "тербеледі" → спектрдің Доплер жылжуы
- **Береді**: минималды масса, период

#### 3. Тікелей бақылау — ашылымдардың 2%
Жұлдызды коронографпен бұғаттау → планетадан жарық
- **Береді**: атмосфера, температура, орбита

#### 4. Микролинзалау
Планета гравитациясы фондық жұлдыз жарығын бүгеді
- **Бір реттік** оқиға

#### 5. Астрометрия (Gaia)
Жұлдыздың аспандағы тербелісін дәл өлшеу
- **Береді**: масса және орбита

### Ашылым статистикасы (2024)
- **5,500+** расталған экзопланеталар
- **70+** мекендеуге жарамды
- **Kepler**: 2,700+ планета
- **TESS**: 500+ планета
            """
        }
    },
    
    'formulas': {
        'title': {'ru': '📐 Формулы', 'en': '📐 Formulas', 'kz': '📐 Формулалар'},
        'content': {
            'ru': """
### Основные астрофизические формулы

#### Светимость звезды (закон Стефана-Больцмана)
```
L = R² × (T/5778)⁴ [L☉]
```
R — радиус в R☉, T — температура в K

#### Равновесная температура планеты
```
Teq = T★ × √(R★/(2a)) × (1-A)^0.25
```
A — альбедо (~0.3), a — орбита в AU

#### Границы зоны обитаемости
```
HZ_inner = 0.75 × √L [AU]
HZ_outer = 1.77 × √L [AU]
```

#### Третий закон Кеплера
```
a³ = (P/365.25)² × M★ [AU]
```
P — период в днях, M★ — масса звезды в M☉

#### Поверхностная гравитация
```
g = M/R² [g⊕]
```
M, R — масса и радиус в земных единицах

#### Вторая космическая скорость
```
v_esc = 11.2 × √(M/R) [км/с]
```
Для Земли: 11.2 км/с

#### Плотность
```
ρ = M/R³ [ρ⊕]
```
Земля: 5.51 г/см³

#### Индекс подобия Земле (ESI)
```
ESI = √[(1-|R-1|/(R+1))^0.57 × (1-|T-288|/(T+288))^5.58]
```

#### Сфера Хилла (стабильность спутников)
```
r_Hill = a × (m/(3M★))^(1/3)
```
            """,
            'en': """
### Key Astrophysical Formulas

#### Stellar Luminosity (Stefan-Boltzmann Law)
```
L = R² × (T/5778)⁴ [L☉]
```
R — radius in R☉, T — temperature in K

#### Planetary Equilibrium Temperature
```
Teq = T★ × √(R★/(2a)) × (1-A)^0.25
```
A — albedo (~0.3), a — orbit in AU

#### Habitable Zone Boundaries
```
HZ_inner = 0.75 × √L [AU]
HZ_outer = 1.77 × √L [AU]
```

#### Kepler's Third Law
```
a³ = (P/365.25)² × M★ [AU]
```
P — period in days, M★ — stellar mass in M☉

#### Surface Gravity
```
g = M/R² [g⊕]
```
M, R — mass and radius in Earth units

#### Escape Velocity
```
v_esc = 11.2 × √(M/R) [km/s]
```
Earth: 11.2 km/s

#### Density
```
ρ = M/R³ [ρ⊕]
```
Earth: 5.51 g/cm³

#### Earth Similarity Index (ESI)
```
ESI = √[(1-|R-1|/(R+1))^0.57 × (1-|T-288|/(T+288))^5.58]
```

#### Hill Sphere (moon stability)
```
r_Hill = a × (m/(3M★))^(1/3)
```
            """,
            'kz': """
### Негізгі астрофизикалық формулалар

#### Жұлдыз жарықтығы (Стефан-Больцман заңы)
```
L = R² × (T/5778)⁴ [L☉]
```

#### Планетаның тепе-теңдік температурасы
```
Teq = T★ × √(R★/(2a)) × (1-A)^0.25
```

#### Мекендеуге жарамды аймақ шекаралары
```
HZ_inner = 0.75 × √L [AU]
HZ_outer = 1.77 × √L [AU]
```

#### Кеплердің үшінші заңы
```
a³ = (P/365.25)² × M★ [AU]
```

#### Бетіндегі гравитация
```
g = M/R² [g⊕]
```

#### Екінші ғарыштық жылдамдық
```
v_esc = 11.2 × √(M/R) [км/с]
```

#### Тығыздық
```
ρ = M/R³ [ρ⊕]
```

#### Жерге ұқсастық индексі (ESI)
```
ESI = √[(1-|R-1|/(R+1))^0.57 × (1-|T-288|/(T+288))^5.58]
```

#### Хилл сферасы
```
r_Hill = a × (m/(3M★))^(1/3)
```
            """
        }
    }
}
# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR - Compact & Clean
# ═══════════════════════════════════════════════════════════════════════════════

# Initialize session timer
import time
if 'session_start' not in st.session_state:
    st.session_state.session_start = time.time()

# Random ATLAS notifications (toast)
import random
if random.random() < 0.20:  # 20% chance
    toast_messages = {
        'ru': [
            "📡 TESS передал новый пакет данных",
            "🔭 Kepler завершил калибровку", 
            "⚡ Активность на Проксиме Центавра",
            "🛰️ Сигнал от Voyager 1",
            "📊 База NASA обновлена",
            "🌟 Транзит в TOI-700",
            "🔬 JWST: спектральный анализ",
        ],
        'en': [
            "📡 TESS transmitted new data",
            "🔭 Kepler calibration complete",
            "⚡ Activity on Proxima Centauri", 
            "🛰️ Signal from Voyager 1",
            "📊 NASA database updated",
            "🌟 Transit in TOI-700",
            "🔬 JWST: spectral analysis",
        ]
    }
    lang = st.session_state.get('lang', 'ru')
    msgs = toast_messages.get(lang, toast_messages['en'])
    st.toast(random.choice(msgs), icon="🛸")

# Check achievements
check_all_achievements()

# Render achievement popup if any
render_achievement_popup()

st.markdown(get_css(), unsafe_allow_html=True)

NAV_ITEMS = [
    ('missions', {'en': 'Missions', 'kz': '?????????'}),
    ('system', {'en': 'System', 'kz': '????'}),
    ('map', {'en': 'Map', 'kz': '?????'}),
    ('analysis', {'en': 'Analysis', 'kz': '??????'}),
    ('compare', {'en': 'Compare', 'kz': '?????????'}),
    ('nasa_eyes', {'en': 'NASA Eyes', 'kz': 'NASA Eyes'}),
    ('ai_chat', {'en': 'AI Chat', 'kz': 'AI Chat'}),
]

MORE_ITEMS = [
    ('encyclopedia', {'en': 'Reference', 'kz': '???????????'}),
    ('history', {'en': 'History', 'kz': '?????'}),
    ('achievements', {'en': 'Achievements', 'kz': '???????????'})
]

PAGE_META = {
    'missions': {
        'eyebrow': {'en': 'Mission Dashboard', 'kz': '?????? ????????'},
        'title': {'en': 'Field operations for future worlds', 'kz': '??????? ????????? ???????? ??????'},
        'subtitle': {
            'en': 'ATLAS scans nearby catalogs, records promising systems, and keeps your mission archive in one place.',
            'kz': 'ATLAS ????? ???????????? ???????????, ???????? ??? ????????? ???????? ???? ?????? ????????? ??? ????? ????????.'
        }
    },
    'system': {
        'eyebrow': {'en': 'System View', 'kz': '???? ????????'},
        'title': {'en': 'Loaded system intelligence', 'kz': '????????? ???? ???????'},
        'subtitle': {'en': 'Inspect the active star, orbit model, and planetary diagnostics.', 'kz': '???????? ????????, ?????? ??????? ???? ?????????? ?????????????? ?????????.'}
    },
    'map': {
        'eyebrow': {'en': 'Stellar Map', 'kz': '?????? ???????'},
        'title': {'en': 'Neighborhood navigation', 'kz': '????? ???????? ???????????'},
        'subtitle': {'en': 'Explore the local stellar neighborhood and mission priorities.', 'kz': '?????????? ?????? ?????????? ???? ?????? ????????????? ?????????.'}
    },
    'analysis': {
        'eyebrow': {'en': 'Planet Analysis', 'kz': '??????? ???????'},
        'title': {'en': 'Model-driven habitability review', 'kz': '???????? ??????????? ??????'},
        'subtitle': {'en': 'Predict conditions, compare signals, and surface the strongest candidates.', 'kz': '??????????? ????????, ??????????? ???????????? ???? ?? ????? ????????????? ???????.'}
    },
    'compare': {
        'eyebrow': {'en': 'Comparison Lab', 'kz': '????????? ??????????'},
        'title': {'en': 'Side-by-side world comparison', 'kz': '????????? ????? ?????????'},
        'subtitle': {'en': 'Contrast atmospheric, thermal, and survivability indicators.', 'kz': '????????????, ??????? ???? ???? ???? ?????????????? ????????????.'}
    },
    'encyclopedia': {
        'eyebrow': {'en': 'Reference Archive', 'kz': '??????????? ???'},
        'title': {'en': 'Guides for missions and science terms', 'kz': '????????? ??? ????? ??????????'},
        'subtitle': {'en': 'Keep formulas, detection methods, and star classes close at hand.', 'kz': '??????????, ??????? ???????? ???? ?????? ???????? ??? ????????? ??????.'}
    },
    'history': {
        'eyebrow': {'en': 'Mission History', 'kz': '?????? ??????'},
        'title': {'en': 'Saved scans and archive control', 'kz': '????????? ????????? ???? ????????? ???????'},
        'subtitle': {'en': 'Review studied systems, save progress locally, and manage stored mission data.', 'kz': '?????????? ????????? ?????, ????????? ?????????? ????? ??????, ?????? ?????????? ??????????.'}
    },
    'achievements': {
        'eyebrow': {'en': 'Explorer Log', 'kz': '????????? ???????'},
        'title': {'en': 'Milestones unlocked by ATLAS crews', 'kz': 'ATLAS ?????????? ????? ???????????'},
        'subtitle': {'en': 'Track progress across exploration, AI research, and habitable discoveries.', 'kz': '???????, AI ??????? ???? ?????????? ??????? ??????? ??????? ????????? ?????????.'}
    },
    'nasa_eyes': {
        'eyebrow': {'en': 'NASA Eyes', 'kz': 'NASA Eyes'},
        'title': {'en': 'Live solar system portal', 'kz': '??? ????????? ???? ???????'},
        'subtitle': {'en': 'Launch into NASA?s real-time interactive visualization tools.', 'kz': 'NASA-??? ????? ????????? ???????????? ???????????????? ???????.'}
    },
    'ai_chat': {
        'eyebrow': {'en': 'ATLAS AI', 'kz': 'ATLAS AI'},
        'title': {'en': 'Mission support conversation', 'kz': '???????? ?????? ???????'},
        'subtitle': {'en': 'Ask for explanations, summaries, and research guidance without leaving the app.', 'kz': '?????????? ??????-?? ??????????, ??????? ???? ???? ??????? ??????????? ??????.'}
    }
}


def asset_to_data_uri(path_str):
    path = Path(path_str)
    if not path.exists():
        return ''
    mime = 'image/png' if path.suffix.lower() == '.png' else 'image/jpeg'
    encoded = base64.b64encode(path.read_bytes()).decode('ascii')
    return f'data:{mime};base64,{encoded}'


def get_route_state():
    try:
        params = st.experimental_get_query_params()
    except Exception:
        params = {}

    page = params.get('page', [st.session_state.get('current_page', 'missions')])
    lang = params.get('lang', [st.session_state.get('lang', 'en')])

    page = page[0] if isinstance(page, list) else page
    lang = lang[0] if isinstance(lang, list) else lang

    valid_pages = {key for key, _ in NAV_ITEMS} | {key for key, _ in MORE_ITEMS}
    if page not in valid_pages:
        page = 'missions'
    if lang not in ('en', 'kz'):
        lang = 'en'

    st.session_state.current_page = page
    st.session_state.lang = lang
    return page, lang


def build_href(page_key, lang_code):
    return f'?page={page_key}&amp;lang={lang_code}'


def render_top_nav(current_page, lang):
    main_links = []
    for key, label_map in NAV_ITEMS:
        css_class = 'atlas-nav-link active' if current_page == key else 'atlas-nav-link'
        main_links.append(f"<a class='{css_class}' href='{build_href(key, lang)}'>{label_map[lang]}</a>")

    more_links = []
    for key, label_map in MORE_ITEMS:
        css_class = 'active' if current_page == key else ''
        more_links.append(f"<a class='{css_class}' href='{build_href(key, lang)}'>{label_map[lang]}</a>")

    more_label = {'en': 'More', 'kz': '????'}[lang]
    more_class = 'atlas-nav-link active' if current_page in {key for key, _ in MORE_ITEMS} else 'atlas-nav-ghost'
    lang_en_class = 'atlas-nav-lang active' if lang == 'en' else 'atlas-nav-lang'
    lang_kz_class = 'atlas-nav-lang active' if lang == 'kz' else 'atlas-nav-lang'

    nav_html = f"""
    <div class='atlas-nav-shell'>
      <div class='atlas-nav-bar'>
        <div class='atlas-brand'><span class='atlas-brand-dot'></span>ATLAS</div>
        <div class='atlas-nav-links'>
          {''.join(main_links)}
        </div>
        <div class='atlas-nav-right'>
          <div class='atlas-nav-lang-group'>
            <a class='{lang_en_class}' href='{build_href(current_page, 'en')}'>EN</a>
            <a class='{lang_kz_class}' href='{build_href(current_page, 'kz')}'>KZ</a>
          </div>
          <details class='atlas-more'>
            <summary class='{more_class}'>{more_label}</summary>
            <div class='atlas-more-menu'>
              {''.join(more_links)}
            </div>
          </details>
        </div>
      </div>
    </div>
    """
    st.markdown(nav_html, unsafe_allow_html=True)


def render_mission_hero(lang):
    background_uri = asset_to_data_uri(r'C:\Users\user\advanced_app\background.png')
    now_label = datetime.now().strftime('%a %H:%M').upper()
    systems_count = len(st.session_state.get('saved_systems', {}))
    habitable_count = st.session_state.get('habitable_count', 0)
    worlds_count = st.session_state.get('total_planets_found', 0)

    quotes = {
        'en': [
            {'title': 'Dreams of the future', 'author': 'Neil Armstrong', 'body': 'ATLAS studies stellar systems, reviews exoplanets, and highlights the worlds most worth a closer look.'},
            {'title': 'Signals beyond the horizon', 'author': 'Sally Ride', 'body': 'Every scan connects catalog data, orbital logic, and mission memory into one clean exploration workflow.'},
            {'title': 'A map for tomorrow', 'author': 'Carl Sagan', 'body': 'We move from raw observations to habitable candidates, preserving discoveries as a living archive of research.'}
        ],
        'kz': [
            {'title': '??????? ?????? ????????', 'author': '??? ?????????', 'body': 'ATLAS ?????? ????????? ???????, ???????????????? ???????? ???? ?? ??????? ????????? ????? ?????????.'},
            {'title': '?????????? ???? ?????????', 'author': '????? ????', 'body': '????? ???? ??????? ??????????, ????????? ???????? ???? ?????? ??????? ??? ?????? ???????.'},
            {'title': '??????? ???????? ?????', 'author': '???? ?????', 'body': '?????????? ?????????? ??????? ???????????? ???????, ??????? ???????? ??????? ?????????.'}
        ]
    }

    ui = {
        'en': {'eyebrow': 'Mission Dashboard', 'see_more': '[ SEE MORE ]', 'stats': ['Systems', 'Habitable', 'Worlds'], 'nav': ['Home', 'Products', 'About']},
        'kz': {'eyebrow': '?????? ????????', 'see_more': '[ ????????? ]', 'stats': ['???????', '???????? ??????', '???????'], 'nav': ['????? ???', '???????', '???????']}
    }[lang]

    hero_html = f"""
    <html>
    <head>
      <style>
        body {{ margin: 0; background: transparent; font-family: 'Manrope', sans-serif; }}
        .hero {{ position: relative; min-height: 640px; overflow: hidden; border-radius: 34px; background: url('{background_uri}') center center / cover no-repeat; box-shadow: 0 28px 80px rgba(0,0,0,0.34); }}
        .hero::before {{ content: ''; position: absolute; inset: 0; background: linear-gradient(90deg, rgba(16,14,14,0.38) 0%, rgba(16,14,14,0.18) 34%, rgba(16,14,14,0.03) 56%, rgba(16,14,14,0.0) 100%); }}
        .frame {{ position: relative; z-index: 2; padding: 28px 34px 28px 42px; height: 640px; box-sizing: border-box; color: #f6f0e8; }}
        .top {{ display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; }}
        .brand {{ font-size: 1.55rem; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; }}
        .mini-nav {{ display: inline-flex; gap: 34px; justify-self: center; font-size: 0.84rem; color: rgba(246,240,232,0.72); text-transform: uppercase; letter-spacing: 0.1em; }}
        .mini-nav span:first-child {{ color: #fffaf1; position: relative; }}
        .mini-nav span:first-child::after {{ content: ''; position: absolute; left: 50%; transform: translateX(-50%); bottom: -12px; width: 7px; height: 7px; border-radius: 50%; background: #d5a14f; }}
        .clock {{ justify-self: end; font-size: 0.9rem; font-weight: 700; color: rgba(246,240,232,0.92); }}
        .content {{ position: absolute; left: 42px; top: 118px; max-width: 43%; }}
        .eyebrow {{ font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.22em; color: rgba(246,240,232,0.82); margin-bottom: 26px; }}
        .ghost {{ position: absolute; left: -12px; top: -14px; font-size: 6.5rem; font-weight: 700; color: rgba(255,255,255,0.045); letter-spacing: -0.08em; pointer-events: none; }}
        .title {{ margin: 0; font-size: 4.3rem; line-height: 0.94; letter-spacing: -0.055em; max-width: 520px; }}
        .author {{ margin-top: 28px; font-family: 'Cormorant Garamond', serif; font-size: 2rem; color: #f5ece0; }}
        .body {{ margin-top: 12px; max-width: 490px; font-size: 1rem; line-height: 1.85; color: rgba(246,240,232,0.72); }}
        .dots {{ display: inline-flex; gap: 14px; margin-top: 24px; align-items: center; }}
        .dot {{ width: 7px; height: 7px; border-radius: 50%; background: rgba(255,255,255,0.32); cursor: pointer; transition: all 0.2s ease; }}
        .dot.active {{ background: #d5a14f; transform: scale(1.15); }}
        .cta {{ margin-top: 34px; display: inline-flex; align-items: center; gap: 12px; background: transparent; color: #fff7eb; border: none; font-weight: 800; font-size: 0.9rem; letter-spacing: 0.08em; cursor: pointer; }}
        .cta-ring {{ width: 30px; height: 30px; border-radius: 50%; border: 2px solid #d5a14f; box-shadow: inset 0 0 0 6px rgba(213,161,79,0.18); }}
        .stats {{ position: absolute; right: 270px; bottom: 44px; display: flex; gap: 56px; }}
        .stat {{ text-align: left; min-width: 82px; }}
        .stat-label {{ font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.14em; color: rgba(246,240,232,0.5); margin-bottom: 8px; }}
        .stat-value {{ font-size: 3rem; line-height: 1; color: #fff8ef; letter-spacing: -0.05em; }}
        .weather {{ position: absolute; left: 42px; bottom: 34px; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.18em; color: rgba(246,240,232,0.44); }}
        @media (max-width: 1100px) {{ .hero {{ min-height: 700px; background-position: 70% center; }} .frame {{ height: 700px; padding: 22px 24px; }} .top {{ grid-template-columns: 1fr; row-gap: 14px; }} .mini-nav, .clock {{ justify-self: start; }} .content {{ left: 24px; right: 24px; top: 132px; max-width: 66%; }} .title {{ font-size: 3.2rem; }} .ghost {{ font-size: 4.5rem; }} .stats {{ left: 24px; right: auto; bottom: 40px; gap: 26px; }} }}
        @media (max-width: 760px) {{ .hero {{ min-height: 760px; background-position: 76% center; }} .frame {{ height: 760px; }} .content {{ max-width: calc(100% - 48px); top: 146px; }} .title {{ font-size: 2.45rem; }} .author {{ font-size: 1.65rem; }} .body {{ font-size: 0.92rem; line-height: 1.7; }} .stats {{ display: grid; grid-template-columns: repeat(3, minmax(70px, 1fr)); gap: 14px; width: calc(100% - 48px); }} }}
      </style>
    </head>
    <body>
      <section class='hero'>
        <div class='frame'>
          <div class='top'>
            <div class='brand'>ATLAS</div>
            <div class='mini-nav'><span>{ui['nav'][0]}</span><span>{ui['nav'][1]}</span><span>{ui['nav'][2]}</span></div>
            <div class='clock'>{now_label}</div>
          </div>
          <div class='content'>
            <div class='eyebrow'>{ui['eyebrow']}</div>
            <div class='ghost' id='ghostTitle'></div>
            <h1 class='title' id='quoteTitle'></h1>
            <div class='author' id='quoteAuthor'></div>
            <div class='body' id='quoteBody'></div>
            <div class='dots' id='quoteDots'></div>
            <button class='cta' type='button'><span class='cta-ring'></span>{ui['see_more']}</button>
          </div>
          <div class='weather'>_ATLAS</div>
          <div class='stats'>
            <div class='stat'><div class='stat-label'>{ui['stats'][0]}</div><div class='stat-value'>{systems_count}</div></div>
            <div class='stat'><div class='stat-label'>{ui['stats'][1]}</div><div class='stat-value'>{habitable_count}</div></div>
            <div class='stat'><div class='stat-label'>{ui['stats'][2]}</div><div class='stat-value'>{worlds_count}</div></div>
          </div>
        </div>
      </section>
      <script>
        const quotes = {json.dumps(quotes[lang], ensure_ascii=False)};
        let active = 0;
        const titleNode = document.getElementById('quoteTitle');
        const authorNode = document.getElementById('quoteAuthor');
        const bodyNode = document.getElementById('quoteBody');
        const ghostNode = document.getElementById('ghostTitle');
        const dotsNode = document.getElementById('quoteDots');

        function drawDots() {{
          dotsNode.innerHTML = quotes.map((_, idx) => '<span class="dot ' + (idx === active ? 'active' : '') + '" data-index="' + idx + '"></span>').join('');
          dotsNode.querySelectorAll('.dot').forEach(dot => {{
            dot.addEventListener('click', () => {{
              active = Number(dot.dataset.index);
              renderQuote();
              restartTicker();
            }});
          }});
        }}

        function renderQuote() {{
          const item = quotes[active];
          titleNode.textContent = item.title;
          authorNode.textContent = item.author;
          bodyNode.textContent = item.body;
          ghostNode.textContent = item.title.split(' ')[0] || item.title;
          drawDots();
        }}

        let ticker = null;
        function restartTicker() {{
          if (ticker) clearInterval(ticker);
          ticker = setInterval(() => {{
            active = (active + 1) % quotes.length;
            renderQuote();
          }}, 5000);
        }}

        renderQuote();
        restartTicker();
      </script>
    </body>
    </html>
    """
    components.html(hero_html, height=650)


def render_internal_stage(page_key, lang):
    background_uri = asset_to_data_uri(r'C:\Users\user\advanced_app\background_none.png')
    meta = PAGE_META[page_key]
    stage_html = f"""
    <html>
    <head>
      <style>
        body {{ margin: 0; background: transparent; font-family: 'Manrope', sans-serif; }}
        .stage {{ position: relative; min-height: 290px; overflow: hidden; border-radius: 34px; background: url('{background_uri}') center center / cover no-repeat; box-shadow: 0 24px 60px rgba(0,0,0,0.28); }}
        .stage::before {{ content: ''; position: absolute; inset: 0; background: linear-gradient(90deg, rgba(15,13,13,0.42) 0%, rgba(15,13,13,0.18) 46%, rgba(15,13,13,0.08) 100%); }}
        .frame {{ position: relative; z-index: 1; padding: 28px 34px; color: #f5efe4; }}
        .brand {{ font-size: 1.4rem; font-weight: 800; letter-spacing: 0.16em; text-transform: uppercase; }}
        .eyebrow {{ margin-top: 54px; font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.24em; color: rgba(245,239,228,0.62); }}
        .title {{ margin: 14px 0 10px; font-size: 3rem; letter-spacing: -0.05em; max-width: 700px; }}
        .subtitle {{ max-width: 640px; color: rgba(245,239,228,0.74); line-height: 1.7; font-size: 0.98rem; }}
        @media (max-width: 760px) {{ .stage {{ min-height: 320px; }} .frame {{ padding: 22px 20px; }} .eyebrow {{ margin-top: 58px; }} .title {{ font-size: 2.2rem; }} }}
      </style>
    </head>
    <body>
      <section class='stage'>
        <div class='frame'>
          <div class='brand'>ATLAS</div>
          <div class='eyebrow'>{meta['eyebrow'][lang]}</div>
          <div class='title'>{meta['title'][lang]}</div>
          <div class='subtitle'>{meta['subtitle'][lang]}</div>
        </div>
      </section>
    </body>
    </html>
    """
    components.html(stage_html, height=310)


def render_achievements_page(lang):
    render_internal_stage('achievements', lang)
    unlocked = set(st.session_state.get('achievements_unlocked', []))
    total = len(ACHIEVEMENTS)
    solved = len(unlocked)
    progress = solved / total if total else 0
    label = {'en': 'Mission completion', 'kz': '?????? ?????????'}[lang]
    st.markdown(f"<div class='atlas-stage-caption'>{label}</div>", unsafe_allow_html=True)
    st.progress(progress)
    st.caption(f'{solved}/{total}')

    keys = list(ACHIEVEMENTS.keys())
    cols = st.columns(3)
    for idx, ach_id in enumerate(keys):
        ach = ACHIEVEMENTS[ach_id]
        active = ach_id in unlocked
        status = {'en': 'Unlocked', 'kz': '??????'}[lang] if active else {'en': 'In progress', 'kz': '??????????'}[lang]
        border = '#d5a14f' if active else 'rgba(255,255,255,0.12)'
        glow = 'rgba(213,161,79,0.18)' if active else 'rgba(255,255,255,0.04)'
        with cols[idx % 3]:
            st.markdown(f"""
                <div style='background: rgba(31,29,28,0.92); border: 1px solid {border}; border-radius: 24px; padding: 20px; min-height: 200px; box-shadow: 0 16px 44px {glow};'>
                    <div style='font-size: 2rem; margin-bottom: 12px;'>{ach.get('icon', '??')}</div>
                    <div style='font-size: 1.08rem; font-weight: 800; color: #f6efe5; margin-bottom: 8px;'>{ach.get(lang, ach.get('en', ach_id))}</div>
                    <div style='font-size: 0.9rem; color: rgba(246,239,229,0.72); line-height: 1.65;'>{ach.get(f'desc_{lang}', ach.get('desc_en', ''))}</div>
                    <div style='margin-top: 16px; display: inline-block; padding: 6px 10px; border-radius: 999px; border: 1px solid {border}; color: #ece1cf; font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.08em;'>{status}</div>
                </div>
            """, unsafe_allow_html=True)

current_page, lang = get_route_state()
render_top_nav(current_page, lang)

save_to_local_storage()

# ???????????????????????????????????????????????????????????????????????????????
# TAB 0: MISSIONS
# ═══════════════════════════════════════════════════════════════════════════════
if current_page == 'missions':
    render_mission_hero(lang)
    st.markdown(
        f"<div class='atlas-stage-caption'>{'Mission Control' if lang == 'en' else '???????? ???????'}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"### {'Expedition Console' if lang == 'en' else '?????????? ???????'}"
    )
    st.caption(
        'Launch quick scans, manage catalog sweeps, and review the latest archive signals.'
        if lang == 'en'
        else '?????? ??????????? ???? ?????, ???????????? ????????, ????? ????? ??????????? ???????.'
    )

    quick_title = 'Priority targets' if lang == 'en' else '????? ????????'
    st.markdown(f"<div class='atlas-stage-caption'>{quick_title}</div>", unsafe_allow_html=True)
    quick_cols = st.columns(4)
    quick_stars = ['TRAPPIST-1', 'TOI-700', 'Kepler-442', 'Proxima']
    for i, star_name in enumerate(quick_stars):
        scanned = is_star_scanned(star_name)
        label = f"? {star_name}" if scanned else f"? {star_name}"
        with quick_cols[i]:
            if st.button(label, key=f"hero_q_{star_name}", use_container_width=True, disabled=scanned):
                result = fetch_nasa_data(star_name)
                if result:
                    star = {k: result[0].get(k) for k in ['st_teff', 'st_rad', 'st_lum', 'st_mass', 'st_spectype', 'st_age', 'st_met']}
                    planets = [process_planet_data(p, star) for p in result]
                    hostname = result[0].get('hostname', star_name)
                    save_system(hostname, star, planets)
                    mark_star_scanned(star_name)
                    load_system(hostname)
                    st.session_state['total_planets_found'] = st.session_state.get('total_planets_found', 0) + len(planets)
                    save_to_local_storage()
                    st.rerun()

    st.markdown("<div class='atlas-divider'></div>", unsafe_allow_html=True)
    
    # Three column layout: Controls | Mission | News
    col1, col2, col3 = st.columns([1.2, 1.5, 1])
    
    with col1:
        # Catalog selection
        lang = st.session_state.lang
        catalog_options = {k: v['name'][lang] for k, v in CATALOGS.items()}
        selected_catalog = st.selectbox(
            t('select_catalog'),
            options=list(catalog_options.keys()),
            format_func=lambda x: catalog_options[x],
            index=list(catalog_options.keys()).index(st.session_state.selected_catalog)
        )
        st.session_state.selected_catalog = selected_catalog
        
        # Track catalog exploration for achievement
        if 'catalogs_explored' not in st.session_state:
            st.session_state.catalogs_explored = set()
        st.session_state.catalogs_explored.add(selected_catalog)
        
        # Available stars info
        all_stars = CATALOGS[selected_catalog]['stars']
        unscanned = get_unscanned_stars(selected_catalog, skip_scanned=True)
        stars_available_text = 'stars available' if lang == 'en' else '?????? ??????????'
        st.info(f"{len(unscanned)}/{len(all_stars)} {stars_available_text}")
        
        # Options
        skip_scanned = st.checkbox(t('skip_scanned'), value=True)
        max_targets = len(unscanned) if skip_scanned else len(all_stars)
        target_count = st.slider(t('targets'), 1, max(1, min(10, max_targets)), min(5, max_targets))
        
        # Clear button
        if st.button(t('clear_scanned'), use_container_width=True):
            st.session_state.scanned_stars = set()
            st.rerun()
    
    with col2:
        # Mission button
        can_start = len(unscanned) > 0 if skip_scanned else True
        start_mission = st.button(
            ('Start Mission' if lang == 'en' else '???????? ??????'),
            use_container_width=True,
            type="primary",
            disabled=not can_start
        )
        
        # Progress and log placeholders
        progress_area = st.empty()
        log_area = st.empty()
        results_area = st.container()
    
    with col3:
        # NEWS PANEL (like news.jpg reference)
        news_header = {'en': 'Latest News', 'kz': '????? ??????????'}
        st.markdown(f"#### {news_header.get(lang, news_header['en'])}")
        
        try:
            news = fetch_nasa_news()
            for item in news[:5]:
                # News card with tag
                tag = random.choice(['NASA', 'JWST', 'TESS', 'Kepler', 'Exoplanet'])
                st.markdown(f"""
                <div class='news-card'>
                    <span class='news-tag'>{tag}</span>
                    <div style='margin-top: 10px; font-size: 0.9rem; font-weight: 500; line-height: 1.4;'>
                        {item['title']}
                    </div>
                    <div style='margin-top: 8px; font-size: 0.75rem; opacity: 0.5;'>
                        {item.get('date', 'Today')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        except:
            st.caption("News unavailable")
    
    # Execute mission
    if start_mission:
        stars_to_scan = unscanned[:target_count] if skip_scanned else all_stars[:target_count]
        
        if stars_to_scan:
            results = []
            log_lines = []
            
            with progress_area.container():
                progress_bar = st.progress(0)
                status_text = st.empty()
            
            # Phase 1: Initialize
            status_text.info('Initializing ATLAS systems...')
            log_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] Initializing...")
            log_area.code('\n'.join(log_lines), language=None)
            time.sleep(0.4)
            
            log_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] Systems online")
            log_area.code('\n'.join(log_lines), language=None)
            progress_bar.progress(0.1)
            time.sleep(0.3)
            
            # Phase 2: Connect
            status_text.info('Connecting to NASA Exoplanet Archive...')
            log_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] Connecting to NASA API...")
            log_area.code('\n'.join(log_lines), language=None)
            time.sleep(0.4)
            
            log_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] Connection established")
            log_area.code('\n'.join(log_lines), language=None)
            progress_bar.progress(0.15)
            time.sleep(0.3)
            
            # Phase 3: Scan stars
            for i, star_name in enumerate(stars_to_scan):
                progress = 0.15 + (i + 1) / len(stars_to_scan) * 0.75
                
                status_text.info(f"🔍 Scanning {star_name}...")
                log_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Scanning {star_name}...")
                log_area.code('\n'.join(log_lines), language=None)
                time.sleep(0.3)
                
                data = fetch_nasa_data(star_name)
                
                if data:
                    star = {k: data[0].get(k) for k in ['st_teff', 'st_rad', 'st_lum', 'st_mass', 'st_spectype', 'st_age', 'st_met']}
                    planets = [process_planet_data(p, star) for p in data]
                    hostname = data[0].get('hostname', star_name)
                    
                    save_system(hostname, star, planets)
                    mark_star_scanned(star_name)
                    
                    # Update total planets count
                    st.session_state['total_planets_found'] = st.session_state.get('total_planets_found', 0) + len(planets)
                    
                    log_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {hostname}: {len(planets)} planets found")
                    log_area.code('\n'.join(log_lines), language=None)
                    
                    for p in planets:
                        # Check achievements for each planet
                        if p.get('esi', 0) > 0.8:
                            check_achievement('earth_twin')
                        if p.get('hab_score', 0) >= 85:
                            check_achievement('rare_find')
                        if p.get('in_hz', False):
                            # Count HZ planets
                            hz_count = sum(1 for sys in st.session_state.saved_systems.values() 
                                          for pl in sys.get('planets', []) if pl.get('in_hz', False))
                            if hz_count >= 5:
                                check_achievement('life_zone')
                        
                        if p['hab_score'] >= 40:
                            results.append({'planet': p, 'star': star, 'host': hostname})
                            log_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}]    ⭐ {p['name']} — Score {p['hab_score']}")
                            log_area.code('\n'.join(log_lines), language=None)
                else:
                    log_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ {star_name}: No data")
                    log_area.code('\n'.join(log_lines), language=None)
                
                progress_bar.progress(progress)
                time.sleep(0.2)
            
            # Phase 4: Complete
            progress_bar.progress(1.0)
            status_text.success(f"{t('mission_complete')} {len(results)} {t('candidates_found')}")
            
            log_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] ════════════════════════════")
            log_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ MISSION COMPLETE")
            log_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 Systems: {len(stars_to_scan)} | Candidates: {len(results)}")
            log_area.code('\n'.join(log_lines), language=None)
            
            st.session_state.atlas_results = results
            
            # Save progress to localStorage
            save_to_local_storage()
            
            # Display results
            if results:
                with results_area:
                    st.markdown(f"### 🏆 {t('slide_top')} Candidates")
                    sorted_results = sorted(results, key=lambda x: x['planet']['hab_score'], reverse=True)[:6]
                    
                    cols = st.columns(min(len(sorted_results), 3))
                    for i, r in enumerate(sorted_results):
                        p = r['planet']
                        with cols[i % 3]:
                            score_color = '#ece1cf' if p['hab_score'] >= 70 else '#d5a14f' if p['hab_score'] >= 50 else '#ffbb00'
                            st.markdown(f"""
                            <div style='background: rgba(34,31,30,0.70); border: 2px solid {score_color}; 
                                        border-radius: 16px; padding: 20px; text-align: center; margin: 5px 0;'>
                                <div style='font-size: 2.5rem;'>{p['emoji']}</div>
                                <h4 style='margin: 10px 0; color: white;'>{p['name']}</h4>
                                <div style='font-size: 2.2rem; color: {score_color}; font-weight: bold;'>{p['hab_score']}</div>
                                <div style='opacity: 0.6;'>/100</div>
                                <div style='margin-top: 12px; font-size: 0.9rem; opacity: 0.8;'>
                                    ESI: {p['esi']} • R: {p['radius']:.2f} R⊕<br>
                                    {p['temp']:.0f}K • {'✅ HZ' if p['in_hz'] else '❌ HZ'}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Load best button
                    if st.button(t('load_best'), use_container_width=True):
                        best = sorted_results[0]
                        load_system(best['host'])
                        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: SYSTEM VIEW - ATLAS JARVIS MODE
# ═══════════════════════════════════════════════════════════════════════════════
if current_page == 'system':
    render_internal_stage('system', lang)
    if 'planets' in st.session_state and st.session_state['planets']:
        planets = st.session_state['planets']
        star = st.session_state.get('star', {})
        sel_idx = st.session_state.get('selected_idx', 0)
        
        hostname = planets[0].get('hostname', '?')
        best = max(planets, key=lambda x: x['hab_score'])
        lang = st.session_state.get('lang', 'ru')
        is_dark = st.session_state.get('theme', 'dark') == 'dark'
        
        # Theme colors
        if is_dark:
            card_bg = 'rgba(31,29,28,0.88)'
            card_border = 'rgba(0,212,255,0.3)'
            text_main = '#ffffff'
            text_dim = 'rgba(255,255,255,0.7)'
            accent = '#d5a14f'
            accent2 = '#ece1cf'
        else:
            card_bg = 'rgba(255,255,255,0.95)'
            card_border = 'rgba(2,132,199,0.3)'
            text_main = '#0f172a'
            text_dim = '#64748b'
            accent = '#d5a14f'
            accent2 = '#ece1cf'
        
        # ═══════════════════════════════════════════════════════════════════════
        # ATLAS HEADER - JARVIS STYLE
        # ═══════════════════════════════════════════════════════════════════════
        atlas_greeting = {
            'ru': f"Система **{hostname}** загружена. Обнаружено **{len(planets)}** планет. Провожу глубокий анализ...",
            'en': f"System **{hostname}** loaded. **{len(planets)}** planets detected. Running deep analysis...",
            'kz': f"**{hostname}** жүйесі жүктелді. **{len(planets)}** планета табылды. Терең талдау жүргізілуде..."
        }
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {card_bg}, rgba(213,161,79,0.10));
                    border: 2px solid {accent}; border-radius: 20px; padding: 25px; margin-bottom: 20px;
                    box-shadow: 0 0 30px rgba(0,212,255,0.2);'>
            <div style='display: flex; align-items: center; gap: 15px;'>
                <div style='font-size: 3rem;'>🛰️</div>
                <div>
                    <h2 style='margin: 0; color: {accent}; font-family: Orbitron, monospace;'>ATLAS AI</h2>
                    <p style='margin: 5px 0 0 0; color: {text_dim}; font-size: 1.1rem;'>{atlas_greeting[lang]}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # ═══════════════════════════════════════════════════════════════════════
        # STAR ANALYSIS CARD
        # ═══════════════════════════════════════════════════════════════════════
        star_section_title = {'ru': 'Центральная звезда', 'en': 'Central Star', 'kz': 'Орталық жұлдыз'}[lang]
        st.markdown(f"### ⭐ {star_section_title}")
        
        # Get star color by temperature
        st_teff = star.get('st_teff', 5778)
        if st_teff > 7500:
            star_color = '#a0c4ff'
            star_class = 'A/F'
            star_desc = {'ru': 'Горячая белая звезда', 'en': 'Hot white star', 'kz': 'Ыстық ақ жұлдыз'}[lang]
        elif st_teff > 6000:
            star_color = '#ffffa0'
            star_class = 'F/G'
            star_desc = {'ru': 'Жёлтый карлик (как Солнце)', 'en': 'Yellow dwarf (Sun-like)', 'kz': 'Сары ергежейлі (Күнге ұқсас)'}[lang]
        elif st_teff > 5000:
            star_color = '#ffcc66'
            star_class = 'G/K'
            star_desc = {'ru': 'Оранжевый карлик — оптимален для жизни!', 'en': 'Orange dwarf — optimal for life!', 'kz': 'Қызғылт сары ергежейлі — өмір үшін оңтайлы!'}[lang]
        elif st_teff > 3500:
            star_color = '#ff8866'
            star_class = 'K/M'
            star_desc = {'ru': 'Красный карлик — риск вспышек', 'en': 'Red dwarf — flare risk', 'kz': 'Қызыл ергежейлі — жарқылдар қаупі'}[lang]
        else:
            star_color = '#ff6644'
            star_class = 'M'
            star_desc = {'ru': 'Ультрахолодный карлик', 'en': 'Ultracool dwarf', 'kz': 'Ультрасуық ергежейлі'}[lang]
        
        st_rad = star.get('st_rad', 1.0) or 1.0
        st_mass = star.get('st_mass', 1.0) or 1.0
        st_lum = star.get('st_lum')
        if not st_lum and st_teff and st_rad:
            st_lum = (st_rad ** 2) * ((st_teff / 5778) ** 4)
        st_age = star.get('st_age')
        st_met = star.get('st_met')
        
        # Localized labels
        lbl_params = {'ru': 'Параметры звезды', 'en': 'Star Parameters', 'kz': 'Жұлдыз параметрлері'}[lang]
        lbl_temp = {'ru': 'Температура', 'en': 'Temperature', 'kz': 'Температура'}[lang]
        lbl_rad = {'ru': 'Радиус', 'en': 'Radius', 'kz': 'Радиус'}[lang]
        lbl_mass = {'ru': 'Масса', 'en': 'Mass', 'kz': 'Масса'}[lang]
        lbl_lum = {'ru': 'Светимость', 'en': 'Luminosity', 'kz': 'Жарықтылық'}[lang]
        lbl_age = {'ru': 'Возраст', 'en': 'Age', 'kz': 'Жасы'}[lang]
        lbl_met = {'ru': 'Металличность', 'en': 'Metallicity', 'kz': 'Металдылық'}[lang]
        lum_compare = '🔆 Ярче Солнца' if st_lum and st_lum > 1 else '🔅 Тусклее Солнца' if st_lum else ''
        
        star_cols = st.columns([1, 2])
        
        with star_cols[0]:
            # Star visualization
            st.markdown(f"""
            <div style='background: radial-gradient(circle, {star_color} 0%, rgba(0,0,0,0) 70%);
                        width: 200px; height: 200px; border-radius: 50%; margin: 20px auto;
                        box-shadow: 0 0 60px {star_color}, 0 0 100px {star_color}40;
                        display: flex; align-items: center; justify-content: center;'>
                <span style='font-size: 3rem;'>⭐</span>
            </div>
            <div style='text-align: center; margin-top: 10px;'>
                <div style='font-size: 1.5rem; font-weight: bold; color: {star_color};'>{star.get('st_spectype', star_class)}</div>
                <div style='color: {text_dim}; font-size: 0.9rem;'>{star_desc}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with star_cols[1]:
            # Star parameters
            st.markdown(f"""
            <div style='background: {card_bg}; border: 1px solid {card_border}; border-radius: 16px; padding: 20px;'>
                <h4 style='color: {accent}; margin-bottom: 15px;'>📊 {lbl_params}</h4>
                <table style='width: 100%; color: {text_main};'>
                    <tr>
                        <td style='padding: 8px 0; color: {text_dim};'>🌡️ {lbl_temp}</td>
                        <td style='padding: 8px 0; font-weight: bold; text-align: right;'>{st_teff:,.0f} K</td>
                        <td style='padding: 8px 0; color: {text_dim}; font-size: 0.85rem;'>(☀️ 5778K)</td>
                    </tr>
                    <tr>
                        <td style='padding: 8px 0; color: {text_dim};'>📏 {lbl_rad}</td>
                        <td style='padding: 8px 0; font-weight: bold; text-align: right;'>{st_rad:.3f} R☉</td>
                        <td style='padding: 8px 0; color: {text_dim}; font-size: 0.85rem;'>({st_rad * 696340:.0f} km)</td>
                    </tr>
                    <tr>
                        <td style='padding: 8px 0; color: {text_dim};'>⚖️ {lbl_mass}</td>
                        <td style='padding: 8px 0; font-weight: bold; text-align: right;'>{st_mass:.3f} M☉</td>
                        <td style='padding: 8px 0; color: {text_dim}; font-size: 0.85rem;'>({st_mass * 1.989e30:.2e} kg)</td>
                    </tr>
                    <tr>
                        <td style='padding: 8px 0; color: {text_dim};'>💡 {lbl_lum}</td>
                        <td style='padding: 8px 0; font-weight: bold; text-align: right;'>{st_lum:.4f if st_lum else '?'} L☉</td>
                        <td style='padding: 8px 0; color: {text_dim}; font-size: 0.85rem;'>{lum_compare}</td>
                    </tr>
                    <tr>
                        <td style='padding: 8px 0; color: {text_dim};'>🕐 {lbl_age}</td>
                        <td style='padding: 8px 0; font-weight: bold; text-align: right;'>{f'{st_age:.2f} Gyr' if st_age else '?'}</td>
                        <td style='padding: 8px 0; color: {text_dim}; font-size: 0.85rem;'>(☀️ 4.6 Gyr)</td>
                    </tr>
                    <tr>
                        <td style='padding: 8px 0; color: {text_dim};'>🧪 {lbl_met}</td>
                        <td style='padding: 8px 0; font-weight: bold; text-align: right;'>{f'{st_met:+.2f}' if st_met else '?'} [Fe/H]</td>
                        <td style='padding: 8px 0; color: {text_dim}; font-size: 0.85rem;'>(☀️ 0.00)</td>
                    </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            
            # ATLAS comment on star
            if 4500 < st_teff < 6500:
                star_comment = {'ru': '💬 **ATLAS:** Звезда класса G/K — идеальный хозяин для обитаемых планет. Стабильное излучение, долгий срок жизни.', 
                               'en': '💬 **ATLAS:** G/K class star — ideal host for habitable planets. Stable radiation, long lifespan.',
                               'kz': '💬 **ATLAS:** G/K класты жұлдыз — мекендеуге жарамды планеталар үшін тамаша.'}[lang]
            elif st_teff < 4000:
                star_comment = {'ru': '💬 **ATLAS:** M-карлик — планеты близко к звезде, риск приливного захвата и вспышек.',
                               'en': '💬 **ATLAS:** M-dwarf — planets close to star, tidal locking and flare risks.',
                               'kz': '💬 **ATLAS:** M-ергежейлі — планеталар жақын, қауіптер бар.'}[lang]
            else:
                star_comment = {'ru': '💬 **ATLAS:** Горячая звезда — короткий срок жизни, зона обитаемости далеко.',
                               'en': '💬 **ATLAS:** Hot star — short lifespan, habitable zone far away.',
                               'kz': '💬 **ATLAS:** Ыстық жұлдыз — қысқа өмір.'}[lang]
            st.info(star_comment)
        
        st.markdown("---")
        
        # ═══════════════════════════════════════════════════════════════════════
        # 3D SYSTEM VISUALIZATION
        # ═══════════════════════════════════════════════════════════════════════
        st.plotly_chart(create_system_3d(planets, star, sel_idx), use_container_width=True)
        
        # ═══════════════════════════════════════════════════════════════════════
        # PLANET SELECTOR
        # ═══════════════════════════════════════════════════════════════════════
        st.markdown(f"### 🪐 {t('select_planet')}")
        cols = st.columns(min(len(planets), 5))
        
        for i, p in enumerate(planets):
            with cols[i % 5]:
                is_selected = (i == sel_idx)
                score_color = '#ece1cf' if p['hab_score'] >= 70 else '#d5a14f' if p['hab_score'] >= 50 else '#ffbb00' if p['hab_score'] >= 30 else '#ff6666'
                
                if st.button(f"{p['emoji']} {p['name']}", key=f"pl_{i}", use_container_width=True,
                            type="primary" if is_selected else "secondary"):
                    st.session_state['selected_idx'] = i
                    st.rerun()
                
                st.markdown(f"""
                <div style='text-align: center; font-size: 0.85rem; color: {text_main};'>
                    <span style='color: {score_color}; font-weight: bold;'>{p['hab_score']}</span>/100<br>
                    R: {p['radius']:.2f} • {p['temp']:.0f}K
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ═══════════════════════════════════════════════════════════════════════
        # ATLAS ANALYSIS BANNER
        # ═══════════════════════════════════════════════════════════════════════
        sel_p = planets[sel_idx]
        
        analysis_text = {
            'ru': f"Анализирую планету **{sel_p['name']}**. Обрабатываю данные NASA, применяю ML модель...",
            'en': f"Analyzing planet **{sel_p['name']}**. Processing NASA data, applying ML model...",
            'kz': f"**{sel_p['name']}** планетасын талдаймын. NASA деректерін өңдеу, ML модель қолдану..."
        }
        
        st.markdown(f"""
        <div style='background: linear-gradient(90deg, rgba(236,225,207,0.12), rgba(213,161,79,0.12));
                    border-left: 4px solid {accent2}; border-radius: 8px; padding: 15px; margin: 15px 0;'>
            <div style='display: flex; align-items: center; gap: 10px;'>
                <span style='font-size: 1.5rem;'>🧠</span>
                <div>
                    <strong style='color: {accent2};'>ATLAS Analysis Active</strong><br>
                    <span style='color: {text_dim};'>{analysis_text[lang]}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # ═══════════════════════════════════════════════════════════════════════
        # DETAILED PLANET ANALYSIS - EXPANDED
        # ═══════════════════════════════════════════════════════════════════════
        st.markdown(f"### {t('detailed_analysis')}: {sel_p['emoji']} {sel_p['name']}")
        
        # Type card with ATLAS comment
        type_comment = {
            'ru': {
                'Earth-like': '🌱 Идеальный кандидат для колонизации!',
                'Super-Earth': '💎 Возможен толстый слой воды или льда',
                'Mini-Neptune': '🌊 Вероятен водородный океан',
                'Gas Giant': '🌀 Газовый гигант — жизнь маловероятна',
                'Ice Giant': '❄️ Ледяной мир — экстремофилы возможны'
            },
            'en': {
                'Earth-like': '🌱 Ideal colonization candidate!',
                'Super-Earth': '💎 Possible thick water or ice layer',
                'Mini-Neptune': '🌊 Likely hydrogen ocean',
                'Gas Giant': '🌀 Gas giant — life unlikely',
                'Ice Giant': '❄️ Ice world — extremophiles possible'
            }
        }
        default_comment = {'ru': '📊 Анализ завершён', 'en': '📊 Analysis complete', 'kz': '📊 Талдау аяқталды'}
        atlas_type_comment = type_comment.get(lang, type_comment['en']).get(sel_p['type'], default_comment[lang])
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, rgba(0,100,180,0.15), rgba(120,0,180,0.1));
                    border: 2px solid {card_border}; border-radius: 16px; padding: 20px; margin: 15px 0;'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <h3 style='margin: 0 0 10px 0; color: {text_main};'>{sel_p['emoji']} {sel_p['type']}</h3>
                    <p style='margin: 0; color: {text_dim};'>{sel_p['type_desc']}</p>
                </div>
                <div style='text-align: right;'>
                    <div style='font-size: 2.5rem; font-weight: bold; color: {accent};'>{sel_p['hab_score']}</div>
                    <div style='color: {text_dim};'>/100 Score</div>
                </div>
            </div>
            <div style='margin-top: 15px; padding-top: 15px; border-top: 1px solid {card_border}; color: {accent2};'>
                💬 <strong>ATLAS:</strong> {atlas_type_comment}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # ═══════════════════════════════════════════════════════════════════════
        # PARAMETERS - 5 COLUMNS NOW
        # ═══════════════════════════════════════════════════════════════════════
        c1, c2, c3, c4, c5 = st.columns(5)
        
        with c1:
            st.markdown(f"#### {t('physical')}")
            st.metric(t('radius'), f"{sel_p['radius']:.3f} R⊕")
            st.metric(t('mass'), f"{sel_p['mass']:.2f} M⊕" if sel_p['mass'] else t('unknown'))
            st.metric(t('density'), f"{sel_p['density']:.2f} ρ⊕" if sel_p['density'] else t('unknown'))
            st.metric(t('gravity'), f"{sel_p['gravity']:.2f} g" if sel_p['gravity'] else t('unknown'))
            st.metric(t('escape_v'), f"{sel_p['escape_v']:.1f} km/s" if sel_p['escape_v'] else t('unknown'))
            st.metric(t('pressure'), f"{sel_p['pressure']:.1f} atm" if sel_p['pressure'] else t('unknown'))
        
        with c2:
            st.markdown(f"#### {t('orbital')}")
            st.metric(t('orbit'), f"{sel_p['orbit_au']:.4f} AU" if sel_p['orbit_au'] else t('unknown'))
            st.metric(t('period'), f"{sel_p['period']:.2f} d" if sel_p['period'] else t('unknown'))
            st.metric(t('year_len'), f"{sel_p['year_len']:.3f} yr" if sel_p['year_len'] else t('unknown'))
            day_str = f"{sel_p['day_len']:.1f} h" if sel_p['day_len'] else "Tidal lock?"
            st.metric("Day Length", day_str)
            st.metric(t('distance'), f"{sel_p['distance']:.1f} ly" if sel_p['distance'] else t('unknown'))
        
        with c3:
            lbl_climate = {'ru': 'Климат', 'en': 'Climate', 'kz': 'Климат'}[lang]
            st.markdown(f"#### 🌡️ {lbl_climate}")
            st.metric(t('temp'), f"{sel_p['temp']:.0f} K")
            temp_c = sel_p['temp'] - 273.15
            st.metric("°C", f"{temp_c:.0f}°C")
            
            # Climate zone
            if temp_c > 50:
                climate = {'ru': '🔥 Экстремально горячо', 'en': '🔥 Extremely hot', 'kz': '🔥 Өте ыстық'}
            elif temp_c > 30:
                climate = {'ru': '☀️ Жарко', 'en': '☀️ Hot', 'kz': '☀️ Ыстық'}
            elif temp_c > 10:
                climate = {'ru': '🌤️ Умеренно', 'en': '🌤️ Temperate', 'kz': '🌤️ Қалыпты'}
            elif temp_c > -10:
                climate = {'ru': '❄️ Прохладно', 'en': '❄️ Cool', 'kz': '❄️ Салқын'}
            elif temp_c > -50:
                climate = {'ru': '🥶 Холодно', 'en': '🥶 Cold', 'kz': '🥶 Суық'}
            else:
                climate = {'ru': '🧊 Криогенно', 'en': '🧊 Cryogenic', 'kz': '🧊 Криогенді'}
            st.info(climate[lang])
            st.metric(t('temp_source'), sel_p['temp_source'])
        
        with c4:
            st.markdown(f"#### {t('habitability')}")
            st.metric(t('esi'), f"{sel_p['esi']}")
            st.metric(t('in_hz'), t('yes') if sel_p['in_hz'] else t('no'))
            st.metric(t('mag_field'), sel_p['mag_field'])
            st.metric(t('moons'), sel_p['moon_desc'])
            hz_range = f"{sel_p['hz_inner']:.2f}-{sel_p['hz_outer']:.2f}"
            st.metric("HZ Range", f"{hz_range} AU")
        
        with c5:
            st.markdown("#### 🧠 AI Prediction")
            if sel_p.get('ml_probability') is not None:
                prob = sel_p['ml_probability']
                prob_pct = prob * 100
                prob_color = '#ece1cf' if prob >= 0.7 else '#d5a14f' if prob >= 0.5 else '#ffbb00' if prob >= 0.3 else '#ff6666'
                
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, rgba(213,161,79,0.12), rgba(236,225,207,0.08));
                            border: 2px solid {prob_color}; border-radius: 12px; padding: 15px; text-align: center;'>
                    <div style='font-size: 2.5rem; font-weight: bold; color: {prob_color};'>{prob_pct:.0f}%</div>
                    <div style='font-size: 0.9rem; color: {text_dim};'>Habitability</div>
                </div>
                """, unsafe_allow_html=True)
                st.caption(sel_p.get('ml_confidence', ''))
            else:
                st.info("Model not loaded")
            
            # ATLAS verdict
            if sel_p['hab_score'] >= 70:
                verdict = {'ru': '⭐ ВЫСОКИЙ ПРИОРИТЕТ', 'en': '⭐ HIGH PRIORITY', 'kz': '⭐ ЖОҒАРЫ БАСЫМДЫҚ'}
            elif sel_p['hab_score'] >= 50:
                verdict = {'ru': '📊 УМЕРЕННЫЙ ИНТЕРЕС', 'en': '📊 MODERATE INTEREST', 'kz': '📊 ОРТАША ҚЫЗЫҒУШЫЛЫҚ'}
            else:
                verdict = {'ru': '📉 НИЗКИЙ ПОТЕНЦИАЛ', 'en': '📉 LOW POTENTIAL', 'kz': '📉 ТӨМЕН ӘЛЕУЕТ'}
            st.success(verdict[lang])
        
        # ═══════════════════════════════════════════════════════════════════════
        # ATMOSPHERE & HAZARDS & BIOSIGNATURES
        # ═══════════════════════════════════════════════════════════════════════
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown(f"#### 🌫️ {t('atmosphere')}")
            st.info(f"**Type:** {sel_p['atmo_type']}")
            if sel_p['atmo_comp']:
                for comp in sel_p['atmo_comp']:
                    st.markdown(f"• {comp}")
        
        with c2:
            st.markdown(f"#### ⚠️ {t('hazards')}")
            hazards = predict_hazards(sel_p['temp'], sel_p['gravity'], sel_p['radius'],
                                      sel_p['orbit_au'], star.get('st_teff'), sel_p['period'])
            for h_name, h_desc in hazards[:3]:  # Top 3 hazards
                if any(x in h_name for x in ['LETHAL', 'CRUSHING', 'CRYOGENIC', 'СМЕРТЕЛЬНЫЙ', 'ДАВЯЩАЯ', 'КРИОГЕННЫЙ']):
                    st.error(f"**{h_name}**")
                elif '✅' in h_name:
                    st.success(f"**{h_name}**")
                else:
                    st.warning(f"**{h_name}**")
        
        with c3:
            st.markdown(f"#### 🧬 {t('biosignatures')}")
            life_type, life_score, life_factors = predict_life_potential(
                sel_p['temp'], sel_p['radius'], sel_p['in_hz'], sel_p['esi'], sel_p['atmo_type'])
            st.info(life_type)
            st.progress(life_score / 100)
        
        # ═══════════════════════════════════════════════════════════════════════
        # ATLAS FINAL REPORT
        # ═══════════════════════════════════════════════════════════════════════
        st.markdown("---")
        
        report_title = {'ru': '📋 Отчёт ATLAS', 'en': '📋 ATLAS Report', 'kz': '📋 ATLAS есебі'}
        st.markdown(f"### {report_title[lang]}")
        
        # Generate dynamic report
        if sel_p['hab_score'] >= 70 and sel_p['in_hz']:
            report = {
                'ru': f"""
**Заключение:** Планета **{sel_p['name']}** демонстрирует **высокий потенциал обитаемости**.

🔬 **Ключевые факторы:**
• ESI {sel_p['esi']} — близко к земным условиям
• Температура {sel_p['temp']:.0f}K ({sel_p['temp']-273:.0f}°C) — возможна жидкая вода
• Находится в зоне обитаемости звезды
• Радиус {sel_p['radius']:.2f} R⊕ — вероятна твёрдая поверхность

📡 **Рекомендация:** Приоритетная цель для спектроскопического анализа атмосферы. Поиск биомаркеров: O₂, CH₄, H₂O.

*— Автономный анализ выполнен системой ATLAS v21*
                """,
                'en': f"""
**Conclusion:** Planet **{sel_p['name']}** demonstrates **high habitability potential**.

🔬 **Key factors:**
• ESI {sel_p['esi']} — close to Earth conditions
• Temperature {sel_p['temp']:.0f}K ({sel_p['temp']-273:.0f}°C) — liquid water possible
• Located in stellar habitable zone
• Radius {sel_p['radius']:.2f} R⊕ — likely solid surface

📡 **Recommendation:** Priority target for atmospheric spectroscopy. Search for biomarkers: O₂, CH₄, H₂O.

*— Autonomous analysis by ATLAS v21*
                """
            }
        elif sel_p['hab_score'] >= 50:
            report = {
                'ru': f"""
**Заключение:** Планета **{sel_p['name']}** представляет **умеренный интерес**.

🔬 **Анализ:** Некоторые параметры благоприятны, но есть ограничения. {'Температура вне оптимального диапазона.' if not (250 <= sel_p['temp'] <= 310) else ''} {'Находится вне классической зоны обитаемости.' if not sel_p['in_hz'] else ''}

📡 **Рекомендация:** Дополнительный анализ состава атмосферы.

*— ATLAS v21*
                """,
                'en': f"""
**Conclusion:** Planet **{sel_p['name']}** is of **moderate interest**.

🔬 **Analysis:** Some parameters favorable, but limitations exist. {'Temperature outside optimal range.' if not (250 <= sel_p['temp'] <= 310) else ''} {'Outside classical habitable zone.' if not sel_p['in_hz'] else ''}

📡 **Recommendation:** Additional atmospheric analysis needed.

*— ATLAS v21*
                """
            }
        else:
            report = {
                'ru': f"""
**Заключение:** Планета **{sel_p['name']}** имеет **низкий потенциал** для классической жизни.

🔬 **Факторы риска:** {'Экстремальная температура. ' if sel_p['temp'] > 400 or sel_p['temp'] < 200 else ''}{'Размер указывает на газовый состав. ' if sel_p['radius'] > 3 else ''}{'Вне зоны обитаемости.' if not sel_p['in_hz'] else ''}

💡 **Однако:** Экзотические формы жизни не исключены.

*— ATLAS v21*
                """,
                'en': f"""
**Conclusion:** Planet **{sel_p['name']}** has **low potential** for classical life.

🔬 **Risk factors:** {'Extreme temperature. ' if sel_p['temp'] > 400 or sel_p['temp'] < 200 else ''}{'Size indicates gaseous composition. ' if sel_p['radius'] > 3 else ''}{'Outside habitable zone.' if not sel_p['in_hz'] else ''}

💡 **However:** Exotic life forms not excluded.

*— ATLAS v21*
                """
            }
        
        # Render report properly - box first, then markdown content
        st.markdown(f"""
        <div style='background: {card_bg}; border: 2px solid {accent}; border-radius: 16px; padding: 25px;
                    box-shadow: 0 0 20px rgba(0,212,255,0.1);'>
        </div>
        """, unsafe_allow_html=True)
        
        # The actual report content as proper markdown
        st.markdown(report.get(lang, report['en']))
        
        st.markdown("---")
        
        # ═══════════════════════════════════════════════════════════════════════
        # SPACE WEATHER FORECAST
        # ═══════════════════════════════════════════════════════════════════════
        weather_title = {'ru': '🌤️ Космический прогноз погоды', 'en': '🌤️ Space Weather Forecast', 'kz': '🌤️ Ғарыштық ауа райы'}[lang]
        st.markdown(f"### {weather_title}")
        
        # Track weather views for achievement
        if 'weather_views' not in st.session_state:
            st.session_state.weather_views = set()
        st.session_state.weather_views.add(sel_p['name'])
        if len(st.session_state.weather_views) >= 10:
            check_achievement('weather_watcher')
        
        forecasts = generate_space_weather(sel_p, star, lang)
        
        weather_cols = st.columns(5)
        for i, forecast in enumerate(forecasts):
            with weather_cols[i]:
                temp_color = '#ff6666' if forecast['temp'] > 100 else '#d5a14f' if forecast['temp'] > 0 else '#66b3ff' if forecast['temp'] > -50 else '#a0c4ff'
                st.markdown(f"""
                <div style='background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
                            border-radius: 12px; padding: 12px; text-align: center;'>
                    <div style='font-size: 0.75rem; opacity: 0.6;'>{forecast['day']}</div>
                    <div style='font-size: 1.5rem; margin: 8px 0;'>{forecast['condition'].split()[0]}</div>
                    <div style='font-size: 1.1rem; font-weight: bold; color: {temp_color};'>{forecast['temp']:.0f}°C</div>
                    <div style='font-size: 0.7rem; opacity: 0.5;'>💨 {forecast['wind']} km/h</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ═══════════════════════════════════════════════════════════════════════
        # QR CODE & SHARE
        # ═══════════════════════════════════════════════════════════════════════
        share_cols = st.columns([2, 1])
        
        with share_cols[0]:
            # Add to compare button
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
                        'emoji': sel_p['emoji']
                    }
                    st.success(f"✅ {sel_p['name']} added!")
        
        with share_cols[1]:
            # QR Code button
            qr_label = {'ru': '📱 QR-код для презентации', 'en': '📱 QR for Presentation', 'kz': '📱 QR-код презентацияға'}[lang]
            if st.button(qr_label, use_container_width=True):
                st.session_state['show_qr'] = sel_p['name']
        
        # Show QR modal - LARGE for presentations
        if st.session_state.get('show_qr') == sel_p['name']:
            qr_img, qr_url = generate_planet_qr(sel_p['name'])
            
            qr_title = {'ru': '📡 Передать координаты на мобильный терминал', 'en': '📡 Transfer Coordinates to Mobile Terminal', 'kz': '📡 Координаталарды мобильді терминалға жіберу'}[lang]
            
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, rgba(0,212,255,0.1), rgba(0,255,136,0.05));
                        border: 2px solid rgba(0,212,255,0.3); border-radius: 20px; padding: 30px;
                        text-align: center; margin: 20px 0;'>
                <h3 style='color: #d5a14f; margin-bottom: 20px;'>{qr_title}</h3>
            """, unsafe_allow_html=True)
            
            if qr_img:
                qr_cols = st.columns([1, 2, 1])
                with qr_cols[1]:
                    st.markdown(f"""
                    <div style='background: white; padding: 20px; border-radius: 20px; 
                                display: inline-block; box-shadow: 0 10px 40px rgba(0,0,0,0.3);'>
                        <img src='data:image/png;base64,{qr_img}' width='350' style='display: block;'>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    scan_text = {
                        'ru': f"📱 **Наведите камеру телефона на QR-код**\n\nДанные планеты **{sel_p['name']}** откроются на вашем устройстве",
                        'en': f"📱 **Point your phone camera at the QR code**\n\nPlanet **{sel_p['name']}** data will open on your device",
                        'kz': f"📱 **Телефон камерасын QR-кодқа бағыттаңыз**\n\n**{sel_p['name']}** деректері құрылғыңызда ашылады"
                    }[lang]
                    st.markdown(scan_text)
                    st.code(qr_url, language=None)
            else:
                st.info("Install `qrcode` library: `pip install qrcode[pil]`")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            if st.button("✖️ Закрыть / Close", key="close_qr", use_container_width=True):
                st.session_state['show_qr'] = None
                st.rerun()
    
    else:
        st.info(t('no_system'))


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: STAR MAP
# ═══════════════════════════════════════════════════════════════════════════════
if current_page == 'map':
    render_internal_stage('map', lang)
    st.markdown(f"### {t('starmap_title')}")
    st.markdown(f"*{t('starmap_desc')}*")
    
    if st.session_state.saved_systems:
        # Statistics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"🔍 {t('stat_systems')}", len(st.session_state.saved_systems))
        
        total_planets = sum(d['planet_count'] for d in st.session_state.saved_systems.values())
        c2.metric(f"🪐 {t('planets')}", total_planets)
        
        distances = [d['distance'] for d in st.session_state.saved_systems.values() if d.get('distance')]
        if distances:
            c3.metric("📏 Nearest", f"{min(distances):.1f} ly")
            c4.metric("📏 Farthest", f"{max(distances):.1f} ly")
        
        # 3D Star Map
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
        st.markdown(f"### {t('saved_systems')}")
        
        sorted_systems = sorted(
            st.session_state.saved_systems.items(),
            key=lambda x: x[1].get('distance') or 9999
        )
        
        for hostname, data in sorted_systems[:10]:
            dist_str = f"{data['distance']:.1f} ly" if data.get('distance') else "?"
            score_color = '#ece1cf' if data['best_score'] >= 70 else '#d5a14f' if data['best_score'] >= 50 else '#ffbb00'
            
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**🌟 {hostname}** — {dist_str} — {data['planet_count']} planets — Best: <span style='color:{score_color}'>{data['best_score']}</span>", unsafe_allow_html=True)
            with col2:
                if st.button(t('load_system'), key=f"map_load_{hostname}"):
                    load_system(hostname)
                    st.rerun()
    else:
        st.info(t('starmap_empty'))


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: AI ANALYSIS (ENHANCED)
# ═══════════════════════════════════════════════════════════════════════════════
if current_page == 'analysis':
    render_internal_stage('analysis', lang)
    st.markdown(f"### {t('analysis_title')}")
    
    all_planets = get_all_planets()
    
    if len(st.session_state.saved_systems) >= 1 and all_planets:
        # Overview metrics row
        st.markdown("#### 📈 Research Overview")
        m1, m2, m3, m4, m5 = st.columns(5)
        
        scores = [p['hab_score'] for p in all_planets]
        m1.metric("🔍 Systems", len(st.session_state.saved_systems))
        m2.metric("🪐 Planets", len(all_planets))
        m3.metric("⭐ Avg Score", f"{sum(scores)/len(scores):.1f}")
        m4.metric("🌱 In HZ", sum(1 for p in all_planets if p['in_hz']))
        m5.metric("🌍 Earth-like", sum(1 for p in all_planets if 0.8 <= p['radius'] <= 1.5))
        
        st.markdown("---")
        
        # Visualizations grid
        st.markdown("#### 📊 Data Visualizations")
        
        viz_col1, viz_col2 = st.columns(2)
        
        with viz_col1:
            st.markdown("**🌡️ Temperature vs Radius**")
            st.caption("Green zone = Earth-like conditions")
            st.plotly_chart(create_temp_vs_radius_scatter(), use_container_width=True)
        
        with viz_col2:
            st.markdown("**🪐 Planet Types Distribution**")
            st.plotly_chart(create_planet_types_pie(), use_container_width=True)
        
        viz_col3, viz_col4 = st.columns(2)
        
        with viz_col3:
            st.markdown("**📊 Habitability Score Distribution**")
            st.plotly_chart(create_score_distribution_chart(), use_container_width=True)
        
        with viz_col4:
            st.markdown("**📏 Distance Distribution**")
            st.plotly_chart(create_distance_histogram(), use_container_width=True)
        
        st.markdown("---")
        
        # Generate analysis button
        st.markdown("#### 🧠 AI Analysis")
        if st.button(t('generate_analysis'), use_container_width=True, type="primary"):
            st.session_state.recommendations = generate_recommendations()
            st.session_state.hypotheses = generate_hypotheses()
            st.rerun()
        
        # Display in two columns
        rec_col, hyp_col = st.columns(2)
        
        with rec_col:
            if st.session_state.recommendations:
                st.markdown(f"##### {t('recommendations')}")
                for i, rec in enumerate(st.session_state.recommendations[:3]):
                    with st.expander(rec['title'], expanded=(i == 0)):
                        st.markdown(f"**{rec['reason']}**")
                        st.info(f"💡 {rec['action']}")
        
        with hyp_col:
            if st.session_state.hypotheses:
                st.markdown(f"##### {t('hypotheses')}")
                for i, hyp in enumerate(st.session_state.hypotheses[:3]):
                    with st.expander(hyp['title'], expanded=(i == 0)):
                        st.markdown(f"**{hyp['hypothesis']}**")
                        st.caption(hyp['analysis'][:200] + "...")
        
        # Current system analysis
        if st.session_state.get('current_system'):
            st.markdown("---")
            hostname = st.session_state['current_system']
            analysis = generate_system_analysis(hostname)
            
            if analysis:
                st.markdown(f"#### 🔬 Current System: {hostname}")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(analysis['system_type'])
                    st.markdown(analysis['star_analysis'])
                with col2:
                    st.markdown(analysis['hz_analysis'])
                    st.markdown(analysis['best_candidate'])
                st.info(analysis['recommendation'])
    
    else:
        st.info(t('no_data_analysis'))
# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: COMPARE (FIXED TABLE with HTML styling)
# ═══════════════════════════════════════════════════════════════════════════════
if current_page == 'compare':
    render_internal_stage('compare', lang)
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
        # Planet selector
        st.markdown(f"**{t('select_planets')}**")
        
        selected_planets = st.multiselect(
            "Planets",
            options=list(available_planets.keys()),
            default=st.session_state.compare[:4] if st.session_state.compare else list(available_planets.keys())[:3],
            max_selections=6,
            label_visibility="collapsed"
        )
        
        if st.button(t('clear_selection')):
            st.session_state.compare = []
            st.rerun()
        
        if selected_planets and len(selected_planets) >= 2:
            selected_data = {name: available_planets[name] for name in selected_planets}
            
            # Charts
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown(f"#### {t('radar_chart')}")
                st.plotly_chart(create_radar_chart(selected_data), use_container_width=True)
            
            with c2:
                st.markdown(f"#### {t('bar_chart')}")
                st.plotly_chart(create_bar_comparison(selected_data), use_container_width=True)
            
            # FIXED Comparison table using HTML with theme-aware colors
            st.markdown(f"#### {t('comparison_table')}")
            
            # Detect theme
            is_dark = st.session_state.get('theme', 'dark') == 'dark'
            
            # Theme colors
            if is_dark:
                bg_header = '#3a312b'
                bg_cell = '#1e1a18'
                bg_hover = '#2b2521'
                text_color = '#e0e0e0'
                text_accent = '#d5a14f'
                border_color = '#5a4a3a'
                border_accent = '#d5a14f'
            else:
                bg_header = '#f1f5f9'
                bg_cell = '#ffffff'
                bg_hover = '#f8fafc'
                text_color = '#0f172a'
                text_accent = '#d5a14f'
                border_color = '#cbd5e1'
                border_accent = '#d5a14f'
            
            # Build HTML table with inline styles
            html = f"""
            <table style="width: 100%; border-collapse: collapse; margin: 16px 0; font-family: 'Inter', sans-serif;">
            <thead>
                <tr>
                    <th style="background: {bg_header}; color: {text_color}; padding: 14px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid {border_accent};">🪐 Planet</th>
                    <th style="background: {bg_header}; color: {text_color}; padding: 14px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid {border_accent};">Radius (R⊕)</th>
                    <th style="background: {bg_header}; color: {text_color}; padding: 14px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid {border_accent};">Mass (M⊕)</th>
                    <th style="background: {bg_header}; color: {text_color}; padding: 14px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid {border_accent};">Temp (K)</th>
                    <th style="background: {bg_header}; color: {text_color}; padding: 14px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid {border_accent};">ESI</th>
                    <th style="background: {bg_header}; color: {text_color}; padding: 14px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid {border_accent};">Gravity (g)</th>
                    <th style="background: {bg_header}; color: {text_color}; padding: 14px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid {border_accent};">Distance (ly)</th>
                </tr>
            </thead>
            <tbody>
            """
            
            for name in selected_planets:
                p = available_planets[name]
                emoji = p.get('emoji', '🪐')
                radius = f"{p.get('radius', 0):.2f}" if isinstance(p.get('radius'), (int, float)) else '?'
                mass = f"{p.get('mass', 0):.2f}" if isinstance(p.get('mass'), (int, float)) else '?'
                temp = f"{p.get('temp', 0):.0f}" if isinstance(p.get('temp'), (int, float)) else '?'
                esi = f"{p.get('esi', 0):.3f}" if isinstance(p.get('esi'), (int, float)) else '?'
                gravity = f"{p.get('gravity', 0):.2f}" if isinstance(p.get('gravity'), (int, float)) else '?'
                distance = f"{p.get('distance', 0):.1f}" if isinstance(p.get('distance'), (int, float)) else '?'
                
                html += f"""
                <tr>
                    <td style="background: {bg_cell}; color: {text_accent}; padding: 12px; border-bottom: 1px solid {border_color}; font-weight: 600;">{emoji} {name}</td>
                    <td style="background: {bg_cell}; color: {text_color}; padding: 12px; border-bottom: 1px solid {border_color};">{radius}</td>
                    <td style="background: {bg_cell}; color: {text_color}; padding: 12px; border-bottom: 1px solid {border_color};">{mass}</td>
                    <td style="background: {bg_cell}; color: {text_color}; padding: 12px; border-bottom: 1px solid {border_color};">{temp}</td>
                    <td style="background: {bg_cell}; color: {text_color}; padding: 12px; border-bottom: 1px solid {border_color};">{esi}</td>
                    <td style="background: {bg_cell}; color: {text_color}; padding: 12px; border-bottom: 1px solid {border_color};">{gravity}</td>
                    <td style="background: {bg_cell}; color: {text_color}; padding: 12px; border-bottom: 1px solid {border_color};">{distance}</td>
                </tr>
                """
            
            html += """
            </tbody>
            </table>
            """
            
            st.markdown(html, unsafe_allow_html=True)
        
        elif selected_planets:
            st.info("Select at least 2 planets to compare")
    
    else:
        st.info("Explore more systems to unlock comparison features!")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: ENCYCLOPEDIA
# ═══════════════════════════════════════════════════════════════════════════════
if current_page == 'encyclopedia':
    render_internal_stage('encyclopedia', lang)
    st.markdown(f"### {t('encyclopedia_title')}")
    
    lang = st.session_state.lang
    
    # Topic selector
    topic_options = {
        'star_types': ENCYCLOPEDIA['star_types']['title'][lang],
        'planet_types': ENCYCLOPEDIA['planet_types']['title'][lang],
        'habitability': ENCYCLOPEDIA['habitability']['title'][lang],
        'detection': ENCYCLOPEDIA['detection']['title'][lang],
        'formulas': ENCYCLOPEDIA['formulas']['title'][lang]
    }
    
    cols = st.columns(5)
    selected_topic = st.session_state.get('encyclopedia_topic', 'star_types')
    
    for i, (key, title) in enumerate(topic_options.items()):
        with cols[i]:
            if st.button(title, key=f"enc_{key}", use_container_width=True,
                        type="primary" if selected_topic == key else "secondary"):
                st.session_state.encyclopedia_topic = key
                st.rerun()
    
    st.markdown("---")
    
    # Display content
    topic_data = ENCYCLOPEDIA.get(selected_topic, ENCYCLOPEDIA['star_types'])
    st.markdown(topic_data['content'][lang])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6: HISTORY
# ═══════════════════════════════════════════════════════════════════════════════
if current_page == 'history':
    render_internal_stage('history', lang)
    st.markdown(f"### {t('history_title')}")
    storage_label = "Local storage" if lang == 'en' else 'Жергілікті сақтау'
    save_label = "Save mission data" if lang == 'en' else 'Миссия деректерін сақтау'
    clear_all_label = "Clear saved data" if lang == 'en' else 'Сақталған деректерді тазалау'
    status_text = "Available" if LOCAL_STORAGE_AVAILABLE else "Unavailable"
    st.caption(f"{storage_label}: {status_text}")
    history_actions = st.columns([1, 1.2, 3])
    with history_actions[0]:
        if st.button(save_label, use_container_width=True, key="history_save_data"):
            save_to_local_storage()
            st.toast("Data saved locally" if lang == 'en' else 'Деректер жергілікті сақталды', icon="💾")
    with history_actions[1]:
        if st.button(clear_all_label, use_container_width=True, key="history_clear_all_data"):
            for key in list(st.session_state.keys()):
                if key not in ['theme', 'lang', 'current_page', 'local_storage_loaded']:
                    del st.session_state[key]
            clear_local_storage()
            st.rerun()
    
    if st.session_state.saved_systems:
        # Sort by timestamp (newest first)
        sorted_systems = sorted(
            st.session_state.saved_systems.items(),
            key=lambda x: x[1].get('timestamp', ''),
            reverse=True
        )
        
        # Clear button
        if st.button(t('clear_history'), type="secondary", key="clear_history_btn_history_tab"):
            st.session_state.saved_systems = {}
            st.session_state.scanned_stars = set()
            st.session_state.scan_count = 0
            st.session_state.habitable_count = 0
            st.rerun()
        
        st.markdown("---")
        
        # Display systems
        for hostname, data in sorted_systems:
            score_color = '#ece1cf' if data['best_score'] >= 70 else '#d5a14f' if data['best_score'] >= 50 else '#ffbb00' if data['best_score'] >= 30 else '#ff6666'
            
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
# TAB 7: NASA EYES (replaces Travel)
# ═══════════════════════════════════════════════════════════════════════════════
if current_page == 'nasa_eyes':
    render_internal_stage('nasa_eyes', lang)
    st.markdown("### 🌌 NASA Eyes on the Solar System")
    
    lang = st.session_state.lang
    desc = {
        'ru': "Интерактивная 3D визуализация Солнечной системы от NASA. Исследуйте планеты, спутники и экзопланеты!",
        'en': "Interactive 3D visualization of the Solar System by NASA. Explore planets, moons, and exoplanets!",
        'kz': "NASA-ның Күн жүйесінің интерактивті 3D визуализациясы. Планеталарды, серіктерді және экзопланеталарды зерттеңіз!"
    }
    st.markdown(f"*{desc[lang]}*")
    
    # Quick navigation buttons
    st.markdown("**Quick Navigation:**")
    nav_cols = st.columns(6)
    
    destinations = [
        ("🏠 Home", "home"),
        ("🌍 Earth", "earth"),
        ("🔴 Mars", "mars"),
        ("🪐 Jupiter", "jupiter"),
        ("💫 Saturn", "saturn"),
        ("🌌 Exoplanets", "exoplanets")
    ]
    
    current_dest = st.session_state.get('nasa_eyes_dest', 'home')
    
    for i, (label, dest) in enumerate(destinations):
        with nav_cols[i]:
            if st.button(label, key=f"nasa_{dest}", use_container_width=True,
                        type="primary" if current_dest == dest else "secondary"):
                st.session_state.nasa_eyes_dest = dest
                st.rerun()
    
    # Time rate selector
    st.markdown("**⏱️ Time Speed:**")
    time_cols = st.columns(5)
    time_rates = [
        ("1x Real", 1),
        ("1 hour/sec", 3600),
        ("1 day/sec", 86400),
        ("1 week/sec", 604800),
        ("1 month/sec", 2592000)
    ]
    
    current_rate = st.session_state.get('nasa_eyes_rate', 86400)  # Default: 1 day/sec
    
    for i, (label, rate) in enumerate(time_rates):
        with time_cols[i]:
            if st.button(label, key=f"rate_{rate}", use_container_width=True,
                        type="primary" if current_rate == rate else "secondary"):
                st.session_state.nasa_eyes_rate = rate
                st.rerun()
    
    # Build iframe URL with time rate
    base_url = "https://eyes.nasa.gov/apps/solar-system/"
    params = f"?logo=false&shareButton=false&collapseSettingsOptions=true&rate={current_rate}"
    
    if current_dest == 'exoplanets':
        iframe_url = f"https://eyes.nasa.gov/apps/exo/?logo=false&shareButton=false"
    else:
        iframe_url = f"{base_url}{params}#/{current_dest}"
    
    # Embed iframe using streamlit components
    import streamlit.components.v1 as components
    
    components.iframe(iframe_url, height=600, scrolling=False)
    
    # Info about controls
    with st.expander("🎮 Controls / Управление"):
        controls = {
            'ru': """
            - **Мышь**: Вращение камеры
            - **Колёсико**: Приближение/отдаление
            - **Клик на объект**: Информация
            - **Двойной клик**: Фокус на объекте
            """,
            'en': """
            - **Mouse**: Rotate camera
            - **Scroll**: Zoom in/out
            - **Click object**: Show info
            - **Double-click**: Focus on object
            """,
            'kz': """
            - **Тінтуір**: Камераны айналдыру
            - **Айналдыру**: Үлкейту/кішірейту
            - **Объектіге басу**: Ақпарат көрсету
            """
        }
        st.markdown(controls[lang])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 8: AI CHAT (ML model + pattern matching)
# ═══════════════════════════════════════════════════════════════════════════════
if current_page == 'ai_chat':
    render_internal_stage('ai_chat', lang)
    st.markdown('### AI Assistant')
    
    lang = st.session_state.lang
    
    # Show ML model status
    if CHATBOT_AVAILABLE:
        st.success('ML model loaded - smart responses enabled')
    else:
        st.info('Pattern matching mode - place exo_chatbot_model.pkl in the app folder for ML support')
    
    subtitle = {
        'ru': "Задайте вопрос об экзопланетах, ваших открытиях или астрофизике",
        'en': "Ask about exoplanets, your discoveries, or astrophysics",
        'kz': "Экзопланеталар, ашылымдарыңыз немесе астрофизика туралы сұраңыз"
    }
    st.markdown(f"*{subtitle[lang]}*")
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Chat display area
    chat_container = st.container()
    
    with chat_container:
        for msg in st.session_state.chat_history[-10:]:  # Show last 10 messages
            if msg['role'] == 'user':
                st.markdown(f"""
                <div style='background: rgba(213,161,79,0.12); border-radius: 12px; padding: 12px 16px; 
                            margin: 8px 0; margin-left: 20%; border-left: 3px solid #d5a14f;'>
                    <strong>You:</strong> {msg['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                source_badge = msg.get('source', '')
                st.markdown(f"""
                <div style='background: rgba(236,225,207,0.10); border-radius: 12px; padding: 12px 16px; 
                            margin: 8px 0; margin-right: 10%; border-left: 3px solid #ece1cf;'>
                    <strong>ATLAS {source_badge}:</strong>
                    
{msg['content']}
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick question buttons
    quick_q = {
        'ru': ["📊 Статистика", "🌍 Что такое ESI?", "🌱 Зона обитаемости", "🔴 TRAPPIST-1", "🏆 Лучшая находка"],
        'en': ["📊 Statistics", "🌍 What is ESI?", "🌱 Habitable zone", "🔴 TRAPPIST-1", "🏆 Best find"],
        'kz': ["📊 Статистика", "🌍 ESI дегеніміз?", "🌱 Мекендеуге жарамды аймақ", "🔴 TRAPPIST-1", "🏆 Үздік табыс"]
    }
    
    st.markdown("**Quick questions:**")
    q_cols = st.columns(5)
    
    for i, q in enumerate(quick_q[lang]):
        with q_cols[i]:
            if st.button(q, key=f"quick_{i}", use_container_width=True):
                st.session_state.chat_history.append({'role': 'user', 'content': q})
                response, source = get_smart_response(q)
                st.session_state.chat_history.append({'role': 'assistant', 'content': response, 'source': source})
                st.rerun()
    
    # Text input
    user_input = st.text_input(
        "Message",
        placeholder="Ask me anything about exoplanets...",
        label_visibility="collapsed",
        key="chat_input"
    )
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        if st.button('Send', use_container_width=True, type='primary'):
            if user_input:
                st.session_state.chat_history.append({'role': 'user', 'content': user_input})
                with st.spinner('Thinking...'):
                    response, source = get_smart_response(user_input)
                st.session_state.chat_history.append({'role': 'assistant', 'content': response, 'source': source})
                st.rerun()
    
    with col2:
        if st.button('Clear', use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
if current_page == 'achievements':
    render_achievements_page(lang)


# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('---')
st.markdown("""
<div style='text-align: center; padding: 20px; opacity: 0.72;'>
    <p><b>ATLAS v21</b> - Autonomous Terrestrial Life Analysis System</p>
    <p>Diploma Project &bull; 2024-2025 &bull; Powered by NASA Exoplanet Archive</p>
    <p style='font-size: 0.8rem;'>Data source: NASA Exoplanet Archive TAP Service</p>
</div>
""", unsafe_allow_html=True)
