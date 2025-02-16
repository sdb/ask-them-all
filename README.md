# 🗣️💬 AskThemAll

This Python application provides a user-friendly interface for chatting with various Large Language Models (LLMs) and
storing the conversation history in a database. Built using Streamlit, this app allows users to easily switch between
different LLMs, manage their chat history, and revisit past conversations.

## ✨ Features

* **Chat with Multiple LLMs:** Seamlessly switch between different Large Language Models (LLMs) such as Google's
  Gemini and models supported by Groq.
* **Conversation History with OpenSearch:** Leverage OpenSearch to persistently store and manage your chat history.
* **Streamlit UI:** Enjoy a clean and intuitive user interface powered by Streamlit for effortless interaction.
* **Conversation Management:** View, delete, and revisit past conversations. Search within past conversations to
  quickly find specific information.
* **Markdown Rendering:** LLM responses are formatted using Markdown, enabling enhanced readability with code
  highlighting, bullet points, and structured text.

## 🛠️ Technologies Used

* **Python:** Primary programming language.
* **Streamlit:** UI framework for building the user interface.
* **Google Generative AI Python Library:** For interacting with Google's Gemini API.
* **Groq Python Library:** For interacting with the Groq API.
* **opensearch-py:** For database interaction with OpenSearch.
* **Docker:** For running the application in a containerized environment.

## ⬇️ Installation

This project uses [Poetry](https://python-poetry.org/) for dependency management. If you don't have Poetry installed,
you can install it following the instructions on the [Poetry website](https://python-poetry.org/docs/#installation).

1. **Clone the repository:**

   ```bash
   git clone https://github.com/sdb/ask-them-all.git
   cd ask-them-all
   ```

2. **Install dependencies:**

   ```bash
    poetry install
    ```

## ⚙️ Configuration

1. **Environment Variables:**

   Create a `.env` file in the root directory and set the necessary environment variables.

    1. **Rename the template:** Rename the `.env.example` file (included in the repository) to `.env`.
    2. **Populate the variables:** Edit the `.env` file and replace the placeholder values with your actual credentials.

   Example `.env` file:

    ```
    GOOGLE__API_KEY=xxx
    GROQ__API_KEY=xxx

    OPENSEARCH__HOST=localhost
    OPENSEARCH__PORT=9200

    GEMINI_2_0_FLASH_EXP__ENABLED=true
    GEMINI_2_0_FLASH_EXP__NAME=Gemini 2.0

    GROQ_MIXTRAL_8X7B_32768__ENABLED=true
    GROQ_MIXTRAL_8X7B_32768__NAME=Groq Mixtral
    ```

2. **Database Setup:**

   The application uses OpenSearch to store chat history. See the [🔍 OpenSearch Setup](#opensearch-setup) section below
   for more details.

### OpenSearch Setup

This application utilizes OpenSearch to store and retrieve chat history. To ensure proper functionality, you'll need to
configure OpenSearch.

**1. Installation & Setup:**

* Follow the official OpenSearch documentation to install and configure OpenSearch on your chosen platform (e.g.,
  Docker, AWS OpenSearch Service, local installation). Make sure you have a running OpenSearch cluster accessible from
  your application.
* You can find the documentation here: [https://opensearch.org/docs/latest/](https://opensearch.org/docs/latest/)
* **Example using Docker Compose (for local testing):**

  Create a file named `compose.yaml` with the following content:

  ```yaml
  services:
    opensearch:
      image: opensearchproject/opensearch:latest  # Or specify a specific version
      ports:
        - "9200:9200"
        - "9600:9600"
      environment:
        - "discovery.type=single-node"
        - "plugins.security.disabled=true"  #  DISABLES SECURITY - FOR TESTING ONLY
      volumes:
        - opensearch:/usr/share/opensearch/data
  volumes:
    opensearch:
      external: true
  ```

  Then, run: `docker-compose up -d`

  This will start a basic OpenSearch instance.

**2. Configuration:**

* **Connection Details:** These can be set using environment variables (see the "Configuration" section above). The
  default port for OpenSearch is 9200.

* **Indices:** Indices will be automatically created when the application starts.

* **CRITICAL: Authentication is currently *not* fully supported. 🚨** This application *primarily* assumes your
  OpenSearch instance is accessible *without* authentication.

## ▶️ Running the Application

1. **Navigate to the project directory:**

   ```bash
   cd ask-them-all
   ```

2. **Activate the virtual environment:**

   While Poetry manages the virtual environment automatically when running commands with `poetry run`, you might want to
   activate it explicitly.

    ```bash
    eval $(poetry env activate)
    ```

   To deactivate the virtual environment, simply type `deactivate`.

3. **Run the Streamlit app:**

   ```bash
   streamlit run main.py
   ```

4. **🌐 Open the app in your browser:**

   Streamlit will provide a URL (usually `http://localhost:8501`) that you can open in your web browser.

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## 📝 License

This project is licensed under the [MIT License](LICENSE).
