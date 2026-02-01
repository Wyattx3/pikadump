# Telegram Card Extractor

Telegram channels နဲ့ groups မှ credit/debit card information တွေကို real-time monitoring လုပ်ပြီး extract လုပ်ပေးတဲ့ script ဖြစ်ပါတယ်။

## Features

- ✅ Real-time message monitoring
- ✅ Multiple card format detection (Visa, Mastercard, American Express, JCB, Discover)
- ✅ Card number validation (Luhn algorithm)
- ✅ Multiple output formats (CSV, JSON, TXT)
- ✅ Duplicate detection
- ✅ Phone number authentication
- ✅ Message history processing

## Requirements

- Python 3.7 or higher
- Telegram API credentials (API ID & API Hash)

## Installation

### 1. Clone or Download Project

```bash
cd "card checking"
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Get Telegram API Credentials

1. https://my.telegram.org/apps ကို သွားပါ
2. Login လုပ်ပါ (phone number နဲ့)
3. "API development tools" ကို click လုပ်ပါ
4. App ကို create လုပ်ပါ (app title, short name, platform စတာတွေ ထည့်ပါ)
5. **api_id** နဲ့ **api_hash** ကို copy လုပ်ပါ

### 4. Configure Environment Variables

`.env.example` file ကို `.env` အဖြစ် copy လုပ်ပါ:

```bash
copy .env.example .env
```

`.env` file ကို open လုပ်ပြီး API credentials တွေ ထည့်ပါ:

```
API_ID=your_api_id_here
API_HASH=your_api_hash_here
```

## Usage

### Run the Script

```bash
python main.py
```

### First Time Setup

1. **Phone Number Login**: Script run လုပ်တဲ့အခါ phone number ထည့်ရပါမယ် (country code ပါရပါမယ်)
   - Example: `+959123456789`

2. **Verification Code**: Telegram app မှာ code ရရှိပါမယ်၊ အဲ့ code ကို enter လုပ်ပါ

3. **2FA Password** (if enabled): 2FA ဖွင့်ထားရင် password ထည့်ရပါမယ်

4. **Session File**: Login လုပ်ပြီးရင် `telegram_card_extractor.session` file ကို create လုပ်ပါမယ်။ နောက်တခါ run လုပ်တဲ့အခါ login ထပ်လုပ်စရာမလိုပါဘူး။

### Select Channels/Groups

Script run လုပ်တဲ့အခါ available channels/groups list ကို ပြပါမယ်။

- **Single selection**: Number တခု enter လုပ်ပါ (e.g., `1`)
- **Multiple selection**: Numbers တွေကို comma နဲ့ separate လုပ်ပါ (e.g., `1,2,3`)
- **All**: `all` လို့ enter လုပ်ပါ (channels/groups အားလုံးကို monitor လုပ်မယ်)

### Process Message History (Optional)

Existing messages တွေကို process လုပ်ချင်ရင်:

- **All history**: `yes` enter လုပ်ပါ
- **Last N messages**: Number enter လုပ်ပါ (e.g., `1000`)
- **Skip**: Enter ကို press လုပ်ပါ

### Real-time Monitoring

Script က real-time monitoring mode မှာ run လုပ်နေပါမယ်။

- New messages တွေကို automatically check လုပ်ပါမယ်
- Cards တွေ့ရှိရင် console မှာ display လုပ်ပါမယ်
- Cards တွေကို automatically save လုပ်ပါမယ်

### Stop the Script

`Ctrl+C` ကို press လုပ်ပြီး stop လုပ်နိုင်ပါတယ်။ Script က graceful shutdown လုပ်ပြီး statistics တွေ display လုပ်ပါမယ်။

## Output Files

Extracted cards တွေကို `output/` folder မှာ save လုပ်ပါမယ်:

- **cards.csv**: CSV format (Excel compatible)
- **cards.json**: JSON format (structured data)
- **cards.txt**: Text format (human-readable)

### CSV Format

```csv
card_number,card_type,expiry_month,expiry_year,cvv,source_channel,date_found
5290995290999938,Visa,11,2027,381,Channel Name,2026-02-02 10:30:45
```

### JSON Format

```json
[
  {
    "card_number": "5290995290999938",
    "card_type": "Visa",
    "expiry_month": 11,
    "expiry_year": 2027,
    "cvv": "381",
    "source_channel": "Channel Name",
    "date_found": "2026-02-02 10:30:45"
  }
]
```

## Supported Card Formats

Script က အောက်ပါ format တွေကို detect လုပ်နိုင်ပါတယ်:

- `5290995290999938199936818062 11 2027` (digits with spaces, MM YYYY)
- `53815290999936818062 11 27` (digits with spaces, MM YY)
- `5290 9952 9099 9938` (formatted with spaces)
- `5290-9952-9099-9938` (formatted with dashes)
- `5290995290999938` (no separators)

## Supported Card Types

- **Visa**: Starts with 4, 13-19 digits
- **Mastercard**: Starts with 51-55 or 2221-2720, 16 digits
- **American Express**: Starts with 34 or 37, 15 digits
- **JCB**: Starts with 35, 16 digits
- **Discover**: Starts with 6011, 65, or 644-649, 16 digits

## Configuration

`config.py` file မှာ settings တွေကို modify လုပ်နိုင်ပါတယ်:

- `ALLOWED_CARD_TYPES`: Filter specific card types (empty list = all types)
- `OUTPUT_DIR`: Output directory path
- `SESSION_NAME`: Telegram session file name

## Security Notes

- `.env` file ကို git မှာ commit မလုပ်ပါနဲ့
- `*.session` files တွေကို git မှာ commit မလုပ်ပါနဲ့
- API credentials တွေကို share မလုပ်ပါနဲ့

## Troubleshooting

### "API_ID နဲ့ API_HASH ကို .env file မှာ သတ်မှတ်ပေးရပါမယ်"

`.env` file ကို create လုပ်ပြီး API credentials တွေ ထည့်ပါ။

### "Session file not found"

First time run လုပ်တဲ့အခါ phone number login လုပ်ရပါမယ်။

### "No channels/groups found"

Telegram account မှာ channels/groups တွေ join လုပ်ထားရပါမယ်။

### Cards not detected

- Card numbers တွေက valid format ဖြစ်ရပါမယ်
- Luhn algorithm validation pass ဖြစ်ရပါမယ်
- Card type တွေက supported types ဖြစ်ရပါမယ်

## License

This script is for educational purposes only. Use responsibly and in accordance with Telegram's Terms of Service.
