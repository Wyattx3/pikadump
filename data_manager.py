"""
Data Manager
Handles storage and export of extracted card data
"""
import json
import csv
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime
from config import CSV_FILE, JSON_FILE, TXT_FILE


class DataManager:
    """Manages card data storage and export"""
    
    def __init__(self):
        self.csv_file = CSV_FILE
        self.json_file = JSON_FILE
        self.txt_file = TXT_FILE
        
        # Track seen cards to prevent duplicates
        # Key: (card_number, expiry_month, expiry_year)
        self.seen_cards: Set[tuple] = set()
        
        # Load existing cards to track duplicates
        self._load_existing_cards()
    
    def _load_existing_cards(self):
        """Load existing cards from JSON file to track duplicates"""
        if self.json_file.exists():
            try:
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for card in data:
                            key = (
                                card.get('card_number'),
                                card.get('expiry_month'),
                                card.get('expiry_year')
                            )
                            self.seen_cards.add(key)
            except Exception:
                pass
    
    def is_duplicate(self, card_info: Dict) -> bool:
        """
        Check if card is duplicate
        Based on card_number + expiry_month + expiry_year
        """
        key = (
            card_info.get('card_number'),
            card_info.get('expiry_month'),
            card_info.get('expiry_year')
        )
        
        if key in self.seen_cards:
            return True
        
        self.seen_cards.add(key)
        return False
    
    def save_to_csv(self, card_info: Dict):
        """Append card to CSV file"""
        file_exists = self.csv_file.exists()
        
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            fieldnames = [
                'card_number',
                'card_type',
                'expiry_month',
                'expiry_year',
                'cvv',
                'source_channel',
                'date_found'
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # Write header if file is new
            if not file_exists:
                writer.writeheader()
            
            # Prepare row data
            row = {
                'card_number': card_info.get('card_number', ''),
                'card_type': card_info.get('card_type', ''),
                'expiry_month': card_info.get('expiry_month', ''),
                'expiry_year': card_info.get('expiry_year', ''),
                'cvv': card_info.get('cvv', ''),
                'source_channel': card_info.get('source_channel', ''),
                'date_found': card_info.get('date_found', '')
            }
            
            writer.writerow(row)
    
    def save_to_json(self, card_info: Dict):
        """Append card to JSON file"""
        cards = []
        
        # Load existing cards
        if self.json_file.exists():
            try:
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    cards = json.load(f)
                    if not isinstance(cards, list):
                        cards = []
            except Exception:
                cards = []
        
        # Add new card
        cards.append(card_info)
        
        # Save updated list
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(cards, f, indent=2, ensure_ascii=False)
    
    def save_to_txt(self, card_info: Dict):
        """Append card to TXT file in human-readable format"""
        with open(self.txt_file, 'a', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write(f"Card Number: {card_info.get('card_number', 'N/A')}\n")
            f.write(f"Card Type: {card_info.get('card_type', 'N/A')}\n")
            
            expiry_month = card_info.get('expiry_month')
            expiry_year = card_info.get('expiry_year')
            if expiry_month and expiry_year:
                f.write(f"Expiry Date: {expiry_month:02d}/{expiry_year}\n")
            else:
                f.write("Expiry Date: N/A\n")
            
            cvv = card_info.get('cvv')
            if cvv:
                f.write(f"CVV: {cvv}\n")
            else:
                f.write("CVV: N/A\n")
            
            source = card_info.get('source_channel', 'N/A')
            f.write(f"Source: {source}\n")
            
            date_found = card_info.get('date_found', 'N/A')
            f.write(f"Found Date: {date_found}\n")
            
            f.write("=" * 60 + "\n\n")
    
    def save_card(self, card_info: Dict, source_channel: str = "") -> bool:
        """
        Save card to all formats (CSV, JSON, TXT)
        Returns True if saved, False if duplicate
        """
        # Add metadata
        card_info['source_channel'] = source_channel
        card_info['date_found'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Check for duplicates
        if self.is_duplicate(card_info):
            return False
        
        # Save to all formats
        try:
            self.save_to_csv(card_info)
            self.save_to_json(card_info)
            self.save_to_txt(card_info)
            return True
        except Exception as e:
            print(f"Error saving card: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get statistics about saved cards"""
        stats = {
            'total_cards': len(self.seen_cards),
            'by_type': {},
            'by_channel': {}
        }
        
        if self.json_file.exists():
            try:
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    cards = json.load(f)
                    if isinstance(cards, list):
                        for card in cards:
                            # Count by type
                            card_type = card.get('card_type', 'Unknown')
                            stats['by_type'][card_type] = stats['by_type'].get(card_type, 0) + 1
                            
                            # Count by channel
                            channel = card.get('source_channel', 'Unknown')
                            stats['by_channel'][channel] = stats['by_channel'].get(channel, 0) + 1
            except Exception:
                pass
        
        return stats
