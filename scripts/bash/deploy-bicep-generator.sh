#!/bin/bash
# Production deployment script for Bicep Generator feature

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Default values
DRY_RUN=false
SKIP_TESTS=false
SKIP_BUILD=false
ENVIRONMENT="production"
PUBLISH_PYPI=false

# Help function
show_help() {
    cat << EOF
Usage: ${0##*/} [OPTIONS]

Deploy Bicep Generator feature to production

OPTIONS:
    -h, --help              Show this help message
    -n, --dry-run           Show what would be done without deploying
    -t, --skip-tests        Skip running tests before deployment
    -b, --skip-build        Skip building distribution packages
    -e, --environment ENV   Target environment (dev, staging, production)
    -p, --publish           Publish to PyPI
    -v, --version VERSION   Override version (default: from pyproject.toml)

EXAMPLES:
    ${0##*/}                                    # Full production deployment
    ${0##*/} -n                                 # Dry-run to see what would happen
    ${0##*/} -e staging                         # Deploy to staging
    ${0##*/} -t                                 # Skip tests (not recommended)
    ${0##*/} -p                                 # Build and publish to PyPI

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -n|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -t|--skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -b|--skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -p|--publish)
            PUBLISH_PYPI=true
            shift
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Get version from pyproject.toml if not specified
if [ -z "$VERSION" ]; then
    VERSION=$(grep -E '^version = ' "$REPO_ROOT/pyproject.toml" | sed -E 's/version = "(.*)"/\1/')
fi

echo -e "${GREEN}=== Bicep Generator Deployment ===${NC}"
echo "Version: $VERSION"
echo "Environment: $ENVIRONMENT"
echo "Dry Run: $DRY_RUN"
echo "Skip Tests: $SKIP_TESTS"
echo "Skip Build: $SKIP_BUILD"
echo "Publish to PyPI: $PUBLISH_PYPI"
echo ""

# Change to repo root
cd "$REPO_ROOT"

# Step 1: Validate environment
echo -e "${BLUE}Step 1: Validating environment...${NC}"

# Check if git working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}Warning: Working directory has uncommitted changes${NC}"
    if [ "$DRY_RUN" = false ]; then
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}Deployment cancelled${NC}"
            exit 1
        fi
    fi
fi

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Check required tools
echo "Checking required tools..."
for tool in git pip pytest; do
    if ! command -v $tool &> /dev/null; then
        echo -e "${RED}Error: Required tool '$tool' not found${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✓ Environment validated${NC}"
echo ""

# Step 2: Run tests
if [ "$SKIP_TESTS" = false ]; then
    echo -e "${BLUE}Step 2: Running tests...${NC}"
    
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}Would run: pytest tests/bicep -m 'not azure' --cov=src/specify_cli/bicep --cov-fail-under=80${NC}"
    else
        pytest tests/bicep -m "not azure" --cov=src/specify_cli/bicep --cov-fail-under=80
        if [ $? -ne 0 ]; then
            echo -e "${RED}✗ Tests failed${NC}"
            exit 1
        fi
    fi
    
    echo -e "${GREEN}✓ Tests passed${NC}"
    echo ""
else
    echo -e "${YELLOW}Skipping tests (not recommended for production)${NC}"
    echo ""
fi

# Step 3: Build distribution
if [ "$SKIP_BUILD" = false ]; then
    echo -e "${BLUE}Step 3: Building distribution...${NC}"
    
    # Clean previous builds
    if [ "$DRY_RUN" = false ]; then
        rm -rf dist/ build/ *.egg-info
    else
        echo -e "${YELLOW}Would clean: dist/, build/, *.egg-info${NC}"
    fi
    
    # Install build dependencies
    if [ "$DRY_RUN" = false ]; then
        pip install --upgrade build twine
    else
        echo -e "${YELLOW}Would install: build, twine${NC}"
    fi
    
    # Build package
    if [ "$DRY_RUN" = false ]; then
        python -m build
        
        # Check distribution
        twine check dist/*
        if [ $? -ne 0 ]; then
            echo -e "${RED}✗ Distribution check failed${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}Would run: python -m build${NC}"
        echo -e "${YELLOW}Would run: twine check dist/*${NC}"
    fi
    
    echo -e "${GREEN}✓ Distribution built${NC}"
    echo ""
else
    echo -e "${YELLOW}Skipping build${NC}"
    echo ""
fi

# Step 4: Tag release
echo -e "${BLUE}Step 4: Creating git tag...${NC}"

TAG="v$VERSION"
if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Tag $TAG already exists${NC}"
else
    if [ "$DRY_RUN" = false ]; then
        git tag -a "$TAG" -m "Release $TAG - Bicep Generator Feature"
        echo -e "${GREEN}✓ Created tag $TAG${NC}"
        echo -e "${YELLOW}Push with: git push origin $TAG${NC}"
    else
        echo -e "${YELLOW}Would create tag: $TAG${NC}"
    fi
fi
echo ""

# Step 5: Publish to PyPI (optional)
if [ "$PUBLISH_PYPI" = true ]; then
    echo -e "${BLUE}Step 5: Publishing to PyPI...${NC}"
    
    if [ "$DRY_RUN" = false ]; then
        # Check if PYPI_API_TOKEN is set
        if [ -z "$PYPI_API_TOKEN" ]; then
            echo -e "${RED}Error: PYPI_API_TOKEN environment variable not set${NC}"
            exit 1
        fi
        
        twine upload dist/* --skip-existing
        if [ $? -ne 0 ]; then
            echo -e "${RED}✗ PyPI upload failed${NC}"
            exit 1
        fi
        
        echo -e "${GREEN}✓ Published to PyPI${NC}"
    else
        echo -e "${YELLOW}Would run: twine upload dist/*${NC}"
    fi
    echo ""
else
    echo -e "${YELLOW}Skipping PyPI publication${NC}"
    echo ""
fi

# Step 6: Summary
echo -e "${GREEN}=== Deployment Summary ===${NC}"
echo "Version: $VERSION"
echo "Tag: $TAG"
echo "Environment: $ENVIRONMENT"
if [ "$PUBLISH_PYPI" = true ] && [ "$DRY_RUN" = false ]; then
    echo "PyPI: https://pypi.org/project/specify-cli/$VERSION/"
fi
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}This was a dry-run. No changes were made.${NC}"
    echo "Run without --dry-run to perform actual deployment."
else
    echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Push the tag: git push origin $TAG"
    echo "2. Create GitHub release with notes from docs/bicep-generator/RELEASE-NOTES.md"
    if [ "$PUBLISH_PYPI" = false ]; then
        echo "3. Optionally publish to PyPI: $0 -p"
    fi
fi
