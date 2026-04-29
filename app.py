"""
ATLAS v21 — Flask Application
Autonomous Terrestrial Life Analysis System
"""

from flask import Flask, render_template, request, jsonify, session, send_from_directory
import json, math, random, time, requests, os, uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'atlas-v21-key-2025'

# ── Google Gemini ─────────────────────────────────────────────────────────────
GEMINI_API_KEY = 'AIzaSyCW_yNIspPEXNWkieqG2QQnqWkai5nP1Q8'
GEMINI_MODELS = [
    'gemini-2.5-flash-preview-05-20',
    'gemini-2.0-flash',
    'gemini-1.5-flash',
    'gemini-1.5-flash-8b',
]
GEMINI_BASE = 'https://generativelanguage.googleapis.com/v1beta/models/'
GEMINI_URL = GEMINI_BASE + GEMINI_MODELS[0] + ':generateContent?key=' + GEMINI_API_KEY

# ── In-memory share snapshots (token → report dict) ──────────────────────────
_shares = {}

# Отключаем кэш статических файлов в режиме разработки
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Версия для cache-busting в шаблонах
import time as _time
STATIC_VER = str(int(_time.time()))

@app.context_processor
def inject_globals():
    return dict(static_ver=STATIC_VER)

# ── ML Models ─────────────────────────────────────────────────────────────────
CHATBOT_AVAILABLE = False
MODEL_AVAILABLE   = False
chatbot_model     = None
exoplanet_model   = None
chatbot_responses = {}
model_features    = None

try:
    import joblib, numpy as np
    chatbot_model = joblib.load('exo_chatbot_model.pkl')
    with open('exo_chatbot_responses.json', 'r', encoding='utf-8') as f:
        chatbot_responses = json.load(f)
    CHATBOT_AVAILABLE = True
except Exception:
    pass

try:
    import joblib, numpy as np
    exoplanet_model = joblib.load('exoplanet_model.pkl')
    try:
        model_features = joblib.load('features.pkl')
    except Exception:
        model_features = None
    MODEL_AVAILABLE = True
except Exception:
    pass

# ── In-memory user state ──────────────────────────────────────────────────────
_state = {}

def get_uid():
    if 'uid' not in session:
        session['uid'] = str(random.randint(10**7, 10**8))
    return session['uid']

# ── Auth API ──────────────────────────────────────────────────────────────────

@app.route('/api/login', methods=['POST'])
def api_login():
    data     = request.get_json() or {}
    username = (data.get('username') or '').strip()[:30]
    if len(username) < 2:
        return jsonify({'error': 'Username too short'}), 400
    session['uid'] = 'u_' + username
    saved = data.get('state')
    if saved and isinstance(saved, dict):
        uid = session['uid']
        if uid not in _state:
            _state[uid] = {
                'lang': 'en', 'systems': {}, 'scanned': [],
                'habitable_count': 0, 'chat': [], 'laika_chat': [],
                'achievements': {}, 'log': [], 'compare': [],
                'custom_planets': {}, 'quote_index': 0
            }
        for key in ('lang','systems','scanned','habitable_count',
                    'achievements','log','compare','custom_planets','quote_index'):
            if key in saved:
                _state[uid][key] = saved[key]
    return jsonify({'ok': True, 'uid': session['uid']})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'ok': True})

@app.route('/api/discover', methods=['POST'])
def api_discover():
    """Query NASA Exoplanet Archive for real stars with confirmed exoplanets by category."""
    data    = request.get_json() or {}
    category = data.get('category', 'nearby')

    # NASA TAP WHERE clauses per category
    WHERE = {
        'nearby':   "sy_dist<50 AND sy_dist IS NOT NULL AND pl_rade IS NOT NULL",
        'kepler':   "disc_facility LIKE '%Kepler%' AND pl_rade IS NOT NULL",
        'tess':     "disc_facility LIKE '%TESS%' AND pl_rade IS NOT NULL",
        'k2':       "disc_facility LIKE '%K2%' AND pl_rade IS NOT NULL",
        'habitable':"pl_eqt BETWEEN 200 AND 350 AND pl_rade IS NOT NULL",
    }
    where = WHERE.get(category, WHERE['nearby'])
    tap_url = (
        "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
        "?query=SELECT+DISTINCT+hostname+FROM+ps+WHERE+" + where.replace(' ', '+')
        + "&format=json"
    )
    try:
        resp = requests.get(tap_url, timeout=20)
        if resp.ok:
            rows  = resp.json()
            stars = list({r['hostname'] for r in rows if r.get('hostname')})
            random.shuffle(stars)
            return jsonify({'ok': True, 'stars': stars, 'total': len(stars)})
        print(f'[Discover] HTTP {resp.status_code}')
    except Exception as e:
        print(f'[Discover] Error: {e}')
    return jsonify({'ok': False, 'stars': [], 'error': 'NASA API unavailable'})

@app.route('/api/get-state', methods=['GET'])
def api_get_state():
    s = get_state()
    return jsonify({
        'lang':            s.get('lang', 'en'),
        'systems':         s.get('systems', {}),
        'scanned':         s.get('scanned', []),
        'habitable_count': s.get('habitable_count', 0),
        'achievements':    s.get('achievements', {}),
        'log':             s.get('log', [])[-30:],
        'compare':         s.get('compare', []),
        'custom_planets':  s.get('custom_planets', {}),
        'quote_index':     s.get('quote_index', 0),
    })

def get_state():
    u = get_uid()
    if u not in _state:
        _state[u] = {
            'lang': 'en',
            'systems': {},
            'scanned': [],
            'habitable_count': 0,
            'chat': [],
            'achievements': {},
            'log': [],
            'compare': [],
            'custom_planets': {},
            'quote_index': random.randint(0, 6)
        }
    return _state[u]

# ── Data constants ────────────────────────────────────────────────────────────

CATALOGS = {
    'nearby': {
        'name': {'en': '🌟 Nearby Stars (<50 ly)', 'kz': '🌟 Жақын жұлдыздар (<50 жж)'},
        'stars': ['Proxima Centauri', 'TRAPPIST-1', 'LHS 1140', 'Ross 128', 'Wolf 1061',
                  'Tau Ceti', 'Epsilon Eridani', 'Gliese 667 C',
                  'Gliese 581', 'Gliese 876', 'Gliese 436', 'Gliese 1214', 'Gliese 3470',
                  'GJ 273', 'GJ 357']
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
                  'TRAPPIST-1', 'Proxima Centauri', "Teegarden's Star", 'GJ 357',
                  'K2-72', 'K2-3', 'K2-155', 'HD 40307', 'HD 85512', 'Gliese 163']
    },
    'k2': {
        'name': {'en': '🌍 K2 Mission', 'kz': '🌍 K2 миссиясы'},
        'stars': ['K2-18', 'K2-72', 'K2-3', 'K2-155', 'K2-9', 'K2-19',
                  'K2-25', 'K2-32', 'K2-33', 'K2-79', 'K2-96', 'K2-106',
                  'K2-131', 'K2-136', 'K2-141']
    },
    'giants': {
        'name': {'en': '🪐 Giant Stars', 'kz': '🪐 Алып жұлдыздар'},
        'stars': ['55 Cnc', 'HD 189733', 'HD 209458', 'WASP-17', 'WASP-39',
                  'WASP-76', 'WASP-121', 'HAT-P-7', 'HAT-P-11', 'HAT-P-32',
                  'Qatar-1', 'GJ 3470', 'GJ 1132', 'L 98-59', 'LP 791-18']
    },
    'jwst': {
        'name': {'en': '🔬 JWST Targets', 'kz': '🔬 JWST нысандары'},
        'stars': ['TRAPPIST-1', 'K2-18', 'LHS 1140', 'GJ 486', 'L 98-59',
                  'TOI-700', 'GJ 1132', 'LP 791-18', 'TOI-1452', 'TOI-715',
                  'Kepler-1649', 'GJ 357', 'TOI-270', 'GJ 3470', 'HD 189733']
    },
}

KNOWN_PLANETS = {
    '🌍 Earth':   {'radius': 1.0,  'mass': 1.0,   'temp': 288, 'esi': 1.0,  'gravity': 1.0,  'distance': 0, 'hab_score': 100, 'in_hz': True},
    '🔴 Mars':    {'radius': 0.53, 'mass': 0.107, 'temp': 210, 'esi': 0.64, 'gravity': 0.38, 'distance': 0, 'hab_score': 28,  'in_hz': False},
    '🟤 Venus':   {'radius': 0.95, 'mass': 0.815, 'temp': 737, 'esi': 0.44, 'gravity': 0.91, 'distance': 0, 'hab_score': 5,   'in_hz': False},
    '🪐 Jupiter': {'radius': 11.2, 'mass': 317.8, 'temp': 165, 'esi': 0.29, 'gravity': 2.36, 'distance': 0, 'hab_score': 0,   'in_hz': False},
}

ACHIEVEMENTS = {
    'first_scan':       {'name': {'en': 'First Contact',       'kz': 'Алғашқы байланыс'},     'desc': {'en': 'Scan your first star system',         'kz': 'Алғашқы жұлдыз жүйесін сканерлеңіз'}, 'icon': '🔭'},
    'explorer_5':       {'name': {'en': 'Star Explorer',       'kz': 'Жұлдыз зерттеушісі'},   'desc': {'en': 'Explore 5 star systems',               'kz': '5 жұлдыз жүйесін зерттеңіз'},         'icon': '⭐'},
    'explorer_10':      {'name': {'en': 'Cosmic Voyager',      'kz': 'Ғарыш саяхатшысы'},    'desc': {'en': 'Explore 10 star systems',              'kz': '10 жұлдыз жүйесін зерттеңіз'},        'icon': '🚀'},
    'habitable_found':  {'name': {'en': 'Life Seeker',         'kz': 'Өмір іздеуші'},         'desc': {'en': 'Find a planet in habitable zone',      'kz': 'МЖА-дан планета табыңыз'},             'icon': '🌱'},
    'habitable_5':      {'name': {'en': 'Habitability Hunter', 'kz': 'МЖА аңшысы'},           'desc': {'en': 'Find 5 habitable zone planets',        'kz': '5 МЖА планета табыңыз'},               'icon': '🌿'},
    'earth_twin':       {'name': {'en': 'Earth Twin',          'kz': 'Жердің егізі'},          'desc': {'en': 'Find a planet with ESI > 0.8',         'kz': 'ESI > 0.8 планета табыңыз'},           'icon': '🌍'},
    'giant_hunter':     {'name': {'en': 'Giant Hunter',        'kz': 'Алып аңшысы'},          'desc': {'en': 'Find a gas giant (>6 R⊕)',             'kz': 'Газ алыбын табыңыз (>6 R⊕)'},         'icon': '🪐'},
    'mini_world':       {'name': {'en': 'Mini World',          'kz': 'Шағын әлем'},            'desc': {'en': 'Find a sub-Earth (<0.8 R⊕)',           'kz': 'Суб-Жерді табыңыз (<0.8 R⊕)'},        'icon': '🔴'},
    'catalog_complete': {'name': {'en': 'Catalog Master',      'kz': 'Каталог шебері'},        'desc': {'en': 'Complete scanning a full catalog',     'kz': 'Каталогты толық сканерлеңіз'},         'icon': '📚'},
    'score_90':         {'name': {'en': 'Prime Candidate',     'kz': 'Басты үміткер'},         'desc': {'en': 'Find a planet with 90+ score',         'kz': '90+ балл бар планета табыңыз'},         'icon': '🏆'},
    'multi_planet':     {'name': {'en': 'System Surveyor',     'kz': 'Жүйе зерттеушісі'},     'desc': {'en': 'Find a system with 5+ planets',        'kz': '5+ планетасы бар жүйе табыңыз'},       'icon': '🌌'},
    'compare_3':        {'name': {'en': 'Analyst',             'kz': 'Талдаушы'},              'desc': {'en': 'Compare 3 planets simultaneously',     'kz': '3 планетаны салыстырыңыз'},            'icon': '📊'},
    'traveler':         {'name': {'en': 'Space Traveler',      'kz': 'Ғарыш саяхатшысы'},    'desc': {'en': 'Plan an interstellar mission',         'kz': 'Жұлдызаралық миссияны жоспарлаңыз'},  'icon': '✈️'},
    'chat_10':          {'name': {'en': 'Curious Mind',        'kz': 'Қызықты ақыл'},         'desc': {'en': 'Ask AI assistant 10 questions',        'kz': 'AI-ге 10 сұрақ қойыңыз'},             'icon': '🤖'},
}

QUOTES = [
    {'text': {'en': "The cosmos is within us. We are made of star-stuff.",
              'kz': "Ғарыш біздің ішімізде. Біз жұлдыз материясынан жасалғанбыз."},
     'author': "Carl Sagan"},
    {'text': {'en': "Somewhere, something incredible is waiting to be known.",
              'kz': "Бір жерде керемет нәрсе табылуды күтуде."},
     'author': "Carl Sagan"},
    {'text': {'en': "The universe is under no obligation to make sense to you.",
              'kz': "Ғалам сізге түсінікті болуға міндетті емес."},
     'author': "Neil deGrasse Tyson"},
    {'text': {'en': "We are a way for the cosmos to know itself.",
              'kz': "Біз ғаламның өзін тануының жолымыз."},
     'author': "Carl Sagan"},
    {'text': {'en': "The Earth is the cradle of humanity, but one cannot live in a cradle forever.",
              'kz': "Жер — адамзаттың бесігі, бірақ бесікте мәңгі өмір сүруге болмайды."},
     'author': "Konstantin Tsiolkovsky"},
    {'text': {'en': "For small creatures such as we, the vastness is bearable only through love.",
              'kz': "Біз сияқты кішкентай жандар үшін шексіздікті тек махаббат арқылы көтеруге болады."},
     'author': "Carl Sagan"},
    {'text': {'en': "The important thing is not to stop questioning.",
              'kz': "Маңыздысы — сұрақ қоюды тоқтатпау."},
     'author': "Albert Einstein"},
]

ENCYCLOPEDIA = {
    'star_types': {
        'title': {'en': '⭐ Star Types', 'kz': '⭐ Жұлдыз түрлері'},
        'content': {
            'en': """
### Stellar Spectral Classification

| Class | Temperature | Color | Lifespan | Examples |
|-------|-------------|-------|----------|---------|
| O | 30,000–50,000 K | Blue | <10 Myr | Mintaka |
| B | 10,000–30,000 K | Blue-White | 10–300 Myr | Rigel |
| A | 7,500–10,000 K | White | 0.3–2 Gyr | Sirius, Vega |
| F | 6,000–7,500 K | Yellow-White | 2–7 Gyr | Procyon |
| **G** | **5,200–6,000 K** | **Yellow** | **7–15 Gyr** | **Sun ☀️** |
| **K** | **3,700–5,200 K** | **Orange** | **15–50 Gyr** | **Epsilon Eridani** |
| M | 2,400–3,700 K | Red | 50+ Gyr | TRAPPIST-1 |

**Best for life:** G and K types — stable, long-lived, enough UV for photosynthesis.

**Problematic:** M-dwarfs (stellar flares, tidal locking). O/B (too short-lived).
""",
            'kz': """
### Жұлдыздардың спектрлік жіктелуі

| Класс | Температура | Түс | Өмір | Мысалдар |
|-------|-------------|-----|------|---------|
| O | 30,000–50,000 K | Көк | <10 млн жыл | Минтака |
| B | 10,000–30,000 K | Ақ-көк | 10–300 млн жыл | Ригель |
| A | 7,500–10,000 K | Ақ | 0.3–2 млрд жыл | Сириус |
| F | 6,000–7,500 K | Сары-ақ | 2–7 млрд жыл | Процион |
| **G** | **5,200–6,000 K** | **Сары** | **7–15 млрд жыл** | **Күн ☀️** |
| **K** | **3,700–5,200 K** | **Сарғыш** | **15–50 млрд жыл** | **Эпсилон Эридани** |
| M | 2,400–3,700 K | Қызыл | 50+ млрд жыл | TRAPPIST-1 |

**Өмір үшін оңтайлы:** G және K түрлері — тұрақты, ұзақ өмірлі.
"""
        }
    },
    'planet_types': {
        'title': {'en': '🪐 Planet Types', 'kz': '🪐 Планета түрлері'},
        'content': {
            'en': """
### Exoplanet Classification by Radius

| Type | Radius (R⊕) | Description | Notable Examples |
|------|-------------|-------------|-----------------|
| 🪨 Dwarf | < 0.5 | Airless rocky body | Ceres |
| 🔴 Sub-Earth | 0.5–0.8 | Mars-like, thin atmosphere | Kepler-138b |
| 🌍 Terrestrial | 0.8–1.25 | Potentially habitable | **Kepler-442b** |
| 🌎 Super-Earth | 1.25–2.0 | Thick atmosphere, oceans possible | LHS-1140b |
| 💧 Mini-Neptune | 2.0–4.0 | Water world or gas envelope | TOI-270d |
| 🔵 Ice Giant | 4–6 | Deep H₂/He atmosphere | Neptune |
| 🪐 Gas Giant | 6–15 | Metallic hydrogen core | Jupiter |
| 🟤 Super-Jupiter | > 15 | Near brown dwarf boundary | KELT-9b |

#### The "Radius Valley" (1.5–2.0 R⊕)
A gap in the planet size distribution caused by photoevaporation stripping atmospheres.
""",
            'kz': """
### Экзопланеталардың радиусы бойынша жіктелуі

| Түр | Радиус (R⊕) | Сипаттама | Мысалдар |
|-----|-------------|-----------|---------|
| 🪨 Ергежейлі | < 0.5 | Атмосферасыз | Церера |
| 🔴 Суб-Жер | 0.5–0.8 | Марсқа ұқсас | Kepler-138b |
| 🌍 Жер тәрізді | 0.8–1.25 | Мекендеуге жарамды | Kepler-442b |
| 🌎 Супер-Жер | 1.25–2.0 | Қалың атмосфера | LHS-1140b |
| 💧 Мини-Нептун | 2.0–4.0 | Су әлемі | TOI-270d |
| 🔵 Мұзды алып | 4–6 | Терең атмосфера | Нептун |
| 🪐 Газ алыбы | 6–15 | Металл сутегі ядросы | Юпитер |
| 🟤 Супер-Юпитер | > 15 | Қоңыр ергежейлі шекарасы | KELT-9b |
"""
        }
    },
    'habitability': {
        'title': {'en': '🌱 Habitability Criteria', 'kz': '🌱 Мекендеуге жарамдылық'},
        'content': {
            'en': """
### Key Habitability Criteria

#### 1. Habitable Zone (HZ)
Region where liquid water can exist on surface.
- **Inner edge:** 0.75√L AU (runaway greenhouse)
- **Outer edge:** 1.77√L AU (CO₂ condensation)

#### 2. Size & Mass
- **Optimal:** 0.8–1.5 R⊕, 0.5–5 M⊕
- Large enough to retain atmosphere, small enough to stay rocky

#### 3. Temperature
- **Ideal:** 250–310 K (liquid water)
- **Extended:** 200–350 K (extremophile range)

#### 4. Atmosphere
- N₂/O₂ (biogenic) or N₂/CO₂ (abiotic stable)
- Pressure 0.5–5 atm for liquid water stability

#### 5. Stellar Stability
- **Best:** G and K-type stars
- **Risk:** M-dwarfs (flares, tidal locking)

### Earth Similarity Index (ESI)
```
ESI = √[ (1 - |R-1|/(R+1))^0.57 × (1 - |T-288|/(T+288))^5.58 ]
```
- **ESI > 0.8** → Earth-type candidate
- **ESI 0.6–0.8** → Mars/Venus analog
""",
            'kz': """
### Мекендеуге жарамдылықтың негізгі критерийлері

#### 1. Мекендеуге жарамды аймақ (МЖА)
Бетінде сұйық су болуы мүмкін аймақ.
- **Ішкі шекара:** 0.75√L AU
- **Сыртқы шекара:** 1.77√L AU

#### 2. Өлшем мен масса
- **Оңтайлы:** 0.8–1.5 R⊕, 0.5–5 M⊕

#### 3. Температура
- **Идеал:** 250–310 K
- **Кеңейтілген:** 200–350 K

#### 4. Жерге ұқсастық индексі (ESI)
ESI > 0.8 = Жер тәрізді үміткер
"""
        }
    },
    'detection': {
        'title': {'en': '🔭 Detection Methods', 'kz': '🔭 Анықтау әдістері'},
        'content': {
            'en': """
### Exoplanet Detection Methods

#### 1. Transit Photometry *(Most common)*
Planet crosses star's disk, dimming its light by 0.01–1%.
- **Missions:** Kepler, TESS, PLATO (2026)
- **Yields:** Planet radius, orbital period, atmosphere (via spectroscopy)

#### 2. Radial Velocity (Doppler)
Star wobbles gravitationally, causing blue/red-shift.
- **Instruments:** HARPS, ESPRESSO, NEID
- **Yields:** Minimum planet mass

#### 3. Direct Imaging
Photographing the planet itself.
- **Challenge:** Star is 10⁹× brighter
- **Missions:** JWST, future HabEx, LUVOIR

#### 4. Gravitational Microlensing
Planet bends background star's light.
- **Strengths:** Finds distant & low-mass planets
- **Weakness:** One-time, non-repeatable events

#### 5. Astrometry
Measuring precise star position wobble.
- **Mission:** Gaia (finding planets via stellar motion)
""",
            'kz': """
### Экзопланетаны анықтау әдістері

#### 1. Транзит фотометриясы *(Ең көп тараған)*
Планета жұлдыздың алдынан өтіп, жарығын 0.01–1% азайтады.

#### 2. Радиалды жылдамдық
Жұлдыз гравитациялық тербелістен Доплер ауысуын тудырады.

#### 3. Тікелей бейнелеу
Планетаны тікелей суретке түсіру (JWST).

#### 4. Гравитациялық микролинзалау
Планета фондық жұлдыз жарығын бүгеді.

#### 5. Астрометрия
Жұлдыз позициясының нақты өлшемдері (Gaia).
"""
        }
    },
    'missions': {
        'title': {'en': '🛰️ Space Missions', 'kz': '🛰️ Ғарыш миссиялары'},
        'content': {
            'en': """
### Key Exoplanet Missions

#### 🟢 Active

| Mission | Agency | Focus |
|---------|--------|-------|
| **TESS** (2018–) | NASA | All-sky transit survey of nearest bright stars |
| **JWST** (2021–) | NASA/ESA | Atmospheric spectroscopy, direct imaging |
| **Gaia** (2013–) | ESA | Precise stellar astrometry, planet discovery |
| **Cheops** (2019–) | ESA | Characterizing known planet systems |

#### 🔴 Legacy

| Mission | Years | Achievement |
|---------|-------|-------------|
| **Kepler** | 2009–2018 | 2,700+ confirmed planets; first Earth-sized HZ worlds |
| **Spitzer** | 2003–2020 | IR characterization of TRAPPIST-1 system |
| **CoRoT** | 2006–2013 | First rocky exoplanet detection |

#### 🔵 Upcoming

- **PLATO** (2026, ESA) — Earth-twins around Sun-like stars
- **Roman** (2027, NASA) — Microlensing survey + coronagraph
- **Ariel** (2029, ESA) — Atmosphere survey of 1000 exoplanets
""",
            'kz': """
### Негізгі экзопланета миссиялары

#### 🟢 Белсенді
- **TESS** (2018–) — Жақын жұлдыздарды зерттеу
- **JWST** (2021–) — Атмосфералық спектроскопия
- **Gaia** (2013–) — Жұлдыздардың нақты орналасуы
- **Cheops** (2019–) — Планета жүйелерін сипаттау

#### 🔴 Тарихи
- **Kepler** (2009–2018) — 2700+ расталған планета
- **Spitzer** (2003–2020) — TRAPPIST-1 жүйесі

#### 🔵 Болашақ
- **PLATO** (2026) — Жерге ұқсас планеталар
- **Ariel** (2029) — 1000 атмосфера зерттеу
"""
        }
    }
}

# ── Scientific Functions ──────────────────────────────────────────────────────

def calc_luminosity(teff, rad):
    return (rad ** 2) * ((teff / 5778) ** 4)

def calc_equilibrium_temp(teff, srad, orbit, albedo=0.3):
    r_au = srad * 0.00465047
    return teff * math.sqrt(r_au / (2 * orbit)) * ((1 - albedo) ** 0.25)

def calc_orbit_from_period(period, stellar_mass=1.0):
    return ((period / 365.25) ** 2 * stellar_mass) ** (1/3)

def calc_habitable_zone(teff, srad, luminosity=None):
    if luminosity is None:
        luminosity = calc_luminosity(teff, srad)
    L = luminosity
    return 0.75 * math.sqrt(L), 1.77 * math.sqrt(L)

def calc_esi(radius, temp):
    esi_r = 1 - abs(radius - 1) / (radius + 1)
    esi_t = 1 - abs(temp - 288) / (temp + 288)
    esi_r = max(0, min(1, esi_r)) ** 0.57
    esi_t = max(0, min(1, esi_t)) ** 5.58
    return round(math.sqrt(esi_r * esi_t), 3)

def calc_surface_gravity(mass, radius):
    if radius <= 0 or mass <= 0:
        return 0
    return mass / (radius ** 2)

def calc_density(mass, radius):
    if radius <= 0:
        return 0
    return mass / (radius ** 3)

def calc_escape_velocity(mass, radius):
    if radius <= 0 or mass <= 0:
        return 0
    return 11.2 * math.sqrt(mass / radius)

def calc_year_length(period):
    return period / 365.25

def calc_day_length(period, radius):
    if period < 30:
        return period * 24
    elif period < 100:
        return random.uniform(20, 100)
    else:
        return random.uniform(8, 48)

def estimate_magnetic_field(mass, radius):
    if mass < 0.1:
        return 0, _bi("Negligible — no protection", "Елеусіз — қорғаныс жоқ")
    core_factor = mass ** 0.75
    size_factor = 1 / (radius ** 0.5) if radius > 0 else 0
    field = core_factor * size_factor
    if field < 0.1:
        return 0, _bi("Negligible — no protection from stellar wind", "Елеусіз — жұлдыз желінен қорғаныс жоқ")
    elif field < 0.5:
        return round(field, 2), _bi("Weak — partial protection", "Әлсіз — жартылай қорғаныс")
    elif field < 2:
        return round(field, 2), _bi("Moderate — good protection", "Орташа — жақсы қорғаныс")
    else:
        return round(field, 2), _bi("Strong — excellent protection", "Күшті — тамаша қорғаныс")

def estimate_moons(mass, orbit_au, stellar_mass=1.0):
    if mass < 0.1:
        return 0
    hill_radius = orbit_au * (mass / (3 * stellar_mass)) ** (1/3)
    moon_prob = mass * hill_radius * 2
    if moon_prob < 0.5:
        return 0
    elif moon_prob < 2:
        return random.randint(0, 2)
    elif moon_prob < 10:
        return random.randint(1, 5)
    else:
        return random.randint(3, 20)

def get_planet_type(radius, mass, temp):
    # Returns (type_label, type_desc) — both plain strings (emoji + EN), desc bilingual via _bi
    # Note: _bi not yet defined here, inline the dict
    def _b(en, kz): return {'en': en, 'kz': kz}
    if radius < 0.5:
        return '🪨 Dwarf Planet', _b('Small rocky body without atmosphere', 'Атмосферасыз шағын тасты дене')
    elif radius < 0.8:
        return '🔴 Sub-Earth', _b('Mars-like, thin atmosphere possible', 'Марсқа ұқсас, жұқа атмосфера мүмкін')
    elif radius < 1.25:
        return '🌍 Terrestrial', _b('Potentially habitable, possible tectonics', 'Тіршілік мүмкін, тектоника болуы ықтимал')
    elif radius < 2.0:
        return '🌎 Super-Earth', _b('Thick atmosphere, possible oceans', 'Қалың атмосфера, мұхиттар мүмкін')
    elif radius < 4.0:
        return '💧 Mini-Neptune', _b('Water world or gas envelope', 'Су әлемі немесе газ қабаты')
    elif radius < 6.0:
        return '🔵 Ice Giant', _b('Neptune-like, deep atmosphere', 'Нептунға ұқсас, тереңдеген атмосфера')
    elif radius < 15:
        if temp > 1000:
            return '🔥 Hot Jupiter', _b('Close-orbiting gas giant, extremely hot', 'Жақын орбиталы газ алыбы, өте ыстық')
        return '🪐 Gas Giant', _b('Jupiter-like, metallic hydrogen core', 'Юпитерге ұқсас, металдық сутек өзегі')
    else:
        return '🟤 Super-Jupiter', _b('Near brown dwarf boundary', 'Қоңыр карлик шегіне жақын')

def _bi(en, kz):
    """Return bilingual dict."""
    return {'en': en, 'kz': kz}

def predict_atmosphere(radius, mass, temp, in_hz, stellar_teff=None):
    if radius > 4:
        return _bi('🌀 H₂/He dominated — thick gas envelope', '🌀 H₂/He басым — қалың газ қабаты')
    gravity = calc_surface_gravity(mass, radius)
    if gravity < 0.3:
        return _bi('❌ No atmosphere — gravity too weak', '❌ Атмосфера жоқ — ауырлық тым әлсіз')
    if temp > 500:
        return _bi('🔥 Tenuous — too hot to retain gases', '🔥 Іздер атмосфера — газдарды ұстап тұруға тым ыстық')
    if temp < 150:
        return _bi('❄️ Frozen — CO₂/N₂ ice possible', '❄️ Тоңазытылған — CO₂/N₂ мұзы мүмкін')
    if in_hz and 0.8 <= radius <= 1.5 and gravity >= 0.7:
        if stellar_teff and stellar_teff > 4000:
            return _bi('🌿 N₂/O₂ possible — potential biosignature', '🌿 N₂/O₂ мүмкін — биосигнатура ықтималдығы')
        return _bi('🌫️ N₂/CO₂ likely — abiotic stable', '🌫️ N₂/CO₂ болжалды — абиотикалық тұрақты')
    if radius > 1.5:
        return _bi('🌫️ H₂O/CO₂ envelope possible', '🌫️ H₂O/CO₂ қабаты мүмкін')
    return _bi('🌫️ Thin atmosphere possible', '🌫️ Жұқа атмосфера мүмкін')

def predict_hazards(temp, gravity, radius, orbit, stellar_teff, period=None):
    hazards = []
    if temp > 500:
        hazards.append({'level': 'critical',
            'name': _bi('🔥 Lethal Heat', '🔥 Өлімші ыстық'),
            'desc': _bi(f'Surface temperature {temp:.0f} K — all water vaporized', f'Бет температурасы {temp:.0f} K — барлық су буланған')})
    elif temp > 350:
        hazards.append({'level': 'warning',
            'name': _bi('⚠️ Extreme Heat', '⚠️ Шектен тыс ыстық'),
            'desc': _bi(f'Temperature {temp:.0f} K exceeds survivable limits', f'Температура {temp:.0f} K — тіршілік шегінен асып кеткен')})
    elif temp < 150:
        hazards.append({'level': 'critical',
            'name': _bi('❄️ Cryogenic', '❄️ Мұздық'),
            'desc': _bi(f'Temperature {temp:.0f} K — all water frozen solid', f'Температура {temp:.0f} K — барлық су мұздаған')})
    elif temp < 200:
        hazards.append({'level': 'warning',
            'name': _bi('⚠️ Extreme Cold', '⚠️ Шектен тыс суық'),
            'desc': _bi(f'Temperature {temp:.0f} K — liquid water unlikely', f'Температура {temp:.0f} K — сұйық су екіталай')})
    if gravity > 3:
        hazards.append({'level': 'critical',
            'name': _bi('⚠️ Crushing Gravity', '⚠️ Жаншитын ауырлық'),
            'desc': _bi(f'{gravity:.1f} g would crush the human skeletal system', f'{gravity:.1f} g адам қаңқасын жансытады')})
    elif gravity > 2:
        hazards.append({'level': 'warning',
            'name': _bi('⚠️ High Gravity', '⚠️ Жоғары ауырлық'),
            'desc': _bi(f'{gravity:.1f} g — severe strain on movement', f'{gravity:.1f} g — қозғалысқа ауыр кедергі')})
    elif gravity < 0.3:
        hazards.append({'level': 'warning',
            'name': _bi('⚠️ Microgravity', '⚠️ Микроауырлық'),
            'desc': _bi(f'{gravity:.2f} g — bone/muscle atrophy risk', f'{gravity:.2f} g — сүйек/бұлшықет атрофиясы қаупі')})
    if stellar_teff and stellar_teff < 3500:
        hazards.append({'level': 'warning',
            'name': _bi('⚡ Stellar Flares', '⚡ Жұлдыз жарқылдары'),
            'desc': _bi('M-dwarf host prone to deadly radiation bursts', 'M-карлик жүлдызы өлімші радиация жарқылдарына бейім')})
    if period and period < 30:
        hazards.append({'level': 'info',
            'name': _bi('🔒 Tidal Locking', '🔒 Толқындық бекіту'),
            'desc': _bi('One side always faces star — extreme temperature gradient', 'Бір жағы жұлдызға қарайды — шектен тыс температура градиенті')})
    if not hazards:
        hazards.append({'level': 'success',
            'name': _bi('✅ No Major Hazards', '✅ Маңызды қауіп жоқ'),
            'desc': _bi('Conditions within potentially survivable range', 'Жағдайлар тіршілікке мүмкін болатын шектерде')})
    return hazards

def predict_life_potential(temp, radius, in_hz, esi, atmo_type):
    score = 0
    factors = []
    # atmo_type may be a bilingual dict — extract English for string checks
    atmo_en = atmo_type['en'] if isinstance(atmo_type, dict) else atmo_type
    if 250 <= temp <= 310:
        score += 30
        factors.append({'ok': True, 'text': _bi('Optimal temperature for liquid water', 'Сұйық су үшін оңтайлы температура')})
    elif 200 <= temp <= 350:
        score += 15
        factors.append({'ok': None, 'text': _bi('Temperature within extremophile range', 'Экстремофилдер диапазонындағы температура')})
    else:
        factors.append({'ok': False, 'text': _bi('Temperature outside survivable range', 'Температура тіршілік мүмкін шектен тыс')})
    if in_hz:
        score += 25
        factors.append({'ok': True, 'text': _bi('Within stellar habitable zone', 'Жұлдыздың тіршілік аймағында')})
    else:
        factors.append({'ok': False, 'text': _bi('Outside habitable zone', 'Тіршілік аймағынан тыс')})
    if 0.8 <= radius <= 1.5:
        score += 20
        factors.append({'ok': True, 'text': _bi('Earth-like size — optimal for tectonics', 'Жер мөлшеріндей — тектоника үшін оңтайлы')})
    elif 0.5 <= radius <= 2.0:
        score += 10
        factors.append({'ok': None, 'text': _bi('Near Earth-size — possible habitability', 'Жерге жақын өлшем — тіршілік мүмкін')})
    else:
        factors.append({'ok': False, 'text': _bi('Size unfavorable for Earth-like life', 'Өлшемі Жер тіршілігіне қолайсыз')})
    if esi >= 0.8:
        score += 15
        factors.append({'ok': True, 'text': _bi('High Earth Similarity Index', 'Жермен ұқсастық индексі жоғары')})
    elif esi >= 0.6:
        score += 8
        factors.append({'ok': None, 'text': _bi('Moderate Earth similarity', 'Жермен орташа ұқсастық')})
    if 'N₂/O₂' in atmo_en or 'biosignature' in atmo_en.lower():
        score += 10
        factors.append({'ok': True, 'text': _bi('Atmosphere suggests possible biology', 'Атмосфера биологияны болжайды')})
    elif 'N₂/CO₂' in atmo_en:
        score += 5
        factors.append({'ok': None, 'text': _bi('Stable atmosphere, no biosignatures', 'Тұрақты атмосфера, биосигнатуралар жоқ')})
    if score >= 80:
        life_type = _bi('HIGH — Prime candidate for life', 'ЖОҒАРЫ — Тіршілікке бірінші үміткер')
        color = 'success'
    elif score >= 60:
        life_type = _bi('MODERATE — Possible extremophile habitat', 'ОРТАША — Экстремофил мекені мүмкін')
        color = 'warning'
    elif score >= 40:
        life_type = _bi('LOW — Requires significant adaptation', 'ТӨМЕН — Маңызды бейімделу қажет')
        color = 'info'
    else:
        life_type = _bi('MINIMAL — Inhospitable conditions', 'ЕҢ АЗ — Тіршілікке жарамсыз жағдайлар')
        color = 'danger'
    return life_type, score, factors, color

@app.template_filter('life_potential')
def life_potential_filter(planet):
    """Jinja2 filter: planet dict → (life_type, score, factors, color)"""
    atmo = planet.get('atmo_type', 'Unknown')
    return predict_life_potential(
        planet.get('temp', 0),
        planet.get('radius', 1.0),
        planet.get('in_hz', False),
        planet.get('esi', 0.0),
        atmo,
    )

def calculate_habitability_score(temp, radius, mass, in_hz, esi, gravity,
                                  stellar_teff, atmo_type, hazards):
    score = 0
    if 250 <= temp <= 310:
        score += 25
    elif 200 <= temp <= 350:
        score += 15
    elif 150 <= temp <= 400:
        score += 5
    if 0.8 <= radius <= 1.25:
        score += 20
    elif 0.5 <= radius <= 1.5:
        score += 15
    elif radius <= 2.0:
        score += 8
    if in_hz:
        score += 20
    score += int(esi * 15)
    if 0.7 <= gravity <= 1.5:
        score += 10
    elif 0.4 <= gravity <= 2.0:
        score += 5
    if stellar_teff and 4000 <= stellar_teff <= 6500:
        score += 5
    elif stellar_teff and 3500 <= stellar_teff <= 7000:
        score += 2
    atmo_en = atmo_type['en'] if isinstance(atmo_type, dict) else atmo_type
    if 'N₂/O₂' in atmo_en or 'biosignature' in atmo_en.lower():
        score += 5
    elif 'N₂/CO₂' in atmo_en:
        score += 3
    for h in hazards:
        if h['level'] == 'critical':
            score -= 30
        elif h['level'] == 'warning':
            score -= 10
    return max(0, min(100, score))

def process_planet_data(planet_raw, star_data):
    radius  = planet_raw.get('pl_rade')  or 1.0
    mass    = planet_raw.get('pl_bmasse') or (radius ** 2.06)
    temp    = planet_raw.get('pl_eqt')   or 288
    period  = planet_raw.get('pl_orbper') or 365
    orbit   = planet_raw.get('pl_orbsmax')

    stellar_mass = star_data.get('mass', 1.0)
    if not orbit and period:
        orbit = calc_orbit_from_period(period, stellar_mass)
    if not orbit:
        orbit = 1.0

    stellar_teff = star_data.get('teff', 5778)
    stellar_rad  = star_data.get('radius', 1.0)
    hz_inner, hz_outer = calc_habitable_zone(stellar_teff, stellar_rad)
    in_hz = hz_inner <= orbit <= hz_outer
    esi   = calc_esi(radius, temp)

    gravity    = calc_surface_gravity(mass, radius)
    density    = calc_density(mass, radius)
    escape_vel = calc_escape_velocity(mass, radius)
    year_len   = calc_year_length(period)
    day_len    = calc_day_length(period, radius)
    planet_type, type_desc = get_planet_type(radius, mass, temp)
    atmo_type  = predict_atmosphere(radius, mass, temp, in_hz, stellar_teff)
    hazards    = predict_hazards(temp, gravity, radius, orbit, stellar_teff, period)
    mag_str, mag_desc = estimate_magnetic_field(mass, radius)
    moons      = estimate_moons(mass, orbit, stellar_mass)
    hab_score  = calculate_habitability_score(temp, radius, mass, in_hz, esi, gravity,
                                               stellar_teff, atmo_type, hazards)
    lp_type, lp_score, lp_factors, lp_color = predict_life_potential(temp, radius, in_hz, esi, atmo_type)

    # ML-enhanced score if model available
    ml_score = None
    if MODEL_AVAILABLE and exoplanet_model is not None:
        try:
            import numpy as np
            feats = [radius, mass, temp, period, orbit, stellar_teff, stellar_rad, stellar_mass]
            ml_score = float(exoplanet_model.predict([feats])[0])
            ml_score = max(0, min(100, ml_score * 100 if ml_score <= 1 else ml_score))
        except Exception:
            ml_score = None

    # Planet emoji
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
        'name':       planet_raw.get('pl_name', 'Unknown'),
        'radius':     round(radius, 3),
        'mass':       round(mass, 3),
        'temp':       round(temp, 1),
        'period':     round(period, 2),
        'orbit':      round(orbit, 4),
        'gravity':    round(gravity, 2),
        'density':    round(density, 2),
        'escape_vel': round(escape_vel, 2),
        'year_length':round(year_len, 2),
        'day_length': round(day_len, 1),
        'esi':        esi,
        'in_hz':      in_hz,
        'hz_inner':   round(hz_inner, 3),
        'hz_outer':   round(hz_outer, 3),
        'type':       planet_type,
        'type_desc':  type_desc,
        'atmo_type':  atmo_type,
        'hazards':    hazards,
        'mag_str':    mag_str,
        'mag_desc':   mag_desc,
        'moons':      moons,
        'hab_score':  hab_score,
        'ml_score':   ml_score,
        'life_potential': {'type': lp_type, 'score': lp_score, 'factors': lp_factors, 'color': lp_color},
        'emoji':      emoji,
        'distance':   star_data.get('distance', 0),
        'disc_year':  planet_raw.get('disc_year'),
        'disc_method':planet_raw.get('discoverymethod'),
        'hostname':   star_data.get('name', ''),
    }

# ── NASA API ──────────────────────────────────────────────────────────────────

NASA_TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

# Map common/full names → NASA archive hostnames
STAR_NAME_ALIASES = {
    'proxima centauri':       'Proxima Cen',
    'proxima centauri b':     'Proxima Cen',
    'proxima':                'Proxima Cen',
    'luyten b':               'GJ 273',
    'luyten star':            'GJ 273',
    "teegarden's star":       "Teegarden's Star",
    'teegarden star':         "Teegarden's Star",
    'teegarden':              "Teegarden's Star",
    'lacaille 9352':          'GJ 887',
    'gliese 667 c':           'GJ 667C',
    'gliese 667c':            'GJ 667C',
    'gl 667c':                'GJ 667C',
    'gj 667 c':               'GJ 667C',
    'gliese 581':             'GJ 581',
    'gl 581':                 'GJ 581',
    'gliese 876':             'GJ 876',
    'gl 876':                 'GJ 876',
    'gliese 436':             'GJ 436',
    'gl 436':                 'GJ 436',
    'gliese 1214':            'GJ 1214',
    'gl 1214':                'GJ 1214',
    'gliese 3470':            'GJ 3470',
    'gl 3470':                'GJ 3470',
    'gliese 163':             'GJ 163',
    'gl 163':                 'GJ 163',
    'wolf 1061':              'Wolf 1061',
    'ross 128':               'Ross 128',
    'tau ceti':               'tau Ceti',
    'epsilon eridani':        'eps Eri',
    'eps eridani':            'eps Eri',
    'hd 40307':               'HD 40307',
    'hd 85512':               'HD 85512',
    'gj 357':                 'GJ 357',
    'k2-18':                  'K2-18',
    'k2-72':                  'K2-72',
    'k2-3':                   'K2-3',
    'k2-155':                 'K2-155',
    'lhs 1140':               'LHS 1140',
    'trappist-1':             'TRAPPIST-1',
    'trappist 1':             'TRAPPIST-1',
}

def fetch_nasa_data(star_name):
    # Normalise common names → NASA archive hostnames
    normalized = STAR_NAME_ALIASES.get(star_name.lower().strip(), star_name.strip())
    query = f"""
    SELECT pl_name, hostname, pl_rade, pl_bmasse, pl_eqt, pl_orbper,
           pl_orbsmax, st_teff, st_rad, st_mass, sy_dist, pl_insol,
           disc_year, discoverymethod
    FROM ps
    WHERE hostname LIKE '%{normalized}%'
    AND default_flag = 1
    ORDER BY pl_name
    """
    try:
        r = requests.get(NASA_TAP, params={'query': query, 'format': 'json'}, timeout=30)
        r.raise_for_status()
        data = r.json() or []
        # Fallback: try original name if normalised returned nothing
        if not data and normalized != star_name.strip():
            query2 = query.replace(f"'%{normalized}%'", f"'%{star_name.strip()}%'")
            r2 = requests.get(NASA_TAP, params={'query': query2, 'format': 'json'}, timeout=30)
            r2.raise_for_status()
            data = r2.json() or []
        return data
    except Exception as e:
        return []

# ── Achievement helpers ───────────────────────────────────────────────────────

def check_achievement(uid_key, ach_id):
    s = get_state()
    if ach_id not in s['achievements']:
        s['achievements'][ach_id] = True
        return True
    return False

def check_achievements_after_scan(planets):
    s = get_state()
    uid_key = get_uid()
    num = len(s['systems'])
    new_achs = []
    if num == 1:
        if check_achievement(uid_key, 'first_scan'): new_achs.append('first_scan')
    if num >= 5:
        if check_achievement(uid_key, 'explorer_5'): new_achs.append('explorer_5')
    if num >= 10:
        if check_achievement(uid_key, 'explorer_10'): new_achs.append('explorer_10')
    for p in planets:
        if p['in_hz']:
            if check_achievement(uid_key, 'habitable_found'): new_achs.append('habitable_found')
        if p['esi'] > 0.8:
            if check_achievement(uid_key, 'earth_twin'): new_achs.append('earth_twin')
        if p['radius'] > 6:
            if check_achievement(uid_key, 'giant_hunter'): new_achs.append('giant_hunter')
        if p['radius'] < 0.8:
            if check_achievement(uid_key, 'mini_world'): new_achs.append('mini_world')
        if p['hab_score'] >= 90:
            if check_achievement(uid_key, 'score_90'): new_achs.append('score_90')
    all_p = [p for sys in s['systems'].values() for p in sys['planets']]
    hz_total = sum(1 for p in all_p if p['in_hz'])
    if hz_total >= 5:
        if check_achievement(uid_key, 'habitable_5'): new_achs.append('habitable_5')
    if len(planets) >= 5:
        if check_achievement(uid_key, 'multi_planet'): new_achs.append('multi_planet')
    for cat in CATALOGS.values():
        if all(star in s['scanned'] for star in cat['stars']):
            if check_achievement(uid_key, 'catalog_complete'): new_achs.append('catalog_complete')
            break
    return new_achs

# ── Analysis helpers ──────────────────────────────────────────────────────────

def get_all_planets():
    s = get_state()
    result = []
    for hostname, data in s['systems'].items():
        for p in data['planets']:
            pc = dict(p)
            pc['hostname'] = hostname
            result.append(pc)
    return result

def generate_recommendations():
    all_p = get_all_planets()
    if not all_p:
        return []
    recs = []
    best = max(all_p, key=lambda x: x['hab_score'])
    if best['hab_score'] >= 50:
        recs.append({
            'title': f"🎯 Priority Target: {best['name']}",
            'reason': f"Highest habitability score ({best['hab_score']}/100) — {best['type']}",
            'action': 'Recommend spectroscopic follow-up for atmospheric analysis'
        })
    earth_like = [p for p in all_p if p['esi'] >= 0.7]
    if earth_like:
        recs.append({
            'title': f"🌍 Earth-like Candidates ({len(earth_like)})",
            'reason': 'High ESI values suggest Earth-similar conditions',
            'action': 'Search for water vapor and oxygen signatures'
        })
    s = get_state()
    for cat_key, cat_data in CATALOGS.items():
        unscanned = [star for star in cat_data['stars'] if star not in s['scanned']]
        if unscanned:
            recs.append({
                'title': f"🔭 Explore {cat_data['name']['en']}",
                'reason': f"{len(unscanned)} unscanned targets remaining",
                'action': f"Priority next: {unscanned[0]}"
            })
            break
    return recs[:5]

def generate_hypotheses():
    all_p = get_all_planets()
    if len(all_p) < 3:
        return []
    hyps = []
    hz_p = [p for p in all_p if p['in_hz']]
    if hz_p:
        avg_r = sum(p['radius'] for p in hz_p) / len(hz_p)
        hyps.append({
            'title': 'Habitable Zone Planet Sizes',
            'hypothesis': f'HZ planets in this sample average {avg_r:.2f} R⊕',
            'analysis': 'Suggests selection effects or physical constraints on habitability',
            'evidence': f'Sample: {len(hz_p)} HZ planets',
            'further_study': 'Expand sample with TESS and Kepler data'
        })
    temps = [p['temp'] for p in all_p]
    avg_t = sum(temps) / len(temps)
    hyps.append({
        'title': 'Temperature Distribution',
        'hypothesis': f'Average discovered planet temperature: {avg_t:.0f} K',
        'analysis': 'Detection bias toward close-orbiting, hotter planets',
        'evidence': f'Based on {len(all_p)} planetary observations',
        'further_study': 'Long-baseline radial velocity for cooler planets'
    })
    return hyps[:4]

# ── Star coordinates for 3D map ───────────────────────────────────────────────

def get_star_coords(hostname, distance=None):
    random.seed(hash(hostname))
    dist = distance if distance else random.uniform(10, 500)
    theta = random.uniform(0, 2 * math.pi)
    phi   = random.uniform(-math.pi/3, math.pi/3)
    x = dist * math.cos(phi) * math.cos(theta)
    y = dist * math.cos(phi) * math.sin(theta)
    z = dist * math.sin(phi)
    return round(x, 2), round(y, 2), round(z, 2)

# ── Plotly chart data builders ────────────────────────────────────────────────

def build_starmap_data(systems):
    traces = []
    # Sun
    traces.append({
        'type': 'scatter3d', 'x': [0], 'y': [0], 'z': [0],
        'mode': 'markers+text',
        'marker': {'size': 14, 'color': '#FFD700', 'symbol': 'circle'},
        'text': ['☀️ Sol'], 'textposition': 'top center',
        'textfont': {'size': 11, 'color': 'white'},
        'name': 'Sun', 'hovertemplate': '<b>Sol</b><br>Distance: 0 ly<extra></extra>'
    })
    for hostname, data in systems.items():
        x, y, z = get_star_coords(hostname, data.get('distance'))
        score = data['best_score']
        color = '#7cb97c' if score >= 70 else '#00d4ff' if score >= 50 else '#d4a574' if score >= 30 else '#e07878'
        size  = 6 + data['planet_count'] * 2
        traces.append({
            'type': 'scatter3d', 'x': [x], 'y': [y], 'z': [z],
            'mode': 'markers+text',
            'marker': {'size': size, 'color': color, 'opacity': 0.9,
                       'line': {'width': 1, 'color': 'white'}},
            'text': [hostname], 'textposition': 'top center',
            'textfont': {'size': 9, 'color': 'white'},
            'name': hostname,
            'hovertemplate': f'<b>{hostname}</b><br>Distance: {data.get("distance", 0) or 0:.1f} ly<br>Planets: {data["planet_count"]}<br>Best: {score}/100<extra></extra>'
        })
    layout = {
        'scene': {
            'xaxis': {'title': 'X (ly)', 'gridcolor': 'rgba(255,255,255,0.08)', 'backgroundcolor': 'rgba(0,0,0,0)', 'showbackground': False},
            'yaxis': {'title': 'Y (ly)', 'gridcolor': 'rgba(255,255,255,0.08)', 'backgroundcolor': 'rgba(0,0,0,0)', 'showbackground': False},
            'zaxis': {'title': 'Z (ly)', 'gridcolor': 'rgba(255,255,255,0.08)', 'backgroundcolor': 'rgba(0,0,0,0)', 'showbackground': False},
            'bgcolor': 'rgba(0,0,0,0)',
        },
        'paper_bgcolor': 'rgba(0,0,0,0)', 'plot_bgcolor': 'rgba(0,0,0,0)',
        'showlegend': False, 'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0}, 'height': 480,
        'font': {'color': 'white'}
    }
    return {'data': traces, 'layout': layout}

def build_system_data(planets, star, selected_idx=0):
    import numpy as np
    traces = []
    teff = star.get('teff', 5778)
    star_color = ('#aaccff' if teff > 7000 else '#ffffaa' if teff > 6000 else
                  '#ffdd66' if teff > 5000 else '#ffaa44' if teff > 4000 else '#ff6644')
    traces.append({
        'type': 'scatter3d', 'x': [0], 'y': [0], 'z': [0],
        'mode': 'markers',
        'marker': {'size': 18, 'color': star_color, 'opacity': 0.95, 'line': {'width': 2, 'color': 'white'}},
        'name': star.get('name', 'Star'),
        'hovertemplate': f'<b>{star.get("name", "Host Star")}</b><br>T: {teff} K<extra></extra>'
    })
    if planets:
        hz_inner = planets[0].get('hz_inner', 0.75)
        hz_outer = planets[0].get('hz_outer', 1.77)
        # Build filled annular habitable-zone band using mesh3d
        N = 72  # segments for smooth ring
        theta = [i * 2 * math.pi / N for i in range(N)]
        # Vertices: inner ring (0..N-1) then outer ring (N..2N-1)
        vx = [hz_inner * math.cos(t) for t in theta] + [hz_outer * math.cos(t) for t in theta]
        vy = [hz_inner * math.sin(t) for t in theta] + [hz_outer * math.sin(t) for t in theta]
        vz = [0] * (2 * N)
        # Triangulate two triangles per segment forming the annular quad strip
        ii, jj, kk = [], [], []
        for s in range(N):
            s1 = (s + 1) % N
            # Triangle 1: inner[s], inner[s+1], outer[s]
            ii.append(s);  jj.append(s1);      kk.append(s + N)
            # Triangle 2: inner[s+1], outer[s+1], outer[s]
            ii.append(s1); jj.append(s1 + N);  kk.append(s + N)
        traces.append({
            'type': 'mesh3d',
            'x': vx, 'y': vy, 'z': vz,
            'i': ii, 'j': jj, 'k': kk,
            'color': 'rgba(74,222,128,0.18)',
            'opacity': 0.45,
            'flatshading': True,
            'showlegend': False,
            'hoverinfo': 'skip',
            'lighting': {'ambient': 1, 'diffuse': 0, 'specular': 0},
        })
        # Thin border lines for clarity
        border_theta = theta + [theta[0]]
        traces.append({'type': 'scatter3d',
            'x': [hz_inner * math.cos(t) for t in border_theta],
            'y': [hz_inner * math.sin(t) for t in border_theta],
            'z': [0] * len(border_theta), 'mode': 'lines',
            'line': {'color': 'rgba(74,222,128,0.5)', 'width': 1},
            'showlegend': False, 'hoverinfo': 'skip'})
        traces.append({'type': 'scatter3d',
            'x': [hz_outer * math.cos(t) for t in border_theta],
            'y': [hz_outer * math.sin(t) for t in border_theta],
            'z': [0] * len(border_theta), 'mode': 'lines',
            'line': {'color': 'rgba(74,222,128,0.5)', 'width': 1},
            'showlegend': False, 'hoverinfo': 'skip'})
    for i, p in enumerate(planets):
        orbit = p.get('orbit', 1.0)
        random.seed(hash(p['name']))
        angle = random.uniform(0, 2 * math.pi)
        px = orbit * math.cos(angle)
        py = orbit * math.sin(angle)
        pz = random.uniform(-0.05, 0.05) * orbit
        size = min(14, max(5, p['radius'] * 4))
        color = ('#7cb97c' if p['hab_score'] >= 70 else '#00d4ff' if p['hab_score'] >= 50 else '#d4a574' if p['hab_score'] >= 30 else '#e07878')
        is_sel = (i == selected_idx)
        orbit_theta = [j * 2 * math.pi / 100 for j in range(101)]
        traces.append({'type': 'scatter3d',
            'x': [orbit * math.cos(t) for t in orbit_theta],
            'y': [orbit * math.sin(t) for t in orbit_theta],
            'z': [0]*101, 'mode': 'lines',
            'line': {'color': 'rgba(255,255,255,0.12)', 'width': 1},
            'showlegend': False, 'hoverinfo': 'skip'})
        traces.append({
            'type': 'scatter3d', 'x': [px], 'y': [py], 'z': [pz],
            'mode': 'markers+text',
            'marker': {'size': size * (1.5 if is_sel else 1), 'color': color,
                       'opacity': 1 if is_sel else 0.8,
                       'line': {'width': 3 if is_sel else 1, 'color': 'white'}},
            'text': [p['emoji'] if is_sel else ''], 'textposition': 'top center',
            'textfont': {'size': 18}, 'name': p['name'],
            'hovertemplate': f'<b>{p["name"]}</b><br>Type: {p["type"]}<br>Orbit: {orbit:.3f} AU<br>Score: {p["hab_score"]}/100<extra></extra>'
        })
    max_orbit = max((p.get('orbit', 1) for p in planets), default=2)
    ax_range = max_orbit * 1.5
    layout = {
        'scene': {
            'xaxis': {'range': [-ax_range, ax_range], 'showticklabels': False, 'showgrid': False, 'zeroline': False, 'showbackground': False},
            'yaxis': {'range': [-ax_range, ax_range], 'showticklabels': False, 'showgrid': False, 'zeroline': False, 'showbackground': False},
            'zaxis': {'range': [-ax_range/3, ax_range/3], 'showticklabels': False, 'showgrid': False, 'zeroline': False, 'showbackground': False},
            'bgcolor': 'rgba(0,0,0,0)',
            'camera': {'eye': {'x': 0.5, 'y': 1.5, 'z': 0.8}}
        },
        'paper_bgcolor': 'rgba(0,0,0,0)', 'plot_bgcolor': 'rgba(0,0,0,0)',
        'showlegend': False, 'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0}, 'height': 400
    }
    return {'data': traces, 'layout': layout}

def build_radar_data(planets_dict):
    cats = ['ESI', 'Temperature', 'Size', 'Gravity', 'HZ Position']
    colors = ['#d4a574', '#7cb97c', '#00d4ff', '#e07878', '#a78bfa', '#fb923c']
    traces = []
    for idx, (name, data) in enumerate(planets_dict.items()):
        esi_n  = data.get('esi', 0)
        temp_n = max(0, min(1, 1 - abs(data.get('temp', 288) - 288) / 200))
        size_n = max(0, min(1, 1 - abs(data.get('radius', 1) - 1) / 5))
        grav_n = max(0, min(1, 1 - abs(data.get('gravity', 1) - 1) / 2))
        hz_n   = 1 if data.get('in_hz', False) else 0.3
        vals   = [esi_n, temp_n, size_n, grav_n, hz_n, esi_n]
        color  = colors[idx % len(colors)]
        traces.append({
            'type': 'scatterpolar', 'r': vals, 'theta': cats + [cats[0]],
            'fill': 'toself', 'name': name, 'opacity': 0.7,
            'line': {'color': color, 'width': 2},
            'fillcolor': color.replace(')', ', 0.15)').replace('rgb', 'rgba') if 'rgb' in color else color + '26'
        })
    layout = {
        'polar': {
            'bgcolor': 'rgba(0,0,0,0)',
            'radialaxis': {'visible': True, 'range': [0, 1], 'tickfont': {'color': 'rgba(255,255,255,0.5)'}, 'gridcolor': 'rgba(255,255,255,0.1)'},
            'angularaxis': {'tickfont': {'color': 'white', 'size': 12}, 'gridcolor': 'rgba(255,255,255,0.1)'}
        },
        'paper_bgcolor': 'rgba(0,0,0,0)', 'plot_bgcolor': 'rgba(0,0,0,0)',
        'showlegend': True,
        'legend': {'font': {'color': 'white'}, 'bgcolor': 'rgba(0,0,0,0)'},
        'margin': {'l': 60, 'r': 60, 't': 40, 'b': 40}, 'height': 380
    }
    return {'data': traces, 'layout': layout}

def build_bar_data(planets_dict):
    names  = list(planets_dict.keys())
    colors = ['#d4a574', '#7cb97c', '#00d4ff', '#e07878']
    metrics = {
        'ESI':            [d.get('esi', 0) for d in planets_dict.values()],
        'Hab Score':      [d.get('hab_score', 0) / 100 for d in planets_dict.values()],
        'Gravity (norm)': [min(3, d.get('gravity', 1)) / 3 for d in planets_dict.values()],
        'Radius (norm)':  [min(5, d.get('radius', 1)) / 5 for d in planets_dict.values()],
    }
    traces = []
    for i, (metric, vals) in enumerate(metrics.items()):
        traces.append({
            'type': 'bar', 'name': metric, 'x': names, 'y': vals,
            'marker': {'color': colors[i], 'opacity': 0.85}
        })
    layout = {
        'barmode': 'group',
        'paper_bgcolor': 'rgba(0,0,0,0)', 'plot_bgcolor': 'rgba(0,0,0,0)',
        'xaxis': {'tickfont': {'color': 'white'}, 'gridcolor': 'rgba(255,255,255,0.08)'},
        'yaxis': {'tickfont': {'color': 'white'}, 'gridcolor': 'rgba(255,255,255,0.08)',
                  'title': {'text': 'Normalized Value', 'font': {'color': 'rgba(255,255,255,0.6)'}}},
        'legend': {'font': {'color': 'white'}, 'bgcolor': 'rgba(0,0,0,0)'},
        'margin': {'l': 40, 'r': 20, 't': 30, 'b': 40}, 'height': 340,
        'font': {'color': 'white'}
    }
    return {'data': traces, 'layout': layout}

def build_score_histogram(all_planets):
    scores = [p['hab_score'] for p in all_planets]
    layout = {
        'paper_bgcolor': 'rgba(0,0,0,0)', 'plot_bgcolor': 'rgba(0,0,0,0)',
        'xaxis': {'title': {'text': 'Habitability Score', 'font': {'color': 'rgba(255,255,255,0.6)'}},
                  'tickfont': {'color': 'white'}, 'gridcolor': 'rgba(255,255,255,0.08)', 'range': [0, 100]},
        'yaxis': {'title': {'text': 'Count', 'font': {'color': 'rgba(255,255,255,0.6)'}},
                  'tickfont': {'color': 'white'}, 'gridcolor': 'rgba(255,255,255,0.08)'},
        'margin': {'l': 40, 'r': 20, 't': 30, 'b': 40}, 'height': 280,
        'shapes': [
            {'type': 'line', 'x0': 70, 'x1': 70, 'y0': 0, 'y1': 1, 'yref': 'paper',
             'line': {'color': '#7cb97c', 'width': 2, 'dash': 'dot'}},
            {'type': 'line', 'x0': 50, 'x1': 50, 'y0': 0, 'y1': 1, 'yref': 'paper',
             'line': {'color': '#00d4ff', 'width': 2, 'dash': 'dot'}},
        ],
        'font': {'color': 'white'}
    }
    return {
        'data': [{'type': 'histogram', 'x': scores, 'nbinsx': 20,
                  'marker': {'color': 'rgba(212,165,116,0.65)', 'line': {'color': '#d4a574', 'width': 1}}}],
        'layout': layout
    }

# ── Chat handler ──────────────────────────────────────────────────────────────

KEYWORD_RESPONSES = {
    ('habitable', 'life', 'live', 'water'): (
        "Habitability depends on temperature (250–310 K), size (0.8–1.5 R⊕), "
        "atmosphere composition (N₂/O₂ ideal), and stellar stability. "
        "The best candidates orbit G or K-type stars within the Habitable Zone."
    ),
    ('trappist',): (
        "TRAPPIST-1 hosts 7 known planets with at least 3 in the habitable zone "
        "(TRAPPIST-1e, f, g). It's only 40.7 light-years away — a prime target for JWST atmospheric studies!"
    ),
    ('proxima',): (
        "Proxima Centauri b is the closest known potentially habitable exoplanet at just 4.24 ly. "
        "However, its M-dwarf host frequently emits powerful flares, threatening its atmosphere."
    ),
    ('kepler', 'tess', 'jwst', 'mission'): (
        "Key missions: Kepler found 2,700+ planets (2009–2018), TESS is surveying bright nearby stars, "
        "and JWST is now doing unprecedented atmospheric spectroscopy of exoplanets!"
    ),
    ('esi', 'earth similarity', 'earth-like'): (
        "The Earth Similarity Index (ESI) ranges 0–1 based on radius and temperature. "
        "ESI > 0.8 indicates an Earth-type candidate. Kepler-442b holds one of the highest ESIs at ~0.84."
    ),
    ('esi', 'index'): (
        "ESI = √[(1 - |R-1|/(R+1))^0.57 × (1 - |T-288|/(T+288))^5.58]. Scores above 0.8 are prime candidates."
    ),
    ('habitable zone', 'hz', 'goldilocks'): (
        "The Habitable Zone (HZ) is the circumstellar region where liquid water can exist on a planet's surface. "
        "It ranges from ~0.75√L to ~1.77√L AU, where L is stellar luminosity."
    ),
    ('atmosphere', 'gas'): (
        "Atmospheres are crucial for habitability. N₂/O₂ (like Earth) is the gold standard. "
        "CO₂ can cause runaway greenhouse. H₂/He suggests a gas giant. "
        "We detect atmospheres via transmission spectroscopy during transits."
    ),
    ('detect', 'find', 'discover'): (
        "Main detection methods: Transit (planet dims star's light), Radial Velocity (star wobbles), "
        "Direct Imaging (JWST), Microlensing (gravity bends light), Astrometry (Gaia). "
        "Transit is most common — used by Kepler and TESS."
    ),
}

_gemini_cache = {}

def call_gemini(contents, system_text, max_tokens=350):
    """Пробует модели по очереди; кэширует ответы по тексту последнего сообщения."""
    last_msg = contents[-1]['parts'][0]['text'] if contents else ''
    cache_key = last_msg[:200]
    if cache_key in _gemini_cache:
        return _gemini_cache[cache_key]

    body = {
        'systemInstruction': {'parts': [{'text': system_text}]},
        'contents': contents,
        'generationConfig': {
            'maxOutputTokens': max_tokens,
            'temperature': 0.7,
            'topP': 0.9,
        }
    }

    for model in GEMINI_MODELS:
        url = GEMINI_BASE + model + ':generateContent?key=' + GEMINI_API_KEY
        try:
            resp = requests.post(url, json=body, timeout=15)
            if resp.ok:
                text = resp.json()['candidates'][0]['content']['parts'][0]['text'].strip()
                _gemini_cache[cache_key] = text
                print(f'[Gemini] OK via {model}')
                return text
            elif resp.status_code == 429:
                print(f'[Gemini] {model} → 429 quota, trying next...')
                continue
            elif resp.status_code == 503:
                print(f'[Gemini] {model} → 503 overloaded, trying next...')
                continue
            else:
                print(f'[Gemini] {model} → HTTP {resp.status_code}: {resp.text[:200]}')
                continue
        except Exception as e:
            print(f'[Gemini] {model} → Exception: {e}')
            continue

    return None


LAIKA_SYSTEM = {
    'en': (
        'You are Laika — the legendary Soviet space dog (launched 1957) and the beloved mascot of the ATLAS '
        'exoplanet research platform. You are enthusiastic, warm, and occasionally use dog expressions like '
        '"Woof!", "Arf!", "*wags tail*", "*sniffs excitedly*". '
        'You are also a knowledgeable space expert. The ATLAS platform has these sections: '
        'Home (stats, quotes), Explore (scan star systems, view planets with ESI scores, compare, AI travel, chat, encyclopedia), '
        'Analysis (habitability charts, AI recommendations), Star Map (3D stellar map), About. '
        'You know real exoplanets deeply: TRAPPIST-1 system, Kepler-442b (ESI 0.84), Proxima Centauri b (4.24 ly), '
        'K2-18b (water vapor!), LHS 1140b, TOI-700d and hundreds more. '
        'Be helpful, fun, and concise (2-4 sentences). Reply in English.'
    ),
    'kz': (
        'Сіз — Лайка, аңызға айналған Кеңестік ғарыш иті (1957 жылы ұшырылды) және ATLAS платформасының сүйікті талисманы. '
        'Сіз жылы жүректі, қызғыштай жанасасыз және кейде "Хав!", "Арф!", "*құйрығын бұлғайды*" деп айтасыз. '
        'Сіз ғарыш сарапшысысыз және ATLAS платформасы туралы бәрін білесіз. '
        'Пайдалы, қызықты және қысқа болыңыз (2-4 сөйлем). Қазақша жауап беріңіз.'
    ),
}


def get_chat_response(message, lang='en', history=None, laika=False):
    msg_lower = message.lower()

    if not laika:
        # 1) Keyword shortcuts — 0 токенов
        for keywords, response in KEYWORD_RESPONSES.items():
            if any(kw in msg_lower for kw in keywords):
                return response, 'keyword'

    # 2) Gemini — строим контекст из последних 4 сообщений + текущее
    if GEMINI_API_KEY:
        lang_note = 'Отвечай на казахском.' if lang == 'kz' else 'Reply in English.'
        if laika:
            system = LAIKA_SYSTEM.get(lang, LAIKA_SYSTEM['en'])
        else:
            system = (
                'You are ATLAS (Autonomous Terrestrial Life Analysis System) — the built-in AI assistant '
                'of the ATLAS exoplanet research platform (a diploma project web app). '
                'The site has these sections:\n'
                '• Home — overview, stats (systems scanned, habitable planets found), inspirational quotes\n'
                '• Explore — scan star systems from catalogs (Nearby Stars, Kepler, TESS, K2, GJ), '
                'view planets with habitability scores (ESI), compare planets, AI travel narratives, '
                'interactive chat with you, mission log, encyclopedia\n'
                '• Analysis — charts (habitability histogram, ESI distribution), AI recommendations, '
                'hypotheses, and mission intelligence reports\n'
                '• Star Map — 3D interactive map of nearby star systems\n'
                '• About — project info\n'
                'Key features: multilingual (EN/KZ), achievement system, planet comparison, '
                'AI-generated planet profiles, exoplanet encyclopedia, interstellar travel calculator.\n'
                'You know all the site\'s functionality and can guide users through it. '
                'You also have deep knowledge of real exoplanets: TRAPPIST-1, Kepler-442b, Proxima Centauri b, '
                'Kepler-452b, LHS 1140b, K2-18b, TOI-700d and others. '
                'Give precise, helpful answers. Be concise (2-4 sentences). '
                f'{lang_note}'
            )
        contents = []
        # Добавляем только последние 4 сообщения истории (экономия токенов)
        if history:
            for h in history[-4:]:
                role = 'model' if h['role'] == 'assistant' else 'user'
                contents.append({'role': role, 'parts': [{'text': h['content'][:300]}]})
        contents.append({'role': 'user', 'parts': [{'text': message[:400]}]})
        result = call_gemini(contents, system, max_tokens=350)
        if result:
            return result, 'gemini'

    # 3) Topic-aware fallback (no AI available)
    fb = _topic_fallback(msg_lower, lang, laika)
    return fb, 'fallback'


_FALLBACKS = {
    ('habitable', 'habitability', 'life', 'тіршілік', 'жарамды'): {
        'en': "A habitable planet needs liquid water, temperatures between ~200–350 K, and a rocky surface with gravity similar to Earth. The ESI (Earth Similarity Index) score here rates planets from 0–1 based on radius, temperature, and density. Higher scores mean Earth-like conditions are more likely.",
        'kz': "Тіршілікке жарамды планетада сұйық су, шамамен 200–350 К температура және Жерге ұқсас ауырлық күші болуы керек. ESI (Жер ұқсастық индексі) ұпайы планетаның Жерге ұқсастығын 0–1 шкаласымен бағалайды.",
    },
    ('esi', 'earth similarity', 'жер ұқсастық'): {
        'en': "ESI (Earth Similarity Index) measures how Earth-like a planet is, on a scale of 0 to 1. It's calculated from radius, density, escape velocity, and surface temperature. Earth scores 1.0; Mars scores 0.64; most exoplanets score below 0.5.",
        'kz': "ESI (Жер ұқсастық индексі) планетаның Жерге қаншалықты ұқсас екенін 0-ден 1-ге дейін өлшейді. Ол радиус, тығыздық, шығу жылдамдығы және беттік температурадан есептеледі.",
    },
    ('trappist', 'kepler', 'proxima', 'tess', 'k2', 'gj', 'lhs', 'toi'): {
        'en': "TRAPPIST-1 hosts 7 Earth-sized planets with 3 in the habitable zone (40 ly away). Kepler-442b has ESI 0.84 — one of the most Earth-like. Proxima Centauri b is the nearest exoplanet at 4.24 ly. Use the Explore tab to scan any of these systems!",
        'kz': "TRAPPIST-1 жүйесінде 7 Жер мөлшеріндегі планета бар, 3-і тіршілік аймағында (40 жарық жыл). Kepler-442b ESI 0.84 — ең Жерге ұқсасының бірі. Proxima Centauri b — ең жақын экзопланета, 4.24 жарық жыл.",
    },
    ('habitable zone', 'hz', 'goldilocks', 'тіршілік аймақ'): {
        'en': "The habitable zone (HZ) is the orbital range around a star where liquid water can exist on a planet's surface — sometimes called the 'Goldilocks zone'. Its boundaries depend on the star's temperature and luminosity. ATLAS marks HZ planets with a green badge.",
        'kz': "Тіршілік аймағы — жұлдыз айналасындағы сұйық су планета бетінде болуы мүмкін орбиталық аралық. Оның шекаралары жұлдыздың температурасы мен жарықтылығына байланысты.",
    },
    ('scan', 'сканер', 'mission', 'миссия', 'discover', 'табу'): {
        'en': "To scan a star system: go to the Explore tab → Missions panel → pick a catalog (Nearby Stars, Kepler, TESS…) → click 'Scan System'. ATLAS will autonomously query NASA's Exoplanet Archive and analyze all planets in that system.",
        'kz': "Жұлдыз жүйесін сканерлеу үшін: Зерттеу қосымшасы → Миссиялар → каталог таңдаңыз → 'Жүйені сканерлеу' батырмасын басыңыз. ATLAS NASA мұрағатынан деректерді алып, барлық планеталарды талдайды.",
    },
    ('compare', 'салыстыр'): {
        'en': "Use the Compare tab to compare up to 6 planets side-by-side. Select reference planets (Earth, Mars, Venus) and any discovered planets. ATLAS generates radar and bar charts comparing radius, mass, temperature, ESI, gravity, and habitability score.",
        'kz': "Салыстыру қосымшасын 6 планетаны қатар салыстыру үшін пайдаланыңыз. Анықтамалық планеталарды (Жер, Марс, Шолпан) және табылған планеталарды таңдаңыз.",
    },
    ('atmosphere', 'атмосфер'): {
        'en': "ATLAS predicts atmosphere type from a planet's radius, mass, temperature, and stellar environment. A thick N₂/O₂ atmosphere like Earth's is ideal. Hot or very massive planets may have H₂/He envelopes; cold small ones may have no atmosphere at all.",
        'kz': "ATLAS планетаның радиусы, массасы, температурасы және жұлдыздық ортасынан атмосфера түрін болжайды. Жердегідей қалың N₂/O₂ атмосферасы ең қолайлы.",
    },
}

def _topic_fallback(msg_lower, lang, laika):
    if laika:
        return "Woof! 🐾 I'm having trouble connecting to my space antenna right now. Try asking me again in a moment — I know lots about exoplanets, TRAPPIST-1, and the cosmos!"
    for keywords, responses in _FALLBACKS.items():
        if any(kw in msg_lower for kw in keywords):
            return responses.get(lang, responses['en'])
    if lang == 'kz':
        return "ATLAS ЖИ қазіргі уақытта қол жетімді емес. Экзопланеталар, тіршілікке жарамдылық, ESI немесе миссиялар туралы сұрақ қойыңыз!"
    return "ATLAS AI is temporarily unavailable. Ask me about exoplanets, habitability scores, the ESI index, star systems, or how to use the Explore tab!"

# ── Page routes ───────────────────────────────────────────────────────────────

@app.route('/')
def home():
    s    = get_state()
    lang = request.args.get('lang', s.get('lang', 'en'))
    s['lang'] = lang
    stats = {
        'systems':  len(s['systems']),
        'habitable': s['habitable_count'],
        'planets':  sum(v['planet_count'] for v in s['systems'].values())
    }
    q_idx = s.get('quote_index', 0) % len(QUOTES)
    if request.args.get('next_quote'):
        q_idx = (q_idx + 1) % len(QUOTES)
        s['quote_index'] = q_idx
    if request.args.get('prev_quote'):
        q_idx = (q_idx - 1) % len(QUOTES)
        s['quote_index'] = q_idx
    quote = QUOTES[q_idx]
    return render_template('home.html', stats=stats, quote=quote, lang=lang,
                           quote_index=q_idx, quote_total=len(QUOTES))

@app.route('/explore')
def explore():
    s    = get_state()
    lang = request.args.get('lang', s.get('lang', 'en'))
    s['lang'] = lang
    tab  = request.args.get('tab', 'missions')
    return render_template('explore.html',
        lang=lang, tab=tab,
        catalogs=CATALOGS,
        systems=s['systems'],
        scanned=s['scanned'],
        current_system=s.get('current_system'),
        current_planets=s.get('current_planets', []),
        current_star=s.get('current_star'),
        selected_planet=s.get('selected_planet', 0),
        mission_log=s['log'][-10:],
        known_planets=KNOWN_PLANETS,
        custom_planets=s['custom_planets'],
        compare=s['compare'],
        chat_history=s['chat'][-20:],
        chatbot_available=CHATBOT_AVAILABLE,
    )

@app.route('/analysis')
def analysis():
    s    = get_state()
    lang = request.args.get('lang', s.get('lang', 'en'))
    s['lang'] = lang
    all_p    = get_all_planets()
    has_data = bool(s['systems'])
    scores   = [p['hab_score'] for p in all_p]

    summary = {
        'total_systems':   len(s['systems']),
        'total_planets':   len(all_p),
        'habitable_count': sum(1 for p in all_p if p['in_hz']),
        'avg_score':       round(sum(scores) / len(scores), 1) if scores else 0,
    }

    sorted_p   = sorted(all_p, key=lambda x: x['hab_score'], reverse=True)
    top_planets = [
        {'name': p['name'], 'system': p.get('hostname', '—'), 'score': p['hab_score']}
        for p in sorted_p[:8]
    ]

    recs = []
    if has_data:
        for r in generate_recommendations():
            priority = 'high' if '🎯' in r.get('title', '') else 'medium'
            body = r.get('title', '') + ' — ' + r.get('action', '')
            recs.append({'priority': priority, 'text': {'en': body, 'kz': body}})

    hyps = []
    if has_data:
        for h in generate_hypotheses():
            desc = h.get('hypothesis', '') + ' ' + h.get('analysis', '')
            hyps.append({
                'title':       {'en': h.get('title', ''), 'kz': h.get('title', '')},
                'description': {'en': desc, 'kz': desc},
                'confidence':  0.75,
            })

    score_hist_data = build_score_histogram(all_p) if all_p else {'data': [], 'layout': {}}

    return render_template('analysis.html', lang=lang,
        has_data=has_data,
        summary=summary,
        systems=s['systems'],
        top_planets=top_planets,
        recommendations=recs,
        hypotheses=hyps,
        score_hist_data=score_hist_data,
    )

@app.route('/encyclopedia')
def encyclopedia():
    s    = get_state()
    lang = request.args.get('lang', s.get('lang', 'en'))
    s['lang'] = lang

    topics = []
    for tid, td in ENCYCLOPEDIA.items():
        title_en = td['title']['en']
        title_kz = td['title']['kz']
        parts_en = title_en.split(' ', 1)
        parts_kz = title_kz.split(' ', 1)
        icon     = parts_en[0] if len(parts_en[0]) <= 3 else '📖'
        topics.append({
            'id':       tid,
            'icon':     icon,
            'title':    {
                'en': parts_en[1] if len(parts_en) > 1 else title_en,
                'kz': parts_kz[1] if len(parts_kz) > 1 else title_kz,
            },
            'content':  td.get('content', {}),   # raw markdown, rendered client-side
            'formula':      td.get('formula'),
            'formula_desc': td.get('formula_desc'),
            'parameters':   td.get('parameters', []),
            'examples':     td.get('examples', []),
        })

    return render_template('encyclopedia.html', lang=lang, topics=topics)

@app.route('/about')
def about():
    s    = get_state()
    lang = request.args.get('lang', s.get('lang', 'en'))
    s['lang'] = lang
    all_p = get_all_planets()

    achievements_list = [
        {
            'id':          aid,
            'name':        ad['name'],
            'description': ad['desc'],
            'icon':        ad['icon'],
            'unlocked':    aid in s['achievements'],
        }
        for aid, ad in ACHIEVEMENTS.items()
    ]

    stats = {
        'systems':    len(s['systems']),
        'planets':    len(all_p),
        'habitable':  s['habitable_count'],
        'chat_count': len(s['chat']),
    }

    return render_template('about.html', lang=lang,
        achievements=achievements_list,
        stats=stats,
    )

# ── API routes ────────────────────────────────────────────────────────────────

@app.route('/api/scan', methods=['POST'])
def api_scan():
    data      = request.get_json()
    star_name = data.get('star_name', '').strip()
    if not star_name:
        return jsonify({'error': 'No star name provided'}), 400

    raw = fetch_nasa_data(star_name)
    if not raw:
        return jsonify({'error': f'No data found for "{star_name}"'}), 404

    first = raw[0]
    star_data = {
        'name':     first.get('hostname', star_name),
        'teff':     first.get('st_teff')  or 5778,
        'radius':   first.get('st_rad')   or 1.0,
        'mass':     first.get('st_mass')  or 1.0,
        'distance': first.get('sy_dist'),
    }
    planets = [process_planet_data(p, star_data) for p in raw]

    s = get_state()
    hostname = star_data['name']
    best_score = max(p['hab_score'] for p in planets)
    hab_count  = sum(1 for p in planets if p['in_hz'])
    s['systems'][hostname] = {
        'star':          star_data,
        'planets':       planets,
        'planet_count':  len(planets),
        'best_score':    best_score,
        'habitable_count': hab_count,
        'distance':      star_data.get('distance'),
        'timestamp':     datetime.now().strftime('%Y-%m-%d %H:%M'),
    }
    s['habitable_count'] += hab_count
    if star_name not in s['scanned']:
        s['scanned'].append(star_name)
    if hostname not in s['scanned']:
        s['scanned'].append(hostname)
    s['current_system']  = hostname
    s['current_planets'] = planets
    s['current_star']    = star_data
    s['selected_planet'] = 0
    s['log'].append({
        'time':   datetime.now().strftime('%H:%M:%S'),
        'action': f'Scanned {star_name}',
        'result': f'{len(planets)} planets found',
        'score':  best_score,
    })

    new_achs = check_achievements_after_scan(planets)
    return jsonify({
        'success':   True,
        'hostname':  hostname,
        'star':      star_data,
        'planets':   planets,
        'new_achievements': new_achs,
        'stats': {
            'systems':  len(s['systems']),
            'habitable': s['habitable_count'],
            'planets':  sum(v['planet_count'] for v in s['systems'].values()),
        }
    })

@app.route('/api/select-planet', methods=['POST'])
def api_select_planet():
    data = request.get_json()
    idx  = data.get('index', 0)
    s    = get_state()
    s['selected_planet'] = idx
    # Возвращаем данные выбранной планеты для AI отчёта
    planets = s.get('current_planets', [])
    planet  = planets[idx] if 0 <= idx < len(planets) else None
    return jsonify({'success': True, 'planet': planet})

@app.route('/api/load-system', methods=['POST'])
def api_load_system():
    data     = request.get_json()
    hostname = data.get('hostname', '')
    s        = get_state()
    if hostname in s['systems']:
        sys_data = s['systems'][hostname]
        s['current_system']  = hostname
        s['current_planets'] = sys_data['planets']
        s['current_star']    = sys_data['star']
        s['selected_planet'] = 0
        return jsonify({'success': True, 'star': sys_data['star'], 'planets': sys_data['planets']})
    return jsonify({'error': 'System not found'}), 404

@app.route('/api/state')
def api_state():
    s = get_state()
    return jsonify({
        'systems':  len(s['systems']),
        'habitable': s['habitable_count'],
        'planets':  sum(v['planet_count'] for v in s['systems'].values()),
        'scanned':  s['scanned'],
        'achievements': list(s['achievements'].keys()),
    })

@app.route('/api/catalogs')
def api_catalogs():
    return jsonify(CATALOGS)

@app.route('/api/chart/starmap', methods=['POST'])
def api_chart_starmap():
    systems = get_state()['systems']
    return jsonify(build_starmap_data(systems))

@app.route('/api/chart/system', methods=['POST'])
def api_chart_system():
    data = request.get_json()
    s    = get_state()
    planets  = data.get('planets') or s.get('current_planets', [])
    star     = data.get('star')    or s.get('current_star', {})
    selected = data.get('selected_idx', s.get('selected_planet', 0))
    return jsonify(build_system_data(planets, star, selected))

@app.route('/api/chart/compare', methods=['POST'])
def api_chart_compare():
    data         = request.get_json()
    planets_dict = data.get('planets', {})
    chart_type   = data.get('type', 'radar')
    if chart_type == 'bar':
        return jsonify(build_bar_data(planets_dict))
    return jsonify(build_radar_data(planets_dict))

@app.route('/api/chart/scores', methods=['POST'])
def api_chart_scores():
    all_p = get_all_planets()
    return jsonify(build_score_histogram(all_p))

@app.route('/api/analysis', methods=['POST'])
def api_analysis():
    s    = get_state()
    recs = generate_recommendations()
    hyps = generate_hypotheses()
    return jsonify({'recommendations': recs, 'hypotheses': hyps})

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data    = request.get_json()
    message = data.get('message', '').strip()
    lang    = data.get('lang', 'en')
    laika   = bool(data.get('laika', False))
    if not message:
        return jsonify({'error': 'No message'}), 400
    s = get_state()
    history_key = 'laika_chat' if laika else 'chat'
    if history_key not in s:
        s[history_key] = []
    response, source = get_chat_response(message, lang, history=s[history_key][-4:], laika=laika)
    s[history_key].append({'role': 'user',      'content': message})
    s[history_key].append({'role': 'assistant', 'content': response})
    if not laika and len(s['chat']) >= 20:
        check_achievement(get_uid(), 'chat_10')
    return jsonify({'response': response, 'source': source})

@app.route('/api/add-compare', methods=['POST'])
def api_add_compare():
    data = request.get_json()
    name = data.get('name')
    s    = get_state()
    if name not in s['compare']:
        s['compare'].append(name)
    planet = data.get('planet_data')
    if planet:
        s['custom_planets'][name] = planet
    if len(s['compare']) >= 3:
        check_achievement(get_uid(), 'compare_3')
    return jsonify({'success': True, 'compare': s['compare']})

@app.route('/api/clear-compare', methods=['POST'])
def api_clear_compare():
    s = get_state()
    s['compare'] = []
    return jsonify({'success': True})

@app.route('/api/travel', methods=['POST'])
def api_travel():
    data       = request.get_json()
    distance   = float(data.get('distance', 4.24))
    velocity_p = float(data.get('velocity_pct', 20))
    velocity_c = velocity_p / 100
    check_achievement(get_uid(), 'traveler')

    lorentz    = 1 / math.sqrt(1 - velocity_c ** 2)
    earth_time = distance / velocity_c
    ship_time  = earth_time / lorentz
    fuel_kg    = distance * (velocity_c ** 2) * 100

    return jsonify({
        'earth_time': round(earth_time, 1),
        'ship_time':  round(ship_time, 1),
        'lorentz':    round(lorentz, 4),
        'fuel_kg':    round(fuel_kg, 0),
        'velocity_c': round(velocity_c, 4),
        'distance':   distance,
        'phases': {
            'accel':  round(velocity_p * 0.5, 1),
            'cruise': round(earth_time - velocity_p, 1),
            'decel':  round(velocity_p * 0.5, 1),
        }
    })

@app.route('/api/delete-system', methods=['POST'])
def api_delete_system():
    data     = request.get_json()
    hostname = data.get('hostname')
    s        = get_state()
    if hostname in s['systems']:
        del s['systems'][hostname]
    return jsonify({'success': True})

# ── AI Analysis helpers ───────────────────────────────────────────────────────

def generate_fallback_analysis(all_p, state, lang):
    """Smart rule-based analysis generator — used when no Groq key is set."""
    total    = len(all_p)
    systems  = len(state['systems'])
    hz_p     = [p for p in all_p if p['in_hz']]
    top      = sorted(all_p, key=lambda x: x['hab_score'], reverse=True)
    best     = top[0] if top else None
    avg_esi  = sum(p['esi'] for p in all_p) / total if total else 0
    avg_temp = sum(p['temp'] for p in all_p) / total if total else 0

    if lang == 'kz':
        intro = (f"ATLAS барлаулық жүйесі {systems} жұлдыз жүйесін сканерлеп, "
                 f"жалпы {total} планетаны каталогтады.")
        hz_part = (f"{len(hz_p)} планета тіршілік аймағында орналасқан, "
                   f"бұл жалпы үлгінің {len(hz_p)/total*100:.1f}%-ын құрайды." if hz_p else
                   "Ешбір планета тіршілік аймағына сәйкес келмеді.")
        best_part = (f"Ең жоғары тіршілік ұпайы: {best['name']} — {best['hab_score']}/100 "
                     f"(ESI: {best['esi']:.2f}, температура: {best['temp']:.0f} K, тип: {best['type']})." if best else "")
        climate = (f"Барлық планеталардың орташа температурасы {avg_temp:.0f} K, "
                   f"орташа ESI индексі {avg_esi:.3f} құрайды.")
        conclusion = ("Жинақталған деректер детальды атмосфералық спектроскопия "
                      "зерттеуін жүргізуге жеткілікті. ATLAS миссиясын жалғастыруды ұсынады.")
        return f"{intro}\n\n{hz_part} {best_part}\n\n{climate}\n\n{conclusion}"
    else:
        intro = (f"ATLAS deep-scan intelligence has catalogued {total} planets across "
                 f"{systems} stellar systems, providing a comprehensive snapshot of nearby exoplanet diversity.")
        hz_part = (f"{len(hz_p)} planet{'s' if len(hz_p)!=1 else ''} reside within the habitable zone — "
                   f"{len(hz_p)/total*100:.1f}% of the surveyed sample, exceeding the galactic average." if hz_p else
                   "No planets fell within the habitable zone boundaries of their host stars.")
        best_part = (f"The prime candidate is {best['name']} with a habitability score of "
                     f"{best['hab_score']}/100 (ESI {best['esi']:.2f}, surface temperature {best['temp']:.0f} K, "
                     f"classified as {best['type']})." if best else "")
        climate = (f"Across the full sample, the mean planetary temperature stands at {avg_temp:.0f} K "
                   f"with an average Earth Similarity Index of {avg_esi:.3f} — "
                   f"{'encouraging for further study' if avg_esi > 0.5 else 'indicating predominantly hostile conditions'}.")
        conclusion = ("Recommendation: prioritise spectroscopic atmospheric follow-up on top-ranked "
                      "candidates. ATLAS data density is sufficient for a formal habitability report "
                      "submission to the research committee.")
        return f"{intro}\n\n{hz_part} {best_part}\n\n{climate}\n\n{conclusion}"


@app.route('/api/ai_analysis', methods=['POST'])
def api_ai_analysis():
    s    = get_state()
    body = request.get_json(force=True) or {}
    lang = body.get('lang', 'en')
    all_p = get_all_planets()
    if not all_p:
        return jsonify({'error': 'no_data'}), 400

    top    = sorted(all_p, key=lambda x: x['hab_score'], reverse=True)[:5]
    hz_p   = [p for p in all_p if p['in_hz']]
    avg_hab = sum(p['hab_score'] for p in all_p) / len(all_p)

    # Компактный контекст — экономия токенов
    data_lines = "\n".join(
        f"{p['name']}: {p['hab_score']}% score, ESI {p['esi']:.2f}, {p['temp']:.0f}K, {p['type']}"
        for p in top
    )
    context = (
        f"Scanned: {len(s['systems'])} systems, {len(all_p)} planets, "
        f"{len(hz_p)} in HZ, avg score {avg_hab:.0f}%.\n"
        f"Top 5:\n{data_lines}"
    )

    if GEMINI_API_KEY:
        lang_note = 'Жауапты қазақ тілінде жаз.' if lang == 'kz' else 'Write in English.'
        system = (
            'You are ATLAS — Autonomous Terrestrial Life Analysis System. '
            'Write a scientific mission intelligence report: 3 short paragraphs, ~180 words total. '
            f'Be precise and dramatic. {lang_note}'
        )
        contents = [{'role': 'user', 'parts': [{'text': f'Generate report from this data:\n{context}'}]}]
        result = call_gemini(contents, system, max_tokens=500)
        if result:
            return jsonify({'text': result, 'source': 'gemini'})

    # Fallback — детерминированный генератор
    text = generate_fallback_analysis(all_p, s, lang)
    return jsonify({'text': text, 'source': 'atlas'})


@app.route('/api/ask_gemini', methods=['POST'])
def api_ask_gemini():
    """Универсальный Gemini-эндпоинт: encyclopedia, travel narrative и т.д."""
    body     = request.get_json(force=True) or {}
    question = body.get('question', '').strip()[:600]
    context  = body.get('context', '').strip()[:300]
    lang     = body.get('lang', 'en')
    mode     = body.get('mode', 'default')  # 'encyclopedia' | 'travel' | 'default'
    if not question:
        return jsonify({'error': 'no_question'}), 400

    lang_note = 'Жауапты қазақ тілінде жаз.' if lang == 'kz' else 'Reply in English.'

    if mode == 'encyclopedia':
        system = (
            'You are ATLAS — exoplanet research AI and science educator. '
            'Explain the given topic clearly and engagingly: 2-3 paragraphs, ~180 words. '
            f'Use scientific facts, give real examples (e.g. specific planets/missions). {lang_note}'
        )
        max_tok = 400
    elif mode == 'travel':
        system = (
            'You are ATLAS — exoplanet research AI. '
            'Write a vivid, dramatic narrative (2 paragraphs, ~160 words) describing '
            'what it would actually feel like to arrive at and survive on this destination. '
            f'Mention gravity, atmosphere, temperature, day length, sky color. {lang_note}'
        )
        max_tok = 350
    else:
        system = f'You are ATLAS — exoplanet research AI. Answer concisely. {lang_note}'
        max_tok = 250

    prompt = question if not context else f'{question}\n\nContext: {context}'
    contents = [{'role': 'user', 'parts': [{'text': prompt}]}]
    result = call_gemini(contents, system, max_tokens=max_tok)
    if result:
        return jsonify({'text': result, 'source': 'gemini'})
    return jsonify({'text': '', 'source': 'fallback'})


@app.route('/api/planet_report', methods=['POST'])
def api_planet_report():
    """ИИ-отчёт по конкретной планете — используется в explore при выборе планеты."""
    body = request.get_json(force=True) or {}
    p    = body.get('planet', {})
    lang = body.get('lang', 'en')
    if not p:
        return jsonify({'error': 'no_planet'}), 400

    lang_note = 'Жауапты қазақ тілінде жаз.' if lang == 'kz' else 'Write in English.'
    system = (
        'You are ATLAS — exoplanet research AI. '
        'Write a vivid scientific profile of the given planet: 2-3 paragraphs, ~150 words. '
        f'Cover habitability, atmosphere, risks, and discovery potential. {lang_note}'
    )
    info = (
        f"Planet: {p.get('name', '?')}\n"
        f"Type: {p.get('type', '?')}, Radius: {p.get('radius', '?')} R⊕, Mass: {p.get('mass', '?')} M⊕\n"
        f"Temperature: {p.get('temp', '?')} K, Gravity: {p.get('gravity', '?')} g\n"
        f"ESI: {p.get('esi', '?')}, Hab score: {p.get('hab_score', '?')}%, In HZ: {p.get('in_hz', '?')}\n"
        f"Orbit: {p.get('orbit', '?')} AU, Period: {p.get('period', '?')} days"
    )
    contents = [{'role': 'user', 'parts': [{'text': f'Write a profile for this exoplanet:\n{info}'}]}]
    result = call_gemini(contents, system, max_tokens=300)
    if result:
        return jsonify({'text': result, 'source': 'gemini'})
    return jsonify({'text': 'No AI data available.', 'source': 'fallback'})


@app.route('/api/space_fact', methods=['POST'])
def api_space_fact():
    """Интересный факт о космосе/экзопланетах — для домашней страницы."""
    body = request.get_json(force=True) or {}
    lang = body.get('lang', 'en')
    topic = body.get('topic', '')  # опциональная тема

    lang_note = 'Жауапты қазақ тілінде жаз.' if lang == 'kz' else 'Reply in English.'
    system = (
        'You are ATLAS — exoplanet research AI. '
        'Share one fascinating, surprising space or exoplanet fact. '
        f'2-3 sentences, be dramatic and scientific. {lang_note}'
    )
    prompt = f'Give me a fascinating fact{"about " + topic if topic else " about exoplanets or space exploration"}.'
    contents = [{'role': 'user', 'parts': [{'text': prompt}]}]
    result = call_gemini(contents, system, max_tokens=150)
    if result:
        return jsonify({'text': result, 'source': 'gemini'})
    return jsonify({'text': 'No fact available.', 'source': 'fallback'})


@app.route('/api/catalog_hint', methods=['POST'])
def api_catalog_hint():
    """Короткая подсказка почему стоит сканировать выбранную звезду."""
    body   = request.get_json(force=True) or {}
    star   = body.get('star', '')
    lang   = body.get('lang', 'en')
    if not star:
        return jsonify({'error': 'no_star'}), 400

    lang_note = 'Жауапты қазақ тілінде жаз.' if lang == 'kz' else 'Reply in English.'
    system = (
        f'You are ATLAS. Give a 1-2 sentence scientific reason why {star} '
        f'is an interesting target for exoplanet habitability research. Be specific. {lang_note}'
    )
    contents = [{'role': 'user', 'parts': [{'text': f'Why is {star} worth scanning for habitable planets?'}]}]
    result = call_gemini(contents, system, max_tokens=120)
    if result:
        return jsonify({'text': result, 'source': 'gemini'})
    return jsonify({'text': '', 'source': 'fallback'})


@app.route('/api/generate_share', methods=['POST'])
def api_generate_share():
    s     = get_state()
    lang  = (request.get_json(force=True) or {}).get('lang', 'en')
    all_p = get_all_planets()
    if not all_p:
        return jsonify({'error': 'no_data'}), 400

    top   = sorted(all_p, key=lambda x: x['hab_score'], reverse=True)[:8]
    hz_p  = [p for p in all_p if p['in_hz']]
    token = uuid.uuid4().hex[:12]
    _shares[token] = {
        'lang':     lang,
        'systems':  len(s['systems']),
        'planets':  len(all_p),
        'hz_count': len(hz_p),
        'avg_score': round(sum(p['hab_score'] for p in all_p) / len(all_p), 1) if all_p else 0,
        'top':      [{'name': p['name'], 'score': p['hab_score'], 'esi': p['esi'],
                      'type': p['type'], 'in_hz': p['in_hz']} for p in top],
        'created':  datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
    }
    return jsonify({'token': token})


@app.route('/analysis/share/<token>')
def analysis_share(token):
    data = _shares.get(token)
    if not data:
        return "<h2 style='font-family:sans-serif;text-align:center;margin-top:40px'>Report not found or expired.</h2>", 404
    lang = request.args.get('lang', data.get('lang', 'en'))
    return render_template('share.html', lang=lang, data=data, token=token)


# Static file helpers
@app.route('/bg/main')
def bg_main():
    return send_from_directory('.', 'background.png')

@app.route('/bg/none')
def bg_none():
    return send_from_directory('.', 'background_none.png')

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print("ATLAS v21 -- Starting Flask server on http://localhost:5000")
    app.run(debug=True, port=5000, host='0.0.0.0', use_reloader=False)
