# Agent-by-Agent Description of the Multi-Agent System

---

### **Contour 1: Information Gathering, Processing, and Validation**

*These agents work continuously in the background to build the system's knowledge foundation.*

#### **1. Spider Orchestrator**
*   **Analogy:** Head of the Data Collection Department.
*   **Mission:** To manage the continuous and efficient collection of raw information from all specified sources.
*   **Tasks:**
    *   **Planning:** Determines which sources to query and how often, based on their type (e.g., Twitter is queried more frequently than annual reports).
    *   **Job Creation:** Creates specific tasks for the Parsers, indicating the URL, API endpoint, and keywords for the search.
    *   **Duplicate Prevention:** Checks against the *Publication Graph* before dispatching a job to avoid re-downloading already processed materials.
    *   **Routing:** Upon receiving raw data from a Parser, it forwards the data down the pipeline to the Entity Parser.
*   **Interactions:**
    *   **Issues commands to:** Parsers.
    *   **Receives information from:** The Parser Builder (about new sources/keywords) and consults the *Publication Graph*.

#### **2. Parsers (A set of agents)**
*   **Analogy:** Field operatives.
*   **Mission:** To extract raw information from one specific source.
*   **Tasks:**
    *   **Connection:** Interacts with a source's API (e.g., PubMed E-utilities, Twitter API) or performs web scraping if an API is unavailable.
    *   **Extraction:** Retrieves data (article text, JSON response, HTML page) according to the job assigned by the Spider Orchestrator.
    *   **Transmission:** Returns the fetched raw data to the Spider Orchestrator.
*   **Interactions:**
    *   **Receives commands from:** The Spider Orchestrator.
    *   **Interacts with:** External data sources.

#### **3. Parser Builder**
*   **Analogy:** Scout or Development Agent.
*   **Mission:** To ensure the system's list of sources and search queries remains current and comprehensive.
*   **Tasks:**
    *   **New Source Discovery:** Scans the internet in the background for new relevant blogs, databases, and journals in the longevity space.
    *   **New Keyword Discovery:** Analyzes trends in publications to identify new terms (e.g., the name of a new technology) that should be added to search queries.
    *   **Proposal Generation:** Suggests found sources and keywords to the system administrator for approval.
*   **Interactions:**
    *   **Provides recommendations to:** The system administrator and the Spider Orchestrator.

#### **4. Entity Parser**
*   **Analogy:** Library Cataloger.
*   **Mission:** To transform unstructured text into structured, machine-readable data.
*   **Tasks:**
    *   **Named Entity Recognition (NER):** Finds and classifies mentions of genes, proteins, companies, drugs, methods, and scientists' names within the text.
    *   **Fact Extraction:** Identifies the key hypothesis, main conclusions, methods used, and sample sizes.
    *   **Summarization:** Creates a concise summary of the material.
*   **Interactions:**
    *   **Receives data from:** The Spider Orchestrator.
    *   **Transmits data:** A structured object with all extracted entities is passed to the next validation stage.

#### **5. Link Classifier**
*   **Analogy:** Bibliographer.
*   **Mission:** To build a map of the connections between scientific works.
*   **Tasks:**
    *   **Bibliography Analysis:** Finds the reference list in a publication and parses it, extracting links to other works.
    *   **Graph Edge Creation:** Creates "cites / is cited by" relationships between nodes in the *Publication Graph*.
*   **Interactions:**
    *   **Receives data:** The publication text from the Entity Parser.
    *   **Writes data to:** The *Publication Graph* database.

#### **6. Author Detector**
*   **Analogy:** Archival service or identity detective.
*   **Mission:** To uniquely identify each author and link them to a single, unified profile.
*   **Tasks:**
    *   **Identification:** Extracts author names and their affiliations from the publication.
    *   **Disambiguation:** Compares the name and affiliation against existing profiles in the *Author Database* to distinguish, for example, Michael S. Brown from Michael J. Brown.
    *   **Profile Update:** Links the publication to an existing author profile or creates a new one if the author is encountered for the first time.
*   **Interactions:**
    *   **Reads from and writes to:** The *Author Database*.

#### **7. Fuzzy Estimator**
*   **Analogy:** Club Bouncer / Face Control.
*   **Mission:** To perform a quick, initial assessment of the information's reliability based on its origin.
*   **Tasks:**
    *   **Source Evaluation:** Assigns a preliminary trust score based on the source's category (e.g., a publication in *Nature* gets a high score, while a Reddit post gets a low one).
    *   **Filtering:** Materials with an extremely low score (blatant spam, off-topic content) can be immediately discarded.
*   **Interactions:**
    *   **Receives:** A structured object from the Entity Parser.
    *   **Transmits:** The same object, but with an added trust score tag, to Agent "James Randy".

#### **8. Randy Collector & Agent "James Randy"**
*   **Analogy:** Internal Control and Audit Department.
*   **Mission:** To identify signs of pseudoscience and methodological flaws in the content.
*   **Tasks of the "Randy Collector":**
    *   Purposefully gathers information on retracted articles, scientific debunking, and known cases of academic fraud.
    *   Populates the *Negative Knowledge Base* with patterns and examples of bad science.
*   **Tasks of Agent "James Randy":**
    *   Compares the content of an incoming material against the patterns from the *Negative Knowledge Base*.
    *   Looks for logical fallacies, lack of control groups, extremely small sample sizes, and unsubstantiated generalizations.
    *   Issues a verdict: the material either proceeds, or it receives a "red flag" and is either discarded or saved with a corresponding warning label.
*   **Interactions:**
    *   **"Randy Collector" writes to:** The *Negative Knowledge Base*.
    *   **Agent "James Randy" reads from:** The *Negative Knowledge Base* and gives the final "go/no-go" for writing to the main databases.

---

### **Contour 2: Knowledge Synthesis and Updating**

*These agents don't just collect information; they comprehend it, creating a high-level overview of the subject area.*

#### **9. Agent "Thomas Kuhn"**
*   **Analogy:** Historian of science, identifying revolutions.
*   **Mission:** To detect potentially groundbreaking, "revolutionary" ideas capable of shifting the scientific paradigm.
*   **Tasks:**
    *   Analyzes the stream of new, already-validated information (the "Daily chunk").
    *   Assesses how much a new idea contradicts or significantly adds to the established knowledge in the *Consensus Base*.
    *   If a fundamentally new or strongly contradictory piece of information is found, it sends a signal to the Main Orchestrator about the need to revise the *Consensus Base*.
*   **Interactions:**
    *   **Reads from:** The *Knowledge Base* and the *Consensus Base*.
    *   **Sends a signal to:** The Main Orchestrator.

#### **10. Main Orchestrator**
*   **Analogy:** Editor-in-Chief of a scientific almanac.
*   **Mission:** To create and maintain the *Consensus Base*—a concentrated summary of the most critical knowledge.
*   **Tasks:**
    *   **Question Formulation:** Maintains and slowly updates a JSON file with key questions (e.g., "What are the main approaches to rejuvenation?", "Who are the key players in the market?").
    *   **Delegation:** Sends these questions to its "team" of five analyst agents.
    *   **Synthesis:** Gathers the answers from the team and, using a consensus mechanism, forms or updates the entries in the *Consensus Base*.
    *   **Signal Reaction:** Initiates an unscheduled update based on a signal from "Thomas Kuhn" or from the analysis of user queries.
*   **Interactions:**
    *   **Issues commands to:** Its team of 5 agents.
    *   **Writes to:** The *Consensus Base*.
    *   **Receives signals from:** "Thomas Kuhn" and the user query analysis module.

#### **11. The Orchestrator's Team (5 Analyst Agents)**
*   **Analogy:** A team of columnists with different perspectives.
*   **Mission:** To search the main *Knowledge Base* for answers to the Orchestrator's questions, each with its unique style.
*   **The Agents:**
    *   **The Actualizer:** Seeks the most recent data on the topic.
    *   **The Wildcard ("Bez bashni"):** Finds the most audacious and unorthodox hypotheses.
    *   **Rising Star:** Looks for works by promising but lesser-known scientists.
    *   **The Pragmatist:** Relies on the most proven facts and large-scale studies.
    *   **The Maximalist:** Searches for ideas with the greatest potential impact on life extension.
*   **Interactions:**
    *   **Receive a job from:** The Main Orchestrator.
    *   **Read from:** The *Knowledge Base*, *Publication Graph*, and *Author Database*.
    *   **Send a response to:** The Main Orchestrator.

---

### **Contour 3: In-depth Analysis and Debates**

*This contour is activated on-demand to resolve complex, ambiguous tasks.*

#### **12. Digital Twin Constructor**
*   **Analogy:** Stage director or profiler.
*   **Mission:** To create digital personas of real scientists to participate in debates.
*   **Tasks:**
    *   On request (e.g., from the Debate Organizer), selects a scientist from the *Author Database*.
    *   Analyzes all their publications, argumentation style, key ideas, and viewpoints.
    *   Generates a prompt or a behavioral model for an LLM that will play the role of this "digital twin."
*   **Interactions:**
    *   **Reads from:** The *Author Database* and the *Knowledge Base*.
    *   **Creates:** "Digital twins".

#### **13. Debate Organizer & Arbiter**
*   **Analogy:** Talk show host and judge.
*   **Mission:** To conduct a structured discussion between opposing viewpoints and issue a verdict.
*   **Tasks of the "Organizer":**
    *   Formulates the debate topic (e.g., "The efficacy of metformin for longevity").
    *   Selects "digital twins" with opposing views.
    *   Moderates the discussion, forcing the agents to cite facts and publications.
*   **Tasks of the "Arbiter":**
    *   Analyzes the flow of the debate.
    *   Evaluates the strength of each side's arguments.
    *   Issues a final decision, which is then passed to the user.
*   **Interactions:**
    *   **Receive a request from:** The "Butler" agent.
    *   **Manage:** The "Digital twins".
    *   **Send the result to:** The "Butler" agent.

---

### **Contour 4: User Interaction**

*This is the "face" of the system that the end-user communicates with.*

#### **14. Agent "Butler"**
*   **Analogy:** A personal concierge or a highly qualified scientific consultant.
*   **Mission:** To serve as the single point of entry for the user, understand their request within the context of their role, and provide the most relevant and accurate answer.
*   **Tasks:**
    *   **Profile Identification:** The user's role (Researcher, Investor, etc.) is determined by a hard-coded UI choice (e.g., a button click), not an LLM interaction.
    *   **Query Analysis:** Understands the user's question, taking into account their pre-selected profile and the conversation history.
    *   **Quick Response:** First, it searches for an answer in the *Consensus Base*. If found, it provides the answer immediately.
    *   **Complex Query Delegation:** If no answer is found or the question requires deep analysis, it:
        *   Forms a search query for the main databases, **prioritizing sources according to the user's profile**.
        *   If necessary, initiates the "Debate Organizer".
    *   **Final Response Formulation:** Gathers the results from other agents and presents them to the user in a clear, well-structured format.
*   **Interactions:**
    *   **Communicates with:** The User.
    *   **Reads from:** The *Consensus Base* and all main databases.
    *   **Issues commands to:** The "Debate Organizer" and the search modules.