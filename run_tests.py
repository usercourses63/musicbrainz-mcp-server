#!/usr/bin/env python3
"""
Test runner for MusicBrainz MCP server.

This script provides different test execution modes and generates
comprehensive test reports with coverage information.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    if description:
        print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    return result.returncode == 0


def check_dependencies():
    """Check that required dependencies are installed."""
    print("Checking test dependencies...")
    
    required_packages = [
        "pytest",
        "pytest-asyncio",
        "httpx",
        "fastmcp",
        "pydantic"
    ]
    
    optional_packages = [
        "pytest-cov",
        "pytest-html",
        "pytest-timeout",
        "pytest-xdist"
    ]
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_required.append(package)
    
    for package in optional_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_optional.append(package)
    
    if missing_required:
        print(f"❌ Missing required packages: {', '.join(missing_required)}")
        print("Install with: pip install " + " ".join(missing_required))
        return False
    
    if missing_optional:
        print(f"⚠️  Missing optional packages: {', '.join(missing_optional)}")
        print("Install with: pip install " + " ".join(missing_optional))
    
    print("✅ All required dependencies are available")
    return True


def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests only."""
    cmd = ["python", "-m", "pytest", "-m", "unit"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=src/musicbrainz_mcp",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing"
        ])
    
    return run_command(cmd, "Unit Tests")


def run_integration_tests(verbose=False):
    """Run integration tests only."""
    cmd = ["python", "-m", "pytest", "-m", "integration and not api"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "Integration Tests (No API)")


def run_api_tests(verbose=False):
    """Run API tests (requires internet)."""
    cmd = ["python", "-m", "pytest", "-m", "api"]
    
    if verbose:
        cmd.append("-v")
    
    print("\n⚠️  API tests require internet connection and may be slow")
    return run_command(cmd, "API Tests (Real MusicBrainz API)")


def run_all_tests(verbose=False, coverage=False, include_api=False):
    """Run all tests."""
    cmd = ["python", "-m", "pytest"]
    
    if not include_api:
        cmd.extend(["-m", "not api"])
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=src/musicbrainz_mcp",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ])
    
    description = "All Tests"
    if not include_api:
        description += " (Excluding API Tests)"
    
    return run_command(cmd, description)


def run_specific_test(test_path, verbose=False):
    """Run a specific test file or test function."""
    cmd = ["python", "-m", "pytest", test_path]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, f"Specific Test: {test_path}")


def run_performance_tests():
    """Run performance-related tests."""
    cmd = ["python", "-m", "pytest", "-m", "slow", "-v"]
    return run_command(cmd, "Performance Tests")


def generate_test_report():
    """Generate comprehensive test report."""
    print("\n" + "="*60)
    print("Generating Comprehensive Test Report")
    print("="*60)
    
    # Run tests with coverage and HTML report
    cmd = [
        "python", "-m", "pytest",
        "-m", "not api",  # Exclude API tests for reliability
        "--cov=src/musicbrainz_mcp",
        "--cov-report=html:htmlcov",
        "--cov-report=term-missing",
        "--cov-report=xml:coverage.xml",
        "--html=test_report.html",
        "--self-contained-html",
        "-v"
    ]
    
    success = run_command(cmd, "Test Report Generation")
    
    if success:
        print("\n✅ Test report generated successfully!")
        print("📊 Coverage report: htmlcov/index.html")
        print("📋 Test report: test_report.html")
    
    return success


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Test runner for MusicBrainz MCP server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --unit                    # Run unit tests only
  python run_tests.py --integration             # Run integration tests
  python run_tests.py --all --coverage          # Run all tests with coverage
  python run_tests.py --api                     # Run API tests (requires internet)
  python run_tests.py --specific tests/test_client.py  # Run specific test file
  python run_tests.py --report                  # Generate comprehensive report
        """
    )
    
    # Test selection options
    test_group = parser.add_mutually_exclusive_group(required=True)
    test_group.add_argument("--unit", action="store_true", help="Run unit tests only")
    test_group.add_argument("--integration", action="store_true", help="Run integration tests")
    test_group.add_argument("--api", action="store_true", help="Run API tests (requires internet)")
    test_group.add_argument("--all", action="store_true", help="Run all tests")
    test_group.add_argument("--performance", action="store_true", help="Run performance tests")
    test_group.add_argument("--specific", metavar="TEST_PATH", help="Run specific test file or function")
    test_group.add_argument("--report", action="store_true", help="Generate comprehensive test report")
    
    # Options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true", help="Generate coverage report")
    parser.add_argument("--include-api", action="store_true", help="Include API tests in --all mode")
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies and exit")
    
    args = parser.parse_args()
    
    # Change to project root directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Check dependencies
    if args.check_deps:
        success = check_dependencies()
        sys.exit(0 if success else 1)
    
    if not check_dependencies():
        sys.exit(1)
    
    # Run selected tests
    success = False
    
    if args.unit:
        success = run_unit_tests(args.verbose, args.coverage)
    elif args.integration:
        success = run_integration_tests(args.verbose)
    elif args.api:
        success = run_api_tests(args.verbose)
    elif args.all:
        success = run_all_tests(args.verbose, args.coverage, args.include_api)
    elif args.performance:
        success = run_performance_tests()
    elif args.specific:
        success = run_specific_test(args.specific, args.verbose)
    elif args.report:
        success = generate_test_report()
    
    # Print summary
    print("\n" + "="*60)
    if success:
        print("🎉 Tests completed successfully!")
    else:
        print("❌ Tests failed!")
    print("="*60)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
