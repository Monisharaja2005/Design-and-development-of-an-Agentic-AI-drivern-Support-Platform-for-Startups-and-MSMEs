from engine.scheme_crawler import crawl_schemes
from engine.pdf_collector import collect_pdfs
from engine.scheme_parser import parse_schemes

def run():
    print("🚀 Starting REAL Scheme Intelligence Engine")

    crawl_schemes()
    collect_pdfs()
    parse_schemes()

    print("🎉 Scheme Intelligence Engine Completed")

if __name__ == "__main__":
    run()
