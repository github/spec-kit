import argparse
from datetime import datetime

def lint():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"The linter is complete {timestamp}")

def deploy():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Staging deployment is completed at {timestamp}")

def main():
    parser = argparse.ArgumentParser(description="Extension Commands Mock python Script")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--lint", action="store_true", help="Run the mock linter")
    group.add_argument("--deploy", action="store_true", help="Run the mock deployer")
    args = parser.parse_args()

    if args.lint:
        lint()
    elif args.deploy:
        deploy()

if __name__ == "__main__":
    main()
