# 🤖 MOSDAC AI Help Bot (LangChain + Graphiti + Neo4j)

Conversational AI system to answer queries related to ISRO's MOSDAC platform using scraped data, knowledge graph modeling (Graphiti + Neo4j), and a smart agent interface built with Pydantic AI.

<p align="center">
  <a href="https://github.com/TechFreak2003/mosdac-ai-helpbot/issues"><img src="https://img.shields.io/github/issues/TechFreak2003/mosdac-ai-helpbot"></a>
  <a href="https://github.com/TechFreak2003/mosdac-ai-helpbot/stargazers"><img src="https://img.shields.io/github/stars/TechFreak2003/mosdac-ai-helpbot"></a>
  <a href="https://github.com/TechFreak2003/mosdac-ai-helpbot/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-blue.svg">
  </a>
</p>

<p align="center">
  <a href="#-features">Features</a> |
  <a href="#%EF%B8%8F-tech-stack">Tech Stack</a> |
  <a href="#-installation">Installation</a> |
  <a href="#-project-structure">Project Structure</a> |
  <a href="#-contributing">Contributing</a> |
  <a href="#%EF%B8%8F-author">Author</a>
</p>

## 🌟 Features

* 🔄 Scrapes data from [mosdac.gov.in](https://mosdac.gov.in) including:

  * Satellite Missions
  * Product Metadata
  * Open Data Datasets
  * Documents (PDF links)
  * Mission Metadata
  * FAQs
* 🧠 Knowledge graph creation with temporal facts using Graphiti + Neo4j
* 💬 Interactive AI agent (Pydantic AI) to answer questions using knowledge graph
* ✅ Time-aware responses with rich source provenance
* 📁 Modular microservices-based scrapers

## 🛠️ Tech Stack

* **Language**: Python 3.10+
* **Backend AI**: Pydantic AI (OpenAI/GPT wrapper)
* **Graph DB**: Neo4j (via Graphiti)
* **Data Scraping**: Selenium, BeautifulSoup
* **Environment Config**: python-dotenv
* **Visualization (optional)**: rich, matplotlib

## 🚀 Installation

### Prerequisites

* Python 3.10+
* Neo4j Desktop (or Aura Cloud instance)
* OpenAI API key

### Steps

```bash
# Clone the repository
https://github.com/TechFreak2003/mosdac-ai-helpbot.git
cd mosdac-ai-helpbot

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env  # Add your OPENAI_API_KEY and NEO4J creds

# Run data scraping scripts
python Scrapper/satellite_scraper.py
python Scrapper/products_scraper.py
python Scrapper/faq_scraper.py
...

# Load data into Neo4j
python ML_microservices/mosdac_graph_loader.py

# Launch the conversational agent
python ML_microservices/agent.py
```

## 📁 Project Structure

```
mosdac-ai-helpbot/
├── Scrapper/                      # Data collection modules
│   ├── satellite_scraper.py
│   ├── product_scraper.py
│   └── faq_scraper.py
│   └── ...
│
├── data/                         # Scraped JSON data
│   ├── satellites.json
│   ├── products.json
│   └── faqs.json
│
├── ML_microservices/             # Core loading + AI agent
│   ├── mosdac_graph_loader.py
│   └── agent.py
│
├── requirements.txt              # Dependencies
├── .env                          # Env variables (not committed)
├── LICENSE
└── README.md
```

## 📈 Results

The bot is capable of answering:

* What is INSAT-3DR?
* Which documents are linked to Megha-Tropiques?
* When was Oceansat-3 launched?
* Where can I download data for rainfall from SAPHIR?

All answers include source citations, timestamps, and optionally links to documents or datasets.

## 👥 Contributing

Contributions are welcome! Please check [issues](https://github.com/TechFreak2003/mosdac-ai-helpbot/issues) and submit PRs to:

* Improve scraping coverage
* Extend agent capabilities
* Add streamlit frontend

### To contribute:

1. Fork the repo
2. Create a new branch (`git checkout -b feature-name`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push and open a Pull Request

## 👨‍💻 Contributors

| Avatar                                                                        | Name          | GitHub                                            | Role    | Contributions                       |
| ----------------------------------------------------------------------------- | ------------- | ------------------------------------------------- | ------- | ----------------------------------- |
| <img src="https://github.com/TechFreak2003.png" width="50px" height="50px" /> | Suvrodeep Das | [TechFreak2003](https://github.com/TechFreak2003) | Creator | Scraping, Graph Loader, Agent, Docs |

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 🙋‍♂️ Author

Created with 💙 by [Suvrodeep Das](https://suvrodeepdas.dev)
