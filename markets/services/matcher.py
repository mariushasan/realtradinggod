import re
from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from markets.models import Market, MarketMatch, Exchange


class MarketMatcher:
    """NLP-based matching service for cross-exchange markets"""

    SIMILARITY_THRESHOLD = 0.6  # Minimum similarity score to consider a match

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 3),
            max_features=5000
        )

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for better matching"""
        text = text.lower()
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @staticmethod
    def extract_key_terms(text: str) -> set:
        """Extract key terms from market title"""
        text = MarketMatcher.normalize_text(text)
        # Common prediction market keywords to ignore
        ignore_words = {
            'will', 'be', 'the', 'to', 'in', 'on', 'at', 'by', 'yes', 'no',
            'market', 'win', 'winner', 'price', 'above', 'below', 'over', 'under'
        }
        words = set(text.split())
        return words - ignore_words

    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute similarity between two texts"""
        text1_norm = self.normalize_text(text1)
        text2_norm = self.normalize_text(text2)

        # TF-IDF similarity
        try:
            tfidf_matrix = self.vectorizer.fit_transform([text1_norm, text2_norm])
            tfidf_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except Exception:
            tfidf_sim = 0.0

        # Jaccard similarity on key terms
        terms1 = self.extract_key_terms(text1)
        terms2 = self.extract_key_terms(text2)

        if terms1 and terms2:
            jaccard_sim = len(terms1 & terms2) / len(terms1 | terms2)
        else:
            jaccard_sim = 0.0

        # Combined score (weighted average)
        combined_sim = 0.6 * tfidf_sim + 0.4 * jaccard_sim

        return combined_sim

    def generate_match_reason(self, kalshi_title: str, poly_title: str, similarity: float) -> str:
        """Generate human-readable match reason"""
        kalshi_terms = self.extract_key_terms(kalshi_title)
        poly_terms = self.extract_key_terms(poly_title)
        common_terms = kalshi_terms & poly_terms

        reasons = []

        if common_terms:
            reasons.append(f"Shared key terms: {', '.join(sorted(common_terms)[:5])}")

        reasons.append(f"Text similarity score: {similarity:.1%}")

        if similarity >= 0.8:
            reasons.append("High confidence match")
        elif similarity >= 0.7:
            reasons.append("Good confidence match")
        else:
            reasons.append("Moderate confidence - manual verification recommended")

        return " | ".join(reasons)

    def find_matches(
        self,
        kalshi_markets: List[Market],
        polymarket_markets: List[Market],
        threshold: float = None
    ) -> List[Tuple[Market, Market, float, str]]:
        """
        Find matching markets between Kalshi and Polymarket.

        Returns list of tuples: (kalshi_market, poly_market, similarity_score, reason)
        """
        threshold = threshold or self.SIMILARITY_THRESHOLD
        matches = []

        if not kalshi_markets or not polymarket_markets:
            return matches

        # Build title lists
        kalshi_titles = [m.title for m in kalshi_markets]
        poly_titles = [m.title for m in polymarket_markets]

        # Compute TF-IDF matrix for all titles
        all_titles = kalshi_titles + poly_titles
        all_titles_norm = [self.normalize_text(t) for t in all_titles]

        try:
            tfidf_matrix = self.vectorizer.fit_transform(all_titles_norm)
            kalshi_vectors = tfidf_matrix[:len(kalshi_titles)]
            poly_vectors = tfidf_matrix[len(kalshi_titles):]

            # Compute similarity matrix
            similarity_matrix = cosine_similarity(kalshi_vectors, poly_vectors)

            # Find matches above threshold
            for i, kalshi_market in enumerate(kalshi_markets):
                best_match_idx = np.argmax(similarity_matrix[i])
                best_score = similarity_matrix[i][best_match_idx]

                if best_score >= threshold:
                    poly_market = polymarket_markets[best_match_idx]

                    # Compute more detailed similarity
                    detailed_sim = self.compute_similarity(
                        kalshi_market.title,
                        poly_market.title
                    )

                    reason = self.generate_match_reason(
                        kalshi_market.title,
                        poly_market.title,
                        detailed_sim
                    )

                    matches.append((kalshi_market, poly_market, detailed_sim, reason))

        except Exception as e:
            # Fallback to pairwise comparison if vectorization fails
            for kalshi_market in kalshi_markets:
                best_match = None
                best_score = 0
                best_reason = ""

                for poly_market in polymarket_markets:
                    score = self.compute_similarity(
                        kalshi_market.title,
                        poly_market.title
                    )

                    if score > best_score and score >= threshold:
                        best_score = score
                        best_match = poly_market
                        best_reason = self.generate_match_reason(
                            kalshi_market.title,
                            poly_market.title,
                            score
                        )

                if best_match:
                    matches.append((kalshi_market, best_match, best_score, best_reason))

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
