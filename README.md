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

This section describes the configuration settings for the AskThemAll application. The configuration is structured using
TOML format and **must be stored in a file named `config.toml` located in the `.askthemall` directory.**

### General Structure

The configuration is divided into several sections: `opensearch`, `google`, `groq`, and `chat_bots`. Each section
contains settings specific to that service or feature.

### Sections

#### `[opensearch]`

This section defines the connection parameters for the OpenSearch instance used by AskThemAll.

* **`host` (string, required):**  The hostname or IP address of the OpenSearch server.
    * **Example:** `"localhost"`
* **`port` (integer, required):** The port number on which the OpenSearch server is listening.
    * **Example:** `9200`
* **`index_prefix` (string, optional):** A prefix to be added to all OpenSearch index names created by AskThemAll. This
  is useful for organizing indices within your OpenSearch cluster. If not specified, the default is `askthemall_`'.
    * **Example:** `"askthemall_dev_"`

#### `[google]`

This section contains the API key required to access Gemini AI services.

* **`api_key` (string, required):** Your API key. This key is used for authenticating requests to Gemini AI services.

#### `[groq]`

This section contains the API key required to access Groq services.

* **`api_key` (string, required):** Your Groq API key. This key is used for authenticating requests to the Groq
  services.

#### `[chat_bots]`

This section defines the configuration for different chatbots that AskThemAll can use. Each chatbot is defined as a
subsection within `[chat_bots]`. The name of the subsection acts as a unique identifier for that bot.

* **`[chat_bots."<bot_id>"]` (subsection, required):** A section defining the configuration for a specific chatbot.
  `<bot_id>` is a unique identifier for this bot.

    * **`name` (string, required):**  A human-readable name for the chatbot. This name will be displayed in the
      application.
        * **Example:** `"Gemini 2.0"`
    * **`client.type` (string, required):**  The type of client to use for this chatbot. This determines which API
      provider to use. Valid values are `"google"` and `"groq"` (and potentially others).
        * **Example:** `"google"`
    * **`client.model_name` (string, required):** The specific model name to use for the chatbot with the chosen
      client. This value depends on the selected client type. Refer to the documentation for the specific API provider
      for available models.
        * **Example:** `"gemini-2.0-flash-exp"`

##### Example Chatbot Configurations:

* **`[chat_bots."gemini-2.0-flash-exp"]`:**  Configuration for the Gemini 2.0 Flash experimental model via the Google
  API.

  ```toml
  [chat_bots."gemini-2.0-flash-exp"]
  name = "Gemini 2.0"
  client.type = "google"
  client.model_name = "gemini-2.0-flash-exp"
  ```

* **`[chat_bots.groq-mixtral-8x7b-32768]`:** Configuration for the Mistral 8x7b model via the Groq API.

  ```toml
  [chat_bots.groq-mixtral-8x7b-32768]
  name = "Mistral"
  client.type = "groq"
  client.model_name = "mixtral-8x7b-32768"
  ```

### Important Notes

* **The settings described in this document must be saved in a file named `config.toml` and placed in the `.askthemall`
  directory in your user's home directory.**
* The `client.model_name` values are specific to the API provider. Ensure you are using valid model names as defined by
  Google, Groq, or any other provider you are using.
* The configuration file format is TOML. Ensure your configuration file adheres to the TOML syntax.
* Future versions of AskThemAll may include additional configuration options. Refer to the latest documentation for the
  most up-to-date information.

### Environment Variables

Create a `.env` file in the root directory and set the necessary environment variables. These variables can override
certain settings found in `config.toml`, particularly for sensitive information and connection details.

* Rename the template: Rename the `.env.example` file (included in the repository) to `.env`.
* Populate the variables: Edit the `.env` file and replace the placeholder values with your actual credentials.

Example `.env` file:

```
GOOGLE__API_KEY=xxx
GROQ__API_KEY=xxx

OPENSEARCH__HOST=localhost
OPENSEARCH__PORT=9200
OPENSEARCH__INDEX_PREFIX=askthemall_dev_
```

**Note:** The environment variables for the API keys and the OpenSearch settings (host, port, index prefix) take
precedence over any corresponding settings in the `config.toml` file. Chatbot enablement and naming are still configured
exclusively in the `config.toml` file.

## 📦 OpenSearch Setup

This application utilizes OpenSearch to store and retrieve chat history. To ensure proper functionality, you'll need to
configure OpenSearch.

**1. Installation & Setup:**

* Follow the official OpenSearch documentation to install and configure OpenSearch on your chosen platform (e.g.,
  Docker, AWS OpenSearch Service, local installation). Make sure you have a running OpenSearch cluster accessible from
  your application.
* You can find the documentation here: [https://opensearch.org/docs/latest/](https://opensearch.org/docs/latest/)
* **Example using Docker Compose:**

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
