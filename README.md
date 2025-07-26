# Browser Agent MCP

Advanced web scraping with AI-powered challenge solving and stealth capabilities.

## 🚀 Features

- **🤖 AI Challenge Solver**: Automatically detects and solves anti-bot challenges
- **🕵️ Stealth Mode**: Random fingerprinting and anti-detection techniques
- **🔧 Manual Intervention**: Fallback to manual challenge solving when AI fails
- **📊 Data Collection**: Robust property data extraction from Zillow
- **🔄 Retry Logic**: Multiple attempts with different strategies
- **📸 Debug Support**: Screenshot capture and detailed logging

## 📁 Project Structure

```
browser-agent-mcp/
├── src/
│   ├── core/           # Core functionality
│   ├── utils/          # Utility functions
│   │   └── stealth.py  # Stealth and anti-detection
│   ├── challenges/     # Challenge solving modules
│   │   ├── ai_solver.py      # AI challenge detection and solving
│   │   └── manual_solver.py  # Manual intervention system
│   └── scrapers/       # Web scrapers
│       └── zillow.py   # Zillow property scraper
├── tests/              # Test files
│   ├── test_basic_agent.py
│   ├── test_full_agent.py
│   └── test_comprehensive_agent.py
├── docs/               # Documentation
├── examples/           # Example scripts
├── main.py            # Main entry point
├── setup.py           # Package setup
├── requirements.txt   # Dependencies
└── README.md         # This file
```

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/browser-agent-mcp.git
   cd browser-agent-mcp
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

3. **Install the package** (optional):
   ```bash
   pip install -e .
   ```

## 🚀 Quick Start

### Basic Usage

```bash
# Scrape Zillow for Austin, TX properties
python main.py zillow --city "Austin, TX"

# Scrape with custom output file
python main.py zillow --city "New York, NY" --output ny_properties.json

# Scrape more properties
python main.py zillow --city "Los Angeles, CA" --max-properties 50

# Run in headless mode
python main.py zillow --city "Chicago, IL" --headless

# Use with proxy
python main.py zillow --city "Miami, FL" --proxy "http://user:pass@host:port"
```

### Advanced Usage

```bash
# Run comprehensive tests
python tests/test_comprehensive_agent.py

# Run full agent test
python tests/test_full_agent.py

# Run basic test
python tests/test_basic_agent.py
```

## 🔧 Configuration

### Environment Variables

- `ZILLOW_CITY`: City to search for (default: "Austin, TX")
- `ZILLOW_OUTPUT`: Output file path (default: "zillow_results.json")
- `ZILLOW_MAX_PROPERTIES`: Maximum properties to collect (default: 20)
- `PROXY`: Proxy server URL
- `HEADLESS`: Run in headless mode (set to "true")

### Command Line Options

- `--city`: City to search for
- `--output`: Output file path
- `--max-properties`: Maximum properties to collect
- `--headless`: Run in headless mode
- `--proxy`: Proxy server URL

## 🤖 AI Challenge Solver

The AI challenge solver can handle various types of anti-bot challenges:

- **Press & Hold**: Human-like press and hold interactions
- **CAPTCHA**: Image-based challenges (manual intervention required)
- **Slider Verification**: Drag and drop sliders
- **Checkbox**: "I'm not a robot" checkboxes
- **Cookie Consent**: Automatic cookie acceptance

### Challenge Detection Methods

1. **Computer Vision**: OCR-based text recognition
2. **Element Detection**: Multiple selector strategies
3. **Human-like Interaction**: Natural mouse movements and timing
4. **Retry Logic**: Multiple attempts with different approaches

## 🕵️ Stealth Features

- **Random Fingerprinting**: User agent, viewport, timezone, geolocation
- **Anti-Detection Scripts**: Masks automation indicators
- **Human-like Behavior**: Natural delays and interactions
- **Proxy Support**: Rotate through different IP addresses

## 📊 Data Collection

The scraper collects the following property data:

- **Title/Address**: Property title and address
- **Price**: Property price
- **URL**: Property listing URL
- **Beds**: Number of bedrooms
- **Baths**: Number of bathrooms
- **Sqft**: Square footage

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python tests/test_comprehensive_agent.py
```

## 📝 Examples

### Basic Scraping

```python
from src.scrapers.zillow import main
import asyncio

# Run the scraper
asyncio.run(main())
```

### Custom Configuration

```python
import os
from src.scrapers.zillow import main
import asyncio

# Set custom configuration
os.environ['ZILLOW_CITY'] = 'San Francisco, CA'
os.environ['ZILLOW_OUTPUT'] = 'sf_properties.json'
os.environ['ZILLOW_MAX_PROPERTIES'] = '30'

# Run the scraper
asyncio.run(main())
```

## 🔍 Debugging

The system provides comprehensive debugging features:

- **Screenshot Capture**: Automatic screenshots during challenge solving
- **Detailed Logging**: Step-by-step execution logs
- **Element Detection**: Shows which selectors are working
- **Challenge Analysis**: OCR text detection and classification

Screenshots are saved in the `challenge_screenshots/` directory.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and research purposes only. Please respect website terms of service and robots.txt files. Use responsibly and in accordance with applicable laws and regulations.

## 🆘 Support

For issues and questions:

1. Check the documentation
2. Review existing issues
3. Create a new issue with detailed information
4. Include screenshots and logs if applicable