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
    parser.add_argument("--lint", action="store_true", help="Run the mock linter")
    parser.add_argument("--deploy", action="store_true", help="Run the mock deployer")
    args = parser.parse_args()

    if args.lint:
        lint()
    elif args.deploy:
        deploy()
    else:
        print("This is a script to test extension commands. Run with --lint or --deploy.")

if __name__ == "__main__":
    main()
