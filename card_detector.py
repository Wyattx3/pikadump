"""
Card Detection Engine
Handles card number detection, validation, and type identification
"""
import re
from typing import Optional, List, Dict
from datetime import datetime


class CardDetector:
    """Detects and validates credit/debit card information from text"""
    
    def __init__(self):
        # Card type patterns
        self.card_patterns = {
            'Visa': {
                'pattern': r'^4[0-9]{12}(?:[0-9]{3,6})?$',
                'lengths': [13, 16, 19]
            },
            'Mastercard': {
                'pattern': r'^(5[1-5][0-9]{14}|222[1-9][0-9]{12}|22[3-9][0-9]{13}|2[3-6][0-9]{14}|27[01][0-9]{13}|2720[0-9]{12})$',
                'lengths': [16]
            },
            'American Express': {
                'pattern': r'^3[47][0-9]{13}$',
                'lengths': [15]
            },
            'JCB': {
                'pattern': r'^(35[0-9]{14})$',
                'lengths': [16]
            },
            'Discover': {
                'pattern': r'^(6011[0-9]{12}|65[0-9]{14}|64[4-9][0-9]{13})$',
                'lengths': [16]
            }
        }
    
    def luhn_check(self, card_number: str) -> bool:
        """Validate card number using Luhn algorithm"""
        digits = re.sub(r'\D', '', card_number)
        
        if not digits or len(digits) < 13:
            return False
        
        digits = digits[::-1]
        total = 0
        for i, digit in enumerate(digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        
        return total % 10 == 0
    
    def detect_card_type(self, card_number: str) -> Optional[str]:
        """Detect card type based on card number"""
        digits = re.sub(r'\D', '', card_number)
        
        if not digits:
            return None
        
        for card_type, info in self.card_patterns.items():
            if re.match(info['pattern'], digits):
                if len(digits) in info['lengths']:
                    return card_type
        
        return None
    
    def parse_expiry(self, expiry_str: str) -> Dict:
        """Parse expiry date from various formats"""
        result = {'month': None, 'year': None}
        
        if not expiry_str:
            return result
        
        expiry_str = expiry_str.strip()
        
        # Try different patterns
        patterns = [
            # MM/YYYY or MM/YY
            r'^(0[1-9]|1[0-2])[/](20\d{2}|\d{2})$',
            # MM-YYYY or MM-YY
            r'^(0[1-9]|1[0-2])[-](20\d{2}|\d{2})$',
            # MMYYYY or MMYY
            r'^(0[1-9]|1[0-2])(20\d{2}|\d{2})$',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, expiry_str)
            if match:
                month = int(match.group(1))
                year_str = match.group(2)
                
                if len(year_str) == 2:
                    year = 2000 + int(year_str)
                else:
                    year = int(year_str)
                
                result['month'] = month
                result['year'] = year
                return result
        
        return result
    
    def parse_card_line(self, line: str) -> Optional[Dict]:
        """
        Parse a single line containing card info
        Supports formats:
        - 5290999936818062|11|2027|381
        - 4689021667993907|04|28|465
        - 5290999936818062|11/2027|381
        - 5290999936818062|11/27|381
        - 5290999936818062 11 2027 381
        - 5290999936818062 11 27 381
        """
        if not line:
            return None
        
        line = line.strip()
        
        # Try pipe-separated format first: card|month|year|cvv or card|mm/yy|cvv
        if '|' in line:
            parts = line.split('|')
            
            if len(parts) >= 3:
                card_number = re.sub(r'\D', '', parts[0])
                
                # Validate card number
                if not (13 <= len(card_number) <= 19):
                    return None
                
                if not self.luhn_check(card_number):
                    return None
                
                card_type = self.detect_card_type(card_number)
                if not card_type:
                    return None
                
                month = None
                year = None
                cvv = None
                
                # Check if format is card|mm/yy|cvv or card|mm|yy|cvv
                if len(parts) == 3:
                    # card|mm/yy|cvv or card|mmyy|cvv
                    expiry_part = parts[1].strip()
                    cvv_part = parts[2].strip()
                    
                    # Parse expiry
                    expiry = self.parse_expiry(expiry_part)
                    month = expiry['month']
                    year = expiry['year']
                    
                    # If still no month/year, try splitting by /
                    if not month and '/' in expiry_part:
                        exp_parts = expiry_part.split('/')
                        if len(exp_parts) == 2:
                            try:
                                month = int(exp_parts[0])
                                yr = int(exp_parts[1])
                                year = 2000 + yr if yr < 100 else yr
                            except:
                                pass
                    
                    # CVV
                    cvv_digits = re.sub(r'\D', '', cvv_part)
                    if 3 <= len(cvv_digits) <= 4:
                        cvv = cvv_digits
                
                elif len(parts) >= 4:
                    # card|mm|yy|cvv or card|mm|yyyy|cvv
                    month_part = parts[1].strip()
                    year_part = parts[2].strip()
                    cvv_part = parts[3].strip() if len(parts) > 3 else ""
                    
                    try:
                        month = int(re.sub(r'\D', '', month_part))
                        yr = int(re.sub(r'\D', '', year_part))
                        year = 2000 + yr if yr < 100 else yr
                    except:
                        pass
                    
                    # CVV
                    cvv_digits = re.sub(r'\D', '', cvv_part)
                    if 3 <= len(cvv_digits) <= 4:
                        cvv = cvv_digits
                
                return {
                    'card_number': card_number,
                    'card_type': card_type,
                    'expiry_month': month if month and 1 <= month <= 12 else None,
                    'expiry_year': year if year and year >= 2020 else None,
                    'cvv': cvv,
                    'raw_text': line[:100]
                }
        
        # Try space-separated format: card mm yy cvv or card mm yyyy cvv
        parts = line.split()
        if len(parts) >= 4:
            card_number = re.sub(r'\D', '', parts[0])
            
            if 13 <= len(card_number) <= 19 and self.luhn_check(card_number):
                card_type = self.detect_card_type(card_number)
                if card_type:
                    try:
                        month = int(parts[1])
                        yr = int(parts[2])
                        year = 2000 + yr if yr < 100 else yr
                        cvv_digits = re.sub(r'\D', '', parts[3])
                        cvv = cvv_digits if 3 <= len(cvv_digits) <= 4 else None
                        
                        return {
                            'card_number': card_number,
                            'card_type': card_type,
                            'expiry_month': month if 1 <= month <= 12 else None,
                            'expiry_year': year if year >= 2020 else None,
                            'cvv': cvv,
                            'raw_text': line[:100]
                        }
                    except:
                        pass
        
        # Try to extract card number and find expiry/cvv nearby
        return self.extract_card_info_flexible(line)
    
    def extract_card_info_flexible(self, text: str) -> Optional[Dict]:
        """Extract card info from text with flexible parsing"""
        if not text:
            return None
        
        # Find potential card numbers (13-19 digits)
        card_matches = re.findall(r'\b(\d{13,19})\b', text)
        
        for card_number in card_matches:
            if not self.luhn_check(card_number):
                continue
            
            card_type = self.detect_card_type(card_number)
            if not card_type:
                continue
            
            # Find expiry date patterns nearby
            month = None
            year = None
            cvv = None
            
            # Look for expiry patterns
            expiry_patterns = [
                r'(0[1-9]|1[0-2])[/\-\s](20\d{2})',  # MM/YYYY or MM-YYYY or MM YYYY
                r'(0[1-9]|1[0-2])[/\-\s](\d{2})\b',   # MM/YY or MM-YY or MM YY
                r'\b(0[1-9]|1[0-2])\s+(\d{2,4})\b',   # MM YY or MM YYYY
            ]
            
            for pattern in expiry_patterns:
                match = re.search(pattern, text)
                if match:
                    month = int(match.group(1))
                    yr = int(match.group(2))
                    year = 2000 + yr if yr < 100 else yr
                    break
            
            # Look for CVV (3-4 digits, not part of card number, not year)
            cvv_matches = re.findall(r'\b(\d{3,4})\b', text)
            for cvv_candidate in cvv_matches:
                cvv_int = int(cvv_candidate)
                # Skip if it's the card number, a year, or month
                if cvv_candidate in card_number:
                    continue
                if 2020 <= cvv_int <= 2040:
                    continue
                if len(cvv_candidate) == 2:
                    continue
                if 3 <= len(cvv_candidate) <= 4:
                    cvv = cvv_candidate
                    break
            
            return {
                'card_number': card_number,
                'card_type': card_type,
                'expiry_month': month if month and 1 <= month <= 12 else None,
                'expiry_year': year if year and year >= 2020 else None,
                'cvv': cvv,
                'raw_text': text[:100]
            }
        
        return None
    
    def parse_message(self, message_text: str) -> List[Dict]:
        """Parse a message and extract all card information"""
        if not message_text:
            return []
        
        cards_found = []
        seen_cards = set()
        
        # Split by newlines and process each line
        lines = message_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            card_info = self.parse_card_line(line)
            if card_info:
                # Avoid duplicates
                key = card_info['card_number']
                if key not in seen_cards:
                    seen_cards.add(key)
                    cards_found.append(card_info)
        
        return cards_found
