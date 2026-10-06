import asyncio
import sys
import os
from src.core.models import TenderInfo
from src.services.documents.parser import DocumentParser
from src.services.scoring.engine import TenderScoringEngine
from src.services.parsers.zakupki import ZakupkiFeedMonitor


async def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else "sample_data/tz_sample_risky.txt"
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    print(f"Reading specification from: {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    feed = ZakupkiFeedMonitor()
    tender = await feed.get_tender_by_id("0373100012324000999")
    if not tender:
        tender = TenderInfo(
            id="0373100012324000999",
            title="Закупка оборудования ЦОД",
            customer="Федеральное ведомство",
            price=48000000.0,
            deadline_date="2026-11-20",
            delivery_days=3,
        )

    engine = TenderScoringEngine()
    print("Evaluating with LLM scoring engine...")
    result = await engine.evaluate(tender=tender, tz_text=text)

    print("\n" + "=" * 60)
    print(f"VERDICT: {result.recommendation.value} (Risk Score: {result.risk_score}/100)")
    print("=" * 60)
    print(f"Summary: {result.summary}")
    print(f"Financials: {result.financial_summary}\n")

    print(f"Identified Risks ({len(result.risks)}):")
    for r in result.risks:
        print(f"  - [{r.category} / {r.severity}]: {r.description}")

    if result.advantages:
        print(f"\nPositive Factors ({len(result.advantages)}):")
        for a in result.advantages:
            print(f"  + {a}")

    if result.missing_docs:
        print(f"\nRequired Licenses / Registries ({len(result.missing_docs)}):")
        for d in result.missing_docs:
            print(f"  * {d}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
