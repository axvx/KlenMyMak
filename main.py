import streamlit as st
import os
import time
from pathlib import Path
import humanize  # pip install humanize
import google.generativeai as genai  # pip install google-generativeai
import send2trash  # pip install send2trash
import concurrent.futures  # New import for concurrent processing

# --- Configuration ---
# --- IMPORTANT: The API key should be entered by the user in the UI. ---

# Configure Streamlit page for a wider layout and dark theme (if supported by browser)
st.set_page_config(
    layout="wide",
    page_title="Klinex - Mac File Cleaner",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark text on light colored boxes to improve readability,
# and generally ensure good contrast.
st.markdown("""
<style>
    /* Ensure text within the color-coded spans is dark for readability on light backgrounds */
    span[style*="background-color: #ffcccc"],
    span[style*="background-color: #ffe0b3"],
    span[style*="background-color: #ffffb3"],
    span[style*="background-color: #ccffcc"] {
        color: #333333 !important; /* Dark grey text */
    }

    /* General text color adjustments for overall UI if needed for contrast in certain themes */
    body {
        color: var(--text-color); /* Uses Streamlit's default text color variable */
    }
    .stButton > button {
        color: white;
        background-color: #4CAF50; /* A pleasant green for buttons */
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    }
    .stButton > button:hover {
        background-color: #45a049;
        box-shadow: 3px 3px 8px rgba(0,0,0,0.3);
    }
    .stCheckbox > label > div {
        color: var(--text-color); /* Ensure checkbox label is readable */
    }
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-color); /* Ensure headers are readable */
    }
    /* Specific style for "Move Selected Files to Trash" button to make it red */
    .stButton button[data-testid="stButton-primary"]:last-of-type {
        background-color: #dc3545; /* Red color for danger */
    }
    .stButton button[data-testid="stButton-primary"]:last-of-type:hover {
        background-color: #c82333; /* Darker red on hover */
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Klinex - Mac File Cleaner")
st.markdown("""
    This application helps you find large files on your macOS system and provides
    **AI-generated suggestions** about their potential deletability.

    ### ⚠️ **IMPORTANT WARNING: USE THIS TOOL WITH EXTREME CAUTION!** ⚠️
    * **The AI suggestions are based on file names/paths and are NOT infallible.** They cannot truly understand your system's dependencies.
    * **Deleting critical system files, application components, or essential user data can damage your macOS installation or lead to data loss.**
    * **ALWAYS manually verify a file's purpose and contents before considering deletion.**
    * **Files are moved to Trash, not permanently deleted, but exercise caution.**
""")

# Initialize session state variables
if 'scanned_files' not in st.session_state:
    st.session_state.scanned_files = []
if 'scan_completed' not in st.session_state:
    st.session_state.scan_completed = False
if 'analysis_completed' not in st.session_state:
    st.session_state.analysis_completed = False
if 'selected_files' not in st.session_state:
    st.session_state.selected_files = set()  # Use a set for efficient lookups and unique paths
if 'space_liberated' not in st.session_state:
    st.session_state.space_liberated = 0  # New: To track liberated space


# --- File Scanning Functions ---

def get_biggest_files(start_path, num_files=50, min_size_mb=50):
    """
    Scans a directory and its subdirectories to find the biggest files.
    Excludes common macOS system directories to prevent permission issues and irrelevant results.
    """
    st.info(f"Scanning for files larger than {min_size_mb} MB in '{start_path}'...")
    file_list = []

    # List of common macOS system directories to exclude from scanning.
    # Scanning these often leads to permission errors and irrelevant/critical system files.
    excluded_dirs_prefixes = [
        '/Applications', '/System', '/Library', '/usr', '/bin', '/sbin',
        '/cores', '/dev', '/etc', '/net', '/private', '/tmp', '/var',
        # Exclude common user-level caches/libraries that are usually managed by macOS
        str(Path.home() / 'Library' / 'Caches'),
        str(Path.home() / 'Library' / 'Containers'),
        str(Path.home() / 'Library' / 'Application Support'),
        str(Path.home() / 'Library' / 'Group Containers')
    ]

    # Progress bar and text placeholders
    progress_text_placeholder = st.empty()
    progress_bar_placeholder = st.progress(0)

    total_files_scanned = 0
    start_time = time.time()

    # Walk through the directory tree
    for root, dirs, files in os.walk(start_path,
                                     followlinks=False):  # followlinks=False to avoid infinite loops and external volumes
        # Skip excluded system directories at the root level of the walk
        # Using a copy of dirs to allow modification during iteration if needed
        dirs_to_skip = []
        for d in dirs:
            current_dir_path = os.path.join(root, d)
            if any(current_dir_path.startswith(prefix) for prefix in excluded_dirs_prefixes):
                dirs_to_skip.append(d)
        # Modify dirs in-place to prune the search tree
        for d_skip in dirs_to_skip:
            dirs.remove(d_skip)

        for file in files:
            file_path = Path(root) / file
            try:
                if file_path.is_file():
                    size = file_path.stat().st_size
                    if size > min_size_mb * 1024 * 1024:  # Convert MB to Bytes
                        file_list.append({'path': str(file_path), 'size': size})

                    total_files_scanned += 1
                    # Update progress bar every 1000 files or every 5 seconds for performance
                    if total_files_scanned % 1000 == 0 or (time.time() - start_time) > 5:
                        progress_bar_placeholder.progress(
                            min(int(total_files_scanned / 50000 * 100), 100))  # Arbitrary scaling for visual
                        progress_text_placeholder.text(
                            f"Scanned {humanize.intword(total_files_scanned)} files... (Found {len(file_list)} large files)")
                        start_time = time.time()  # Reset timer

            except PermissionError:
                # Silently skip files/directories we don't have permission to access
                pass
            except Exception as e:
                # Log other errors for debugging, but don't stop the scan
                # st.warning(f"Error accessing {file_path}: {e}")
                pass

    progress_bar_placeholder.empty()  # Hide progress bar
    progress_text_placeholder.empty()  # Hide progress text
    st.success("File scan complete!")

    # Sort by size in descending order and take the top N
    file_list.sort(key=lambda x: x['size'], reverse=True)
    return file_list[:num_files]


# --- Gemini API for Safety Suggestion (Linguistic Analysis) ---

def get_file_safety_suggestion(file_path_str, gemini_model_instance):
    """
    Uses the Gemini API to provide a safety suggestion based on file name/path.
    **WARNING: This is a linguistic analysis and NOT a reliable indicator of
    whether a file can be safely deleted from an operating system.**
    """
    file_path_obj = Path(file_path_str)
    file_name = file_path_obj.name
    parent_dir = file_path_obj.parent.name
    grandparent_dir = file_path_obj.parent.parent.name if file_path_obj.parent.parent else ""

    prompt = f"""
    Analyze the following file path and name to provide a safety suggestion for deletion on a macOS system.
    This analysis is based ONLY on the textual information (file name, path components), not on the file's content or its actual system function.

    **Categorize the file's deletability into one of four categories based on common macOS file types and locations:**
    -   **Red (Highly Unsafe):** Files likely critical to macOS, applications, or user data (e.g., system libraries, `.app` contents, essential user documents). Deleting these will likely cause system instability or data loss.
    -   **Orange (Potentially Unsafe / Caution Required):** Files that might be important or whose function is unclear (e.g., configuration files, unknown binaries, files in sensitive user Library subdirectories).
    -   **Yellow (Might be Safe with Caution):** Files that are often temporary, cached, or user-generated but might still have some purpose (e.g., old application caches, logs, general downloads). Review carefully.
    -   **Green (Generally Safe):** Files that are very likely safe to delete (e.g., truly temporary files, old installers, large media files explicitly placed in Downloads). Still, always double-check.

    Provide a brief, concise reasoning for your suggestion.

    File Path: {file_path_str}
    File Name: {file_name}
    Parent Directory: {parent_dir}
    Grandparent Directory: {grandparent_dir}

    Example Output Format (MUST be followed exactly):
    Color: [Red/Orange/Yellow/Green]
    Reason: [Your concise reasoning]
    """

    suggestion = "Uncertain - AI analysis failed"
    color_code = "orange"  # Default to caution in case of failure

    try:
        # Use a low temperature for more deterministic, less creative answers
        response = gemini_model_instance.generate_content(prompt, generation_config={"temperature": 0.1})
        text_response = response.text.strip()

        # Parse the response based on the expected format
        color_match = next((line.split("Color:")[1].strip().lower() for line in text_response.split('\n') if
                            line.startswith("Color:")), None)
        reason_match = next(
            (line.split("Reason:", 1)[1].strip() for line in text_response.split('\n') if line.startswith("Reason:")),
            None)

        if color_match and reason_match:
            suggestion = reason_match
            if "red" in color_match:
                color_code = "red"
            elif "orange" in color_match:
                color_code = "orange"
            elif "yellow" in color_match:
                color_code = "yellow"
            elif "green" in color_match:
                color_code = "green"
            else:
                suggestion = f"AI output unparseable: {text_response}"
                color_code = "orange"
        else:
            suggestion = f"AI output format mismatch: {text_response}"
            color_code = "orange"

    except Exception as e:
        suggestion = f"Gemini API Error: {e}. Defaulting to uncertain."
        color_code = "orange"

    return suggestion, color_code


# --- File Deletion Function ---

def delete_file_to_trash(file_path):
    """Moves a file to the system's trash using send2trash for safety.
    Returns success status, message, and the size of the deleted file."""
    try:
        # Get size before deleting
        size_bytes = Path(file_path).stat().st_size
        send2trash.send2trash(str(file_path))  # send2trash expects a string path
        return True, f"Moved to Trash: {file_path.name}", size_bytes
    except FileNotFoundError:
        return False, f"Error: File not found - {file_path}", 0
    except Exception as e:
        return False, f"Error moving '{file_path.name}' to Trash: {e}", 0


# --- Streamlit UI ---

# Sidebar for options
st.sidebar.header("Configuration & Scan Options")

# Gemini API Key input
# The 'key' argument here ensures Streamlit automatically saves the value
# in st.session_state under that key, making it 'remembered' across reruns.
gemini_api_key = st.sidebar.text_input(
    "Enter your Gemini API Key:",
    type="password",
    help="Get your key from Google AI Studio. This is required for AI analysis.",
    key="gemini_api_key_input"  # This key makes the input value persist in session state
)

# Model selection mapping display names to actual model IDs
MODEL_OPTIONS = {
    # Prioritize 'gemini-2.5-flash' as explicitly requested
    "Gemini Flash (gemini-2.5-flash)": "gemini-2.5-flash",
    "Gemini Flash (Preview) (gemini-2.5-flash-preview-04-17)": "gemini-2.5-flash-preview-04-17",
    "Gemini Pro (gemini-pro)": "gemini-pro",
    "Gemini Pro (Preview) (gemini-1.5-pro-preview-0409)": "gemini-1.5-pro-preview-0409"
}

# Set the default model to 'gemini-2.5-flash'
default_model_key_display = "Gemini Flash (gemini-2.5-flash)"
if 'selected_model_id_session' in st.session_state:
    # If a model ID was previously selected, find its display name
    for display_name, model_id in MODEL_OPTIONS.items():
        if model_id == st.session_state.selected_model_id_session:
            default_model_key_display = display_name
            break

selected_display_name = st.sidebar.selectbox(
    "Select Gemini Model:",
    list(MODEL_OPTIONS.keys()),
    index=list(MODEL_OPTIONS.keys()).index(default_model_key_display),  # Set initial selection
    key="gemini_model_selector_display",  # Key for the selectbox widget
    help="Choose between Flash (faster, cheaper) and Pro (more capable) models for AI analysis."
)

# Store the actual model ID in session state for configuration persistence
selected_model_id = MODEL_OPTIONS[selected_display_name]
st.session_state.selected_model_id_session = selected_model_id

gemini_model = None
if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        # Use the selected model ID from the dropdown
        gemini_model = genai.GenerativeModel(selected_model_id)
        st.sidebar.success(f"Gemini API configured successfully with model: {selected_display_name}!")
    except Exception as e:
        st.sidebar.error(f"Failed to configure Gemini API. Please check your API key and model selection: {e}")
        gemini_model = None
else:
    st.sidebar.warning("Please enter your Gemini API Key to enable AI analysis.")

scan_path_input = st.sidebar.text_input("Directory to scan:", str(Path.home()))
num_files_to_show = st.sidebar.slider("Number of largest files to display:", 10, 500, 50)
min_size_mb_filter = st.sidebar.slider("Minimum file size (MB) to include:", 10, 1000, 50)

if st.sidebar.button("Start Scan and AI Analysis", type="primary"):
    if not gemini_model:
        st.error(
            "Please provide a valid Gemini API Key and ensure the model is configured before starting the scan and analysis.")
        st.stop()

    st.session_state.scan_completed = False
    st.session_state.analysis_completed = False
    st.session_state.scanned_files = []  # Clear previous results
    st.session_state.selected_files = set()  # Clear selected files
    st.session_state.space_liberated = 0  # Reset liberated space on new scan

    # Step 1: Scan for large files
    with st.spinner("Step 1/2: Scanning your Mac for large files... This might take a while."):
        st.session_state.scanned_files = get_biggest_files(scan_path_input, num_files_to_show, min_size_mb_filter)
    st.session_state.scan_completed = True

    if not st.session_state.scanned_files:
        st.warning("No large files found matching your criteria in the specified directory after scanning.")
        # If no files found, mark analysis as complete to avoid hanging state
        st.session_state.analysis_completed = True
        st.rerun()  # Rerun to update the UI
        st.stop()  # Stop execution if no files found to avoid AI analysis on empty list

    # Step 2: Analyze files with Gemini API concurrently
    st.success(
        f"Scan complete! Found {len(st.session_state.scanned_files)} large files. Now analyzing with Gemini AI using {selected_display_name}...")
    analysis_progress_bar = st.progress(0,
                                        text=f"Step 2/2: Analyzing files with Gemini AI using {selected_display_name}...")

    analyzed_files_temp = []
    futures = []
    file_info_map = {}  # To map futures back to original file_info objects

    # Max workers for ThreadPoolExecutor. Adjust based on API limits and network conditions.
    MAX_WORKERS = 5

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for i, file_info in enumerate(st.session_state.scanned_files):
            file_path_str = file_info['path']

            # Check if the file still exists before submitting to AI (files might be deleted manually)
            if not Path(file_path_str).exists():
                st.warning(f"File '{Path(file_path_str).name}' no longer exists, skipping AI analysis.")
                continue

            # Submit the AI analysis task to the thread pool
            future = executor.submit(get_file_safety_suggestion, file_path_str, gemini_model)
            futures.append(future)
            file_info_map[future] = file_info  # Keep a reference to the original file_info

        # Process results as they complete
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            original_file_info = file_info_map[future]
            try:
                suggestion, color_code = future.result()
                original_file_info['ai_suggestion'] = suggestion
                original_file_info['color_code'] = color_code
                analyzed_files_temp.append(original_file_info)
            except Exception as exc:
                st.error(f"Error analyzing file {original_file_info['path']}: {exc}")
                original_file_info['ai_suggestion'] = f"AI analysis failed: {exc}"
                original_file_info['color_code'] = "orange"  # Default to caution
                analyzed_files_temp.append(original_file_info)  # Still add to list, but with error

            # Update progress bar based on completed futures
            analysis_progress_bar.progress((i + 1) / len(futures))

    st.session_state.scanned_files = analyzed_files_temp  # Update with only successfully analyzed files
    analysis_progress_bar.empty()
    st.session_state.analysis_completed = True
    st.success("AI analysis complete! Review the suggestions below.")
    st.rerun()  # Re-run to display updated data immediately

# Display results if scan and analysis are complete
if st.session_state.scan_completed and st.session_state.analysis_completed:
    st.header("Largest Files Found and AI Suggestions:")

    color_map = {
        "red": "background-color: #ffcccc; padding: 5px; border-radius: 5px; border: 1px solid #ff0000; color: #333333;",
        "orange": "background-color: #ffe0b3; padding: 5px; border-radius: 5px; border: 1px solid #ffa500; color: #333333;",
        "yellow": "background-color: #ffffb3; padding: 5px; border-radius: 5px; border: 1px solid #cccc00; color: #333333;",
        "green": "background-color: #ccffcc; padding: 5px; border-radius: 5px; border: 1px solid #008000; color: #333333;"
    }

    st.markdown("""
        **Color Code Guide:**
        <span style='background-color: #ffcccc; padding: 2px 5px; border-radius: 3px; border: 1px solid #ff0000; color: #333333;'>**Red:** Highly Unsafe to Delete</span>
        <span style='background-color: #ffe0b3; padding: 2px 5px; border-radius: 3px; border: 1px solid #ffa500; color: #333333;'>**Orange:** Potentially Unsafe / Caution</span>
        <span style='background-color: #ffffb3; padding: 2px 5px; border-radius: 3px; border: 1px solid #cccc00; color: #333333;'>**Yellow:** Might be Safe with Caution</span>
        <span style='background-color: #ccffcc; padding: 2px 5px; border-radius: 3px; border: 1px solid #008000; color: #333333;'>**Green:** Generally Safe to Delete</span>
        """, unsafe_allow_html=True)
    st.markdown("---")

    # Display liberated space
    st.metric(label="Total Space Liberated", value=humanize.naturalsize(st.session_state.space_liberated))
    st.markdown("---")

    if st.session_state.scanned_files:
        # Bulk delete button
        if st.button("Move Selected Files to Trash", type="primary", key="bulk_delete_button"):
            if not st.session_state.selected_files:
                st.warning("No files selected for deletion.")
            else:
                num_deleted = 0
                total_size_deleted = 0
                messages = []

                # Create a list of file_info objects to be deleted
                files_to_delete_info = [
                    f_info for f_info in st.session_state.scanned_files
                    if f_info['path'] in st.session_state.selected_files
                ]

                for file_info_to_delete in files_to_delete_info:
                    file_path_to_delete = file_info_to_delete['path']
                    if Path(file_path_to_delete).exists():  # Double check existence
                        success, message, deleted_size = delete_file_to_trash(Path(file_path_to_delete))
                        if success:
                            num_deleted += 1
                            total_size_deleted += deleted_size
                            messages.append(f"✅ {message}")
                            # Remove from selected_files set immediately
                            st.session_state.selected_files.discard(file_path_to_delete)
                        else:
                            messages.append(f"❌ {message}")
                    else:
                        messages.append(f"⚠️ File '{Path(file_path_to_delete).name}' no longer exists.")
                        st.session_state.selected_files.discard(file_path_to_delete)  # Clean up selection

                # Update total liberated space
                st.session_state.space_liberated += total_size_deleted

                for msg in messages:
                    st.write(msg)
                if num_deleted > 0:
                    st.success(
                        f"Successfully moved {num_deleted} file(s) to Trash. Liberated {humanize.naturalsize(total_size_deleted)}.")
                    # Re-filter scanned_files to remove deleted ones and trigger UI update
                    st.session_state.scanned_files = [
                        f for f in st.session_state.scanned_files
                        if f['path'] not in st.session_state.selected_files
                        # Filter out selected ones (which are now deleted)
                    ]
                    st.rerun()  # Re-run to update the list and liberated space metric
                else:
                    st.info("No files were deleted.")
        st.markdown("---")

        for i, file_info in enumerate(st.session_state.scanned_files):
            file_path = Path(file_info['path'])
            file_size_human = humanize.naturalsize(file_info['size'])
            ai_suggestion = file_info.get('ai_suggestion', 'Analysis pending or failed.')
            color = file_info.get('color_code', 'orange')  # Default to orange if color not set

            # Check if file still exists on disk before showing delete option
            if not file_path.exists():
                st.info(f"File {file_path.name} (originally {file_size_human}) no longer exists on disk.")
                # Ensure it's not in selected_files if it's gone
                st.session_state.selected_files.discard(str(file_path))
                continue  # Skip to next file if already gone

            # Using columns for better layout
            col1, col2, col3, col4 = st.columns([0.5, 3, 2.5, 1.5])

            with col1:
                # Checkbox for multi-selection
                is_selected = st.checkbox(
                    "",
                    value=str(file_path) in st.session_state.selected_files,
                    key=f"select_chk_{i}",
                    on_change=lambda f=str(file_path): (
                        st.session_state.selected_files.add(f)
                        if f not in st.session_state.selected_files else
                        st.session_state.selected_files.discard(f)
                    )
                )
            with col2:
                st.markdown(f"**Path:** `{file_path}`")
                st.markdown(f"**Size:** `{file_size_human}`")
            with col3:
                # The AI suggestion displayed in a color-coded box
                st.markdown(f"**AI Suggestion:** <span style='{color_map.get(color, '')}'>{ai_suggestion}</span>",
                            unsafe_allow_html=True)
            with col4:
                # Individual delete button (for quick single deletion)
                if st.button(f"Move to Trash ({file_path.name})", key=f"delete_btn_{i}", type="primary"):
                    success, message, deleted_size = delete_file_to_trash(file_path)
                    if success:
                        st.success(message)
                        st.session_state.space_liberated += deleted_size  # Add to total
                        # Remove the deleted file from the displayed list
                        st.session_state.scanned_files = [
                            f for j, f in enumerate(st.session_state.scanned_files) if j != i
                        ]
                        st.session_state.selected_files.discard(str(file_path))  # Also deselect
                        st.rerun()  # Re-run to update the UI
                    else:
                        st.error(message)

            st.markdown("---")
    else:
        st.info("No large files found matching your criteria, or scanning/analysis not yet complete.")
else:
    st.info("Click 'Start Scan and AI Analysis' in the sidebar to begin.")

st.markdown("---")
st.caption("Developed with Streamlit and Gemini API (for textual analysis only).")
st.caption("Always exercise caution and verify file importance before deletion.")
