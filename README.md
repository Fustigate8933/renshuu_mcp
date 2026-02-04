## Renshuu MCP
#### Renshuu MCP is a custom MCP server designed to allow LLMs to call the Renshuu API on your behalf, performing actions such as searching the Renshuu dictionary, adding a word to your list, giving your sample sentences of words from your list, etc.

## Usage with Open WebUI:
1. `pip install -r requirements.txt` in your virtual env (or global if you want)
2. configure your environment variables by filling in your Renshuu keys and renaming the env file to .env
3. `export $(grep -v '^#' .env | xargs)` or however you want to set the environment variables
4. `python run_openapi_server.py`
5. start your Open WebUI server however you want (docker, install through pip and run, etc.)
6. go to admin panel > settings > external tools
7. add a new tool server with the following configuration
   <img width="623" height="317" alt="image" src="https://github.com/user-attachments/assets/fa5a2709-ea23-4c2e-9f16-0a57aefc7ebe" />
8. enable tool
9. set system prompt to encourage LLM to call the tool. a sample system prompt is available in the file `system_prompt.txt`
10. Enjoy
