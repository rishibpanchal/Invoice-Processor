"""
Invoice Processing Application Launcher
Comprehensive setup and launch script for the Qt-based invoice processor
"""
import os
import sys
import subprocess
import platform
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def install_requirements():
    """Install required packages"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("✅ All packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False


def check_ollama_server():
    """Check if Ollama server is running"""
    try:
        import requests
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama server is running")
            return True
        else:
            print("⚠️ Ollama server responded with error")
            return False
    except Exception as e:
        print("⚠️ Ollama server not accessible. Please ensure Ollama is installed and running.")
        print("   Download from: https://ollama.ai")
        print(f"   Error: {e}")
        return False


def check_model_availability():
    """Check if the required model is available"""
    try:
        import requests
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            
            # Check for the default model
            target_model = "gemma3n:e2b"
            if any(target_model in name for name in model_names):
                print(f"✅ Model {target_model} is available")
                return True
            else:
                print(f"⚠️ Model {target_model} not found")
                print("Available models:", model_names)
                print(f"To install the model, run: ollama pull {target_model}")
                return False
    except Exception as e:
        print(f"❌ Could not check model availability: {e}")
        return False


def check_sample_files():
    """Check if sample PDF files are available"""
    files_dir = Path(__file__).parent / "files"
    if files_dir.exists():
        pdf_files = list(files_dir.glob("*.pdf"))
        if pdf_files:
            print(f"✅ Sample PDF files found: {len(pdf_files)} files")
            for pdf in pdf_files:
                print(f"   📄 {pdf.name}")
            return True
    
    print("ℹ️ No sample PDF files found in 'files' directory")
    print("   You can add PDF invoices to test the application")
    return True  # Not critical


def launch_gui():
    """Launch the Multi-Stage Qt GUI application"""
    gui_script = Path(__file__).parent / "qt viewer" / "main_multi_stage_qt.py"
    app_name = "Multi-Stage Invoice Processing GUI"
    
    if not gui_script.exists():
        print(f"❌ GUI script not found: {gui_script}")
        return False
    
    print(f"🚀 Launching {app_name}...")
    try:
        # Change to the qt viewer directory for proper imports
        original_dir = os.getcwd()
        os.chdir(gui_script.parent)
        
        subprocess.run([sys.executable, str(gui_script.name)], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to launch GUI: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Application closed by user")
        return True
    finally:
        os.chdir(original_dir)

def show_system_info():
    """Display system information"""
    print("\n" + "="*60)
    print("🖥️  SYSTEM INFORMATION")
    print("="*60)
    print(f"Operating System: {platform.system()} {platform.release()}")
    print(f"Python Version: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Script Location: {Path(__file__).parent}")
    print("="*60)


def show_help():
    """Show help information"""
    print("\n" + "="*60)
    print("📚 MULTI-STAGE INVOICE PROCESSOR HELP")
    print("="*60)
    print("This application extracts structured data from PDF invoices using AI.")
    print("Uses advanced multi-stage extraction for maximum accuracy.")
    print()
    print("Multi-Stage Approach Features:")
    print("• Better accuracy through focused prompts")
    print("• Clear separation between different invoices")
    print("• Progressive data building with error isolation")
    print("• Detailed progress tracking")
    print("• Graceful degradation on partial failures")
    print()
    print("Prerequisites:")
    print("1. Python 3.8+ installed")
    print("2. Ollama installed and running (https://ollama.ai)")
    print("3. Required Python packages (automatically installed)")
    print()
    print("Usage:")
    print("1. Run this script to launch the application")
    print("2. Click 'Load PDF' to select an invoice")
    print("3. Click 'Multi-Stage Process' to extract data")
    print("4. View results in the tabs")
    print("5. Export to JSON or CSV as needed")
    print()
    print("Troubleshooting:")
    print("- Ensure Ollama server is running on localhost:11434")
    print("- Check that the required model is installed")
    print("- Verify PDF files are readable and contain text")
    print("="*60)


def main():
    """Main launcher function"""
    print("🧾 Invoice Processing Application Launcher")
    print("=" * 50)
    
    # Check system requirements
    if not check_python_version():
        sys.exit(1)
    
    # Show system info
    show_system_info()
    
    # Install requirements
    print("\n📋 CHECKING DEPENDENCIES")
    print("-" * 30)
    if not install_requirements():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Check Ollama
    print("\n🤖 CHECKING AI SERVICE")
    print("-" * 30)
    ollama_ok = check_ollama_server()
    if ollama_ok:
        check_model_availability()
    
    # Check sample files
    print("\n📁 CHECKING SAMPLE FILES")
    print("-" * 30)
    check_sample_files()
    
    # Test extraction if possible
    if ollama_ok:
        print("\n🧪 TESTING EXTRACTION")
        print("-" * 30)
        # test_extraction()
    
    # Show help
    show_help()
    
    # Launch the application
    print("\n🚀 LAUNCHING MULTI-STAGE APPLICATION")
    print("-" * 40)
    print("Starting the advanced multi-stage invoice processor...")
    
    if not launch_gui():
        print("❌ Failed to launch application")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Launcher interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
