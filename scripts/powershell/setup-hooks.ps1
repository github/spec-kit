#!/usr/bin/env pwsh

<#
.SYNOPSIS
    Setup Claude Code hooks and skills for the current project.

.DESCRIPTION
    This script detects the project type, frameworks, and generates appropriate
    hook configurations for Claude Code.

.PARAMETER Json
    Output in JSON format

.EXAMPLE
    ./setup-hooks.ps1 -Json
    # Detect project and output JSON

.EXAMPLE
    ./setup-hooks.ps1
    # Human-readable output
#>

param(
    [switch]$Json,
    [switch]$Help
)

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Detailed
    exit 0
}

# Source common functions
. (Join-Path $PSScriptRoot 'common.ps1')

# Get repository root
$RepoRoot = Get-RepoRoot

# Initialize detection variables
$ProjectType = "generic"
$PackageManager = ""
$TestRunner = ""
$Linter = ""
$Formatter = ""
$DetectedTools = @()
$DetectedFrameworks = @()

# Framework documentation URLs mapping
$FrameworkDocs = @{
    # JavaScript/TypeScript Frontend
    "react" = @{ docs = "https://react.dev"; github = "https://github.com/facebook/react" }
    "next" = @{ docs = "https://nextjs.org/docs"; github = "https://github.com/vercel/next.js" }
    "vue" = @{ docs = "https://vuejs.org/guide"; github = "https://github.com/vuejs/core" }
    "nuxt" = @{ docs = "https://nuxt.com/docs"; github = "https://github.com/nuxt/nuxt" }
    "angular" = @{ docs = "https://angular.dev"; github = "https://github.com/angular/angular" }
    "svelte" = @{ docs = "https://svelte.dev/docs"; github = "https://github.com/sveltejs/svelte" }
    "solid" = @{ docs = "https://docs.solidjs.com"; github = "https://github.com/solidjs/solid" }
    "astro" = @{ docs = "https://docs.astro.build"; github = "https://github.com/withastro/astro" }
    "remix" = @{ docs = "https://remix.run/docs"; github = "https://github.com/remix-run/remix" }

    # JavaScript/TypeScript Backend
    "express" = @{ docs = "https://expressjs.com"; github = "https://github.com/expressjs/express" }
    "fastify" = @{ docs = "https://fastify.dev/docs"; github = "https://github.com/fastify/fastify" }
    "nestjs" = @{ docs = "https://docs.nestjs.com"; github = "https://github.com/nestjs/nest" }
    "hono" = @{ docs = "https://hono.dev/docs"; github = "https://github.com/honojs/hono" }
    "koa" = @{ docs = "https://koajs.com"; github = "https://github.com/koajs/koa" }

    # Python Web
    "django" = @{ docs = "https://docs.djangoproject.com"; github = "https://github.com/django/django" }
    "fastapi" = @{ docs = "https://fastapi.tiangolo.com"; github = "https://github.com/tiangolo/fastapi" }
    "flask" = @{ docs = "https://flask.palletsprojects.com"; github = "https://github.com/pallets/flask" }
    "starlette" = @{ docs = "https://www.starlette.io"; github = "https://github.com/encode/starlette" }
    "litestar" = @{ docs = "https://docs.litestar.dev"; github = "https://github.com/litestar-org/litestar" }

    # Python Data/ML
    "pytorch" = @{ docs = "https://pytorch.org/docs"; github = "https://github.com/pytorch/pytorch" }
    "tensorflow" = @{ docs = "https://www.tensorflow.org/api_docs"; github = "https://github.com/tensorflow/tensorflow" }
    "pandas" = @{ docs = "https://pandas.pydata.org/docs"; github = "https://github.com/pandas-dev/pandas" }
    "numpy" = @{ docs = "https://numpy.org/doc"; github = "https://github.com/numpy/numpy" }
    "scikit-learn" = @{ docs = "https://scikit-learn.org/stable/documentation"; github = "https://github.com/scikit-learn/scikit-learn" }
    "langchain" = @{ docs = "https://python.langchain.com/docs"; github = "https://github.com/langchain-ai/langchain" }

    # Java/Kotlin
    "spring" = @{ docs = "https://docs.spring.io/spring-boot/docs/current/reference"; github = "https://github.com/spring-projects/spring-boot" }
    "quarkus" = @{ docs = "https://quarkus.io/guides"; github = "https://github.com/quarkusio/quarkus" }
    "micronaut" = @{ docs = "https://docs.micronaut.io"; github = "https://github.com/micronaut-projects/micronaut-core" }
    "ktor" = @{ docs = "https://ktor.io/docs"; github = "https://github.com/ktorio/ktor" }

    # Scala
    "play" = @{ docs = "https://www.playframework.com/documentation"; github = "https://github.com/playframework/playframework" }
    "akka" = @{ docs = "https://doc.akka.io"; github = "https://github.com/akka/akka" }
    "zio" = @{ docs = "https://zio.dev/reference"; github = "https://github.com/zio/zio" }
    "cats-effect" = @{ docs = "https://typelevel.org/cats-effect"; github = "https://github.com/typelevel/cats-effect" }
    "http4s" = @{ docs = "https://http4s.org/v0.23/docs"; github = "https://github.com/http4s/http4s" }
    "tapir" = @{ docs = "https://tapir.softwaremill.com/en/latest"; github = "https://github.com/softwaremill/tapir" }

    # Go
    "gin" = @{ docs = "https://gin-gonic.com/docs"; github = "https://github.com/gin-gonic/gin" }
    "echo" = @{ docs = "https://echo.labstack.com/docs"; github = "https://github.com/labstack/echo" }
    "fiber" = @{ docs = "https://docs.gofiber.io"; github = "https://github.com/gofiber/fiber" }
    "chi" = @{ docs = "https://go-chi.io"; github = "https://github.com/go-chi/chi" }

    # Rust
    "actix" = @{ docs = "https://actix.rs/docs"; github = "https://github.com/actix/actix-web" }
    "axum" = @{ docs = "https://docs.rs/axum"; github = "https://github.com/tokio-rs/axum" }
    "rocket" = @{ docs = "https://rocket.rs/guide"; github = "https://github.com/rwf2/Rocket" }
    "tokio" = @{ docs = "https://tokio.rs/tokio/tutorial"; github = "https://github.com/tokio-rs/tokio" }
    "tauri" = @{ docs = "https://tauri.app/v1/guides"; github = "https://github.com/tauri-apps/tauri" }

    # Ruby
    "rails" = @{ docs = "https://guides.rubyonrails.org"; github = "https://github.com/rails/rails" }
    "sinatra" = @{ docs = "https://sinatrarb.com/documentation"; github = "https://github.com/sinatra/sinatra" }
    "hanami" = @{ docs = "https://guides.hanamirb.org"; github = "https://github.com/hanami/hanami" }

    # PHP
    "laravel" = @{ docs = "https://laravel.com/docs"; github = "https://github.com/laravel/laravel" }
    "symfony" = @{ docs = "https://symfony.com/doc/current"; github = "https://github.com/symfony/symfony" }

    # .NET
    "aspnet" = @{ docs = "https://learn.microsoft.com/en-us/aspnet/core"; github = "https://github.com/dotnet/aspnetcore" }
    "blazor" = @{ docs = "https://learn.microsoft.com/en-us/aspnet/core/blazor"; github = "https://github.com/dotnet/aspnetcore" }

    # Mobile
    "react-native" = @{ docs = "https://reactnative.dev/docs"; github = "https://github.com/facebook/react-native" }
    "flutter" = @{ docs = "https://docs.flutter.dev"; github = "https://github.com/flutter/flutter" }
    "expo" = @{ docs = "https://docs.expo.dev"; github = "https://github.com/expo/expo" }

    # CSS/UI
    "tailwind" = @{ docs = "https://tailwindcss.com/docs"; github = "https://github.com/tailwindlabs/tailwindcss" }
    "shadcn" = @{ docs = "https://ui.shadcn.com/docs"; github = "https://github.com/shadcn-ui/ui" }
}

# Framework detection functions
function Detect-NodeFrameworks {
    $packageJsonPath = Join-Path $RepoRoot "package.json"
    if (-not (Test-Path $packageJsonPath)) { return }

    $pkg = Get-Content $packageJsonPath -Raw

    # Frontend frameworks
    if ($pkg -match '"react"') {
        $script:DetectedFrameworks += "react"
        if ($pkg -match '"next"') { $script:DetectedFrameworks += "next" }
        if ($pkg -match '"react-native"') { $script:DetectedFrameworks += "react-native" }
        if ($pkg -match '"expo"') { $script:DetectedFrameworks += "expo" }
    }
    if ($pkg -match '"vue"') {
        $script:DetectedFrameworks += "vue"
        if ($pkg -match '"nuxt"') { $script:DetectedFrameworks += "nuxt" }
    }
    if ($pkg -match '"@angular/core"') { $script:DetectedFrameworks += "angular" }
    if ($pkg -match '"svelte"') { $script:DetectedFrameworks += "svelte" }
    if ($pkg -match '"solid-js"') { $script:DetectedFrameworks += "solid" }
    if ($pkg -match '"astro"') { $script:DetectedFrameworks += "astro" }
    if ($pkg -match '"@remix-run"') { $script:DetectedFrameworks += "remix" }

    # Backend frameworks
    if ($pkg -match '"express"') { $script:DetectedFrameworks += "express" }
    if ($pkg -match '"fastify"') { $script:DetectedFrameworks += "fastify" }
    if ($pkg -match '"@nestjs/core"') { $script:DetectedFrameworks += "nestjs" }
    if ($pkg -match '"hono"') { $script:DetectedFrameworks += "hono" }
    if ($pkg -match '"koa"') { $script:DetectedFrameworks += "koa" }

    # UI frameworks
    if ($pkg -match '"tailwindcss"') { $script:DetectedFrameworks += "tailwind" }
    $componentsJson = Join-Path $RepoRoot "components.json"
    if ((Test-Path $componentsJson) -and ((Get-Content $componentsJson -Raw) -match "shadcn")) {
        $script:DetectedFrameworks += "shadcn"
    }
}

function Detect-PythonFrameworks {
    $deps = ""
    $reqPath = Join-Path $RepoRoot "requirements.txt"
    $pyprojectPath = Join-Path $RepoRoot "pyproject.toml"
    $pipfilePath = Join-Path $RepoRoot "Pipfile"

    if (Test-Path $reqPath) { $deps += Get-Content $reqPath -Raw }
    if (Test-Path $pyprojectPath) { $deps += Get-Content $pyprojectPath -Raw }
    if (Test-Path $pipfilePath) { $deps += Get-Content $pipfilePath -Raw }

    if ($deps -match "(?i)django") { $script:DetectedFrameworks += "django" }
    if ($deps -match "(?i)fastapi") { $script:DetectedFrameworks += "fastapi" }
    if ($deps -match "(?i)flask") { $script:DetectedFrameworks += "flask" }
    if ($deps -match "(?i)starlette") { $script:DetectedFrameworks += "starlette" }
    if ($deps -match "(?i)litestar") { $script:DetectedFrameworks += "litestar" }
    if ($deps -match "(?i)torch|pytorch") { $script:DetectedFrameworks += "pytorch" }
    if ($deps -match "(?i)tensorflow") { $script:DetectedFrameworks += "tensorflow" }
    if ($deps -match "(?i)pandas") { $script:DetectedFrameworks += "pandas" }
    if ($deps -match "(?i)numpy") { $script:DetectedFrameworks += "numpy" }
    if ($deps -match "(?i)scikit-learn|sklearn") { $script:DetectedFrameworks += "scikit-learn" }
    if ($deps -match "(?i)langchain") { $script:DetectedFrameworks += "langchain" }
}

function Detect-ScalaFrameworks {
    $deps = ""
    $sbtPath = Join-Path $RepoRoot "build.sbt"
    $millPath = Join-Path $RepoRoot "build.sc"

    if (Test-Path $sbtPath) { $deps += Get-Content $sbtPath -Raw }
    if (Test-Path $millPath) { $deps += Get-Content $millPath -Raw }

    if ($deps -match "(?i)playframework|play-server") { $script:DetectedFrameworks += "play" }
    if ($deps -match "(?i)akka") { $script:DetectedFrameworks += "akka" }
    if ($deps -match "(?i)zio") { $script:DetectedFrameworks += "zio" }
    if ($deps -match "(?i)cats-effect") { $script:DetectedFrameworks += "cats-effect" }
    if ($deps -match "(?i)http4s") { $script:DetectedFrameworks += "http4s" }
    if ($deps -match "(?i)tapir") { $script:DetectedFrameworks += "tapir" }
}

function Detect-RustFrameworks {
    $cargoPath = Join-Path $RepoRoot "Cargo.toml"
    if (-not (Test-Path $cargoPath)) { return }

    $cargo = Get-Content $cargoPath -Raw

    if ($cargo -match "(?i)actix-web") { $script:DetectedFrameworks += "actix" }
    if ($cargo -match "(?i)axum") { $script:DetectedFrameworks += "axum" }
    if ($cargo -match "(?i)rocket") { $script:DetectedFrameworks += "rocket" }
    if ($cargo -match "(?i)tokio") { $script:DetectedFrameworks += "tokio" }
    if ($cargo -match "(?i)tauri") { $script:DetectedFrameworks += "tauri" }
}

function Detect-GoFrameworks {
    $goModPath = Join-Path $RepoRoot "go.mod"
    if (-not (Test-Path $goModPath)) { return }

    $goMod = Get-Content $goModPath -Raw

    if ($goMod -match "(?i)gin-gonic/gin") { $script:DetectedFrameworks += "gin" }
    if ($goMod -match "(?i)labstack/echo") { $script:DetectedFrameworks += "echo" }
    if ($goMod -match "(?i)gofiber/fiber") { $script:DetectedFrameworks += "fiber" }
    if ($goMod -match "(?i)go-chi/chi") { $script:DetectedFrameworks += "chi" }
}

function Detect-RubyFrameworks {
    $gemfilePath = Join-Path $RepoRoot "Gemfile"
    if (-not (Test-Path $gemfilePath)) { return }

    $gemfile = Get-Content $gemfilePath -Raw

    if ($gemfile -match "(?i)rails") { $script:DetectedFrameworks += "rails" }
    if ($gemfile -match "(?i)sinatra") { $script:DetectedFrameworks += "sinatra" }
    if ($gemfile -match "(?i)hanami") { $script:DetectedFrameworks += "hanami" }
}

function Detect-PhpFrameworks {
    $composerPath = Join-Path $RepoRoot "composer.json"
    if (-not (Test-Path $composerPath)) { return }

    $composer = Get-Content $composerPath -Raw

    if ($composer -match "(?i)laravel/framework") { $script:DetectedFrameworks += "laravel" }
    if ($composer -match "(?i)symfony/framework") { $script:DetectedFrameworks += "symfony" }
}

function Detect-JavaFrameworks {
    $deps = ""
    $pomPath = Join-Path $RepoRoot "pom.xml"
    $gradlePath = Join-Path $RepoRoot "build.gradle"
    $gradleKtsPath = Join-Path $RepoRoot "build.gradle.kts"

    if (Test-Path $pomPath) { $deps += Get-Content $pomPath -Raw }
    if (Test-Path $gradlePath) { $deps += Get-Content $gradlePath -Raw }
    if (Test-Path $gradleKtsPath) { $deps += Get-Content $gradleKtsPath -Raw }

    if ($deps -match "(?i)spring-boot|springframework") { $script:DetectedFrameworks += "spring" }
    if ($deps -match "(?i)quarkus") { $script:DetectedFrameworks += "quarkus" }
    if ($deps -match "(?i)micronaut") { $script:DetectedFrameworks += "micronaut" }
    if ($deps -match "(?i)ktor") { $script:DetectedFrameworks += "ktor" }
}

# Detect project type and tools
function Detect-Project {
    # Node.js / TypeScript
    $packageJsonPath = Join-Path $RepoRoot "package.json"
    if (Test-Path $packageJsonPath) {
        $script:ProjectType = "node"
        $script:DetectedTools += "node"

        # Detect package manager
        if (Test-Path (Join-Path $RepoRoot "pnpm-lock.yaml")) {
            $script:PackageManager = "pnpm"
        } elseif (Test-Path (Join-Path $RepoRoot "yarn.lock")) {
            $script:PackageManager = "yarn"
        } elseif (Test-Path (Join-Path $RepoRoot "bun.lockb")) {
            $script:PackageManager = "bun"
        } else {
            $script:PackageManager = "npm"
        }
        $script:DetectedTools += $script:PackageManager

        # Check for TypeScript
        if (Test-Path (Join-Path $RepoRoot "tsconfig.json")) {
            $script:ProjectType = "node-typescript"
            $script:DetectedTools += "typescript"
        }

        # Read package.json for tool detection
        $packageJson = Get-Content $packageJsonPath -Raw

        # Detect test runner
        if ($packageJson -match '"jest"') {
            $script:TestRunner = "jest"
            $script:DetectedTools += "jest"
        } elseif ($packageJson -match '"vitest"') {
            $script:TestRunner = "vitest"
            $script:DetectedTools += "vitest"
        } elseif ($packageJson -match '"mocha"') {
            $script:TestRunner = "mocha"
            $script:DetectedTools += "mocha"
        }

        # Detect linter
        $eslintConfigs = @(".eslintrc.json", ".eslintrc.js", ".eslintrc.cjs", "eslint.config.js", "eslint.config.mjs")
        $hasEslintConfig = $eslintConfigs | Where-Object { Test-Path (Join-Path $RepoRoot $_) } | Select-Object -First 1
        if ($hasEslintConfig -or ($packageJson -match '"eslint"')) {
            $script:Linter = "eslint"
            $script:DetectedTools += "eslint"
        }

        # Detect formatter
        $prettierConfigs = @(".prettierrc", ".prettierrc.json", "prettier.config.js")
        $hasPrettierConfig = $prettierConfigs | Where-Object { Test-Path (Join-Path $RepoRoot $_) } | Select-Object -First 1
        if ($hasPrettierConfig -or ($packageJson -match '"prettier"')) {
            $script:Formatter = "prettier"
            $script:DetectedTools += "prettier"
        }

        Detect-NodeFrameworks
        return
    }

    # Scala (sbt)
    if (Test-Path (Join-Path $RepoRoot "build.sbt")) {
        $script:ProjectType = "scala-sbt"
        $script:PackageManager = "sbt"
        $script:TestRunner = "sbt-test"
        $script:Formatter = "scalafmt"
        $script:DetectedTools = @("scala", "sbt", "scalafmt")

        if (Test-Path (Join-Path $RepoRoot ".scalafix.conf")) {
            $script:Linter = "scalafix"
            $script:DetectedTools += "scalafix"
        }

        Detect-ScalaFrameworks
        return
    }

    # Scala (Mill)
    if (Test-Path (Join-Path $RepoRoot "build.sc")) {
        $script:ProjectType = "scala-mill"
        $script:PackageManager = "mill"
        $script:TestRunner = "mill-test"
        $script:Formatter = "scalafmt"
        $script:DetectedTools = @("scala", "mill", "scalafmt")

        Detect-ScalaFrameworks
        return
    }

    # Python
    $pyprojectPath = Join-Path $RepoRoot "pyproject.toml"
    $requirementsPath = Join-Path $RepoRoot "requirements.txt"
    $setupPyPath = Join-Path $RepoRoot "setup.py"

    if ((Test-Path $pyprojectPath) -or (Test-Path $requirementsPath) -or (Test-Path $setupPyPath)) {
        $script:ProjectType = "python"
        $script:DetectedTools += "python"

        # Detect package manager
        if (Test-Path (Join-Path $RepoRoot "poetry.lock")) {
            $script:PackageManager = "poetry"
            $script:DetectedTools += "poetry"
        } elseif (Test-Path (Join-Path $RepoRoot "Pipfile.lock")) {
            $script:PackageManager = "pipenv"
            $script:DetectedTools += "pipenv"
        } elseif (Test-Path (Join-Path $RepoRoot "uv.lock")) {
            $script:PackageManager = "uv"
            $script:DetectedTools += "uv"
        } else {
            $script:PackageManager = "pip"
            $script:DetectedTools += "pip"
        }

        # Detect test runner and linter from pyproject.toml
        if (Test-Path $pyprojectPath) {
            $pyproject = Get-Content $pyprojectPath -Raw

            if ($pyproject -match "pytest") {
                $script:TestRunner = "pytest"
                $script:DetectedTools += "pytest"
            }
            if ($pyproject -match "ruff" -or (Test-Path (Join-Path $RepoRoot "ruff.toml"))) {
                $script:Linter = "ruff"
                $script:Formatter = "ruff"
                $script:DetectedTools += "ruff"
            }
            if ($pyproject -match "black") {
                $script:Formatter = "black"
                $script:DetectedTools += "black"
            }
            if ($pyproject -match "mypy") {
                $script:DetectedTools += "mypy"
            }
        }

        # Also check pytest.ini
        if (Test-Path (Join-Path $RepoRoot "pytest.ini")) {
            $script:TestRunner = "pytest"
            if ($script:DetectedTools -notcontains "pytest") {
                $script:DetectedTools += "pytest"
            }
        }

        Detect-PythonFrameworks
        return
    }

    # Rust
    if (Test-Path (Join-Path $RepoRoot "Cargo.toml")) {
        $script:ProjectType = "rust"
        $script:PackageManager = "cargo"
        $script:TestRunner = "cargo-test"
        $script:Linter = "clippy"
        $script:Formatter = "rustfmt"
        $script:DetectedTools = @("rust", "cargo", "clippy", "rustfmt")

        Detect-RustFrameworks
        return
    }

    # Go
    if (Test-Path (Join-Path $RepoRoot "go.mod")) {
        $script:ProjectType = "go"
        $script:PackageManager = "go-mod"
        $script:TestRunner = "go-test"
        $script:Formatter = "gofmt"
        $script:Linter = "go-vet"
        $script:DetectedTools = @("go", "gofmt", "go-vet")

        # Check for golangci-lint
        if ((Test-Path (Join-Path $RepoRoot ".golangci.yml")) -or (Test-Path (Join-Path $RepoRoot ".golangci.yaml"))) {
            $script:Linter = "golangci-lint"
            $script:DetectedTools += "golangci-lint"
        }

        Detect-GoFrameworks
        return
    }

    # Java (Maven)
    if (Test-Path (Join-Path $RepoRoot "pom.xml")) {
        $script:ProjectType = "java-maven"
        $script:PackageManager = "maven"
        $script:TestRunner = "maven-test"
        $script:DetectedTools = @("java", "maven")

        Detect-JavaFrameworks
        return
    }

    # Java (Gradle)
    if ((Test-Path (Join-Path $RepoRoot "build.gradle")) -or (Test-Path (Join-Path $RepoRoot "build.gradle.kts"))) {
        $script:ProjectType = "java-gradle"
        $script:PackageManager = "gradle"
        $script:TestRunner = "gradle-test"
        $script:DetectedTools = @("java", "gradle")

        Detect-JavaFrameworks
        return
    }

    # .NET
    $hasCsproj = Get-ChildItem -Path $RepoRoot -Filter "*.csproj" -Recurse -Depth 2 -ErrorAction SilentlyContinue | Select-Object -First 1
    $hasSln = Get-ChildItem -Path $RepoRoot -Filter "*.sln" -Recurse -Depth 2 -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($hasCsproj -or $hasSln) {
        $script:ProjectType = "dotnet"
        $script:PackageManager = "dotnet"
        $script:TestRunner = "dotnet-test"
        $script:DetectedTools = @("dotnet")
        return
    }

    # Ruby
    if (Test-Path (Join-Path $RepoRoot "Gemfile")) {
        $script:ProjectType = "ruby"
        $script:PackageManager = "bundler"
        $script:DetectedTools = @("ruby", "bundler")

        $gemfile = Get-Content (Join-Path $RepoRoot "Gemfile") -Raw
        if ($gemfile -match "rspec") {
            $script:TestRunner = "rspec"
            $script:DetectedTools += "rspec"
        }
        if ($gemfile -match "rubocop") {
            $script:Linter = "rubocop"
            $script:DetectedTools += "rubocop"
        }

        Detect-RubyFrameworks
        return
    }

    # PHP
    if (Test-Path (Join-Path $RepoRoot "composer.json")) {
        $script:ProjectType = "php"
        $script:PackageManager = "composer"
        $script:DetectedTools = @("php", "composer")

        $composer = Get-Content (Join-Path $RepoRoot "composer.json") -Raw
        if ($composer -match "phpunit") {
            $script:TestRunner = "phpunit"
            $script:DetectedTools += "phpunit"
        }

        Detect-PhpFrameworks
        return
    }
}

# Run detection
Detect-Project

# Define output paths
$ClaudeDir = Join-Path $RepoRoot ".claude"
$SettingsFile = Join-Path $ClaudeDir "settings.json"
$SkillsDir = Join-Path $ClaudeDir "skills"
$HooksDir = Join-Path $ClaudeDir "hooks"

# Check if .claude directory already exists
$ClaudeExists = Test-Path $ClaudeDir
$SettingsExists = Test-Path $SettingsFile

# Output results
if ($Json) {
    # Build frameworks array with docs
    $frameworksArray = @()
    foreach ($framework in $DetectedFrameworks) {
        $docs = $FrameworkDocs[$framework]
        if ($docs) {
            $frameworksArray += @{
                name = $framework
                docs_url = $docs.docs
                github_url = $docs.github
            }
        } else {
            $frameworksArray += @{
                name = $framework
                docs_url = ""
                github_url = ""
            }
        }
    }

    $output = @{
        PROJECT_TYPE = $ProjectType
        PACKAGE_MANAGER = $PackageManager
        TEST_RUNNER = $TestRunner
        LINTER = $Linter
        FORMATTER = $Formatter
        DETECTED_TOOLS = $DetectedTools
        DETECTED_FRAMEWORKS = $frameworksArray
        REPO_ROOT = $RepoRoot
        CLAUDE_DIR = $ClaudeDir
        SETTINGS_FILE = $SettingsFile
        SKILLS_DIR = $SkillsDir
        HOOKS_DIR = $HooksDir
        CLAUDE_EXISTS = $ClaudeExists
        SETTINGS_EXISTS = $SettingsExists
    }

    $output | ConvertTo-Json -Depth 4
} else {
    Write-Output "=== Project Detection Results ==="
    Write-Output ""
    Write-Output "Project Type: $ProjectType"
    Write-Output "Package Manager: $(if ($PackageManager) { $PackageManager } else { 'none detected' })"
    Write-Output "Test Runner: $(if ($TestRunner) { $TestRunner } else { 'none detected' })"
    Write-Output "Linter: $(if ($Linter) { $Linter } else { 'none detected' })"
    Write-Output "Formatter: $(if ($Formatter) { $Formatter } else { 'none detected' })"
    Write-Output ""
    Write-Output "Detected Tools: $(if ($DetectedTools.Count -gt 0) { $DetectedTools -join ', ' } else { 'none' })"
    Write-Output ""
    Write-Output "=== Detected Frameworks ==="
    if ($DetectedFrameworks.Count -gt 0) {
        foreach ($framework in $DetectedFrameworks) {
            $docs = $FrameworkDocs[$framework]
            if ($docs) {
                Write-Output "  - $framework"
                Write-Output "    Docs: $($docs.docs)"
                Write-Output "    GitHub: $($docs.github)"
            } else {
                Write-Output "  - $framework"
            }
        }
    } else {
        Write-Output "  No frameworks detected"
    }
    Write-Output ""
    Write-Output "=== Claude Code Paths ==="
    Write-Output "Claude Directory: $ClaudeDir (exists: $ClaudeExists)"
    Write-Output "Settings File: $SettingsFile (exists: $SettingsExists)"
    Write-Output "Skills Directory: $SkillsDir"
    Write-Output "Hooks Directory: $HooksDir"
}
