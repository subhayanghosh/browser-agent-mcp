#!/usr/bin/env python3
"""
Browser Agent MCP - Main Entry Point
Advanced web scraping with AI-powered challenge solving and stealth capabilities.
"""

import asyncio
import argparse
import sys
import os
from src.scrapers.zillow import main as zillow_main


def main():
    """Main entry point for the browser agent application"""
    parser = argparse.ArgumentParser(
        description="Browser Agent MCP - Advanced web scraping with AI challenge solving",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py zillow --city "Austin, TX" --output results.json
  python main.py zillow --city "New York, NY" --max-properties 50
  python main.py zillow --help
        """
    )

    subparsers = parser.add_subparsers(
        dest='command', help='Available commands')

    # Zillow scraper subcommand
    zillow_parser = subparsers.add_parser(
        'zillow', help='Scrape Zillow for property data')
    zillow_parser.add_argument(
        '--city', default='Austin, TX', help='City to search for (default: Austin, TX)')
    zillow_parser.add_argument('--output', default='zillow_results.json',
                               help='Output file (default: zillow_results.json)')
    zillow_parser.add_argument('--max-properties', type=int, default=20,
                               help='Maximum properties to collect (default: 20)')
    zillow_parser.add_argument(
        '--headless', action='store_true', help='Run in headless mode')
    zillow_parser.add_argument(
        '--proxy', help='Proxy server (e.g., http://user:pass@host:port)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Set environment variables from arguments
    os.environ['ZILLOW_CITY'] = args.city
    os.environ['ZILLOW_OUTPUT'] = args.output
    os.environ['ZILLOW_MAX_PROPERTIES'] = str(args.max_properties)
    if args.proxy:
        os.environ['PROXY'] = args.proxy
    if args.headless:
        os.environ['HEADLESS'] = 'true'

    try:
        if args.command == 'zillow':
            print(f"🤖 Starting Zillow scraper...")
            print(f"   City: {args.city}")
            print(f"   Output: {args.output}")
            print(f"   Max Properties: {args.max_properties}")
            print(f"   Headless: {args.headless}")
            if args.proxy:
                print(f"   Proxy: {args.proxy}")
            print()

            asyncio.run(zillow_main())
        else:
            print(f"❌ Unknown command: {args.command}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
