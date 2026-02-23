---
description: Guide deployment options after implementation with selectable paths for local, Docker, and AWS.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. Confirm this command runs after `/speckit.tasks` and `/speckit.implement`.
2. Present a short menu of deployment paths and ask the user to choose one:
   - Local run
   - Docker
   - AWS
   - GCP (disabled)
3. Display only the selected path's steps.
4. If the user chooses GCP, clearly state it is disabled in this release.

## Deployment Paths

### Local Run (show only if selected)

- Explain that commands must be adapted to the current project.
- Provide these example commands:
  - `npm install && npm run build && npm run dev`
  - `uvicorn main:app --reload`
  - `poetry run python main`

### Docker (show only if selected)

- Provide these example commands:
  - `DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose up --build -d`
  - `docker compose up --build -d`
- If no Docker configuration exists, instruct the user to create a
  `Dockerfile` and `docker-compose.yml` before proceeding.

### AWS (show only if selected)

1. **Check prerequisites**
   - Verify AWS CLI is installed.
   - Verify required profiles exist. Example:
     - `aws configure list-profiles| grep backend-pro`
2. **Select AWS services**
   - List services based on the Terraform description (e.g., ECR, ECS, S3, RDS,
     ALB, NAT, API Gateway, Amplify).
3. **Select environment**
   - Choose from available Terraform environments: staging or prod.
4. **Confirm variables**
   - Ask the user to review `terraform.tfvars` before continuing.
5. **Initialize**
   - Run `terraform init` or a project-provided bootstrap script if available.
6. **Plan**
   - Run `terraform plan`.
7. **Apply**
   - Run `terraform apply`.
8. **Status list**
   - List AWS services with status labels:
     - `[yellow]in progress[/yellow]`
     - `[green]success[/green]`
     - `[red]failed[/red]`

### GCP (disabled)

- GCP deployment is disabled in this release.
