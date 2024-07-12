# LLM Release Explorer

This Streamlit app visualizes and explores the release dates of various Large Language Models (LLMs) from different organizations.

## Features

- Monthly graph of LLM releases
- Exploration of models by company
- Exploration of models by release month
- Option to view raw data

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/llm-release-explorer.git
   cd llm-release-explorer
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Prepare the data file:
   - Create a file named `models.json` in the same directory as `app.py`.
   - The `models.json` file should contain an array of objects, each representing a model with "Model", "Organization", and "Release Date" fields.
   - Example format:
     ```json
     [
       {
         "Model": "GPT-4",
         "Organization": "OpenAI",
         "Release Date": "2023-03-14"
       },
       ...
     ]
     ```

## Usage

Run the Streamlit app with:

```
streamlit run app.py
```

The app will open in your default web browser.

## Data

The app uses a JSON file (`models.json`) containing information about various LLMs, including their names, organizations, and release dates. Make sure to keep this data up to date for the most accurate visualizations.

## Contributing

Contributions to improve the app or update the LLM data are welcome. Please feel free to submit a pull request or open an issue.

## License

This project is open source and available under the [MIT License](LICENSE).