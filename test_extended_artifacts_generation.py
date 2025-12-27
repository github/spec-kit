"""
Test script to validate extended artifacts generation.

This demonstrates the new LLM-powered generation methods added in Phase 2.
"""

import asyncio
from pathlib import Path
from speckit import SpecKit

# Configure test environment
TEST_PROJECT = Path("./test-project-artifacts")
TEST_PROJECT.mkdir(exist_ok=True)

# Initialize SpecKit
kit = SpecKit(TEST_PROJECT)

print("=" * 80)
print("TESTING EXTENDED ARTIFACTS GENERATION (Phase 2)")
print("=" * 80)


async def test_full_workflow():
    """Test complete workflow with extended artifacts."""

    # Step 1: Generate Specification
    print("\n[1/7] Generating specification...")
    spec = await kit.specify_async(
        """
        Add user authentication to the application with:
        - Email/password registration and login
        - JWT-based session management
        - Password reset via email
        - OAuth integration (Google, GitHub)
        - Multi-factor authentication (optional)
        """
    )
    kit.save(spec)
    print(f"✓ Specification saved: {spec.feature_id}")

    # Step 2: Generate Technical Plan
    print("\n[2/7] Generating technical plan...")
    plan = await kit.plan_async(spec)
    kit.save(plan)
    print(f"✓ Technical plan saved")

    # Step 3: Generate Data Model
    print("\n[3/7] Generating data model...")
    data_model = await kit.generate_data_model_async(spec, plan)
    kit.storage.save_data_model(data_model, spec.feature_id)
    print(f"✓ Data model saved: {len(data_model.entities)} entities")
    for entity in data_model.entities:
        print(f"  - {entity.name}: {len(entity.fields)} fields")

    # Step 4: Generate Research Findings
    print("\n[4/7] Generating research findings...")
    research = await kit.generate_research_async(plan)
    kit.storage.save_research(research, spec.feature_id)
    print(f"✓ Research saved: {len(research.decisions)} technology decisions")
    for decision in research.decisions:
        print(f"  - {decision.decision_name}: {decision.selected_option}")

    # Step 5: Generate API Contract
    print("\n[5/7] Generating API contract...")
    contract = await kit.generate_api_contract_async(spec, plan)
    kit.storage.save_api_contract(contract, spec.feature_id)
    print(f"✓ API contract saved: {len(contract.endpoints)} endpoints")
    for endpoint in contract.endpoints:
        print(f"  - {endpoint.method} {endpoint.path}")

    # Step 6: Generate Quality Checklist
    print("\n[6/7] Generating quality checklist...")
    checklist = await kit.generate_checklist_async(spec)
    kit.storage.save_checklist(checklist, spec.feature_id)
    total_items = (
        len(checklist.content_quality)
        + len(checklist.requirement_completeness or [])
        + len(checklist.feature_readiness or [])
    )
    print(f"✓ Checklist saved: {total_items} validation items")
    print(f"  - Overall status: {checklist.overall_status}")

    # Step 7: Generate Quickstart Guide
    print("\n[7/7] Generating quickstart guide...")
    quickstart = await kit.generate_quickstart_async(spec, plan)
    kit.storage.save_quickstart(quickstart, spec.feature_id)
    print(f"✓ Quickstart saved:")
    print(f"  - {len(quickstart.prerequisites)} prerequisites")
    print(f"  - {len(quickstart.installation_steps)} installation steps")
    print(f"  - {len(quickstart.usage_examples)} usage examples")

    print("\n" + "=" * 80)
    print("ALL ARTIFACTS GENERATED SUCCESSFULLY!")
    print("=" * 80)

    # Display file structure
    print(f"\nGenerated files in: {TEST_PROJECT}/specs/{spec.feature_id}/")
    spec_dir = TEST_PROJECT / "specs" / spec.feature_id
    if spec_dir.exists():
        for file_path in sorted(spec_dir.rglob("*")):
            if file_path.is_file():
                rel_path = file_path.relative_to(spec_dir)
                size = file_path.stat().st_size
                print(f"  - {rel_path} ({size:,} bytes)")


# Run the test
if __name__ == "__main__":
    print("\n⚠️  This test will call the LLM API and may incur costs.")
    print("Make sure you have ANTHROPIC_API_KEY or OPENAI_API_KEY set.\n")

    try:
        asyncio.run(test_full_workflow())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
