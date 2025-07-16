# 🚀 Klinex - Mac File Cleaner

Klinex is a Streamlit-based application designed to help macOS users identify large files on their system and receive AI-generated suggestions regarding their potential deletability. It provides a user-friendly interface to scan directories, view the biggest files, get AI insights, and safely move selected files to Trash.

## ✨ Features

* **Directory Scanning**: Scan any specified directory on your macOS system for large files.

* **Size Filtering**: Filter files based on a minimum size (in MB) to focus on genuinely large items.

* **Top N Files Display**: Display a configurable number of the largest files found.

* **AI-Powered Deletion Suggestions**: Utilizes the Google Gemini API to provide suggestions on whether a file might be safe to delete, based on its name and path.

* **Color-Coded Safety Guide**: AI suggestions are color-coded (Red, Orange, Yellow, Green) for quick visual understanding of potential risks.

* **Concurrent AI Analysis**: Optimized to analyze multiple files concurrently with the Gemini API, significantly speeding up the analysis phase.

* **Safe Deletion**: Move selected files to macOS Trash, allowing for recovery if a mistake is made.

* **Liberated Space Tracking**: Keeps a running total of the disk space reclaimed through deletions.

## ⚠️ IMPORTANT WARNING: USE WITH EXTREME CAUTION! ⚠️

**This tool provides AI suggestions based solely on file names and paths. The AI cannot understand the actual content of your files or their real-time dependencies within your operating system.**

* **Risk of Data Loss**: Deleting critical system files, application components, or essential user data can severely damage your macOS installation, render applications unusable, or lead to permanent data loss.

* **Always Verify**: **NEVER** delete a file without manually verifying its purpose and contents. If you are unsure, do not delete it. Use online resources or file utility tools to understand a file's function before proceeding.

* **Trash, Not Permanent Deletion**: Files are moved to the macOS Trash, providing a safeguard. However, the Trash can be emptied, making deletion permanent.

**The developer of this tool is not responsible for any data loss or system instability caused by its misuse.**

## ⚙️ Setup and Installation

To run Klinex, you'll need Python 3 and a Google Gemini API Key.

1.  **Clone the Repository (or Download the Script):**

    ```bash
    git clone [https://github.com/your-username/klinex-mac-file-cleaner.git](https://github.com/your-username/klinex-mac-file-cleaner.git)
    cd klinex-mac-file-cleaner
    ```

    (Note: Replace `your-username/klinex-mac-file-cleaner.git` with the actual repository URL if you've hosted it.)

2.  **Create a Virtual Environment (Recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

    If you don't have a `requirements.txt` file, you'll need to install them manually:

    ```bash
    pip install streamlit humanize google-generativeai send2trash
    ```

4.  **Obtain a Google Gemini API Key:**

    * Go to [Google AI Studio](https://aistudio.google.com/app/apikey).

    * Sign in with your Google account.

    * Create a new API key.

    * Keep this key secure; you will enter it into the application's sidebar.

## 🚀 Usage

1.  **Run the Streamlit Application:**

    ```bash
    streamlit run your_script_name.py # Replace 'your_script_name.py' with the actual file name
    ```

    This will open the application in your default web browser (usually at `http://localhost:8501`).

2.  **Configure in the Sidebar:**

    * **Enter your Gemini API Key**: Paste the API key you obtained from Google AI Studio.

    * **Select Gemini Model**: Choose your preferred Gemini model for AI analysis (e.g., `gemini-2.5-flash` for faster results).

    * **Directory to Scan**: Specify the path to the directory you want to scan (e.g., `/Users/YourUsername/Downloads`).

    * **Number of largest files to display**: Adjust how many large files you want to see in the results.

    * **Minimum file size (MB) to include**: Set the minimum size for files to be considered in the scan.

3.  **Start Scan and AI Analysis**:

    * Click the "Start Scan and AI Analysis" button. The application will first scan for files and then concurrently analyze them using the Gemini API. Progress bars will keep you informed.

4.  **Review Results and Take Action**:

    * Once the analysis is complete, a list of large files will appear with their sizes and the AI's safety suggestion (color-coded).

    * **Carefully review each file**: Read the AI's reason, consider the file's path and name, and if necessary, manually investigate the file on your system before selecting it.

    * **Select Files**: Use the checkboxes next to each file to select them for deletion.

    * **Move Selected Files to Trash**: Click this button to move all checked files to your macOS Trash.

    * **Individual Delete**: Each file also has an individual "Move to Trash" button for quick single deletions.

5.  **Monitor Liberated Space**: The "Total Space Liberated" metric will update as you move files to the Trash.

## 🤝 Contributing

Contributions are welcome! If you have suggestions for improvements or find any issues, please open an issue or submit a pull request.

## 📄 License

This project is open-source. (Consider adding a specific license, e.g., MIT, Apache 2.0)
