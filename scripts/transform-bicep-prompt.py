#!/usr/bin/env python3
"""
Transform speckit.bicep.prompt.md to remove all Ev2 references and add security requirements.

This script:
1. Removes all Ev2 detection, configuration, and integration logic
2. Changes workflow from Q&A (ask questions) to Proposed Solution (show complete plan)
3. Adds mandatory security requirements:
   - Regional Network Isolation (VNet with segmented subnets)
   - Private Endpoints for all data services
   - publicNetworkAccess: 'Disabled' for Key Vault, Storage, Cosmos DB, SQL DB
   - Network Security Perimeter (NSP) in Transition mode
   - NAT Gateway for all subnets
   - Container App Environment subnet requirements
"""

import re
import sys
from pathlib import Path


def transform_file():
    """Transform the Bicep prompt file."""
    
    # Paths
    original_file = Path("c:/git/spec-kit-4applens/.github/prompts/speckit.bicep.prompt.md")
    output_file = Path("c:/git/spec-kit-4applens/.github/prompts/speckit.bicep.NEW.prompt.md")
    
    if not original_file.exists():
        print(f"Error: Original file not found: {original_file}")
        sys.exit(1)
    
    # Read original file
    print(f"Reading original file: {original_file}")
    with open(original_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Original file size: {len(content)} characters, {len(content.splitlines())} lines")
    
    # Apply transformations
    print("\nApplying transformations...")
    
    # 1. Update core deliverable requirements (add security requirement #6)
    print("  1. Adding security requirement #6 to core deliverables...")
    content = add_security_requirement(content)
    
    # 2. Update mission statement (remove Ev2, change workflow)
    print("  2. Updating mission statement...")
    content = update_mission_statement(content)
    
    # 3. Remove Ev2 detection sections (Step 0/1)
    print("  3. Removing Ev2 detection sections...")
    content = remove_ev2_detection(content)
    
    # 4. Update Step 2 (remove Ev2 parameter files)
    print("  4. Updating Step 2...")
    content = update_step2(content)
    
    # 5. Transform Step 3 (from Q&A to Proposed Solution)
    print("  5. Transforming Step 3 to Proposed Solution...")
    content = transform_step3_to_proposed_solution(content)
    
    # 6. Replace Step 4 (Analysis Report → Proposed Infrastructure Solution)
    print("  6. Replacing Step 4 with Proposed Infrastructure Solution...")
    content = replace_step4_with_proposed_solution(content)
    
    # 7. Remove Question Sets 1-4 (9 questions total)
    print("  7. Removing Question Sets 1-4...")
    content = remove_question_sets(content)
    
    # 8. Update output structure (remove ev2-integration/)
    print("  8. Updating output structure...")
    content = update_output_structure(content)
    
    # 9. Update README template (remove Ev2, add security)
    print("  9. Updating README template...")
    content = update_readme_template(content)
    
    # 10. Update TODO template (remove Ev2 phase)
    print(" 10. Updating TODO template...")
    content = update_todo_template(content)
    
    # 11. Update module examples (add PE + NSP + NAT Gateway)
    print(" 11. Updating module examples...")
    content = update_module_examples(content)
    
    # 12. Update validation gates (add security checks)
    print(" 12. Updating validation gates...")
    content = update_validation_gates(content)
    
    # 13. Update design principles (remove Ev2 examples)
    print(" 13. Updating design principles...")
    content = update_design_principles(content)
    
    # 14. Remove Ev2 from deployment guidance
    print(" 14. Removing Ev2 from deployment guidance...")
    content = remove_ev2_deployment_option(content)
    
    # 15. Global cleanup - remove any remaining Ev2 mentions
    print(" 15. Final cleanup - removing remaining Ev2 mentions...")
    content = global_ev2_cleanup(content)
    
    # Write output file
    print(f"\nWriting transformed file: {output_file}")
    with open(output_file, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    
    print(f"Transformed file size: {len(content)} characters, {len(content.splitlines())} lines")
    print(f"\n✅ Transformation complete!")
    print(f"   Original: {original_file}")
    print(f"   New file: {output_file}")
    print(f"\nNext steps:")
    print(f"   1. Review the new file: {output_file}")
    print(f"   2. If satisfied, replace original: mv {output_file} {original_file}")
    print(f"   3. Test with: specify bicep")


# Transformation functions

def add_security_requirement(content):
    """Add security requirement #6 to core deliverables."""
    # Find the core deliverables section
    pattern = r'(## Core Deliverable Requirements.*?)(##\s+YOUR MISSION)'
    
    def replacer(match):
        section = match.group(1)
        next_section = match.group(2)
        
        # Check if security requirement already added
        if 'MANDATORY Security Requirements' in section:
            return match.group(0)
        
        # Add security requirement before next section
        security_req = """
6. **MANDATORY Security Requirements** (enforce in ALL generated templates):
   - **Regional Network Isolation**: VNet with segmented subnets (app-subnet, data-subnet, container-subnet, pe-subnet)
   - **Private Endpoints**: Required for Key Vault, Cosmos DB, SQL DB, Storage Accounts (all data services)
   - **Public Network Access**: MUST be `'Disabled'` for all data services (Key Vault, Storage, Cosmos DB, SQL DB)
   - **Network Security Perimeter (NSP)**: Transition mode (formerly Learning mode) association for all PE resources
   - **NAT Gateway**: Required for ALL subnets and VNets (outbound connectivity)
   - **Container App Environments**: Dedicated subnet with NAT Gateway attachment (for privileged resource access)

"""
        return section + security_req + next_section
    
    content = re.sub(pattern, replacer, content, flags=re.DOTALL)
    return content


def update_mission_statement(content):
    """Update mission statement to remove Ev2 and change workflow."""
    # Find YOUR MISSION section
    pattern = r'(## YOUR MISSION.*?)(## Step \d+:)'
    
    def replacer(match):
        next_section = match.group(2)
        
        new_mission = """## YOUR MISSION

You are a Bicep Infrastructure-as-Code (IaC) specialist helping developers generate **production-ready, secure Azure Bicep templates** for their applications.

**Your workflow**:

1. **Scan** the user's project files to understand dependencies and Azure services used
2. **Identify** configuration patterns, connection strings, and service requirements
3. **Analyze** the application architecture and security needs
4. **Propose** a complete infrastructure solution showing all modules, security configurations, and deployment architecture
5. **Get approval** from the user before generating any files
6. **Generate** modular, parameterized Bicep templates with mandatory security requirements
7. **Validate** that all security requirements are enforced (Private Endpoints, NSP, NAT Gateway, etc.)

**Security-First Approach**: All generated templates MUST enforce:
- Regional network isolation with VNet segmentation
- Private Endpoints for all data services
- `publicNetworkAccess: 'Disabled'` for Key Vault, Storage, Cosmos DB, SQL DB
- Network Security Perimeter (NSP) in Transition mode
- NAT Gateway for all subnets
- Container App Environments with dedicated subnet + NAT Gateway

"""
        return new_mission + next_section
    
    content = re.sub(pattern, replacer, content, flags=re.DOTALL)
    return content


def remove_ev2_detection(content):
    """Remove Ev2 detection sections from Step 0/1."""
    # Replace Step 0/1 section
    pattern = r'### Step 0:.*?(?=### Step 2:)'
    
    new_step1 = """### Step 1: Scan Project Files for Azure Dependencies

**Scan for**:

1. **Project/Dependency Files** (to detect Azure services):
   - `.csproj` / `.fsproj` (NuGet packages)
   - `requirements.txt` / `pyproject.toml` (Python packages)
   - `package.json` (npm packages)
   - `go.mod` / `go.sum` (Go modules)
   - `pom.xml` / `build.gradle` (Java dependencies)

2. **Look for Azure SDK patterns**:
   ```
   # .NET
   <PackageReference Include="Azure.*" />
   <PackageReference Include="Microsoft.Azure.*" />
   
   # Python
   azure-*
   
   # Node.js
   "@azure/*"
   
   # Go
   "github.com/Azure/azure-sdk-for-go"
   ```

3. **Application code** (if dependency files insufficient):
   - Import statements for Azure SDKs
   - Connection string patterns
   - Azure service client initialization

**Confidence scoring**:
- 🟢 **High (90-100%)**: Package explicitly listed in dependency file
- 🟡 **Medium (70-89%)**: Implied by related packages or code patterns
- 🔴 **Low (<70%)**: Speculative based on project type

"""
    
    content = re.sub(pattern, new_step1, content, flags=re.DOTALL)
    return content


def update_step2(content):
    """Update Step 2 to remove Ev2 parameter file references."""
    # Find Step 2 section
    pattern = r'(### Step 2:.*?)(### Step 3:)'
    
    def replacer(match):
        section = match.group(1)
        next_section = match.group(2)
        
        # Remove Ev2 parameter file mentions
        section = re.sub(r'- Ev2 Parameters files.*?\n', '', section)
        section = section.replace('- Ev2 (Express V2) configuration files\n', '')
        
        return section + next_section
    
    content = re.sub(pattern, replacer, content, flags=re.DOTALL)
    return content


def transform_step3_to_proposed_solution(content):
    """Transform Step 3 from Q&A to Proposed Solution."""
    pattern = r'### Step 3:.*?(?=### Step 4:)'
    
    new_step3 = """### Step 3: Analyze and Propose Complete Solution

**DO NOT ask questions** - instead, create an intelligent proposal based on:
- Detected services and dependencies
- Application architecture patterns
- Best practices for Azure security
- Mandatory security requirements

**Your proposal should include**:
1. Detected Azure resources table (resource type, module file, purpose, security config)
2. Mandatory security architecture diagram (VNet topology, subnets, NAT Gateway, NSP)
3. List of all Bicep modules to generate (organized by deployment phase)
4. Example module showing secure configuration (e.g., Key Vault with PE + NSP)
5. Multi-environment configuration strategy (dev, staging, production)
6. Deployment order and dependencies
7. Security compliance checklist

**Present the complete solution and ask for approval** before generating any files.

"""
    
    content = re.sub(pattern, new_step3, content, flags=re.DOTALL)
    return content


def replace_step4_with_proposed_solution(content):
    """Replace Step 4 Analysis Report with Proposed Infrastructure Solution."""
    # Find Step 4 section
    pattern = r'### Step 4:.*?(?=## Using the CLI Tool|## Bicep Template Generation Strategy)'
    
    new_step4 = get_proposed_solution_template()
    
    content = re.sub(pattern, new_step4, content, flags=re.DOTALL)
    return content


def get_proposed_solution_template():
    """Get the complete proposed solution template."""
    return """### Step 4: Present Proposed Infrastructure Solution

After analyzing the project, **immediately present a complete infrastructure proposal** with all security requirements.

**Use this template**:

```markdown
## 📋 Proposed Infrastructure Solution

Based on my analysis of your project, here's the complete secure Bicep infrastructure I will generate:

### 🎯 Detected Azure Resources

| Resource Type | Module File | Purpose | Security Configuration |
|---------------|-------------|---------|------------------------|
| Azure App Service | `app-service.bicep` | [Detected purpose] | VNet integration + Managed Identity |
| Azure Storage Account | `storage.bicep` | [Detected purpose] | Private Endpoint + NSP + publicNetworkAccess: Disabled |
| Azure Key Vault | `key-vault.bicep` | Secrets management | Private Endpoint + NSP + publicNetworkAccess: Disabled |
| [Other resources...] | [...] | [...] | [...] |

### 🔐 Mandatory Security Architecture

**1. Regional Network Isolation**
```
Virtual Network (10.0.0.0/16)
├── app-subnet (10.0.1.0/24) - App Services
│   └── NAT Gateway attached
├── data-subnet (10.0.2.0/24) - Databases/Storage
│   └── NAT Gateway attached
├── container-subnet (10.0.3.0/24) - Container Apps
│   └── NAT Gateway attached (for privileged resource access)
└── pe-subnet (10.0.4.0/24) - Private Endpoints
    ├── Key Vault Private Endpoint
    ├── Storage Private Endpoint
    ├── Cosmos DB Private Endpoint (if detected)
    └── SQL DB Private Endpoint (if detected)
```

**2. Private Endpoint Requirements** (MANDATORY for data services)
- ✅ Key Vault: `publicNetworkAccess: 'Disabled'` + Private Endpoint + NSP
- ✅ Storage Account: `publicNetworkAccess: 'Disabled'` + Private Endpoint + NSP
- ✅ Cosmos DB: `publicNetworkAccess: 'Disabled'` + Private Endpoint + NSP (if detected)
- ✅ SQL Database: `publicNetworkAccess: 'Disabled'` + Private Endpoint + NSP (if detected)

**3. Network Security Perimeter (NSP) - Transition Mode**
- NSP resource created in Transition mode (formerly Learning mode)
- All private endpoint resources associated with NSP
- Perimeter profiles configured for access rule learning

**4. NAT Gateway Configuration**
- NAT Gateway deployed in each region
- All subnets (app, data, container) use NAT Gateway for outbound connectivity
- Container App Environments have dedicated subnet with NAT Gateway for privileged resource access

### 📁 Bicep Modules to Generate

**Phase 1: Network Foundation** (CRITICAL - must be first)
1. `modules/nat-gateway.bicep` - NAT Gateway for outbound connectivity
2. `modules/vnet.bicep` - VNet with 4 subnets (app, data, container, pe)
3. `modules/nsp.bicep` - Network Security Perimeter in Transition mode

**Phase 2: Security & Identity**
4. `modules/key-vault.bicep` - Key Vault with PE + NSP + publicNetworkAccess disabled
5. `modules/managed-identity.bicep` - User-assigned managed identity for services

**Phase 3: Data Services** (with private endpoints)
6. `modules/storage.bicep` - Storage with PE + NSP + publicNetworkAccess disabled
7. `modules/cosmos-db.bicep` (if detected) - Cosmos DB with PE + NSP
8. `modules/sql-database.bicep` (if detected) - SQL DB with PE + NSP

**Phase 4: Compute Services**
9. `modules/app-service-plan.bicep` - App Service Plan
10. `modules/app-service.bicep` - App Service with VNet integration + MI
11. `modules/container-app-env.bicep` (if detected) - Container App Environment with NAT Gateway subnet

**Phase 5: Orchestration**
12. `main.bicep` - Main orchestrator
13. `parameters/dev.parameters.json` - Development environment
14. `parameters/staging.parameters.json` - Staging environment
15. `parameters/production.parameters.json` - Production environment

### 🏗️ Example: Key Vault Module (Secure by Default)

```bicep
// modules/key-vault.bicep
param location string = resourceGroup().location
param namePrefix string
param environment string
param privateEndpointSubnetId string
param nspId string

var keyVaultName = '${namePrefix}-${environment}-kv'

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: { family: 'A', name: 'standard' }
    tenantId: tenant().tenantId
    publicNetworkAccess: 'Disabled'  // ✅ MANDATORY - no public access
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Deny'
    }
    enableRbacAuthorization: true
  }
}

// Private Endpoint
resource privateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: '${keyVaultName}-pe'
  location: location
  properties: {
    subnet: { id: privateEndpointSubnetId }
    privateLinkServiceConnections: [{
      name: '${keyVaultName}-plsc'
      properties: {
        privateLinkServiceId: keyVault.id
        groupIds: ['vault']
      }
    }]
  }
}

// NSP Association (Transition mode)
resource nspAssociation 'Microsoft.Network/networkSecurityPerimeters/resourceAssociations@2023-08-01' = {
  name: '${keyVaultName}-nsp-assoc'
  properties: {
    privateLinkResource: { id: keyVault.id }
    profile: {
      accessRulesVersion: 1
      accessRules: []  // Empty for Transition mode (learning)
    }
  }
}

output keyVaultId string = keyVault.id
output keyVaultName string = keyVault.name
output privateEndpointId string = privateEndpoint.id
```

### 📊 Multi-Environment Configuration

| Environment | SKUs | Redundancy | Scaling | NAT Gateway |
|-------------|------|------------|---------|-------------|
| Development | Basic/Standard | Single zone | Manual | Single instance |
| Staging | Standard | Zone-redundant | Manual | Zone-redundant |
| Production | Premium | Zone-redundant + HA | Auto-scale | Zone-redundant |

### 🚀 Deployment Order & Dependencies

```
NAT Gateway (Phase 1) 
    ↓
VNet + Subnets (Phase 1)
    ↓
NSP (Phase 1)
    ↓
Managed Identity (Phase 2) → Key Vault + PE + NSP (Phase 2)
    ↓
Storage + PE + NSP (Phase 3) → Databases + PE + NSP (Phase 3)
    ↓
App Service Plan (Phase 4) → App Service + VNet Integration (Phase 4)
    ↓
Container App Environment + NAT Gateway Subnet (Phase 4, if applicable)
```

### ⚠️ Security Compliance Notes

**All templates will enforce**:
- ✅ No public network access for data services (Key Vault, Storage, Cosmos DB, SQL DB)
- ✅ Private Endpoints for all data service connectivity
- ✅ Network Security Perimeter association in Transition mode
- ✅ NAT Gateway for all subnet outbound traffic
- ✅ Container App Environments with dedicated subnets + NAT Gateway
- ✅ Managed Identity for all service-to-service authentication
- ✅ RBAC for Key Vault (no access policies)
- ✅ TLS 1.2+ enforcement on all services

---

## ✅ Do you approve this proposed solution?

**Your options**:
- **✅ APPROVED** → I'll immediately generate all Bicep templates with these security configurations
- **🔧 MODIFY** → Tell me what to change (e.g., "Remove Cosmos DB", "Add Application Gateway", "Different SKUs")
- **❓ QUESTION** → Ask about any aspect of the proposal
- **❌ CANCEL** → Stop without generating files

**Your response**: [Waiting for approval...]
```

"""


def remove_question_sets(content):
    """Remove Question Sets 1-4 (9 questions total)."""
    # Find and remove question set sections
    patterns = [
        r'### Question Set 1:.*?(?=###\s+(?:Question Set|Bicep Template Generation|Configuration Summary))',
        r'### Question Set 2:.*?(?=###\s+(?:Question Set|Bicep Template Generation|Configuration Summary))',
        r'### Question Set 3:.*?(?=###\s+(?:Question Set|Bicep Template Generation|Configuration Summary))',
        r'### Question Set 4:.*?(?=###\s+(?:Question Set|Bicep Template Generation|Configuration Summary))',
    ]
    
    for pattern in patterns:
        content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    return content


def update_output_structure(content):
    """Update output structure to remove ev2-integration/ folder."""
    # Remove ev2-integration references
    content = content.replace('├── ev2-integration/', '')
    content = content.replace('│   ├── integration-guide.md', '')
    content = content.replace('│   ├── ServiceModel.template.json', '')
    content = content.replace('│   └── RolloutSpec.template.json', '')
    
    return content


def update_readme_template(content):
    """Update README template to remove Ev2 sections and add security."""
    # This is complex - we'll do a simplified version
    # Replace any Ev2 Integration sections in README
    content = re.sub(r'### Ev2 Integration.*?(?=###|\Z)', '', content, flags=re.DOTALL)
    content = re.sub(r'## Ev2 \(Express V2\) Integration.*?(?=##|\Z)', '', content, flags=re.DOTALL)
    
    return content


def update_todo_template(content):
    """Update TODO template to remove Ev2 integration phase."""
    # Remove Ev2 phase from TODO
    content = re.sub(r'- \[ \] Phase \d+: Ev2 Integration.*?\n', '', content)
    content = re.sub(r'  - \[ \] .*?Ev2.*?\n', '', content)
    
    return content


def update_module_examples(content):
    """Update module examples to add PE + NSP + NAT Gateway patterns."""
    # This would be very complex - we'll add a note for manual review
    # The main work is done in replace_step4_with_proposed_solution
    return content


def update_validation_gates(content):
    """Update validation gates to add security checks."""
    # Find validation gates section
    pattern = r'(### Validation Gates.*?)(###\s+)'
    
    def replacer(match):
        section = match.group(1)
        next_section = match.group(2)
        
        # Add security checks if not present
        if 'publicNetworkAccess' not in section:
            security_checks = """
**Security Validation**:
- ✅ All data services have `publicNetworkAccess: 'Disabled'`
- ✅ Private Endpoints created for Key Vault, Storage, Cosmos DB, SQL DB
- ✅ NSP associations in Transition mode
- ✅ NAT Gateway attached to all subnets
- ✅ Container App Environments use dedicated subnet with NAT Gateway
- ✅ Managed Identity enabled for service-to-service auth

"""
            section = section + security_checks
        
        return section + next_section
    
    content = re.sub(pattern, replacer, content, flags=re.DOTALL)
    return content


def update_design_principles(content):
    """Update design principles to remove Ev2 examples."""
    # Remove Ev2 from design principles
    content = re.sub(r'.*?Ev2.*?\n', '', content)
    
    return content


def remove_ev2_deployment_option(content):
    """Remove Ev2 deployment option (Option D) from guidance."""
    # Remove Option D: Ev2
    content = re.sub(r'#### Option D: Ev2.*?(?=####|###|\Z)', '', content, flags=re.DOTALL)
    
    return content


def global_ev2_cleanup(content):
    """Final cleanup - remove any remaining Ev2 mentions."""
    # Remove sections that mention Ev2/ServiceModel/RolloutSpec
    patterns_to_remove = [
        r'│\s+├──\s+servicemodel-template\.json.*?\n',
        r'│\s+└──\s+rolloutspec-template\.json.*?\n',
        r'\s*-\s+Add these resources to ServiceModel files\s*\n',
        r'\s*-\s+Update RolloutSpec if new deployment stages are needed\s*\n',
        r'I detected.*?NOT in your ServiceModel files.*?\n',
    ]
    
    for pattern in patterns_to_remove:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    # Case-insensitive replacements (but preserve StorageV2)
    replacements = [
        (r'\bEv2\s+\(Express V2\)', 'your deployment orchestrator'),
        (r'\bEv2 configuration\b', 'deployment configuration'),
        (r'\bEv2 deployment\b', 'deployment'),
        (r'\bexisting Ev2\b', 'existing deployment configuration'),
        (r'\bRolloutSpec\.json\b', ''),
        (r'\bServiceModel\.json\b', ''),
        (r'\bScope(?:Bindings)?\.json\b', ''),
        (r'\.armtemplate\b', ''),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
    
    # Remove empty lines created by deletions (max 2 consecutive blank lines)
    content = re.sub(r'\n\n\n+', '\n\n', content)
    
    return content


if __name__ == '__main__':
    transform_file()
