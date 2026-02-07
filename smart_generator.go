package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"math/rand"
	"os"
	"sort"
	"strconv"
	"strings"
	"time"
)

type Card struct {
	CardNumber string `json:"card_number"`
	Month      string `json:"month"`
	Year       string `json:"year"`
	CVV        string `json:"cvv"`
	CardType   string `json:"card_type"`
	Level      string `json:"level"`
	Bank       string `json:"bank"`
	Country    string `json:"country"`
}

type PatternData struct {
	Prefix          string
	SuffixDigits    [][]int       // All observed digits at each suffix position
	Months          []string      // All observed months
	Years           []string      // All observed years
	CVVs            []string      // All observed CVVs
	Bank            string
	Country         string
	CardType        string
	Level           string
	Count           int
	Cards           []Card
}

type GeneratedCard struct {
	CardNumber string `json:"card_number"`
	Month      string `json:"month"`
	Year       string `json:"year"`
	CVV        string `json:"cvv"`
	Expiry     string `json:"expiry"`
	CardType   string `json:"card_type"`
	Level      string `json:"level"`
	Bank       string `json:"bank"`
	Country    string `json:"country"`
	BIN        string `json:"bin"`
}

func main() {
	rand.Seed(time.Now().UnixNano())

	fmt.Println("╔════════════════════════════════════════════════════════════════╗")
	fmt.Println("║  🧠 SMART PATTERN-BASED CARD GENERATOR                         ║")
	fmt.Println("║  Reference real patterns + Diverse CVV/Expiry generation       ║")
	fmt.Println("╚════════════════════════════════════════════════════════════════╝")

	// Load real cards
	cards, err := loadCards("cards_realtime.json")
	if err != nil {
		fmt.Printf("❌ Error: %v\n", err)
		return
	}
	fmt.Printf("\n✅ Loaded %d working cards as reference\n", len(cards))

	// Build pattern database from real cards
	fmt.Println("\n🔬 Building pattern database from real cards...")
	patterns := buildPatternDatabase(cards)
	fmt.Printf("   Found %d unique patterns with 2+ cards\n", len(patterns))

	// Analyze real CVV and expiry distributions
	allCVVs, allMonths, allYears := analyzeDistributions(cards)
	fmt.Printf("   Unique CVVs: %d, Months: %d, Years: %d\n", len(allCVVs), len(allMonths), len(allYears))

	// Generate cards
	fmt.Println("\n💳 Generating smart pattern-based cards...")
	
	// Sort patterns by quality
	sortedPatterns := sortPatternsByQuality(patterns)

	// Generate different quantities
	gen500 := generateSmartCards(sortedPatterns, 500, allCVVs, allMonths, allYears)
	gen1000 := generateSmartCards(sortedPatterns, 1000, allCVVs, allMonths, allYears)
	gen2000 := generateSmartCards(sortedPatterns, 2000, allCVVs, allMonths, allYears)

	// Save outputs
	saveCards(gen500, "smart_500")
	saveCards(gen1000, "smart_1000")
	saveCards(gen2000, "smart_2000")

	// Print summary
	printSummary(gen1000)
}

func loadCards(filename string) ([]Card, error) {
	file, err := os.Open(filename)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	var cards []Card
	scanner := bufio.NewScanner(file)
	buf := make([]byte, 0, 64*1024)
	scanner.Buffer(buf, 1024*1024)

	for scanner.Scan() {
		var card Card
		if err := json.Unmarshal(scanner.Bytes(), &card); err != nil {
			continue
		}
		if len(card.CardNumber) >= 15 {
			cards = append(cards, card)
		}
	}
	return cards, scanner.Err()
}

func buildPatternDatabase(cards []Card) map[string]*PatternData {
	patterns := make(map[string]*PatternData)

	for _, card := range cards {
		cn := card.CardNumber
		if len(cn) < 16 {
			continue
		}

		// Use 8-digit prefix as pattern key
		prefix := cn[:8]
		suffix := cn[8:]

		if _, exists := patterns[prefix]; !exists {
			patterns[prefix] = &PatternData{
				Prefix:       prefix,
				SuffixDigits: make([][]int, 8),
			}
			for i := 0; i < 8; i++ {
				patterns[prefix].SuffixDigits[i] = []int{}
			}
		}

		p := patterns[prefix]
		p.Count++
		p.Cards = append(p.Cards, card)

		// Record suffix digits at each position
		for i, ch := range suffix {
			if i < 8 {
				digit := int(ch - '0')
				if digit >= 0 && digit <= 9 {
					p.SuffixDigits[i] = append(p.SuffixDigits[i], digit)
				}
			}
		}

		// Record month, year, cvv
		p.Months = append(p.Months, card.Month)
		p.Years = append(p.Years, card.Year)
		p.CVVs = append(p.CVVs, card.CVV)

		// Set metadata
		if p.Bank == "" && card.Bank != "" {
			p.Bank = card.Bank
			p.Country = card.Country
			p.CardType = card.CardType
			p.Level = card.Level
		}
	}

	// Filter to patterns with 2+ cards
	filtered := make(map[string]*PatternData)
	for k, v := range patterns {
		if v.Count >= 2 {
			filtered[k] = v
		}
	}

	return filtered
}

func analyzeDistributions(cards []Card) ([]string, []string, []string) {
	cvvSet := make(map[string]bool)
	monthSet := make(map[string]bool)
	yearSet := make(map[string]bool)

	for _, card := range cards {
		if len(card.CVV) >= 3 {
			cvvSet[card.CVV] = true
		}
		if len(card.Month) == 2 {
			monthSet[card.Month] = true
		}
		if len(card.Year) == 4 {
			yearSet[card.Year] = true
		}
	}

	cvvs := mapKeys(cvvSet)
	months := mapKeys(monthSet)
	years := mapKeys(yearSet)

	return cvvs, months, years
}

func mapKeys(m map[string]bool) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	return keys
}

func sortPatternsByQuality(patterns map[string]*PatternData) []*PatternData {
	var sorted []*PatternData
	for _, p := range patterns {
		if p.Bank != "" {
			sorted = append(sorted, p)
		}
	}

	sort.Slice(sorted, func(i, j int) bool {
		scoreI := calculatePatternScore(sorted[i])
		scoreJ := calculatePatternScore(sorted[j])
		return scoreI > scoreJ
	})

	return sorted
}

func calculatePatternScore(p *PatternData) int {
	score := p.Count * 10

	// Premium banks bonus
	bankUpper := strings.ToUpper(p.Bank)
	if strings.Contains(bankUpper, "CHASE") ||
		strings.Contains(bankUpper, "CITI") ||
		strings.Contains(bankUpper, "AMERICA") ||
		strings.Contains(bankUpper, "WELLS FARGO") ||
		strings.Contains(bankUpper, "CAPITAL ONE") {
		score += 100
	}

	// Premium countries
	if p.Country == "US" || p.Country == "CA" || p.Country == "GB" || p.Country == "UK" {
		score += 50
	}

	// Credit cards bonus
	if strings.Contains(strings.ToUpper(p.Level), "CREDIT") {
		score += 30
	}

	return score
}

func generateSmartCards(patterns []*PatternData, count int, allCVVs, allMonths, allYears []string) []GeneratedCard {
	var result []GeneratedCard

	// Distribute across patterns
	cardsPerPattern := 5
	patternsNeeded := count / cardsPerPattern
	if patternsNeeded > len(patterns) {
		patternsNeeded = len(patterns)
		cardsPerPattern = count / patternsNeeded
	}

	for i := 0; i < patternsNeeded; i++ {
		p := patterns[i%len(patterns)]

		for j := 0; j < cardsPerPattern; j++ {
			card := generateFromPattern(p, allCVVs, allMonths, allYears)
			result = append(result, card)

			if len(result) >= count {
				break
			}
		}

		if len(result) >= count {
			break
		}
	}

	// Shuffle
	rand.Shuffle(len(result), func(i, j int) {
		result[i], result[j] = result[j], result[i]
	})

	return result
}

func generateFromPattern(p *PatternData, allCVVs, allMonths, allYears []string) GeneratedCard {
	// Determine card length
	cardLen := 16
	cvvLen := 3
	if p.CardType == "AMEX" {
		cardLen = 15
		cvvLen = 4
	}
	suffixLen := cardLen - len(p.Prefix)

	// Generate suffix based on observed digit patterns
	suffix := ""
	for pos := 0; pos < suffixLen-1; pos++ { // -1 for Luhn digit
		if pos < len(p.SuffixDigits) && len(p.SuffixDigits[pos]) > 0 {
			// Pick random digit from observed digits at this position
			digits := p.SuffixDigits[pos]
			digit := digits[rand.Intn(len(digits))]
			suffix += strconv.Itoa(digit)
		} else {
			suffix += strconv.Itoa(rand.Intn(10))
		}
	}
	suffix += "0" // Placeholder for Luhn

	// Build card number
	cardNum := p.Prefix + suffix
	cardNum = makeLuhnValid(cardNum)

	// === DIVERSE CVV GENERATION ===
	// Option 1: Pick from this pattern's observed CVVs (30% chance)
	// Option 2: Pick from all observed CVVs (40% chance)
	// Option 3: Generate random CVV (30% chance)
	var cvv string
	r := rand.Float32()
	if r < 0.30 && len(p.CVVs) > 0 {
		// From pattern's CVVs
		cvv = p.CVVs[rand.Intn(len(p.CVVs))]
	} else if r < 0.70 && len(allCVVs) > 0 {
		// From all observed CVVs
		cvv = allCVVs[rand.Intn(len(allCVVs))]
	} else {
		// Random generate
		cvv = generateRandomDigits(cvvLen)
	}
	// Ensure correct length
	for len(cvv) < cvvLen {
		cvv = "0" + cvv
	}
	if len(cvv) > cvvLen {
		cvv = cvv[:cvvLen]
	}

	// === DIVERSE MONTH GENERATION ===
	// Option 1: Pick from this pattern's months (25% chance)
	// Option 2: Pick from all observed months (50% chance)
	// Option 3: Generate random month (25% chance)
	var month string
	r = rand.Float32()
	if r < 0.25 && len(p.Months) > 0 {
		month = p.Months[rand.Intn(len(p.Months))]
	} else if r < 0.75 && len(allMonths) > 0 {
		month = allMonths[rand.Intn(len(allMonths))]
	} else {
		month = fmt.Sprintf("%02d", rand.Intn(12)+1)
	}

	// === DIVERSE YEAR GENERATION ===
	// Option 1: Pick from this pattern's years (25% chance)
	// Option 2: Pick from all observed years (50% chance)
	// Option 3: Generate random valid year (25% chance)
	var year string
	r = rand.Float32()
	if r < 0.25 && len(p.Years) > 0 {
		year = p.Years[rand.Intn(len(p.Years))]
	} else if r < 0.75 && len(allYears) > 0 {
		year = allYears[rand.Intn(len(allYears))]
	} else {
		year = fmt.Sprintf("%d", 2026+rand.Intn(6))
	}

	// Validate year is not expired
	yearInt, _ := strconv.Atoi(year)
	if yearInt < 2026 {
		year = fmt.Sprintf("%d", 2026+rand.Intn(5))
	}

	return GeneratedCard{
		CardNumber: cardNum,
		Month:      month,
		Year:       year,
		CVV:        cvv,
		Expiry:     month + "/" + year,
		CardType:   p.CardType,
		Level:      p.Level,
		Bank:       p.Bank,
		Country:    p.Country,
		BIN:        p.Prefix[:6],
	}
}

func makeLuhnValid(cardNumber string) string {
	partial := cardNumber[:len(cardNumber)-1]
	checkDigit := calculateLuhnCheckDigit(partial)
	return partial + strconv.Itoa(checkDigit)
}

func calculateLuhnCheckDigit(partial string) int {
	sum := 0
	isSecond := true
	for i := len(partial) - 1; i >= 0; i-- {
		d := int(partial[i] - '0')
		if isSecond {
			d *= 2
			if d > 9 {
				d -= 9
			}
		}
		sum += d
		isSecond = !isSecond
	}
	return (10 - (sum % 10)) % 10
}

func generateRandomDigits(n int) string {
	digits := ""
	for i := 0; i < n; i++ {
		digits += strconv.Itoa(rand.Intn(10))
	}
	return digits
}

func saveCards(cards []GeneratedCard, prefix string) {
	// Simple format
	var simple []string
	for _, c := range cards {
		simple = append(simple, fmt.Sprintf("%s|%s|%s|%s", c.CardNumber, c.Month, c.Year, c.CVV))
	}
	filename := prefix + "_cards.txt"
	os.WriteFile(filename, []byte(strings.Join(simple, "\n")), 0644)
	fmt.Printf("   📁 %s (%d cards)\n", filename, len(cards))

	// Detailed format
	var detailed []string
	for _, c := range cards {
		detailed = append(detailed, fmt.Sprintf("%s|%s|%s|%s | %s | %s | %s | %s",
			c.CardNumber, c.Month, c.Year, c.CVV, c.CardType, c.Level, c.Bank, c.Country))
	}
	detailFile := prefix + "_detailed.txt"
	os.WriteFile(detailFile, []byte(strings.Join(detailed, "\n")), 0644)

	// JSON format
	jsonData, _ := json.MarshalIndent(cards, "", "  ")
	jsonFile := prefix + "_cards.json"
	os.WriteFile(jsonFile, jsonData, 0644)
}

func printSummary(cards []GeneratedCard) {
	fmt.Println("\n╔════════════════════════════════════════════════════════════════╗")
	fmt.Println("║  ✅ SMART GENERATION COMPLETE                                  ║")
	fmt.Println("╚════════════════════════════════════════════════════════════════╝")

	// Analyze diversity
	cvvSet := make(map[string]bool)
	monthSet := make(map[string]bool)
	yearSet := make(map[string]bool)
	bankSet := make(map[string]bool)
	typeCount := make(map[string]int)

	for _, c := range cards {
		cvvSet[c.CVV] = true
		monthSet[c.Month] = true
		yearSet[c.Year] = true
		if c.Bank != "" {
			bankSet[c.Bank] = true
		}
		typeCount[c.CardType]++
	}

	fmt.Printf("\n📊 Diversity Stats (from %d cards):\n", len(cards))
	fmt.Printf("   Unique CVVs:   %d (%.1f%% diversity)\n", len(cvvSet), float64(len(cvvSet))/float64(len(cards))*100)
	fmt.Printf("   Unique Months: %d\n", len(monthSet))
	fmt.Printf("   Unique Years:  %d\n", len(yearSet))
	fmt.Printf("   Unique Banks:  %d\n", len(bankSet))

	fmt.Println("\n🃏 By Card Type:")
	for t, c := range typeCount {
		fmt.Printf("   %-12s : %d\n", t, c)
	}

	fmt.Println("\n📁 Output Files:")
	fmt.Println("   smart_500_cards.txt      - 500 cards")
	fmt.Println("   smart_1000_cards.txt     - 1000 cards")
	fmt.Println("   smart_2000_cards.txt     - 2000 cards")
	fmt.Println("   + detailed.txt and .json versions")

	// Print samples showing diversity
	fmt.Println("\n📋 Sample Cards (showing CVV/Expiry diversity):")
	shown := make(map[string]bool)
	count := 0
	for _, c := range cards {
		key := c.BIN
		if !shown[key] && count < 15 {
			shown[key] = true
			count++
			fmt.Printf("   %s|%s|%s|%s [%s] %s\n",
				c.CardNumber, c.Month, c.Year, c.CVV, c.CardType, truncStr(c.Bank, 25))
		}
	}
}

func truncStr(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n-3] + "..."
}
