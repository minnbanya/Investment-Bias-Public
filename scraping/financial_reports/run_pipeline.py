import subprocess
import sys
import os

def run_script(script_name):
    """Run a Python script and return True if successful, False otherwise."""
    print(f"\n🚀 Running {script_name}...")
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {script_name} completed successfully.")
        print(result.stdout)
        if result.stderr:
            print(f"⚠️ Warnings/Errors from {script_name}:\n{result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_name}: {e}")
        print(f"Error output:\n{e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ Error: {script_name} not found in the working directory.")
        return False

def check_file_exists(file_path):
    """Check if a file exists in the working directory."""
    if not os.path.isfile(file_path):
        print(f"❌ Error: {file_path} not found in the working directory.")
        return False
    return True

def main():
    """Run the pipeline scripts sequentially."""
    print("🌟 Starting Thesis Dataset Pipeline 🌟")

    # List of scripts in order of execution
    scripts = [
        "extract_investment_data.py",
        "generate_control_samples.py",
        "count_samples.py",
        "count_sectors.py"
    ]

    # Check if all required files exist
    required_files = ["tickers.json"] + scripts
    for file in required_files:
        if not check_file_exists(file):
            print("🛑 Pipeline aborted due to missing file.")
            sys.exit(1)

    # Run each script sequentially
    for script in scripts:
        if not run_script(script):
            print(f"🛑 Pipeline aborted due to error in {script}.")
            sys.exit(1)
        # Additional check for output files after relevant scripts
        if script == "extract_investment_data.py":
            if not check_file_exists("investment_metrics.json"):
                print("🛑 Pipeline aborted: investment_metrics.json not generated.")
                sys.exit(1)
        elif script == "generate_control_samples.py":
            if not check_file_exists("control_samples.json"):
                print("🛑 Pipeline aborted: control_samples.json not generated.")
                sys.exit(1)

    print("\n🎉 Thesis Dataset Pipeline completed successfully!")
    print("📂 Outputs generated: investment_metrics.json, control_samples.json")
    print("📊 Check console output above for sample counts and sector distribution.")

if __name__ == "__main__":
    main()