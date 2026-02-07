"""
Smart Pattern-Based Card Generator
Learns from real working cards and generates high-quality validation cards
with diverse CVV/expiry combinations
"""
import json
import random
import os
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict
from datetime import datetime


class PatternData:
    """Stores pattern information for a specific 8-digit prefix"""
    def __init__(self, prefix: str):
        self.prefix = prefix
        self.suffix_digits = [[] for _ in range(8)]  # Observed digits at each position
        self.months = []
        self.years = []
        self.cvvs = []
        self.bank = ""
        self.country = ""
        self.card_type = ""
        self.level = ""
        self.count = 0


class SmartGenerator:
    """Pattern-based card generator that learns from real cards"""
    
    def __init__(self, cards_file: str = "output/cards.json"):
        self.cards_file = Path(cards_file)
        self.patterns: Dict[str, PatternData] = {}
        self.all_cvvs: List[str] = []
        self.all_months: List[str] = []
        self.all_years: List[str] = []
        
    def load_cards(self) -> List[Dict]:
        """Load cards from JSON file"""
        cards = []
        
        if not self.cards_file.exists():
            print(f"[!] Cards file not found: {self.cards_file}")
            return cards
        
        try:
            with open(self.cards_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for card in data:
                        cn = card.get('card_number', '')
                        if len(cn) >= 15:
                            cards.append(card)
        except Exception as e:
            print(f"[X] Error loading cards: {e}")
        
        return cards
    
    def build_patterns(self, cards: List[Dict]):
        """Build pattern database from real cards"""
        cvv_set = set()
        month_set = set()
        year_set = set()
        
        for card in cards:
            cn = card.get('card_number', '')
            if len(cn) < 16:
                continue
            
            prefix = cn[:8]
            suffix = cn[8:]
            
            # Initialize pattern if new
            if prefix not in self.patterns:
                self.patterns[prefix] = PatternData(prefix)
            
            p = self.patterns[prefix]
            p.count += 1
            
            # Record suffix digits at each position
            for i, ch in enumerate(suffix[:8]):
                if ch.isdigit():
                    p.suffix_digits[i].append(int(ch))
            
            # Record month, year, cvv
            month = card.get('expiry_month')
            year = card.get('expiry_year')
            cvv = card.get('cvv', '')
            
            if month:
                month_str = f"{month:02d}" if isinstance(month, int) else str(month).zfill(2)
                p.months.append(month_str)
                month_set.add(month_str)
            
            if year:
                year_str = str(year)
                p.years.append(year_str)
                year_set.add(year_str)
            
            if cvv and len(cvv) >= 3:
                p.cvvs.append(cvv)
                cvv_set.add(cvv)
            
            # Set metadata
            if not p.bank:
                p.card_type = card.get('card_type', '')
        
        # Store global distributions
        self.all_cvvs = list(cvv_set)
        self.all_months = list(month_set)
        self.all_years = list(year_set)
        
        # Filter to patterns with 2+ cards
        self.patterns = {k: v for k, v in self.patterns.items() if v.count >= 2}
        
        print(f"[OK] Built {len(self.patterns)} patterns from {len(cards)} cards")
        print(f"[OK] Global: {len(self.all_cvvs)} CVVs, {len(self.all_months)} months, {len(self.all_years)} years")
    
    def calculate_luhn_check(self, partial: str) -> int:
        """Calculate Luhn check digit"""
        total = 0
        is_second = True
        
        for ch in reversed(partial):
            d = int(ch)
            if is_second:
                d *= 2
                if d > 9:
                    d -= 9
            total += d
            is_second = not is_second
        
        return (10 - (total % 10)) % 10
    
    def make_luhn_valid(self, card_number: str) -> str:
        """Make card number Luhn-valid"""
        partial = card_number[:-1]
        check_digit = self.calculate_luhn_check(partial)
        return partial + str(check_digit)
    
    def generate_from_pattern(self, pattern: PatternData) -> Dict:
        """Generate a card from a specific pattern"""
        # Determine card length
        first_digit = pattern.prefix[0] if pattern.prefix else '4'
        if first_digit == '3':  # AMEX
            card_len = 15
            cvv_len = 4
        else:
            card_len = 16
            cvv_len = 3
        
        suffix_len = card_len - len(pattern.prefix)
        
        # Generate suffix based on observed digit patterns
        suffix = ""
        for pos in range(suffix_len - 1):  # -1 for Luhn digit
            if pos < len(pattern.suffix_digits) and pattern.suffix_digits[pos]:
                # Pick random digit from observed digits at this position
                digit = random.choice(pattern.suffix_digits[pos])
                suffix += str(digit)
            else:
                suffix += str(random.randint(0, 9))
        suffix += "0"  # Placeholder for Luhn
        
        # Build card number
        card_num = pattern.prefix + suffix
        card_num = self.make_luhn_valid(card_num)
        
        # === DIVERSE CVV GENERATION ===
        r = random.random()
        if r < 0.30 and pattern.cvvs:
            cvv = random.choice(pattern.cvvs)
        elif r < 0.70 and self.all_cvvs:
            cvv = random.choice(self.all_cvvs)
        else:
            cvv = ''.join([str(random.randint(0, 9)) for _ in range(cvv_len)])
        
        # Ensure correct length
        cvv = cvv.zfill(cvv_len)[:cvv_len]
        
        # === DIVERSE MONTH GENERATION ===
        r = random.random()
        if r < 0.25 and pattern.months:
            month = random.choice(pattern.months)
        elif r < 0.75 and self.all_months:
            month = random.choice(self.all_months)
        else:
            month = f"{random.randint(1, 12):02d}"
        
        # === DIVERSE YEAR GENERATION ===
        r = random.random()
        if r < 0.25 and pattern.years:
            year = random.choice(pattern.years)
        elif r < 0.75 and self.all_years:
            year = random.choice(self.all_years)
        else:
            year = str(2026 + random.randint(0, 5))
        
        # Validate year is not expired
        try:
            year_int = int(year)
            if year_int < 2026:
                year = str(2026 + random.randint(0, 4))
        except:
            year = "2027"
        
        # Determine card type
        card_type = pattern.card_type or self._get_card_type(card_num)
        
        return {
            'card_number': card_num,
            'expiry_month': int(month),
            'expiry_year': int(year),
            'cvv': cvv,
            'card_type': card_type,
            'bin': pattern.prefix[:6]
        }
    
    def _get_card_type(self, card_number: str) -> str:
        """Detect card type from number"""
        if not card_number:
            return "UNKNOWN"
        
        first = card_number[0]
        if first == '4':
            return "Visa"
        elif first == '5':
            return "Mastercard"
        elif first == '3':
            return "American Express"
        elif first == '6':
            return "Discover"
        return "UNKNOWN"
    
    def get_sorted_patterns(self) -> List[PatternData]:
        """Get patterns sorted by quality score"""
        def score(p: PatternData) -> int:
            s = p.count * 10
            # Prefer VISA and Mastercard
            if p.card_type in ['Visa', 'Mastercard']:
                s += 20
            return s
        
        patterns = list(self.patterns.values())
        patterns.sort(key=score, reverse=True)
        return patterns
    
    def generate_cards(self, count: int) -> List[Dict]:
        """Generate specified number of cards"""
        if not self.patterns:
            print("[!] No patterns loaded. Call build_patterns first.")
            return []
        
        patterns = self.get_sorted_patterns()
        result = []
        
        # Distribute across patterns
        cards_per_pattern = max(1, count // len(patterns))
        
        for pattern in patterns:
            for _ in range(cards_per_pattern):
                card = self.generate_from_pattern(pattern)
                result.append(card)
                
                if len(result) >= count:
                    break
            
            if len(result) >= count:
                break
        
        # Fill remaining if needed
        while len(result) < count and patterns:
            pattern = random.choice(patterns)
            card = self.generate_from_pattern(pattern)
            result.append(card)
        
        # Shuffle
        random.shuffle(result)
        
        return result[:count]
    
    def generate_single(self) -> Optional[Dict]:
        """Generate a single card"""
        if not self.patterns:
            return None
        
        # Pick weighted random pattern (prefer higher count)
        patterns = list(self.patterns.values())
        weights = [p.count for p in patterns]
        total = sum(weights)
        weights = [w / total for w in weights]
        
        pattern = random.choices(patterns, weights=weights, k=1)[0]
        return self.generate_from_pattern(pattern)


# Singleton instance for use across the application
_generator_instance: Optional[SmartGenerator] = None


def get_generator(cards_file: str = "output/cards.json") -> SmartGenerator:
    """Get or create the singleton generator instance"""
    global _generator_instance
    
    if _generator_instance is None:
        _generator_instance = SmartGenerator(cards_file)
        cards = _generator_instance.load_cards()
        if cards:
            _generator_instance.build_patterns(cards)
    
    return _generator_instance


def refresh_patterns(cards_file: str = "output/cards.json"):
    """Reload patterns from updated card data"""
    global _generator_instance
    
    gen = SmartGenerator(cards_file)
    cards = gen.load_cards()
    if cards:
        gen.build_patterns(cards)
        _generator_instance = gen
        print(f"[OK] Refreshed patterns from {len(cards)} cards")


if __name__ == "__main__":
    # Test the generator
    print("\n" + "=" * 60)
    print("   Smart Pattern-Based Card Generator - Test")
    print("=" * 60)
    
    gen = SmartGenerator()
    cards = gen.load_cards()
    
    if cards:
        gen.build_patterns(cards)
        
        print("\n[+] Generating 10 sample cards...")
        generated = gen.generate_cards(10)
        
        for card in generated:
            cn = card['card_number']
            month = card['expiry_month']
            year = card['expiry_year']
            cvv = card['cvv']
            ct = card['card_type']
            print(f"   {cn}|{month:02d}|{year}|{cvv} [{ct}]")
    else:
        print("[!] No cards found to learn from.")
