# Ulla - AI Support Training Bot

Ulla is an automated, AI-driven training bot designed to simulate realistic IT support conversations. It operates entirely over email, where it plays the role of "Ulla," a friendly but non-technical elderly Swedish woman experiencing various computer problems.

The system is built to help IT support students practice their diagnostic, communication, and problem-solving skills in a controlled environment. Students progress through 5 difficulty levels (L1-L5) with automatic unlocks based on successful problem solving.

## Features

-   **Email-Based Interaction:** Communicates using the Microsoft Graph API to send and receive real emails.
-   **Progressive Learning System:** 5 difficulty levels (L1-L5) with automatic progression based on successful problem solving.
-   **Swedish Localization:** Ulla persona responds in Swedish with accessibility-focused communication patterns.
-   **Multi-Database Architecture:**
    - **Progress Tracking:** SQLite database (`conversations.db`) tracks student progress and active conversations
    - **Conversation Archiving:** Completed conversations saved to separate archive database
    - **Debug Database:** Full AI conversation histories with evaluator responses for analysis
-   **Advanced Email Processing:**
    - Intelligent reply detection and conversation threading
    - Email content cleaning and HTML parsing
    - Race condition prevention with parallel processing
-   **Dual-LLM Architecture:**
    -   **Evaluator AI:** Strict logical model that determines if solutions correctly solve problems
    -   **Persona AI:** Creative model simulating Ulla's conversational responses
-   **Multi-User Support:** Handles multiple students simultaneously with conversation persistence.
-   **Race Condition Prevention:** Advanced concurrency management for reliable email processing.
-   **Conversation Management:** Intelligent reply detection and conversation state management.
-   **Analysis Tools:** Comprehensive debugging and conversation analysis capabilities.
-   **Highly Configurable:** Problems, personas, and difficulty levels easily customizable in `prompts.py`.
-   **Utility Commands:** CLI flags for database inspection, debugging, and inbox management.
-   **Test Suite:** Built-in testing utilities for system validation and troubleshooting.

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

Once a problem is successfully solved, the entire conversation transcript is saved to an archive database (`completed_conversations.db`), and the active problem is cleared for that student, allowing them to start a new one.

## Setup and Installation

### Prerequisites

-   Python 3.8+
-   An active [Ollama](https://ollama.com/) instance, running and accessible from where the script is hosted.
-   The LLM models specified in your `.env` file must be pulled in Ollama (e.g., `ollama pull gemma3:12b-it-qat`).
-   An Azure Active Directory (Azure AD) account with permissions to create and manage App Registrations.

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

Ensure your virtual environment is active (`(.venv)` is visible in your terminal).

#### Running in the Foreground
To run the bot and see live log output in your terminal, simply execute the script:
```bash
python MailResponder.py
```
This is recommended for testing and debugging. The script will stop if you close the terminal or press `Ctrl+C`.

#### Running in the Background (Linux/macOS)
For continuous operation on a Linux or macOS system, you can run the script as a background process using the `&` operator. This will free up your terminal for other commands.
```bash
python MailResponder.py &
```
**Note:** Be aware that if you close your terminal session, the background process may also be terminated. This method is suitable for short-term background execution where you plan to keep the session open.

### Utility Commands

-   **Print Database Contents:**
    Prints the contents of both the active and completed databases. You can optionally provide a student's email address to filter the output for just that user.
    ```bash
    # Print all data from all databases
    python MailResponder.py --printdb

    # Print data only for a specific student
    python MailResponder.py --printdb student@example.com
    ```

-   **Print Debug Database:**
    Prints the contents of the debug database including full evaluator AI responses. Useful for debugging evaluator behavior and analyzing conversation patterns.
    ```bash
    # Print all debug data
    python MailResponder.py --printdebugdb

    # Print debug data for a specific student
    python MailResponder.py --printdebugdb student@example.com

    # Print debug data for a specific problem
    python MailResponder.py --printdebugdb "" L1_P001
    ```

-   **Empty the Inbox:** Deletes **ALL** emails from the bot's inbox. Use with caution.
    ```bash
    python MailResponder.py --emptyinbox
    ```

## Project Structure

```
.
├── MailResponder.py          # Main application entry point and CLI interface
├── config.py                 # Configuration management for environment variables
├── database.py               # SQLite database operations and schema management
├── email_parser.py           # Advanced email parsing and reply detection
├── email_processor.py        # Main orchestration logic and email processing
├── response_generator.py     # AI-powered response generation with persona simulation
├── evaluator.py              # Problem evaluation and solution verification
├── conversation_manager.py   # Conversation flow and state management
├── graph_api.py              # Microsoft Graph API integration for email
├── llm_client.py             # LLM API client for Ollama integration
├── problem_catalog.py        # Problem catalogue management and validation
├── prompts.py                # LLM system prompts and problem definitions
├── test.py                   # Testing utilities and validation
├── conversations.db          # SQLite database for tracking student progress
├── completed_conversations.db  # Archive database for completed conversations
├── debug_conversations.db    # Debug database with full AI responses
├── example.env               # Environment configuration template
├── .env                      # Holds all secrets and configuration (git-ignored)
└── requirements.txt          # Python dependencies list
```

## Configuration and Extension

The system is designed for easy customization across multiple configuration files:

### `prompts.py`
The core of the simulation's content resides in this file. To extend the training:

-   **Add New Problems:** Add new problem dictionaries to the `PROBLEM_CATALOGUES` list. Follow the existing structure.
-   **Add New Levels:** Add a new `START_PHRASES` entry and a corresponding list of problems in `PROBLEM_CATALOGUES`.
-   **Change Persona:** Modify the `ULLA_PERSONA_PROMPT` or `EVALUATOR_SYSTEM_PROMPT` to alter the behavior of the AIs.

### `config.py`
Centralized configuration management:

-   **Database Settings:** Configure database paths and schemas
-   **API Integration:** Manage Microsoft Graph API and LLM API endpoints
-   **Environment Variables:** Load and validate configuration from `.env` file

### `problem_catalog.py`
Problem validation and management:

-   **Validate Problem Structure:** Ensure problems meet required format
-   **Manage Difficulty Levels:** Define level progression and unlocking criteria
-   **Problem Templates:** Standardize problem creation patterns

### Database Schema Customization
Modify database operations in `database.py` to:

-   Add new tracking metrics for student progress
-   Extend conversation history with additional metadata
-   Implement custom analysis queries for instructor insights