#!/bin/bash

#
# Bicep Template Generator for Azure Resources (Bash Edition)
# Cross-platform script for Linux/macOS supporting GitHub Copilot integration
# Feature-parity port of the PowerShell bicep_generator.ps1 script
#

set -euo pipefail

# Script configuration
SCRIPT_NAME="bicep_generator.sh"
SCRIPT_VERSION="2.1.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PYTHON_MODULE="specify_cli.bicep.bicep_generator"
BICEP_TEMPLATES_DIR="$PROJECT_ROOT/templates/bicep"
BICEP_OUTPUT_DIR="$PROJECT_ROOT/bicep-templates"
LOG_DIR="$PROJECT_ROOT/.logs"
CONFIG_FILE="$PROJECT_ROOT/bicep_config.json"

# Default configuration
DEFAULT_REGION="eastus"
DEFAULT_ENVIRONMENT="dev"
DEFAULT_COST_ANALYSIS=true
DEFAULT_SECURITY_ANALYSIS=true
DEFAULT_OUTPUT_FORMAT="bicep"

# Function to print colored output
print_color() {
    local color=$1
    shift
    echo -e "${color}$*${NC}"
}

# Function to print info messages
print_info() {
    print_color "$BLUE" "[INFO] $*"
}

# Function to print success messages
print_success() {
    print_color "$GREEN" "[SUCCESS] $*"
}

# Function to print warning messages
print_warning() {
    print_color "$YELLOW" "[WARNING] $*"
}

# Function to print error messages
print_error() {
    print_color "$RED" "[ERROR] $*" >&2
}

# Function to print section headers
print_header() {
    print_color "$CYAN" "
============================================
$*
============================================"
}

# Function to show help
show_help() {
    cat << EOF
${GREEN}Bicep Template Generator for Azure Resources${NC}

${CYAN}USAGE:${NC}
    $SCRIPT_NAME [COMMAND] [OPTIONS]

${CYAN}COMMANDS:${NC}
    analyze         Analyze project requirements and generate analysis
    generate        Generate Bicep templates from analysis
    validate        Validate generated Bicep templates
    deploy          Deploy templates to Azure (ARM format)
    update          Update existing templates with new requirements
    dependencies    Analyze and resolve template dependencies
    sync            Synchronize templates across environments
    review          Review architecture and provide recommendations
    estimate-cost   Estimate deployment costs
    security        Analyze security posture
    explain         Explain template components and architecture
    
${CYAN}GLOBAL OPTIONS:${NC}
    --project-path PATH     Path to project directory (default: current directory)
    --output-dir PATH       Output directory for templates (default: ./bicep-templates)
    --region REGION         Target Azure region (default: $DEFAULT_REGION)
    --environment ENV       Target environment (default: $DEFAULT_ENVIRONMENT)
    --config-file PATH      Configuration file path (default: ./bicep_config.json)
    --log-level LEVEL       Logging level (DEBUG|INFO|WARNING|ERROR) (default: INFO)
    --no-color              Disable colored output
    --json                  Output results in JSON format
    --quiet                 Suppress non-essential output
    --dry-run               Show what would be done without making changes
    --help                  Show this help message
    --version               Show version information

${CYAN}ANALYZE OPTIONS:${NC}
    --include-patterns PATTERNS    File patterns to include (comma-separated)
    --exclude-patterns PATTERNS    File patterns to exclude (comma-separated)
    --analysis-depth LEVEL         Analysis depth (basic|detailed|comprehensive) (default: detailed)
    --include-dependencies         Include dependency analysis
    --output-file FILE             Save analysis to specific file

${CYAN}GENERATE OPTIONS:${NC}
    --template-type TYPE           Template type (webapp|api|database|storage|all) (default: all)
    --architecture ARCH            Architecture pattern (basic|standard|premium) (default: standard)
    --include-monitoring           Include monitoring and logging resources
    --include-security             Include security configurations (default: true)
    --cost-optimization            Enable cost optimization features (default: true)
    --format FORMAT                Output format (bicep|arm|both) (default: bicep)
    --template-style STYLE         Template style (minimal|comprehensive) (default: comprehensive)

${CYAN}VALIDATE OPTIONS:${NC}
    --template-path PATH           Specific template file to validate
    --validation-level LEVEL       Validation level (syntax|semantic|deployment) (default: semantic)
    --skip-cost-analysis           Skip cost analysis during validation
    --skip-security-analysis       Skip security analysis during validation

${CYAN}UPDATE OPTIONS:${NC}
    --template-path PATH           Template file to update
    --strategy STRATEGY            Update strategy (merge|replace|interactive) (default: interactive)
    --backup                       Create backup before updating (default: true)
    --version-increment TYPE       Version increment (major|minor|patch) (default: patch)

${CYAN}EXAMPLES:${NC}
    # Analyze current project
    $SCRIPT_NAME analyze --project-path . --analysis-depth comprehensive
    
    # Generate templates for web application
    $SCRIPT_NAME generate --template-type webapp --architecture standard --region westus2
    
    # Validate all templates
    $SCRIPT_NAME validate --validation-level deployment
    
    # Update existing template
    $SCRIPT_NAME update --template-path ./templates/webapp.bicep --strategy interactive
    
    # Estimate costs
    $SCRIPT_NAME estimate-cost --template-path ./templates/webapp.bicep
    
    # Generate with custom configuration
    $SCRIPT_NAME generate --config-file ./custom-config.json --output-dir ./custom-output

${CYAN}CONFIGURATION FILE FORMAT (JSON):${NC}
    {
        "project": {
            "name": "MyProject",
            "description": "Project description",
            "version": "1.0.0"
        },
        "azure": {
            "subscriptionId": "your-subscription-id",
            "resourceGroupPrefix": "rg-myproject",
            "defaultRegion": "$DEFAULT_REGION",
            "defaultEnvironment": "$DEFAULT_ENVIRONMENT"
        },
        "templates": {
            "outputFormat": "$DEFAULT_OUTPUT_FORMAT",
            "includeMonitoring": true,
            "includeSecurity": $DEFAULT_SECURITY_ANALYSIS,
            "costOptimization": $DEFAULT_COST_ANALYSIS
        },
        "analysis": {
            "includePatterns": ["**/*.py", "**/*.js", "**/*.cs"],
            "excludePatterns": ["**/node_modules/**", "**/__pycache__/**"],
            "analysisDepth": "detailed"
        }
    }

${CYAN}ENVIRONMENT VARIABLES:${NC}
    BICEP_GENERATOR_CONFIG      Path to configuration file
    AZURE_SUBSCRIPTION_ID       Default Azure subscription ID
    AZURE_RESOURCE_GROUP        Default resource group name
    BICEP_TEMPLATES_DIR         Default templates directory
    BICEP_OUTPUT_DIR            Default output directory
    BICEP_LOG_LEVEL             Default logging level

EOF
}

# Function to show version
show_version() {
    echo "$SCRIPT_NAME version $SCRIPT_VERSION"
    echo "Compatible with PowerShell bicep_generator.ps1 v2.1.0"
    echo "Python module: $PYTHON_MODULE"
}

# Function to check prerequisites
check_prerequisites() {
    local errors=0
    
    print_header "Checking Prerequisites"
    
    # Check Python
    if ! command -v python3 >/dev/null 2>&1; then
        print_error "Python 3 is required but not installed"
        ((errors++))
    else
        local python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_info "Python version: $python_version"
        
        # Check if Python module is available
        if ! python3 -c "import $PYTHON_MODULE" >/dev/null 2>&1; then
            print_error "Python module '$PYTHON_MODULE' not found"
            print_info "Install with: pip install -e ."
            ((errors++))
        else
            print_success "Python module '$PYTHON_MODULE' is available"
        fi
    fi
    
    # Check Azure CLI
    if ! command -v az >/dev/null 2>&1; then
        print_warning "Azure CLI not found - some features will be limited"
        print_info "Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    else
        local az_version=$(az --version 2>/dev/null | head -n1 | cut -d' ' -f2)
        print_info "Azure CLI version: $az_version"
        
        # Check Azure login status
        if az account show >/dev/null 2>&1; then
            local subscription=$(az account show --query name -o tsv 2>/dev/null)
            print_success "Logged into Azure subscription: $subscription"
        else
            print_warning "Not logged into Azure - run 'az login' for full functionality"
        fi
    fi
    
    # Check Bicep CLI
    if ! command -v bicep >/dev/null 2>&1; then
        print_warning "Bicep CLI not found - template compilation will be limited"
        print_info "Install from: https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/install"
    else
        local bicep_version=$(bicep --version 2>/dev/null | head -n1)
        print_info "Bicep CLI version: $bicep_version"
    fi
    
    # Check jq for JSON processing
    if ! command -v jq >/dev/null 2>&1; then
        print_warning "jq not found - JSON processing will use Python fallback"
        print_info "Install with: sudo apt-get install jq (Ubuntu) or brew install jq (macOS)"
    else
        print_success "jq available for JSON processing"
    fi
    
    return $errors
}

# Function to create directories
ensure_directories() {
    local dirs=("$BICEP_OUTPUT_DIR" "$LOG_DIR" "$BICEP_TEMPLATES_DIR")
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            print_info "Creating directory: $dir"
            mkdir -p "$dir"
        fi
    done
}

# Function to load configuration
load_config() {
    local config_file="${1:-$CONFIG_FILE}"
    
    if [[ -f "$config_file" ]]; then
        print_info "Loading configuration from: $config_file"
        
        if command -v jq >/dev/null 2>&1; then
            # Use jq if available
            CONFIG_CONTENT=$(cat "$config_file")
        else
            # Fallback to Python
            CONFIG_CONTENT=$(python3 -c "
import json
with open('$config_file') as f:
    print(json.dumps(json.load(f)))
")
        fi
    else
        print_info "No configuration file found, using defaults"
        CONFIG_CONTENT="{}"
    fi
}

# Function to get configuration value
get_config_value() {
    local key="$1"
    local default_value="${2:-}"
    
    if command -v jq >/dev/null 2>&1; then
        echo "$CONFIG_CONTENT" | jq -r "$key // \"$default_value\""
    else
        python3 -c "
import json
import sys
config = json.loads('$CONFIG_CONTENT')
keys = '$key'.split('.')
value = config
try:
    for k in keys:
        if k.startswith('[') and k.endswith(']'):
            value = value[int(k[1:-1])]
        else:
            value = value[k]
    print(value if value is not None else '$default_value')
except:
    print('$default_value')
"
    fi
}

# Function to run Python command
run_python_command() {
    local command="$1"
    shift
    local args=("$@")
    
    print_info "Executing: python3 -m $PYTHON_MODULE $command ${args[*]}"
    
    # Set up environment variables
    export BICEP_PROJECT_ROOT="$PROJECT_ROOT"
    export BICEP_OUTPUT_DIR="$BICEP_OUTPUT_DIR"
    export BICEP_LOG_DIR="$LOG_DIR"
    
    # Run the Python command
    python3 -m "$PYTHON_MODULE" "$command" "${args[@]}"
}

# Function to analyze project
cmd_analyze() {
    print_header "Analyzing Project Requirements"
    
    local args=()
    local project_path="$(pwd)"
    local output_file=""
    local analysis_depth="detailed"
    local include_patterns=""
    local exclude_patterns=""
    local include_dependencies=false
    
    # Parse analyze-specific options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --project-path)
                project_path="$2"
                shift 2
                ;;
            --output-file)
                output_file="$2"
                shift 2
                ;;
            --analysis-depth)
                analysis_depth="$2"
                shift 2
                ;;
            --include-patterns)
                include_patterns="$2"
                shift 2
                ;;
            --exclude-patterns)
                exclude_patterns="$2"
                shift 2
                ;;
            --include-dependencies)
                include_dependencies=true
                shift
                ;;
            *)
                args+=("$1")
                shift
                ;;
        esac
    done
    
    # Build command arguments
    local cmd_args=("--project-path" "$project_path" "--analysis-depth" "$analysis_depth")
    
    [[ -n "$output_file" ]] && cmd_args+=("--output-file" "$output_file")
    [[ -n "$include_patterns" ]] && cmd_args+=("--include-patterns" "$include_patterns")
    [[ -n "$exclude_patterns" ]] && cmd_args+=("--exclude-patterns" "$exclude_patterns")
    [[ "$include_dependencies" == true ]] && cmd_args+=("--include-dependencies")
    
    # Add remaining args
    cmd_args+=("${args[@]}")
    
    run_python_command "analyze" "${cmd_args[@]}"
}

# Function to generate templates
cmd_generate() {
    print_header "Generating Bicep Templates"
    
    local args=()
    local template_type="all"
    local architecture="standard"
    local include_monitoring=false
    local include_security=true
    local cost_optimization=true
    local format="bicep"
    local template_style="comprehensive"
    
    # Parse generate-specific options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --template-type)
                template_type="$2"
                shift 2
                ;;
            --architecture)
                architecture="$2"
                shift 2
                ;;
            --include-monitoring)
                include_monitoring=true
                shift
                ;;
            --include-security)
                include_security=true
                shift
                ;;
            --cost-optimization)
                cost_optimization=true
                shift
                ;;
            --format)
                format="$2"
                shift 2
                ;;
            --template-style)
                template_style="$2"
                shift 2
                ;;
            *)
                args+=("$1")
                shift
                ;;
        esac
    done
    
    # Build command arguments
    local cmd_args=("--template-type" "$template_type" "--architecture" "$architecture")
    cmd_args+=("--format" "$format" "--template-style" "$template_style")
    
    [[ "$include_monitoring" == true ]] && cmd_args+=("--include-monitoring")
    [[ "$include_security" == true ]] && cmd_args+=("--include-security")
    [[ "$cost_optimization" == true ]] && cmd_args+=("--cost-optimization")
    
    # Add remaining args
    cmd_args+=("${args[@]}")
    
    run_python_command "generate" "${cmd_args[@]}"
}

# Function to validate templates
cmd_validate() {
    print_header "Validating Bicep Templates"
    
    local args=()
    local template_path=""
    local validation_level="semantic"
    local skip_cost_analysis=false
    local skip_security_analysis=false
    
    # Parse validate-specific options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --template-path)
                template_path="$2"
                shift 2
                ;;
            --validation-level)
                validation_level="$2"
                shift 2
                ;;
            --skip-cost-analysis)
                skip_cost_analysis=true
                shift
                ;;
            --skip-security-analysis)
                skip_security_analysis=true
                shift
                ;;
            *)
                args+=("$1")
                shift
                ;;
        esac
    done
    
    # Build command arguments
    local cmd_args=("--validation-level" "$validation_level")
    
    [[ -n "$template_path" ]] && cmd_args+=("--template-path" "$template_path")
    [[ "$skip_cost_analysis" == true ]] && cmd_args+=("--skip-cost-analysis")
    [[ "$skip_security_analysis" == true ]] && cmd_args+=("--skip-security-analysis")
    
    # Add remaining args
    cmd_args+=("${args[@]}")
    
    run_python_command "validate" "${cmd_args[@]}"
}

# Function to deploy templates
cmd_deploy() {
    print_header "Deploying Templates to Azure"
    
    # Check Azure CLI login
    if ! az account show >/dev/null 2>&1; then
        print_error "Not logged into Azure. Run 'az login' first."
        exit 1
    fi
    
    run_python_command "deploy" "$@"
}

# Function to update templates
cmd_update() {
    print_header "Updating Existing Templates"
    
    local args=()
    local template_path=""
    local strategy="interactive"
    local backup=true
    local version_increment="patch"
    
    # Parse update-specific options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --template-path)
                template_path="$2"
                shift 2
                ;;
            --strategy)
                strategy="$2"
                shift 2
                ;;
            --no-backup)
                backup=false
                shift
                ;;
            --version-increment)
                version_increment="$2"
                shift 2
                ;;
            *)
                args+=("$1")
                shift
                ;;
        esac
    done
    
    # Build command arguments
    local cmd_args=("--strategy" "$strategy" "--version-increment" "$version_increment")
    
    [[ -n "$template_path" ]] && cmd_args+=("--template-path" "$template_path")
    [[ "$backup" == true ]] && cmd_args+=("--backup")
    
    # Add remaining args
    cmd_args+=("${args[@]}")
    
    run_python_command "update" "${cmd_args[@]}"
}

# Function to analyze dependencies
cmd_dependencies() {
    print_header "Analyzing Template Dependencies"
    run_python_command "dependencies" "$@"
}

# Function to synchronize templates
cmd_sync() {
    print_header "Synchronizing Templates Across Environments"
    run_python_command "sync" "$@"
}

# Function to review architecture
cmd_review() {
    print_header "Reviewing Architecture and Recommendations"
    run_python_command "review" "$@"
}

# Function to estimate costs
cmd_estimate_cost() {
    print_header "Estimating Deployment Costs"
    run_python_command "estimate-cost" "$@"
}

# Function to analyze security
cmd_security() {
    print_header "Analyzing Security Posture"
    run_python_command "security" "$@"
}

# Function to explain templates
cmd_explain() {
    print_header "Explaining Template Components and Architecture"
    run_python_command "explain" "$@"
}

# Function to handle unknown commands
unknown_command() {
    print_error "Unknown command: $1"
    echo
    print_info "Use '$SCRIPT_NAME --help' to see available commands"
    exit 1
}

# Main script logic
main() {
    # Initialize default values from environment or config
    BICEP_TEMPLATES_DIR="${BICEP_TEMPLATES_DIR:-$PROJECT_ROOT/templates/bicep}"
    BICEP_OUTPUT_DIR="${BICEP_OUTPUT_DIR:-$PROJECT_ROOT/bicep-templates}"
    LOG_DIR="${LOG_DIR:-$PROJECT_ROOT/.logs}"
    
    # Parse global options first
    local command=""
    local remaining_args=()
    local show_help_flag=false
    local show_version_flag=false
    local config_file="$CONFIG_FILE"
    local log_level="INFO"
    local no_color=false
    local json_output=false
    local quiet=false
    local dry_run=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help_flag=true
                shift
                ;;
            --version|-v)
                show_version_flag=true
                shift
                ;;
            --config-file)
                config_file="$2"
                shift 2
                ;;
            --project-path)
                PROJECT_ROOT="$2"
                shift 2
                ;;
            --output-dir)
                BICEP_OUTPUT_DIR="$2"
                shift 2
                ;;
            --region)
                export BICEP_DEFAULT_REGION="$2"
                shift 2
                ;;
            --environment)
                export BICEP_DEFAULT_ENVIRONMENT="$2"
                shift 2
                ;;
            --log-level)
                log_level="$2"
                export BICEP_LOG_LEVEL="$log_level"
                shift 2
                ;;
            --no-color)
                no_color=true
                shift
                ;;
            --json)
                json_output=true
                export BICEP_OUTPUT_JSON=true
                shift
                ;;
            --quiet)
                quiet=true
                export BICEP_QUIET=true
                shift
                ;;
            --dry-run)
                dry_run=true
                export BICEP_DRY_RUN=true
                shift
                ;;
            analyze|generate|validate|deploy|update|dependencies|sync|review|estimate-cost|security|explain)
                command="$1"
                shift
                remaining_args=("$@")
                break
                ;;
            *)
                print_error "Unknown option: $1"
                echo
                show_help
                exit 1
                ;;
        esac
    done
    
    # Handle color output
    if [[ "$no_color" == true ]]; then
        RED=''
        GREEN=''
        YELLOW=''
        BLUE=''
        CYAN=''
        NC=''
    fi
    
    # Show help or version if requested
    if [[ "$show_help_flag" == true ]]; then
        show_help
        exit 0
    fi
    
    if [[ "$show_version_flag" == true ]]; then
        show_version
        exit 0
    fi
    
    # If no command provided, show help
    if [[ -z "$command" ]]; then
        show_help
        exit 1
    fi
    
    # Check prerequisites (unless quiet mode)
    if [[ "$quiet" != true ]]; then
        if ! check_prerequisites; then
            print_error "Prerequisites check failed"
            exit 1
        fi
    fi
    
    # Ensure required directories exist
    ensure_directories
    
    # Load configuration
    load_config "$config_file"
    
    # Set additional environment variables
    export BICEP_CONFIG_FILE="$config_file"
    export BICEP_SCRIPT_DIR="$SCRIPT_DIR"
    export BICEP_PROJECT_ROOT="$PROJECT_ROOT"
    
    # Execute the command
    case $command in
        analyze)
            cmd_analyze "${remaining_args[@]}"
            ;;
        generate)
            cmd_generate "${remaining_args[@]}"
            ;;
        validate)
            cmd_validate "${remaining_args[@]}"
            ;;
        deploy)
            cmd_deploy "${remaining_args[@]}"
            ;;
        update)
            cmd_update "${remaining_args[@]}"
            ;;
        dependencies)
            cmd_dependencies "${remaining_args[@]}"
            ;;
        sync)
            cmd_sync "${remaining_args[@]}"
            ;;
        review)
            cmd_review "${remaining_args[@]}"
            ;;
        estimate-cost)
            cmd_estimate_cost "${remaining_args[@]}"
            ;;
        security)
            cmd_security "${remaining_args[@]}"
            ;;
        explain)
            cmd_explain "${remaining_args[@]}"
            ;;
        *)
            unknown_command "$command"
            ;;
    esac
}

# Run main function with all arguments
main "$@"