from typing import List, Dict, Tuple, Optional
from itertools import product
from decimal import Decimal

from markets.models import Market, MarketMatch, ArbitrageOpportunity, Exchange


class ArbitrageDetector:
    """
    Detect arbitrage opportunities across prediction markets.

    For binary markets: If sum of "No" prices < 1, buy all "No" positions
    For cross-exchange: If price_A(Yes) + price_B(No) < 1, buy both
    """

    MIN_PROFIT_THRESHOLD = 0.01  # 1% minimum profit

    @staticmethod
    def get_best_prices(outcomes: List[Dict]) -> Tuple[Optional[float], Optional[float]]:
        """
        Extract best Yes and No prices from outcomes.
        Returns (yes_price, no_price)
        """
        yes_price = None
        no_price = None

        for outcome in outcomes:
            name = outcome.get('name', '').lower()
            price = outcome.get('price', 0)

            if price and price > 0:
                if 'yes' in name or name == 'yes':
                    yes_price = float(price)
                elif 'no' in name or name == 'no':
                    no_price = float(price)

        return yes_price, no_price

    def detect_single_market_arb(self, market: Market) -> Optional[Dict]:
        """
        Detect arbitrage within a single binary market.

        For a binary market, Yes + No should equal 1.
        If Yes_price + No_price < 1, there's arbitrage (buy both).
        """
        yes_price, no_price = self.get_best_prices(market.outcomes)

        if yes_price is None or no_price is None:
            return None

        total_cost = yes_price + no_price

        # If total cost < 1, buying both guarantees profit
        if total_cost < 1 - self.MIN_PROFIT_THRESHOLD:
            profit = 1 - total_cost
            profit_percent = (profit / total_cost) * 100

            return {
                'market': market,
                'positions': [
                    {'outcome': 'Yes', 'price': yes_price, 'market_id': market.id},
                    {'outcome': 'No', 'price': no_price, 'market_id': market.id}
                ],
                'total_cost': total_cost,
                'guaranteed_return': 1.0,
                'profit': profit,
                'profit_percent': profit_percent,
                'expected_value': 1.0 / total_cost
            }

        return None

    def detect_cross_exchange_arb(self, match: MarketMatch) -> Optional[Dict]:
        """
        Detect arbitrage between matched markets on different exchanges.

        Strategies:
        1. Buy Yes on Kalshi + No on Polymarket (or vice versa)
        2. Buy No on both if combined < 1
        """
        kalshi_yes, kalshi_no = self.get_best_prices(match.kalshi_market.outcomes)
        poly_yes, poly_no = self.get_best_prices(match.polymarket_market.outcomes)

        best_arb = None
        best_profit = 0

        # Strategy 1: Kalshi Yes + Polymarket No
        if kalshi_yes and poly_no:
            total_cost = kalshi_yes + poly_no
            if total_cost < 1 - self.MIN_PROFIT_THRESHOLD:
                profit = 1 - total_cost
                profit_percent = (profit / total_cost) * 100
                if profit_percent > best_profit:
                    best_profit = profit_percent
                    best_arb = {
                        'match': match,
                        'positions': [
                            {
                                'exchange': 'kalshi',
                                'outcome': 'Yes',
                                'price': kalshi_yes,
                                'market_id': match.kalshi_market.id
                            },
                            {
                                'exchange': 'polymarket',
                                'outcome': 'No',
                                'price': poly_no,
                                'market_id': match.polymarket_market.id
                            }
                        ],
                        'total_cost': total_cost,
                        'guaranteed_return': 1.0,
                        'profit': profit,
                        'profit_percent': profit_percent,
                        'expected_value': 1.0 / total_cost
                    }

        # Strategy 2: Polymarket Yes + Kalshi No
        if poly_yes and kalshi_no:
            total_cost = poly_yes + kalshi_no
            if total_cost < 1 - self.MIN_PROFIT_THRESHOLD:
                profit = 1 - total_cost
                profit_percent = (profit / total_cost) * 100
                if profit_percent > best_profit:
                    best_profit = profit_percent
                    best_arb = {
                        'match': match,
                        'positions': [
                            {
                                'exchange': 'polymarket',
                                'outcome': 'Yes',
                                'price': poly_yes,
                                'market_id': match.polymarket_market.id
                            },
                            {
                                'exchange': 'kalshi',
                                'outcome': 'No',
                                'price': kalshi_no,
                                'market_id': match.kalshi_market.id
                            }
                        ],
                        'total_cost': total_cost,
                        'guaranteed_return': 1.0,
                        'profit': profit,
                        'profit_percent': profit_percent,
                        'expected_value': 1.0 / total_cost
                    }

        # Strategy 3: Both No positions
        if kalshi_no and poly_no:
            # This only works if the events are truly the same
            # If same event, only one can be Yes, so both No guarantees one wins
            # But this is riskier and requires verification
            pass

        return best_arb

    def find_all_opportunities(self) -> List[Dict]:
        """Find all arbitrage opportunities in the database"""
        opportunities = []

        # Check single market arbitrage (Kalshi)
        kalshi_markets = Market.objects.filter(exchange=Exchange.KALSHI, is_active=True)
        for market in kalshi_markets:
            arb = self.detect_single_market_arb(market)
            if arb:
                arb['type'] = ArbitrageOpportunity.ArbitrageType.KALSHI_ONLY
                opportunities.append(arb)

        # Check single market arbitrage (Polymarket)
        poly_markets = Market.objects.filter(exchange=Exchange.POLYMARKET, is_active=True)
        for market in poly_markets:
            arb = self.detect_single_market_arb(market)
            if arb:
                arb['type'] = ArbitrageOpportunity.ArbitrageType.POLYMARKET_ONLY
                opportunities.append(arb)

        # Check cross-exchange arbitrage
        matches = MarketMatch.objects.select_related(
            'kalshi_market', 'polymarket_market'
        ).filter(
            kalshi_market__is_active=True,
            polymarket_market__is_active=True
        )

        for match in matches:
            arb = self.detect_cross_exchange_arb(match)
            if arb:
                arb['type'] = ArbitrageOpportunity.ArbitrageType.CROSS_EXCHANGE
                opportunities.append(arb)

        # Sort by profit percentage
        opportunities.sort(key=lambda x: x['profit_percent'], reverse=True)

        return opportunities

    def save_opportunities(self, opportunities: List[Dict]) -> List[ArbitrageOpportunity]:
        """Save arbitrage opportunities to database"""
        # Clear old opportunities
        ArbitrageOpportunity.objects.all().update(is_active=False)

        saved = []
        for opp in opportunities:
            arb_opp = ArbitrageOpportunity.objects.create(
                arb_type=opp['type'],
                market_match=opp.get('match'),
                positions={
                    'positions': opp['positions'],
                    'total_cost': opp['total_cost'],
                    'guaranteed_return': opp['guaranteed_return']
                },
                profit_percent=opp['profit_percent'],
                expected_value=opp['expected_value'],
                is_active=True
            )

            # Add related markets
            if opp.get('market'):
                arb_opp.markets.add(opp['market'])
            elif opp.get('match'):
                arb_opp.markets.add(opp['match'].kalshi_market)
                arb_opp.markets.add(opp['match'].polymarket_market)

            saved.append(arb_opp)

        return saved
