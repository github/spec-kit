#!/usr/bin/env bash

# Setup Claude Code hooks and skills for the current project
#
# This script detects the project type and generates appropriate
# hook configurations for Claude Code.
#
# Usage: ./setup-hooks.sh [OPTIONS]
#
# OPTIONS:
#   --json              Output in JSON format
#   --help, -h          Show help message
#
# OUTPUTS:
#   JSON mode: {"PROJECT_TYPE":"...", "DETECTED_TOOLS":[...], ...}
#   Text mode: Human-readable project detection summary

set -e

# Parse command line arguments
JSON_MODE=false

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --help|-h)
            cat << 'EOF'
Usage: setup-hooks.sh [OPTIONS]

Setup Claude Code hooks and skills for the current project.

OPTIONS:
  --json              Output in JSON format
  --help, -h          Show this help message

EXAMPLES:
  # Detect project and output JSON
  ./setup-hooks.sh --json

  # Human-readable output
  ./setup-hooks.sh

EOF
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option '$arg'. Use --help for usage information." >&2
            exit 1
            ;;
    esac
done

# Source common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get repository root
REPO_ROOT=$(get_repo_root)

# Initialize detection variables
PROJECT_TYPE="generic"
PACKAGE_MANAGER=""
TEST_RUNNER=""
LINTER=""
FORMATTER=""
DETECTED_TOOLS=()
DETECTED_FRAMEWORKS=()

# Framework documentation URLs mapping
declare -A FRAMEWORK_DOCS=(
    # JavaScript/TypeScript Frontend
    ["react"]="https://react.dev|https://github.com/facebook/react"
    ["next"]="https://nextjs.org/docs|https://github.com/vercel/next.js"
    ["vue"]="https://vuejs.org/guide|https://github.com/vuejs/core"
    ["nuxt"]="https://nuxt.com/docs|https://github.com/nuxt/nuxt"
    ["angular"]="https://angular.dev|https://github.com/angular/angular"
    ["svelte"]="https://svelte.dev/docs|https://github.com/sveltejs/svelte"
    ["solid"]="https://docs.solidjs.com|https://github.com/solidjs/solid"
    ["astro"]="https://docs.astro.build|https://github.com/withastro/astro"
    ["remix"]="https://remix.run/docs|https://github.com/remix-run/remix"

    # JavaScript/TypeScript Backend
    ["express"]="https://expressjs.com|https://github.com/expressjs/express"
    ["fastify"]="https://fastify.dev/docs|https://github.com/fastify/fastify"
    ["nestjs"]="https://docs.nestjs.com|https://github.com/nestjs/nest"
    ["hono"]="https://hono.dev/docs|https://github.com/honojs/hono"
    ["koa"]="https://koajs.com|https://github.com/koajs/koa"

    # Python Web
    ["django"]="https://docs.djangoproject.com|https://github.com/django/django"
    ["fastapi"]="https://fastapi.tiangolo.com|https://github.com/tiangolo/fastapi"
    ["flask"]="https://flask.palletsprojects.com|https://github.com/pallets/flask"
    ["starlette"]="https://www.starlette.io|https://github.com/encode/starlette"
    ["litestar"]="https://docs.litestar.dev|https://github.com/litestar-org/litestar"

    # Python Data/ML
    ["pytorch"]="https://pytorch.org/docs|https://github.com/pytorch/pytorch"
    ["tensorflow"]="https://www.tensorflow.org/api_docs|https://github.com/tensorflow/tensorflow"
    ["pandas"]="https://pandas.pydata.org/docs|https://github.com/pandas-dev/pandas"
    ["numpy"]="https://numpy.org/doc|https://github.com/numpy/numpy"
    ["scikit-learn"]="https://scikit-learn.org/stable/documentation|https://github.com/scikit-learn/scikit-learn"
    ["langchain"]="https://python.langchain.com/docs|https://github.com/langchain-ai/langchain"

    # Java/Kotlin
    ["spring"]="https://docs.spring.io/spring-boot/docs/current/reference|https://github.com/spring-projects/spring-boot"
    ["quarkus"]="https://quarkus.io/guides|https://github.com/quarkusio/quarkus"
    ["micronaut"]="https://docs.micronaut.io|https://github.com/micronaut-projects/micronaut-core"
    ["ktor"]="https://ktor.io/docs|https://github.com/ktorio/ktor"

    # Scala
    ["play"]="https://www.playframework.com/documentation|https://github.com/playframework/playframework"
    ["akka"]="https://doc.akka.io|https://github.com/akka/akka"
    ["zio"]="https://zio.dev/reference|https://github.com/zio/zio"
    ["cats-effect"]="https://typelevel.org/cats-effect|https://github.com/typelevel/cats-effect"
    ["http4s"]="https://http4s.org/v0.23/docs|https://github.com/http4s/http4s"
    ["tapir"]="https://tapir.softwaremill.com/en/latest|https://github.com/softwaremill/tapir"

    # Go
    ["gin"]="https://gin-gonic.com/docs|https://github.com/gin-gonic/gin"
    ["echo"]="https://echo.labstack.com/docs|https://github.com/labstack/echo"
    ["fiber"]="https://docs.gofiber.io|https://github.com/gofiber/fiber"
    ["chi"]="https://go-chi.io|https://github.com/go-chi/chi"

    # Rust
    ["actix"]="https://actix.rs/docs|https://github.com/actix/actix-web"
    ["axum"]="https://docs.rs/axum|https://github.com/tokio-rs/axum"
    ["rocket"]="https://rocket.rs/guide|https://github.com/rwf2/Rocket"
    ["tokio"]="https://tokio.rs/tokio/tutorial|https://github.com/tokio-rs/tokio"
    ["tauri"]="https://tauri.app/v1/guides|https://github.com/tauri-apps/tauri"

    # Ruby
    ["rails"]="https://guides.rubyonrails.org|https://github.com/rails/rails"
    ["sinatra"]="https://sinatrarb.com/documentation|https://github.com/sinatra/sinatra"
    ["hanami"]="https://guides.hanamirb.org|https://github.com/hanami/hanami"

    # PHP
    ["laravel"]="https://laravel.com/docs|https://github.com/laravel/laravel"
    ["symfony"]="https://symfony.com/doc/current|https://github.com/symfony/symfony"

    # .NET
    ["aspnet"]="https://learn.microsoft.com/en-us/aspnet/core|https://github.com/dotnet/aspnetcore"
    ["blazor"]="https://learn.microsoft.com/en-us/aspnet/core/blazor|https://github.com/dotnet/aspnetcore"

    # Mobile
    ["react-native"]="https://reactnative.dev/docs|https://github.com/facebook/react-native"
    ["flutter"]="https://docs.flutter.dev|https://github.com/flutter/flutter"
    ["expo"]="https://docs.expo.dev|https://github.com/expo/expo"

    # CSS/UI
    ["tailwind"]="https://tailwindcss.com/docs|https://github.com/tailwindlabs/tailwindcss"
    ["shadcn"]="https://ui.shadcn.com/docs|https://github.com/shadcn-ui/ui"
)

# Detect frameworks in Node.js projects
detect_node_frameworks() {
    local pkg_content
    pkg_content=$(cat "$REPO_ROOT/package.json" 2>/dev/null)

    # Frontend frameworks
    if echo "$pkg_content" | grep -q '"react"'; then
        DETECTED_FRAMEWORKS+=("react")
        # Check for Next.js
        if echo "$pkg_content" | grep -q '"next"'; then
            DETECTED_FRAMEWORKS+=("next")
        fi
        # Check for React Native
        if echo "$pkg_content" | grep -q '"react-native"'; then
            DETECTED_FRAMEWORKS+=("react-native")
        fi
        # Check for Expo
        if echo "$pkg_content" | grep -q '"expo"'; then
            DETECTED_FRAMEWORKS+=("expo")
        fi
    fi

    if echo "$pkg_content" | grep -q '"vue"'; then
        DETECTED_FRAMEWORKS+=("vue")
        if echo "$pkg_content" | grep -q '"nuxt"'; then
            DETECTED_FRAMEWORKS+=("nuxt")
        fi
    fi

    if echo "$pkg_content" | grep -q '"@angular/core"'; then
        DETECTED_FRAMEWORKS+=("angular")
    fi

    if echo "$pkg_content" | grep -q '"svelte"'; then
        DETECTED_FRAMEWORKS+=("svelte")
    fi

    if echo "$pkg_content" | grep -q '"solid-js"'; then
        DETECTED_FRAMEWORKS+=("solid")
    fi

    if echo "$pkg_content" | grep -q '"astro"'; then
        DETECTED_FRAMEWORKS+=("astro")
    fi

    if echo "$pkg_content" | grep -q '"@remix-run"'; then
        DETECTED_FRAMEWORKS+=("remix")
    fi

    # Backend frameworks
    if echo "$pkg_content" | grep -q '"express"'; then
        DETECTED_FRAMEWORKS+=("express")
    fi

    if echo "$pkg_content" | grep -q '"fastify"'; then
        DETECTED_FRAMEWORKS+=("fastify")
    fi

    if echo "$pkg_content" | grep -q '"@nestjs/core"'; then
        DETECTED_FRAMEWORKS+=("nestjs")
    fi

    if echo "$pkg_content" | grep -q '"hono"'; then
        DETECTED_FRAMEWORKS+=("hono")
    fi

    if echo "$pkg_content" | grep -q '"koa"'; then
        DETECTED_FRAMEWORKS+=("koa")
    fi

    # UI frameworks
    if echo "$pkg_content" | grep -q '"tailwindcss"'; then
        DETECTED_FRAMEWORKS+=("tailwind")
    fi

    if [[ -f "$REPO_ROOT/components.json" ]] && grep -q "shadcn" "$REPO_ROOT/components.json" 2>/dev/null; then
        DETECTED_FRAMEWORKS+=("shadcn")
    fi
}

# Detect frameworks in Python projects
detect_python_frameworks() {
    local deps=""
    [[ -f "$REPO_ROOT/requirements.txt" ]] && deps+=$(cat "$REPO_ROOT/requirements.txt" 2>/dev/null)
    [[ -f "$REPO_ROOT/pyproject.toml" ]] && deps+=$(cat "$REPO_ROOT/pyproject.toml" 2>/dev/null)
    [[ -f "$REPO_ROOT/Pipfile" ]] && deps+=$(cat "$REPO_ROOT/Pipfile" 2>/dev/null)

    if echo "$deps" | grep -qi "django"; then
        DETECTED_FRAMEWORKS+=("django")
    fi

    if echo "$deps" | grep -qi "fastapi"; then
        DETECTED_FRAMEWORKS+=("fastapi")
    fi

    if echo "$deps" | grep -qi "flask"; then
        DETECTED_FRAMEWORKS+=("flask")
    fi

    if echo "$deps" | grep -qi "starlette"; then
        DETECTED_FRAMEWORKS+=("starlette")
    fi

    if echo "$deps" | grep -qi "litestar"; then
        DETECTED_FRAMEWORKS+=("litestar")
    fi

    # Data/ML frameworks
    if echo "$deps" | grep -qi "torch\|pytorch"; then
        DETECTED_FRAMEWORKS+=("pytorch")
    fi

    if echo "$deps" | grep -qi "tensorflow"; then
        DETECTED_FRAMEWORKS+=("tensorflow")
    fi

    if echo "$deps" | grep -qi "pandas"; then
        DETECTED_FRAMEWORKS+=("pandas")
    fi

    if echo "$deps" | grep -qi "numpy"; then
        DETECTED_FRAMEWORKS+=("numpy")
    fi

    if echo "$deps" | grep -qi "scikit-learn\|sklearn"; then
        DETECTED_FRAMEWORKS+=("scikit-learn")
    fi

    if echo "$deps" | grep -qi "langchain"; then
        DETECTED_FRAMEWORKS+=("langchain")
    fi
}

# Detect frameworks in Scala projects
detect_scala_frameworks() {
    local deps=""
    [[ -f "$REPO_ROOT/build.sbt" ]] && deps+=$(cat "$REPO_ROOT/build.sbt" 2>/dev/null)
    [[ -f "$REPO_ROOT/build.sc" ]] && deps+=$(cat "$REPO_ROOT/build.sc" 2>/dev/null)

    if echo "$deps" | grep -qi "playframework\|play-server"; then
        DETECTED_FRAMEWORKS+=("play")
    fi

    if echo "$deps" | grep -qi "akka"; then
        DETECTED_FRAMEWORKS+=("akka")
    fi

    if echo "$deps" | grep -qi "zio"; then
        DETECTED_FRAMEWORKS+=("zio")
    fi

    if echo "$deps" | grep -qi "cats-effect"; then
        DETECTED_FRAMEWORKS+=("cats-effect")
    fi

    if echo "$deps" | grep -qi "http4s"; then
        DETECTED_FRAMEWORKS+=("http4s")
    fi

    if echo "$deps" | grep -qi "tapir"; then
        DETECTED_FRAMEWORKS+=("tapir")
    fi
}

# Detect frameworks in Rust projects
detect_rust_frameworks() {
    local cargo_content=""
    [[ -f "$REPO_ROOT/Cargo.toml" ]] && cargo_content=$(cat "$REPO_ROOT/Cargo.toml" 2>/dev/null)

    if echo "$cargo_content" | grep -qi "actix-web"; then
        DETECTED_FRAMEWORKS+=("actix")
    fi

    if echo "$cargo_content" | grep -qi "axum"; then
        DETECTED_FRAMEWORKS+=("axum")
    fi

    if echo "$cargo_content" | grep -qi "rocket"; then
        DETECTED_FRAMEWORKS+=("rocket")
    fi

    if echo "$cargo_content" | grep -qi "tokio"; then
        DETECTED_FRAMEWORKS+=("tokio")
    fi

    if echo "$cargo_content" | grep -qi "tauri"; then
        DETECTED_FRAMEWORKS+=("tauri")
    fi
}

# Detect frameworks in Go projects
detect_go_frameworks() {
    local go_mod=""
    [[ -f "$REPO_ROOT/go.mod" ]] && go_mod=$(cat "$REPO_ROOT/go.mod" 2>/dev/null)

    if echo "$go_mod" | grep -qi "gin-gonic/gin"; then
        DETECTED_FRAMEWORKS+=("gin")
    fi

    if echo "$go_mod" | grep -qi "labstack/echo"; then
        DETECTED_FRAMEWORKS+=("echo")
    fi

    if echo "$go_mod" | grep -qi "gofiber/fiber"; then
        DETECTED_FRAMEWORKS+=("fiber")
    fi

    if echo "$go_mod" | grep -qi "go-chi/chi"; then
        DETECTED_FRAMEWORKS+=("chi")
    fi
}

# Detect frameworks in Ruby projects
detect_ruby_frameworks() {
    local gemfile=""
    [[ -f "$REPO_ROOT/Gemfile" ]] && gemfile=$(cat "$REPO_ROOT/Gemfile" 2>/dev/null)

    if echo "$gemfile" | grep -qi "rails"; then
        DETECTED_FRAMEWORKS+=("rails")
    fi

    if echo "$gemfile" | grep -qi "sinatra"; then
        DETECTED_FRAMEWORKS+=("sinatra")
    fi

    if echo "$gemfile" | grep -qi "hanami"; then
        DETECTED_FRAMEWORKS+=("hanami")
    fi
}

# Detect frameworks in PHP projects
detect_php_frameworks() {
    local composer=""
    [[ -f "$REPO_ROOT/composer.json" ]] && composer=$(cat "$REPO_ROOT/composer.json" 2>/dev/null)

    if echo "$composer" | grep -qi "laravel/framework"; then
        DETECTED_FRAMEWORKS+=("laravel")
    fi

    if echo "$composer" | grep -qi "symfony/framework"; then
        DETECTED_FRAMEWORKS+=("symfony")
    fi
}

# Detect frameworks in Java projects
detect_java_frameworks() {
    local deps=""
    [[ -f "$REPO_ROOT/pom.xml" ]] && deps+=$(cat "$REPO_ROOT/pom.xml" 2>/dev/null)
    [[ -f "$REPO_ROOT/build.gradle" ]] && deps+=$(cat "$REPO_ROOT/build.gradle" 2>/dev/null)
    [[ -f "$REPO_ROOT/build.gradle.kts" ]] && deps+=$(cat "$REPO_ROOT/build.gradle.kts" 2>/dev/null)

    if echo "$deps" | grep -qi "spring-boot\|springframework"; then
        DETECTED_FRAMEWORKS+=("spring")
    fi

    if echo "$deps" | grep -qi "quarkus"; then
        DETECTED_FRAMEWORKS+=("quarkus")
    fi

    if echo "$deps" | grep -qi "micronaut"; then
        DETECTED_FRAMEWORKS+=("micronaut")
    fi

    if echo "$deps" | grep -qi "ktor"; then
        DETECTED_FRAMEWORKS+=("ktor")
    fi
}

# Detect project type and tools
detect_project() {
    # Node.js / TypeScript
    if [[ -f "$REPO_ROOT/package.json" ]]; then
        PROJECT_TYPE="node"
        DETECTED_TOOLS+=("node")

        # Detect package manager
        if [[ -f "$REPO_ROOT/pnpm-lock.yaml" ]]; then
            PACKAGE_MANAGER="pnpm"
        elif [[ -f "$REPO_ROOT/yarn.lock" ]]; then
            PACKAGE_MANAGER="yarn"
        elif [[ -f "$REPO_ROOT/bun.lockb" ]]; then
            PACKAGE_MANAGER="bun"
        else
            PACKAGE_MANAGER="npm"
        fi
        DETECTED_TOOLS+=("$PACKAGE_MANAGER")

        # Check for TypeScript
        if [[ -f "$REPO_ROOT/tsconfig.json" ]]; then
            PROJECT_TYPE="node-typescript"
            DETECTED_TOOLS+=("typescript")
        fi

        # Detect test runner from package.json
        if grep -q '"jest"' "$REPO_ROOT/package.json" 2>/dev/null; then
            TEST_RUNNER="jest"
            DETECTED_TOOLS+=("jest")
        elif grep -q '"vitest"' "$REPO_ROOT/package.json" 2>/dev/null; then
            TEST_RUNNER="vitest"
            DETECTED_TOOLS+=("vitest")
        elif grep -q '"mocha"' "$REPO_ROOT/package.json" 2>/dev/null; then
            TEST_RUNNER="mocha"
            DETECTED_TOOLS+=("mocha")
        fi

        # Detect linter
        if [[ -f "$REPO_ROOT/.eslintrc.json" ]] || [[ -f "$REPO_ROOT/.eslintrc.js" ]] || [[ -f "$REPO_ROOT/.eslintrc.cjs" ]] || [[ -f "$REPO_ROOT/eslint.config.js" ]] || [[ -f "$REPO_ROOT/eslint.config.mjs" ]]; then
            LINTER="eslint"
            DETECTED_TOOLS+=("eslint")
        elif grep -q '"eslint"' "$REPO_ROOT/package.json" 2>/dev/null; then
            LINTER="eslint"
            DETECTED_TOOLS+=("eslint")
        fi

        # Detect formatter
        if [[ -f "$REPO_ROOT/.prettierrc" ]] || [[ -f "$REPO_ROOT/.prettierrc.json" ]] || [[ -f "$REPO_ROOT/prettier.config.js" ]]; then
            FORMATTER="prettier"
            DETECTED_TOOLS+=("prettier")
        elif grep -q '"prettier"' "$REPO_ROOT/package.json" 2>/dev/null; then
            FORMATTER="prettier"
            DETECTED_TOOLS+=("prettier")
        fi

        # Detect Node.js frameworks
        detect_node_frameworks

    # Scala (sbt)
    elif [[ -f "$REPO_ROOT/build.sbt" ]]; then
        PROJECT_TYPE="scala-sbt"
        PACKAGE_MANAGER="sbt"
        TEST_RUNNER="sbt-test"
        FORMATTER="scalafmt"
        DETECTED_TOOLS+=("scala" "sbt" "scalafmt")

        # Check for scalafix
        if [[ -f "$REPO_ROOT/.scalafix.conf" ]]; then
            LINTER="scalafix"
            DETECTED_TOOLS+=("scalafix")
        fi

        # Detect Scala frameworks
        detect_scala_frameworks

    # Scala (Mill)
    elif [[ -f "$REPO_ROOT/build.sc" ]]; then
        PROJECT_TYPE="scala-mill"
        PACKAGE_MANAGER="mill"
        TEST_RUNNER="mill-test"
        FORMATTER="scalafmt"
        DETECTED_TOOLS+=("scala" "mill" "scalafmt")

        # Detect Scala frameworks
        detect_scala_frameworks

    # Python
    elif [[ -f "$REPO_ROOT/pyproject.toml" ]] || [[ -f "$REPO_ROOT/requirements.txt" ]] || [[ -f "$REPO_ROOT/setup.py" ]]; then
        PROJECT_TYPE="python"
        DETECTED_TOOLS+=("python")

        # Detect package manager
        if [[ -f "$REPO_ROOT/poetry.lock" ]]; then
            PACKAGE_MANAGER="poetry"
            DETECTED_TOOLS+=("poetry")
        elif [[ -f "$REPO_ROOT/Pipfile.lock" ]]; then
            PACKAGE_MANAGER="pipenv"
            DETECTED_TOOLS+=("pipenv")
        elif [[ -f "$REPO_ROOT/uv.lock" ]]; then
            PACKAGE_MANAGER="uv"
            DETECTED_TOOLS+=("uv")
        else
            PACKAGE_MANAGER="pip"
            DETECTED_TOOLS+=("pip")
        fi

        # Detect test runner
        if [[ -f "$REPO_ROOT/pytest.ini" ]] || grep -q "pytest" "$REPO_ROOT/pyproject.toml" 2>/dev/null || grep -q "pytest" "$REPO_ROOT/requirements.txt" 2>/dev/null; then
            TEST_RUNNER="pytest"
            DETECTED_TOOLS+=("pytest")
        fi

        # Detect linter/formatter
        if grep -q "ruff" "$REPO_ROOT/pyproject.toml" 2>/dev/null || [[ -f "$REPO_ROOT/ruff.toml" ]]; then
            LINTER="ruff"
            FORMATTER="ruff"
            DETECTED_TOOLS+=("ruff")
        fi
        if grep -q "black" "$REPO_ROOT/pyproject.toml" 2>/dev/null; then
            FORMATTER="black"
            DETECTED_TOOLS+=("black")
        fi
        if grep -q "mypy" "$REPO_ROOT/pyproject.toml" 2>/dev/null; then
            DETECTED_TOOLS+=("mypy")
        fi

        # Detect Python frameworks
        detect_python_frameworks

    # Rust
    elif [[ -f "$REPO_ROOT/Cargo.toml" ]]; then
        PROJECT_TYPE="rust"
        PACKAGE_MANAGER="cargo"
        TEST_RUNNER="cargo-test"
        LINTER="clippy"
        FORMATTER="rustfmt"
        DETECTED_TOOLS+=("rust" "cargo" "clippy" "rustfmt")

        # Detect Rust frameworks
        detect_rust_frameworks

    # Go
    elif [[ -f "$REPO_ROOT/go.mod" ]]; then
        PROJECT_TYPE="go"
        PACKAGE_MANAGER="go-mod"
        TEST_RUNNER="go-test"
        FORMATTER="gofmt"
        LINTER="go-vet"
        DETECTED_TOOLS+=("go" "gofmt" "go-vet")

        # Check for golangci-lint
        if [[ -f "$REPO_ROOT/.golangci.yml" ]] || [[ -f "$REPO_ROOT/.golangci.yaml" ]]; then
            LINTER="golangci-lint"
            DETECTED_TOOLS+=("golangci-lint")
        fi

        # Detect Go frameworks
        detect_go_frameworks

    # Java (Maven)
    elif [[ -f "$REPO_ROOT/pom.xml" ]]; then
        PROJECT_TYPE="java-maven"
        PACKAGE_MANAGER="maven"
        TEST_RUNNER="maven-test"
        DETECTED_TOOLS+=("java" "maven")

        # Detect Java frameworks
        detect_java_frameworks

    # Java (Gradle)
    elif [[ -f "$REPO_ROOT/build.gradle" ]] || [[ -f "$REPO_ROOT/build.gradle.kts" ]]; then
        PROJECT_TYPE="java-gradle"
        PACKAGE_MANAGER="gradle"
        TEST_RUNNER="gradle-test"
        DETECTED_TOOLS+=("java" "gradle")

        # Detect Java frameworks
        detect_java_frameworks

    # .NET
    elif [[ -f "$REPO_ROOT/*.csproj" ]] || [[ -f "$REPO_ROOT/*.sln" ]] || find "$REPO_ROOT" -maxdepth 2 -name "*.csproj" -o -name "*.sln" 2>/dev/null | head -1 | grep -q .; then
        PROJECT_TYPE="dotnet"
        PACKAGE_MANAGER="dotnet"
        TEST_RUNNER="dotnet-test"
        DETECTED_TOOLS+=("dotnet")

    # Ruby
    elif [[ -f "$REPO_ROOT/Gemfile" ]]; then
        PROJECT_TYPE="ruby"
        PACKAGE_MANAGER="bundler"
        DETECTED_TOOLS+=("ruby" "bundler")

        if grep -q "rspec" "$REPO_ROOT/Gemfile" 2>/dev/null; then
            TEST_RUNNER="rspec"
            DETECTED_TOOLS+=("rspec")
        fi

        if grep -q "rubocop" "$REPO_ROOT/Gemfile" 2>/dev/null; then
            LINTER="rubocop"
            DETECTED_TOOLS+=("rubocop")
        fi

        # Detect Ruby frameworks
        detect_ruby_frameworks

    # PHP
    elif [[ -f "$REPO_ROOT/composer.json" ]]; then
        PROJECT_TYPE="php"
        PACKAGE_MANAGER="composer"
        DETECTED_TOOLS+=("php" "composer")

        if grep -q "phpunit" "$REPO_ROOT/composer.json" 2>/dev/null; then
            TEST_RUNNER="phpunit"
            DETECTED_TOOLS+=("phpunit")
        fi

        # Detect PHP frameworks
        detect_php_frameworks
    fi
}

# Run detection
detect_project

# Define output paths
CLAUDE_DIR="$REPO_ROOT/.claude"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"
SKILLS_DIR="$CLAUDE_DIR/skills"
HOOKS_DIR="$CLAUDE_DIR/hooks"

# Check if .claude directory already exists
CLAUDE_EXISTS="false"
if [[ -d "$CLAUDE_DIR" ]]; then
    CLAUDE_EXISTS="true"
fi

# Check if settings.json already exists
SETTINGS_EXISTS="false"
if [[ -f "$SETTINGS_FILE" ]]; then
    SETTINGS_EXISTS="true"
fi

# Output results
if $JSON_MODE; then
    # Build JSON array of detected tools
    TOOLS_JSON="["
    first=true
    for tool in "${DETECTED_TOOLS[@]}"; do
        if $first; then
            first=false
        else
            TOOLS_JSON+=","
        fi
        TOOLS_JSON+="\"$tool\""
    done
    TOOLS_JSON+="]"

    # Build JSON array of detected frameworks with docs
    FRAMEWORKS_JSON="["
    first=true
    for framework in "${DETECTED_FRAMEWORKS[@]}"; do
        if $first; then
            first=false
        else
            FRAMEWORKS_JSON+=","
        fi

        # Get documentation URLs
        doc_urls="${FRAMEWORK_DOCS[$framework]:-}"
        if [[ -n "$doc_urls" ]]; then
            docs_url="${doc_urls%%|*}"
            github_url="${doc_urls##*|}"
        else
            docs_url=""
            github_url=""
        fi

        FRAMEWORKS_JSON+="{\"name\":\"$framework\",\"docs_url\":\"$docs_url\",\"github_url\":\"$github_url\"}"
    done
    FRAMEWORKS_JSON+="]"

    cat <<EOF
{
  "PROJECT_TYPE": "$PROJECT_TYPE",
  "PACKAGE_MANAGER": "$PACKAGE_MANAGER",
  "TEST_RUNNER": "$TEST_RUNNER",
  "LINTER": "$LINTER",
  "FORMATTER": "$FORMATTER",
  "DETECTED_TOOLS": $TOOLS_JSON,
  "DETECTED_FRAMEWORKS": $FRAMEWORKS_JSON,
  "REPO_ROOT": "$REPO_ROOT",
  "CLAUDE_DIR": "$CLAUDE_DIR",
  "SETTINGS_FILE": "$SETTINGS_FILE",
  "SKILLS_DIR": "$SKILLS_DIR",
  "HOOKS_DIR": "$HOOKS_DIR",
  "CLAUDE_EXISTS": $CLAUDE_EXISTS,
  "SETTINGS_EXISTS": $SETTINGS_EXISTS
}
EOF
else
    echo "=== Project Detection Results ==="
    echo ""
    echo "Project Type: $PROJECT_TYPE"
    echo "Package Manager: ${PACKAGE_MANAGER:-none detected}"
    echo "Test Runner: ${TEST_RUNNER:-none detected}"
    echo "Linter: ${LINTER:-none detected}"
    echo "Formatter: ${FORMATTER:-none detected}"
    echo ""
    echo "Detected Tools: ${DETECTED_TOOLS[*]:-none}"
    echo ""
    echo "=== Detected Frameworks ==="
    if [[ ${#DETECTED_FRAMEWORKS[@]} -gt 0 ]]; then
        for framework in "${DETECTED_FRAMEWORKS[@]}"; do
            doc_urls="${FRAMEWORK_DOCS[$framework]:-}"
            if [[ -n "$doc_urls" ]]; then
                docs_url="${doc_urls%%|*}"
                github_url="${doc_urls##*|}"
                echo "  - $framework"
                echo "    Docs: $docs_url"
                echo "    GitHub: $github_url"
            else
                echo "  - $framework"
            fi
        done
    else
        echo "  No frameworks detected"
    fi
    echo ""
    echo "=== Claude Code Paths ==="
    echo "Claude Directory: $CLAUDE_DIR (exists: $CLAUDE_EXISTS)"
    echo "Settings File: $SETTINGS_FILE (exists: $SETTINGS_EXISTS)"
    echo "Skills Directory: $SKILLS_DIR"
    echo "Hooks Directory: $HOOKS_DIR"
fi
