import re
from typing import List, Tuple, Set, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from markets.models import Market, MarketMatch, Exchange, Tag, TagMatch


class MarketMatcher:
    """Improved NLP-based matching service for cross-exchange markets"""

    SIMILARITY_THRESHOLD = 0.5  # Lowered threshold with better scoring

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
        for abbrev, expansion in MarketMatcher.ABBREVIATIONS.items():
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
        """Detect which topics this market belongs to"""
        text = text.lower()
        detected = set()
        for topic, keywords in MarketMatcher.TOPICS.items():
            if any(kw in text for kw in keywords):
                detected.add(topic)
        return detected

    @staticmethod
    def extract_key_terms(text: str) -> Set[str]:
        """Extract meaningful key terms"""
        text = MarketMatcher.normalize_text(text)
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
        Compute detailed similarity between two market titles.
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
        # Year match is very important (same event likely has same year)
        # Topic match helps narrow down
        # Term overlap and TF-IDF for semantic similarity
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

    def _find_best_match_for_market(
        self,
        kalshi_market: Market,
        polymarket_markets: List[Market],
        threshold: float
    ) -> Tuple[Market, Market, float, str] | None:
        """Find the best Polymarket match for a single Kalshi market"""
        best_match = None
        best_score = 0
        best_breakdown = {}

        for poly_market in polymarket_markets:
            score, breakdown = self.compute_similarity(
                kalshi_market.title,
                poly_market.title
            )

            if score > best_score:
                best_score = score
                best_match = poly_market
                best_breakdown = breakdown

        if best_match and best_score >= threshold:
            reason = self.generate_match_reason(best_breakdown)
            return (kalshi_market, best_match, best_score, reason)

        return None

    def find_matches(
        self,
        kalshi_markets: List[Market],
        polymarket_markets: List[Market],
        threshold: float = None,
        max_workers: int = 8
    ) -> List[Tuple[Market, Market, float, str]]:
        """
        Find matching markets between Kalshi and Polymarket using parallel processing.
        Returns list of tuples: (kalshi_market, poly_market, similarity_score, reason)
        """
        threshold = threshold or self.SIMILARITY_THRESHOLD
        matches = []

        if not kalshi_markets or not polymarket_markets:
            return matches

        # Process Kalshi markets in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._find_best_match_for_market,
                    kalshi_market,
                    polymarket_markets,
                    threshold
                ): kalshi_market
                for kalshi_market in kalshi_markets
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
        matches: List[Tuple[Market, Market, float, str]]
    ) -> List[MarketMatch]:
        """Create or update MarketMatch records from matches"""
        created_matches = []

        for kalshi_market, poly_market, score, reason in matches:
            match, created = MarketMatch.objects.update_or_create(
                kalshi_market=kalshi_market,
                polymarket_market=poly_market,
                defaults={
                    'similarity_score': score,
                    'match_reason': reason
                }
            )
            created_matches.append(match)

        return created_matches