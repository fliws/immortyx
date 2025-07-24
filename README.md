# ImmortyX - Multi-Agent Longevity Research System

A sophisticated multi-agent system for collecting, processing, and synthesizing knowledge in the longevity and life extension research domain.

## System Overview

ImmortyX is designed as a multi-layered agent system that continuously monitors, processes, and synthesizes information from various scientific and commercial sources in the longevity space. The system serves different user types including researchers, students, journalists, investors, entrepreneurs, policy makers, philosophers, and writers.

## Architecture

### Contour 1: Information Gathering, Processing, and Validation

**Data Collection Layer:**
- `Spider Orchestrator` - Manages data collection scheduling and routing
- `Parsers` - Individual agents for each data source (PubMed, Twitter, etc.)
- `Parser Builder` - Discovers new sources and keywords

**Data Processing Layer:**
- `Entity Parser` - Extracts structured data from unstructured text
- `Link Classifier` - Builds citation networks between publications
- `Author Detector` - Maintains unified author profiles
- `Fuzzy Estimator` - Initial source reliability assessment
- `Randy Collector & Agent "James Randy"` - Pseudoscience detection

### Contour 2: Knowledge Synthesis and Updating

**Analysis Layer:**
- `Agent "Thomas Kuhn"` - Detects paradigm-shifting ideas
- Additional synthesis agents (to be implemented)

## Quick Start

### Prerequisites

```bash
pip install -r requirements.txt
```

### Running the System

1. **Start the Flask chatbot interface:**
```bash
python app.py
```

2. **Access the web interface:**
Open `http://localhost:5000` in your browser

3. **Initialize the system:**
```bash
python main.py
```

## Configuration

The system uses `longevity_config.json` for research themes and query templates. Key configuration includes:

- Research themes (longevity_genetics, aging_interventions, etc.)
- Query templates for each theme
- Source priorities and refresh intervals
- User profile preferences

## Data Sources

The system integrates with various data sources categorized by trust level:

**High Trust (APIs):**
- PubMed (E-utilities API)
- bioRxiv/medRxiv
- ClinicalTrials.gov
- arXiv

**Medium Trust (Web Scraping):**
- Nature Aging, Cell, GeroScience
- Longevity.Technology
- Fight Aging!

**Stub Sources (Paid/Limited):**
- Cochrane Library
- The Lancet Healthy Longevity
- Patent databases

## File Structure

```
immortyx/
├── README.md
├── requirements.txt
├── longevity_config.json
├── app.py                          # Flask chatbot interface
├── main.py                         # System initialization
├── agents/
│   ├── __init__.py
│   ├── spider_orchestrator.py      # Main coordination agent
│   ├── parser_builder.py           # Source discovery agent
│   ├── entity_parser.py            # NER and summarization
│   ├── link_classifier.py          # Citation network builder
│   ├── author_detector.py          # Author identification
│   ├── fuzzy_estimator.py          # Source reliability
│   ├── randy_collector.py          # Pseudoscience detection
│   └── thomas_kuhn.py              # Paradigm shift detection
├── parsers/
│   ├── __init__.py
│   ├── base_parser.py              # Abstract base class
│   ├── pubmed_parser.py            # PubMed E-utilities
│   ├── biorxiv_parser.py           # bioRxiv API
│   ├── medrxiv_parser.py           # medRxiv API
│   ├── arxiv_parser.py             # arXiv API
│   ├── clinicaltrials_parser.py    # ClinicalTrials.gov
│   ├── nature_parser.py            # Nature Aging (stub)
│   ├── cell_parser.py              # Cell journal (stub)
│   ├── cochrane_parser.py          # Cochrane Library (stub)
│   └── lancet_parser.py            # Lancet Healthy Longevity (stub)
├── databases/
│   ├── __init__.py
│   ├── publication_graph.py        # Citation network storage
│   ├── author_database.py          # Author profiles
│   ├── negative_knowledge_base.py  # Pseudoscience patterns
│   └── knowledge_synthesis.py      # Main knowledge base
├── utils/
│   ├── __init__.py
│   ├── llm_client.py              # OpenAI API client wrapper
│   ├── text_processing.py         # Text analysis utilities
│   └── config_loader.py           # Configuration management
├── data/
│   ├── sample_data/               # Mock data for paid sources
│   └── cache/                     # Cached API responses
└── tests/
    ├── __init__.py
    ├── test_parsers.py
    ├── test_agents.py
    └── test_integration.py
```

## User Profiles

The system adapts its behavior based on user profiles:

- **Researcher** - Latest methodologies, protocols, datasets
- **Student/Graduate** - Key papers, hot areas, fundamental concepts
- **Journalist** - Breakthroughs, expert opinions, human stories
- **Investor** - Company pipelines, clinical data, IP analysis
- **Entrepreneur** - Commercialization opportunities, market trends
- **Policy Maker** - Economic impact, social implications
- **Philosopher/Ethicist** - Existential and ethical implications
- **Writer/Screenwriter** - Story ideas, scientific accuracy

## API Integration

### LLM Server Configuration

The system uses a Llama server for natural language processing:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://80.209.242.40:8000/v1",
    api_key="dummy-key"
)
```

### Data Source APIs

- **PubMed E-utilities**: Free, comprehensive biomedical literature
- **bioRxiv/medRxiv**: Preprint servers with RSS feeds
- **ClinicalTrials.gov**: Clinical trial registry
- **arXiv**: Physics and quantitative biology papers

## Development

### Adding New Parsers

1. Create a new parser class inheriting from `BaseParser`
2. Implement required methods: `parse()`, `validate()`
3. Add configuration to `longevity_config.json`
4. Register with `SpiderOrchestrator`

### Adding New Agents

1. Create agent class in `agents/` directory
2. Implement agent-specific logic
3. Add to system initialization in `main.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes with tests
4. Submit a pull request

## License

See LICENSE file for details.

## Status

✅ **Beta Release** - Core functionality implemented and ready for testing.

### Current Status:
- ✅ Complete system architecture implemented
- ✅ Multi-parser system with real APIs and stub implementations
- ✅ Flask chatbot interface with user profiles
- ✅ Entity extraction and processing agents
- ✅ Pseudoscience detection (Randy Collector agent)
- ✅ SQLite-based knowledge synthesis database
- ✅ LLM integration with configurable server
- ✅ Comprehensive testing suite
- ✅ Sample data for paid sources
- ✅ Caching and rate limiting

### Quick Start:
1. **Run the demo**: `python demo.py`
2. **Start the chatbot**: `python app.py`
3. **Run full system**: `python main.py`

### Implemented Parsers:
- ✅ **PubMed** (E-utilities API) - Live data
- ✅ **bioRxiv** (API) - Live preprints
- ✅ **arXiv** (API) - Live physics/biology papers
- ✅ **ClinicalTrials.gov** (API) - Live clinical trials
- ✅ **Nature Aging** (Stub) - Sample data
- ✅ **Cochrane Library** (Stub) - Sample systematic reviews

### Implemented Agents:
- ✅ **Spider Orchestrator** - Coordinates data collection
- ✅ **Entity Parser** - Extracts named entities with LLM
- ✅ **Randy Collector** - Detects pseudoscience patterns

### Next Steps:
1. Add more specialized agents (Thomas Kuhn, Link Classifier)
2. Implement advanced knowledge graph features
3. Add real-time monitoring dashboard
4. Deploy to cloud infrastructure
5. Add more data sources and parsers
