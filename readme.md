# Ulla - AI Support Training Bot

Ulla is an automated, AI-driven training bot designed to simulate realistic IT support conversations. It operates entirely over email, where it plays the role of "Ulla," a friendly but non-technical elderly user experiencing various computer problems.

The system is built to help IT support students practice their diagnostic, communication, and problem-solving skills in a controlled environment. Student progress is tracked, and problems are organized into escalating difficulty levels.

## Features

- **Email-Based Interaction:** Communicates using the Microsoft Graph API to send and receive real emails.
- **Multi-Level Problem Catalogue:** Problems are defined in `prompts.py` and structured into multiple difficulty levels, unlocked as the student succeeds.
- **Persistent Student Tracking:** A SQLite database (`conversations.db`) tracks each student's progress, current level, and active conversation.
- **Dual-LLM Architecture:**
  - **Evaluator AI:** A strict, logical model that determines if a student's suggestion correctly solves the problem.
  - **Persona AI:** A creative model that plays the role of Ulla, responding conversationally based on the Evaluator's verdict.
- **Highly Configurable:** Personas, problems, and difficulty levels can be easily modified or extended by editing the `prompts.py` file.
- **Utility Functions:** Includes command-line flags for database inspection and inbox cleanup.

## How It Works

The system operates in a loop, checking an email inbox for new messages. When a message from a student is found, it triggers the following sequence:

```
+----------------+      1. Student sends email      +---------------------+
| Student's M365 | -------------------------------> |   Bot's M365 Inbox  |
+----------------+                                  +----------+----------+
                                                               | 2. Script fetches email
                                                               v
+------------------+     3. Check DB for active problem     +------------------+
| conversations.db | <------------------------------------- | MailResponder.py |
+------------------+                                        |  (Core Logic)  |
                           4. Is solution correct?           +------+---------+
                                                               |    |
+------------------+      5. Get verdict: [LÖST]/[EJ_LÖST]     |    | 6. Generate reply
|  Evaluator LLM   | <-----------------------------------------+    |    based on verdict
+------------------+                                               |
                                                                    v
+------------------+    7. Get Ulla's response text      +-------------+
|   Persona LLM    | <---------------------------------- | Persona AI  |
+------------------+                                     +-------------+
                                                                    | 8. Script sends reply
                                                                    v
+----------------+      9. Student receives Ulla's reply      +---------------------+
| Student's M365 | <----------------------------------------- |   Bot's M365 Inbox  |
+----------------+                                            +---------------------+
```

## Setup and Installation

### Prerequisites

- Python 3.8+
- An active [Ollama](https://ollama.com/) instance, running and accessible from where the script is hosted.
- The LLM models specified in your `.env` file must be pulled in Ollama (e.g., `ollama pull gemma3:12b-it-qat`).
- An Azure Active Directory (Azure AD) account with permissions to create and manage App Registrations.

### Step 1: Clone the Repository

```bash
git clone <your-repository-url>
cd <your-repository-directory>
```

### Step 2: Create and Activate Virtual Environment

It is critical to use a virtual environment to isolate project dependencies.

1.  **Create the environment:**
    ```bash
    python -m venv .venv
    ```

2.  **Activate the environment:**
    -   On **Windows** (PowerShell/CMD):
        ```bash
        .\.venv\Scripts\activate
        ```
    -   On **Linux / macOS**:
        ```bash
        source .venv/bin/activate
        ```
    Your command prompt should now be prefixed with `(.venv)`.

### Step 3: Install Python Dependencies

With the virtual environment active, install the required libraries from `requirements.txt`.

```bash
pip install -r requirements.txt
```

### Step 4: Azure App Registration

This bot requires access to a mailbox via the Microsoft Graph API. This is the most critical part of the setup.

1.  Go to the [Azure Portal](https://portal.azure.com/) and navigate to **Azure Active Directory** > **App registrations**.
2.  Click **New registration**.
3.  Give it a name (e.g., "UllaSupportBot").
4.  Under "Supported account types," select "Accounts in this organizational directory only."
5.  Click **Register**.
6.  **Save the following values** from the "Overview" page for your `.env` file:
    -   `Application (client) ID`
    -   `Directory (tenant) ID`
7.  Go to **Certificates & secrets** > **New client secret**.
8.  Add a description and set an expiry.
9.  **Immediately copy the `Value` of the new secret.** This is your only chance to see it.
10. Go to **API permissions** > **Add a permission**.
11. Select **Microsoft Graph**.
12. Select **Application permissions** (NOT Delegated permissions).
13. Add the following permissions:
    -   `Mail.ReadWrite`
    -   `Mail.Send`
14. Click **Add permissions**.
15. **Crucially**, grant admin consent by clicking the **Grant admin consent for [Your Tenant]** button and confirming. The status for the permissions must change to "Granted".

### Step 5: Configure Environment Variables

1.  Create a file named `.env` in the root of the project directory.
2.  Copy the following template into it and fill it out with your credentials and configuration.

```dotenv
# --- Azure AD App Registration Credentials ---
AZURE_CLIENT_ID="<Your-Application-Client-ID-from-Azure>"
AZURE_TENANT_ID="<Your-Directory-Tenant-ID-from-Azure>"
AZURE_CLIENT_SECRET="<Your-Client-Secret-Value-from-Azure>"

# --- Target Mailbox ---
# The email address of the M365 account the bot will use to send and receive mail.
# The Azure App must have permissions over this mailbox.
BOT_EMAIL_ADDRESS="ulla.bot@yourdomain.com"

# --- LLM Model Configuration ---
# Models must be available in your Ollama instance. Use the exact tag you have pulled.
PERSONA_MODEL="gemma3:12b-it-qat"
EVAL_MODEL="gemma3:12b-it-qat"

# --- Ollama Host (Optional) ---
# Uncomment and set if Ollama is running on a different machine.
# OLLAMA_HOST="http://192.168.1.100:11434"
```

## Usage

### Running the Bot

Ensure your virtual environment is active (`(.venv)` is visible in your terminal). Then, run the script:

```bash
python MailResponder.py
```

The script will start polling the configured mailbox for unread emails and process them accordingly.

### Utility Commands

-   **Print Database Contents:**
    ```bash
    python MailResponder.py --printdb
    ```

-   **Empty the Inbox:** Deletes **ALL** emails from the bot's inbox. Use with caution.
    ```bash
    python MailResponder.py --emptyinbox
    ```

## Project Structure

```
.
├── MailResponder.py          # Main application script, contains all core logic.
├── prompts.py                # Contains all LLM system prompts and the problem catalogues.
├── conversations.db          # SQLite database for tracking student progress.
├── .env                      # Holds all secrets and configuration variables (MUST be ignored by git).
└── requirements.txt          # List of Python dependencies.
```

## Configuration and Extension

The core of the simulation's content resides in `prompts.py`. To extend the training:

-   **Add New Problems:** Add new problem dictionaries to the `PROBLEM_CATALOGUES` list. Follow the existing structure.
-   **Add New Levels:** Add a new `START_PHRASES` entry and a corresponding list of problems in `PROBLEM_CATALOGUES`.
-   **Change Persona:** Modify the `ULLA_PERSONA_PROMPT` or `EVALUATOR_SYSTEM_PROMPT` to alter the behavior of the AIs.