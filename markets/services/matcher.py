import re
from typing import List, Tuple, Set, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from markets.models import Event, EventMatch, Market, MarketMatch, Exchange, Tag, TagMatch, SportsEvent, SportsEventMatch


class EventMatcher:
    """NLP-based matching service for cross-exchange events"""

    SIMILARITY_THRESHOLD = 0.5  # Threshold for matching

    # Common abbreviations and their expansions
    ABBREVIATIONS = {
        'fed': 'federal reserve',
        'btc': 'bitcoin',
        'eth': 'ethereum',
        'gop': 'republican',
        'dem': 'democrat democratic',
        'potus': 'president',
        'scotus': 'supreme court',
        'gdp': 'gross domestic product',
        'cpi': 'consumer price index',
        'ai': 'artificial intelligence',
        'nba': 'basketball',
        'nfl': 'football',
        'mlb': 'baseball',
        'ufc': 'mma fighting',
    }

    # Topic keywords for category matching
    TOPICS = {
        'politics': {'election', 'president', 'vote', 'congress', 'senate', 'governor', 'trump', 'biden', 'republican', 'democrat', 'gop', 'primary', 'nomination'},
        'crypto': {'bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'blockchain', 'token', 'coin'},
        'economics': {'fed', 'federal reserve', 'rate', 'inflation', 'gdp', 'recession', 'unemployment', 'cpi', 'interest'},
        'tech': {'ai', 'artificial intelligence', 'apple', 'google', 'meta', 'microsoft', 'nvidia', 'openai', 'tesla', 'spacex'},
        'sports': {'nba', 'nfl', 'mlb', 'super bowl', 'championship', 'playoffs', 'world series', 'mvp'},
        'entertainment': {'oscar', 'grammy', 'emmy', 'movie', 'album', 'billboard'},
    }

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 2),
            max_features=3000
        )

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for better matching"""
        text = text.lower()
        # Remove special characters but keep spaces and numbers
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @staticmethod
    def expand_abbreviations(text: str) -> str:
        """Expand common abbreviations"""
        text = text.lower()
        for abbrev, expansion in EventMatcher.ABBREVIATIONS.items():
            # Match whole words only
            text = re.sub(rf'\b{abbrev}\b', f'{abbrev} {expansion}', text)
        return text

    @staticmethod
    def extract_years(text: str) -> Set[str]:
        """Extract years from text (2020-2099)"""
        years = re.findall(r'\b(20[2-9][0-9])\b', text)
        return set(years)

    @staticmethod
    def extract_dates(text: str) -> Set[str]:
        """Extract date patterns like 'December 31', 'Dec 31', 'Jan 1'"""
        months = r'(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)'
        pattern = rf'\b({months})\s*(\d{{1,2}})\b'
        matches = re.findall(pattern, text.lower())
        return set(f"{m[0][:3]}-{m[1]}" for m in matches)

    @staticmethod
    def extract_numbers(text: str) -> Set[str]:
        """Extract significant numbers (prices, percentages, counts)"""
        # Match numbers with optional $ or % or k/m suffix
        numbers = re.findall(r'\$?([\d,]+(?:\.\d+)?)\s*[%km]?\b', text.lower())
        # Filter out years and very small numbers
        return set(n.replace(',', '') for n in numbers if len(n) >= 2 and not re.match(r'^20[2-9][0-9]$', n))

    @staticmethod
    def extract_entities(text: str) -> Set[str]:
        """Extract named entities (simplified - looks for capitalized words)"""
        # Find capitalized words that might be names
        entities = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', text)
        return set(e.lower() for e in entities if len(e) > 2)

    @staticmethod
    def detect_topic(text: str) -> Set[str]:
        """Detect which topics this event belongs to"""
        text = text.lower()
        detected = set()
        for topic, keywords in EventMatcher.TOPICS.items():
            if any(kw in text for kw in keywords):
                detected.add(topic)
        return detected

    @staticmethod
    def extract_key_terms(text: str) -> Set[str]:
        """Extract meaningful key terms"""
        text = EventMatcher.normalize_text(text)
        # Common words to ignore
        ignore_words = {
            'will', 'be', 'the', 'to', 'in', 'on', 'at', 'by', 'yes', 'no',
            'market', 'win', 'winner', 'before', 'after', 'between', 'during',
            'price', 'above', 'below', 'over', 'under', 'more', 'less', 'than',
            'this', 'that', 'these', 'those', 'any', 'all', 'some', 'most',
            'has', 'have', 'had', 'do', 'does', 'did', 'are', 'is', 'was', 'were',
            'for', 'from', 'with', 'into', 'through', 'and', 'or', 'but', 'if'
        }
        words = set(text.split())
        return words - ignore_words

    def compute_similarity(self, text1: str, text2: str) -> Tuple[float, Dict]:
        """
        Compute detailed similarity between two event titles.
        Returns (score, breakdown_dict)
        """
        # Expand abbreviations
        text1_exp = self.expand_abbreviations(text1)
        text2_exp = self.expand_abbreviations(text2)

        # Extract features
        years1 = self.extract_years(text1)
        years2 = self.extract_years(text2)
        dates1 = self.extract_dates(text1)
        dates2 = self.extract_dates(text2)
        numbers1 = self.extract_numbers(text1)
        numbers2 = self.extract_numbers(text2)
        topics1 = self.detect_topic(text1)
        topics2 = self.detect_topic(text2)
        terms1 = self.extract_key_terms(text1_exp)
        terms2 = self.extract_key_terms(text2_exp)
        entities1 = self.extract_entities(text1)
        entities2 = self.extract_entities(text2)

        breakdown = {}

        # Year matching (very important - same year is a strong signal)
        year_score = 0.0
        if years1 and years2:
            common_years = years1 & years2
            if common_years:
                year_score = 1.0
                breakdown['years'] = list(common_years)
        breakdown['year_score'] = year_score

        # Date matching
        date_score = 0.0
        if dates1 and dates2:
            common_dates = dates1 & dates2
            if common_dates:
                date_score = 1.0
                breakdown['dates'] = list(common_dates)
        breakdown['date_score'] = date_score

        # Topic matching
        topic_score = 0.0
        if topics1 and topics2:
            common_topics = topics1 & topics2
            if common_topics:
                topic_score = len(common_topics) / max(len(topics1), len(topics2))
                breakdown['topics'] = list(common_topics)
        breakdown['topic_score'] = topic_score

        # Key term overlap (Jaccard)
        term_score = 0.0
        if terms1 and terms2:
            common_terms = terms1 & terms2
            if common_terms:
                term_score = len(common_terms) / len(terms1 | terms2)
                breakdown['common_terms'] = list(common_terms)[:10]
        breakdown['term_score'] = term_score

        # Entity overlap
        entity_score = 0.0
        if entities1 and entities2:
            common_entities = entities1 & entities2
            if common_entities:
                entity_score = len(common_entities) / max(len(entities1), len(entities2))
                breakdown['entities'] = list(common_entities)
        breakdown['entity_score'] = entity_score

        # Number matching
        number_score = 0.0
        if numbers1 and numbers2:
            common_numbers = numbers1 & numbers2
            if common_numbers:
                number_score = len(common_numbers) / max(len(numbers1), len(numbers2))
                breakdown['numbers'] = list(common_numbers)
        breakdown['number_score'] = number_score

        # TF-IDF cosine similarity
        tfidf_score = 0.0
        try:
            text1_norm = self.normalize_text(text1_exp)
            text2_norm = self.normalize_text(text2_exp)
            tfidf_matrix = self.vectorizer.fit_transform([text1_norm, text2_norm])
            tfidf_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except Exception:
            pass
        breakdown['tfidf_score'] = tfidf_score

        # Combined score with weights
        combined_score = (
            0.25 * year_score +      # Same year is strong signal
            0.10 * date_score +      # Same date even stronger
            0.15 * topic_score +     # Same topic category
            0.20 * term_score +      # Key term overlap
            0.10 * entity_score +    # Named entity overlap
            0.05 * number_score +    # Number matching
            0.15 * tfidf_score       # TF-IDF similarity
        )

        # Bonus for multiple strong signals
        strong_signals = sum([
            year_score > 0.5,
            topic_score > 0.5,
            term_score > 0.3,
            entity_score > 0.3
        ])
        if strong_signals >= 3:
            combined_score = min(1.0, combined_score * 1.2)

        breakdown['combined_score'] = combined_score
        return combined_score, breakdown

    def generate_match_reason(self, breakdown: Dict) -> str:
        """Generate human-readable match reason from breakdown"""
        reasons = []

        if breakdown.get('years'):
            reasons.append(f"Same year: {', '.join(breakdown['years'])}")
        if breakdown.get('dates'):
            reasons.append(f"Same date: {', '.join(breakdown['dates'])}")
        if breakdown.get('topics'):
            reasons.append(f"Topic: {', '.join(breakdown['topics'])}")
        if breakdown.get('common_terms'):
            terms = breakdown['common_terms'][:5]
            reasons.append(f"Shared terms: {', '.join(terms)}")
        if breakdown.get('entities'):
            reasons.append(f"Entities: {', '.join(breakdown['entities'][:3])}")

        score = breakdown.get('combined_score', 0)
        if score >= 0.7:
            reasons.append("HIGH confidence")
        elif score >= 0.5:
            reasons.append("MEDIUM confidence - verify recommended")
        else:
            reasons.append("LOW confidence - manual verification needed")

        return " | ".join(reasons) if reasons else "Low similarity match"

    def _find_best_match_for_event(
        self,
        kalshi_event: Event,
        polymarket_events: List[Event],
        threshold: float
    ) -> Tuple[Event, Event, float, str] | None:
        """Find the best Polymarket match for a single Kalshi event"""
        best_match = None
        best_score = 0
        best_breakdown = {}

        for poly_event in polymarket_events:
            score, breakdown = self.compute_similarity(
                kalshi_event.title,
                poly_event.title
            )

            if score > best_score:
                best_score = score
                best_match = poly_event
                best_breakdown = breakdown

        if best_match and best_score >= threshold:
            reason = self.generate_match_reason(best_breakdown)
            return (kalshi_event, best_match, best_score, reason)

        return None

    def find_matches(
        self,
        kalshi_events: List[Event],
        polymarket_events: List[Event],
        threshold: float = None,
        max_workers: int = 8
    ) -> List[Tuple[Event, Event, float, str]]:
        """
        Find matching events between Kalshi and Polymarket using parallel processing.
        Returns list of tuples: (kalshi_event, poly_event, similarity_score, reason)
        """
        threshold = threshold or self.SIMILARITY_THRESHOLD
        matches = []

        if not kalshi_events or not polymarket_events:
            return matches

        # Process Kalshi events in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._find_best_match_for_event,
                    kalshi_event,
                    polymarket_events,
                    threshold
                ): kalshi_event
                for kalshi_event in kalshi_events
            }

            for future in as_completed(futures):
                result = future.result()
                if result:
                    matches.append(result)

        # Sort by similarity score descending
        matches.sort(key=lambda x: x[2], reverse=True)

        return matches

    def create_match_records(
        self,
        matches: List[Tuple[Event, Event, float, str]]
    ) -> List[EventMatch]:
        """Create or update EventMatch records from matches"""
        created_matches = []

        for kalshi_event, poly_event, score, reason in matches:
            match, created = EventMatch.objects.update_or_create(
                kalshi_event=kalshi_event,
                polymarket_event=poly_event,
                defaults={
                    'similarity_score': score,
                    'match_reason': reason
                }
            )
            created_matches.append(match)

        return created_matches


class SportsEventMatcher:
    """
    Specialized matcher for sports events using structural and semantic matching.

    Matching methods (in order of reliability):
    1. Team code exact match (structural)
    2. Team name fuzzy match
    3. Division/conference match
    4. Season + market type match
    5. Player name match (for awards)
    6. Threshold value match (for win totals)
    7. Semantic title similarity (fallback)
    """

    SIMILARITY_THRESHOLD = 0.4  # Lower threshold since we have more signals

    # NFL team code mappings (Kalshi code -> Standard code)
    NFL_TEAM_CODE_MAP = {
        # Kalshi uses various formats
        'ARI': 'ARI', 'ARZ': 'ARI', 'ARIZONA': 'ARI',
        'ATL': 'ATL', 'ATLANTA': 'ATL',
        'BAL': 'BAL', 'BALTIMORE': 'BAL',
        'BUF': 'BUF', 'BUFFALO': 'BUF',
        'CAR': 'CAR', 'CAROLINA': 'CAR',
        'CHI': 'CHI', 'CHICAGO': 'CHI',
        'CIN': 'CIN', 'CINCINNATI': 'CIN',
        'CLE': 'CLE', 'CLEVELAND': 'CLE',
        'DAL': 'DAL', 'DALLAS': 'DAL',
        'DEN': 'DEN', 'DENVER': 'DEN',
        'DET': 'DET', 'DETROIT': 'DET',
        'GB': 'GB', 'GNB': 'GB', 'GREEN BAY': 'GB', 'GREENBAY': 'GB',
        'HOU': 'HOU', 'HOUSTON': 'HOU',
        'IND': 'IND', 'INDIANAPOLIS': 'IND',
        'JAC': 'JAC', 'JAX': 'JAC', 'JACKSONVILLE': 'JAC',
        'KC': 'KC', 'KAN': 'KC', 'KANSAS CITY': 'KC',
        'LA': 'LAR', 'LAR': 'LAR', 'LOS ANGELES R': 'LAR', 'RAMS': 'LAR',
        'LAC': 'LAC', 'LOS ANGELES C': 'LAC', 'CHARGERS': 'LAC',
        'LV': 'LV', 'LVR': 'LV', 'OAK': 'LV', 'RAIDERS': 'LV', 'LAS VEGAS': 'LV',
        'MIA': 'MIA', 'MIAMI': 'MIA',
        'MIN': 'MIN', 'MINNESOTA': 'MIN',
        'NE': 'NE', 'NEW ENGLAND': 'NE', 'PATRIOTS': 'NE',
        'NO': 'NO', 'NEW ORLEANS': 'NO', 'SAINTS': 'NO',
        'NYG': 'NYG', 'NEW YORK G': 'NYG', 'GIANTS': 'NYG',
        'NYJ': 'NYJ', 'NEW YORK J': 'NYJ', 'JETS': 'NYJ',
        'PHI': 'PHI', 'PHILADELPHIA': 'PHI', 'EAGLES': 'PHI',
        'PIT': 'PIT', 'PITTSBURGH': 'PIT', 'STEELERS': 'PIT',
        'SEA': 'SEA', 'SEATTLE': 'SEA', 'SEAHAWKS': 'SEA',
        'SF': 'SF', 'SAN FRANCISCO': 'SF', '49ERS': 'SF',
        'TB': 'TB', 'TAMPA BAY': 'TB', 'BUCCANEERS': 'TB', 'BUCS': 'TB',
        'TEN': 'TEN', 'TENNESSEE': 'TEN', 'TITANS': 'TEN',
        'WAS': 'WAS', 'WSH': 'WAS', 'WASHINGTON': 'WAS', 'COMMANDERS': 'WAS',
    }

    # City to team code for Polymarket groupItemTitle matching
    NFL_CITY_TO_CODE = {
        'arizona': 'ARI', 'atlanta': 'ATL', 'baltimore': 'BAL', 'buffalo': 'BUF',
        'carolina': 'CAR', 'chicago': 'CHI', 'cincinnati': 'CIN', 'cleveland': 'CLE',
        'dallas': 'DAL', 'denver': 'DEN', 'detroit': 'DET', 'green bay': 'GB',
        'houston': 'HOU', 'indianapolis': 'IND', 'jacksonville': 'JAC',
        'kansas city': 'KC', 'los angeles r': 'LAR', 'los angeles c': 'LAC',
        'las vegas': 'LV', 'miami': 'MIA', 'minnesota': 'MIN', 'new england': 'NE',
        'new orleans': 'NO', 'new york g': 'NYG', 'new york j': 'NYJ',
        'philadelphia': 'PHI', 'pittsburgh': 'PIT', 'seattle': 'SEA',
        'san francisco': 'SF', 'tampa bay': 'TB', 'tennessee': 'TEN',
        'washington': 'WAS',
    }

    # Division mapping
    NFL_DIVISIONS = {
        'NFC WEST': ['ARI', 'LAR', 'SF', 'SEA'],
        'NFC EAST': ['DAL', 'NYG', 'PHI', 'WAS'],
        'NFC NORTH': ['CHI', 'DET', 'GB', 'MIN'],
        'NFC SOUTH': ['ATL', 'CAR', 'NO', 'TB'],
        'AFC WEST': ['DEN', 'KC', 'LAC', 'LV'],
        'AFC EAST': ['BUF', 'MIA', 'NE', 'NYJ'],
        'AFC NORTH': ['BAL', 'CIN', 'CLE', 'PIT'],
        'AFC SOUTH': ['HOU', 'IND', 'JAC', 'TEN'],
    }

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 2),
            max_features=2000
        )

    @classmethod
    def normalize_team_code(cls, code: str) -> str:
        """Normalize team code to standard format"""
        if not code:
            return ''
        code = code.upper().strip()
        return cls.NFL_TEAM_CODE_MAP.get(code, code)

    @classmethod
    def extract_team_code_from_kalshi_ticker(cls, ticker: str) -> str:
        """
        Extract team code from Kalshi event/market ticker.
        Examples:
            KXNFLWINS-CLE-25B -> CLE
            KXNFLNFCWEST-25-SF -> SF
            KXNFLEXACTWINSCLE-25 -> CLE
        """
        if not ticker:
            return ''

        ticker = ticker.upper()

        # Pattern 1: KXNFLWINS-CLE-25B (team code as segment)
        parts = ticker.split('-')
        for part in parts:
            if part in cls.NFL_TEAM_CODE_MAP:
                return cls.normalize_team_code(part)

        # Pattern 2: KXNFLEXACTWINSCLE-25 (team code embedded at end)
        # Look for team codes at the end of segments
        for code in cls.NFL_TEAM_CODE_MAP.keys():
            if len(code) >= 2 and ticker.endswith(code) or f'{code}-' in ticker:
                return cls.normalize_team_code(code)

        # Pattern 3: Check each segment for embedded team codes
        for part in parts:
            for code in cls.NFL_TEAM_CODE_MAP.keys():
                if len(code) >= 2 and part.endswith(code):
                    return cls.normalize_team_code(code)

        return ''

    @classmethod
    def extract_team_code_from_polymarket_image(cls, image_url: str) -> str:
        """
        Extract team code from Polymarket image URL.
        Example: https://...NFL+Team+Logos/ARZ.png -> ARI
        """
        if not image_url:
            return ''

        # Pattern: /TEAMCODE.png
        match = re.search(r'/([A-Z]{2,3})\.png', image_url.upper())
        if match:
            return cls.normalize_team_code(match.group(1))

        return ''

    @classmethod
    def extract_team_from_group_item_title(cls, title: str) -> str:
        """
        Extract team code from Polymarket groupItemTitle.
        Example: "Tampa Bay" -> TB, "Arizona" -> ARI
        """
        if not title:
            return ''

        title_lower = title.lower().strip()
        return cls.NFL_CITY_TO_CODE.get(title_lower, '')

    @classmethod
    def extract_season_from_ticker(cls, ticker: str) -> Tuple[str, int]:
        """
        Extract season info from ticker.
        Returns (season_string, primary_year)
        """
        if not ticker:
            return '', None

        # Pattern: -25 or -25B (year suffix)
        match = re.search(r'-(\d{2})[A-Z]?(?:-|$)', ticker)
        if match:
            year_suffix = match.group(1)
            year = 2000 + int(year_suffix)
            return f"{year}-{year+1}", year

        return '', None

    @classmethod
    def extract_season_from_text(cls, text: str) -> Tuple[str, int]:
        """Extract season from title/description text"""
        if not text:
            return '', None

        # Pattern: 2025-26 or 2025/26
        match = re.search(r'(20\d{2})[-/](\d{2})', text)
        if match:
            year = int(match.group(1))
            return f"{year}-{year+1}", year

        # Pattern: just 2025 or 2026
        match = re.search(r'\b(20\d{2})\b', text)
        if match:
            year = int(match.group(1))
            return str(year), year

        return '', None

    @classmethod
    def detect_market_type(cls, raw_data: dict, title: str) -> str:
        """Detect the type of sports market"""
        title_lower = title.lower()

        # Check Kalshi competition_scope first
        scope = raw_data.get('product_metadata', {}).get('competition_scope', '').lower()

        if 'win total' in scope or 'win totals' in scope:
            return SportsEvent.MarketType.WIN_TOTAL
        if 'exact win' in scope or 'exact wins' in scope:
            return SportsEvent.MarketType.EXACT_WINS
        if 'division' in scope:
            return SportsEvent.MarketType.DIVISION_WINNER

        # Check title for keywords
        if 'mvp' in title_lower:
            return SportsEvent.MarketType.MVP
        if 'comeback' in title_lower or 'player of' in title_lower or 'award' in title_lower:
            return SportsEvent.MarketType.PLAYER_AWARD
        if 'champion' in title_lower:
            if 'nfc' in title_lower or 'afc' in title_lower:
                return SportsEvent.MarketType.CONFERENCE_WINNER
            return SportsEvent.MarketType.CHAMPION
        if 'division' in title_lower:
            return SportsEvent.MarketType.DIVISION_WINNER
        if 'win more than' in title_lower or 'over' in title_lower and 'win' in title_lower:
            return SportsEvent.MarketType.WIN_TOTAL
        if 'exactly' in title_lower and 'win' in title_lower:
            return SportsEvent.MarketType.EXACT_WINS
        if 'playoff' in title_lower or 'wild card' in title_lower:
            return SportsEvent.MarketType.PLAYOFF_WINNER
        if 'super bowl' in title_lower:
            return SportsEvent.MarketType.CHAMPION

        return SportsEvent.MarketType.OTHER

    @classmethod
    def detect_league(cls, raw_data: dict, title: str, category: str) -> str:
        """Detect which league this event belongs to"""
        text = f"{title} {category}".lower()
        competition = raw_data.get('product_metadata', {}).get('competition', '').lower()

        if 'pro football' in competition or 'nfl' in text or 'football' in text:
            return SportsEvent.League.NFL
        if 'basketball' in competition or 'nba' in text:
            return SportsEvent.League.NBA
        if 'baseball' in competition or 'mlb' in text:
            return SportsEvent.League.MLB
        if 'hockey' in competition or 'nhl' in text:
            return SportsEvent.League.NHL
        if 'mls' in text or 'soccer' in text:
            return SportsEvent.League.MLS
        if 'ufc' in text or 'mma' in text:
            return SportsEvent.League.UFC

        return SportsEvent.League.OTHER

    @classmethod
    def extract_division_from_text(cls, text: str) -> str:
        """Extract division name from text"""
        text_upper = text.upper()

        for division in cls.NFL_DIVISIONS.keys():
            if division.replace(' ', '') in text_upper.replace(' ', ''):
                return division

        return ''

    @classmethod
    def extract_threshold_from_kalshi(cls, raw_data: dict) -> Tuple[float, str]:
        """
        Extract threshold value from Kalshi market data.
        Returns (threshold_value, threshold_type)
        """
        # Look at markets for floor_strike
        markets = raw_data.get('markets', [])
        if markets and isinstance(markets, list) and len(markets) > 0:
            market = markets[0]
            floor_strike = market.get('floor_strike')
            if floor_strike is not None:
                # floor_strike of 8 means "over 8.5 wins"
                return float(floor_strike) + 0.5, 'over'
            cap_strike = market.get('cap_strike')
            if cap_strike is not None:
                return float(cap_strike), 'exactly'

        return None, ''

    def compute_sports_match_score(
        self,
        kalshi_se: SportsEvent,
        poly_se: SportsEvent
    ) -> Tuple[float, Dict]:
        """
        Compute detailed match score between two SportsEvents.
        Returns (score, breakdown_dict)
        """
        breakdown = {
            'team_code_match': False,
            'team_name_match': False,
            'league_match': False,
            'market_type_match': False,
            'season_match': False,
            'division_match': False,
            'threshold_match': False,
            'text_similarity': 0.0,
        }

        score = 0.0

        # 1. Team code match (HIGHEST weight - 0.35)
        if kalshi_se.team_code and poly_se.team_code:
            if kalshi_se.team_code == poly_se.team_code:
                score += 0.35
                breakdown['team_code_match'] = True
        elif kalshi_se.team_code and poly_se.image_team_code:
            if kalshi_se.team_code == poly_se.image_team_code:
                score += 0.35
                breakdown['team_code_match'] = True

        # 2. Team name fuzzy match (0.20)
        if not breakdown['team_code_match'] and kalshi_se.team_name and poly_se.team_name:
            k_name = kalshi_se.team_name.lower()
            p_name = poly_se.team_name.lower()
            if k_name == p_name or k_name in p_name or p_name in k_name:
                score += 0.20
                breakdown['team_name_match'] = True

        # 3. League match (0.15)
        if kalshi_se.league == poly_se.league and kalshi_se.league != SportsEvent.League.OTHER:
            score += 0.15
            breakdown['league_match'] = True

        # 4. Market type match (0.10)
        if kalshi_se.market_type == poly_se.market_type and kalshi_se.market_type != SportsEvent.MarketType.OTHER:
            score += 0.10
            breakdown['market_type_match'] = True

        # 5. Season match (0.10)
        if kalshi_se.season_year and poly_se.season_year:
            if kalshi_se.season_year == poly_se.season_year:
                score += 0.10
                breakdown['season_match'] = True

        # 6. Division match (0.05)
        if kalshi_se.division and poly_se.division:
            if kalshi_se.division.upper() == poly_se.division.upper():
                score += 0.05
                breakdown['division_match'] = True

        # 7. Threshold match - for win totals (0.05)
        if kalshi_se.threshold_value and poly_se.threshold_value:
            if abs(kalshi_se.threshold_value - poly_se.threshold_value) < 0.1:
                score += 0.05
                breakdown['threshold_match'] = True

        # 8. Text similarity fallback (up to 0.10)
        try:
            text1 = kalshi_se.normalized_title or kalshi_se.event.title
            text2 = poly_se.normalized_title or poly_se.event.title
            text1_norm = re.sub(r'[^a-z0-9\s]', ' ', text1.lower())
            text2_norm = re.sub(r'[^a-z0-9\s]', ' ', text2.lower())
            tfidf_matrix = self.vectorizer.fit_transform([text1_norm, text2_norm])
            text_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            score += 0.10 * text_sim
            breakdown['text_similarity'] = text_sim
        except Exception:
            pass

        breakdown['total_score'] = score
        return score, breakdown

    def generate_sports_match_reason(self, breakdown: Dict) -> str:
        """Generate human-readable match reason from breakdown"""
        reasons = []
        methods = []

        if breakdown.get('team_code_match'):
            reasons.append("✓ Team codes match")
            methods.append("TEAM_CODE")
        if breakdown.get('team_name_match'):
            reasons.append("✓ Team names match")
            methods.append("TEAM_NAME")
        if breakdown.get('league_match'):
            reasons.append("✓ Same league")
            methods.append("LEAGUE")
        if breakdown.get('market_type_match'):
            reasons.append("✓ Same market type")
            methods.append("MARKET_TYPE")
        if breakdown.get('season_match'):
            reasons.append("✓ Same season")
            methods.append("SEASON")
        if breakdown.get('division_match'):
            reasons.append("✓ Same division")
            methods.append("DIVISION")
        if breakdown.get('threshold_match'):
            reasons.append("✓ Same threshold")
            methods.append("THRESHOLD")

        text_sim = breakdown.get('text_similarity', 0)
        if text_sim > 0.5:
            reasons.append(f"✓ Text similarity: {text_sim:.2f}")
            methods.append("TEXT_SIM")

        score = breakdown.get('total_score', 0)
        if score >= 0.6:
            reasons.append("【HIGH confidence】")
        elif score >= 0.4:
            reasons.append("【MEDIUM confidence】")
        else:
            reasons.append("【LOW confidence - verify】")

        primary_method = methods[0] if methods else "UNKNOWN"
        return " | ".join(reasons), primary_method

    def _find_best_sports_match(
        self,
        kalshi_se: SportsEvent,
        poly_sports_events: List[SportsEvent],
        threshold: float
    ) -> Tuple[SportsEvent, SportsEvent, float, str, str] | None:
        """Find the best Polymarket sports event match for a Kalshi sports event"""
        best_match = None
        best_score = 0
        best_breakdown = {}

        for poly_se in poly_sports_events:
            score, breakdown = self.compute_sports_match_score(kalshi_se, poly_se)

            if score > best_score:
                best_score = score
                best_match = poly_se
                best_breakdown = breakdown

        if best_match and best_score >= threshold:
            reason, method = self.generate_sports_match_reason(best_breakdown)
            return (kalshi_se, best_match, best_score, reason, method)

        return None

    def find_matches(
        self,
        kalshi_sports_events: List[SportsEvent],
        poly_sports_events: List[SportsEvent],
        threshold: float = None,
        max_workers: int = 8
    ) -> List[Tuple[SportsEvent, SportsEvent, float, str, str]]:
        """
        Find matching sports events between Kalshi and Polymarket.
        Returns list of tuples: (kalshi_se, poly_se, score, reason, method)
        """
        threshold = threshold or self.SIMILARITY_THRESHOLD
        matches = []

        if not kalshi_sports_events or not poly_sports_events:
            return matches

        # Process in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._find_best_sports_match,
                    kalshi_se,
                    poly_sports_events,
                    threshold
                ): kalshi_se
                for kalshi_se in kalshi_sports_events
            }

            for future in as_completed(futures):
                result = future.result()
                if result:
                    matches.append(result)

        # Sort by score descending
        matches.sort(key=lambda x: x[2], reverse=True)

        return matches

    def create_match_records(
        self,
        matches: List[Tuple[SportsEvent, SportsEvent, float, str, str]]
    ) -> List[SportsEventMatch]:
        """Create or update SportsEventMatch records from matches"""
        created_matches = []

        for kalshi_se, poly_se, score, reason, method in matches:
            # Parse breakdown from reason
            team_code_match = '✓ Team codes match' in reason
            team_name_match = '✓ Team names match' in reason
            league_match = '✓ Same league' in reason
            market_type_match = '✓ Same market type' in reason
            season_match = '✓ Same season' in reason
            threshold_match = '✓ Same threshold' in reason

            match, created = SportsEventMatch.objects.update_or_create(
                kalshi_sports_event=kalshi_se,
                polymarket_sports_event=poly_se,
                defaults={
                    'similarity_score': score,
                    'match_reason': reason,
                    'match_method': method,
                    'team_code_match': team_code_match,
                    'team_name_match': team_name_match,
                    'league_match': league_match,
                    'market_type_match': market_type_match,
                    'season_match': season_match,
                    'threshold_match': threshold_match,
                }
            )
            created_matches.append(match)

        return created_matches