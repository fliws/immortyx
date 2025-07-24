In total, the system features **five main logical data stores**, some of which can be implemented using hybrid approaches. The field lists are not final and could be expanded.

### 1. Publication Graph

*   **Database Type:** **Graph Database**
    *   *Examples: Neo4j, ArangoDB, Amazon Neptune.*

*   **Structure and Purpose:**
    This is the core of the system for analyzing citations and relationships. Data here is organized not in tables, but as nodes and edges.
    *   **Nodes:** Each node represents a unique entity. Key node types include:
        *   `Publication`: An article, preprint, or patent. Attributes: `ID`, `title`, `DOI`, `publication_date`, `source_type`.
        *   `Author`: A scientist or author. Attributes: `author_ID`, `name`, `affiliations`.
        *   `Source`: A journal or other publication venue. Attributes: `name`, `impact_factor`.
        *   `Keyword`: A keyword or topic. Attributes: `term`.
    *   **Edges (Relationships):** Edges define the relationships between nodes.
        *   `(Publication A) -[:CITES]-> (Publication B)`: The key relationship for citation analysis.
        *   `(Author) -[:WROTE]-> (Publication)`: Connects an author to their work.
        *   `(Publication) -[:PUBLISHED_IN]-> (Journal)`: Defines where a work was published.
        *   `(Publication) -[:HAS_KEYWORD]-> (Keyword)`: A thematic link.

*   **Why a Graph Database?**
    Graph databases are optimized for executing queries that traverse relationships. Tasks like "Find all authors who cited work X and are referenced by author Y" or "Find the most influential works in field Z" are solved orders of magnitude faster in a graph DB than in a relational one.

### 2. Knowledge Base

*   **Database Type:** **Hybrid: Vector DB + Document DB**
    *   *Examples: Pinecone, Weaviate, Milvus (for vectors) + MongoDB, Elasticsearch (for documents and search).*

*   **Structure and Purpose:**
    This is the main repository for extracted information: ideas, facts, methodologies. Semantic search is critically important here.

    1.  **Vector Database Component:**
        *   **What it stores:** Vector representations (embeddings) of text fragments. The "Entity Parser" and other agents break down each article into meaningful "chunks" (e.g., "main hypothesis," "method description," "key conclusion"). Each chunk is converted into a vector and stored.
        *   **Why:** This enables semantic search, not just keyword search. A query for "rejuvenation methods using parabiosis" will find documents that use synonyms or describe the same concept in different words, even if the exact keywords are missing. This is the foundation for most analytical agents.

    2.  **Document/Search Database Component:**
        *   **What it stores:** The text chunks themselves and their structured metadata. Each document can have a JSON structure:
            ```json
            {
              "chunk_id": "pub123_chunk_4",
              "source_publication_id": "pub123",
              "text": "The study found that plasma exchange led to a decrease in inflammatory markers...",
              "vector_id": "vec_xyz789",
              "type": "conclusion",
              "entities": ["plasma exchange", "inflammatory markers"],
              "trust_score": 0.85
            }
            ```
        *   **Why:** To store the full information and allow for filtering based on metadata (e.g., "find all conclusions from articles with a trust score > 0.8").

*   **How does this relate to Graph RAG (Graph Retrieval-Augmented Generation)?**
    Your mention of **Graph RAG** fits perfectly into this concept. It's an advanced approach where:
    1.  A user's query is first used to find relevant nodes in the **Publication Graph** (e.g., find a cluster of articles on a topic).
    2.  The IDs of the text chunks associated with these found publications are then extracted.
    3.  These chunks (or their vector representations) are searched for in the **Knowledge Base (Vector DB)** to find the most semantically similar fragments.
    4.  This rich, structurally and semantically relevant context is then fed to the LLM (the "Butler") to generate an answer. This is far more powerful than a simple vector search.

### 3. Author Database

*   **Database Type:** **Document Database** or **Relational Database**
    *   *Examples: MongoDB, PostgreSQL.*

*   **Structure and Purpose:**
    This stores structured information about each scientist. Data integrity and the ability to build complex profiles are important here. A document model is a very good fit, as a scientist's profile is essentially one complex document.
    ```json
    {
      "author_id": "auth_456",
      "name": "David Sinclair",
      "orcid": "0000-0002-1234-5678",
      "affiliations": ["Harvard Medical School"],
      "publication_ids": ["pub101", "pub123", "pub256"],
      "research_interests": ["epigenetics", "NAD+", "sirtuins"],
      "summary_views": "Focuses on epigenetic information theory of aging..."
    }
    ```
*   **Why not a Graph Database?**
    Although authors exist in the graph, it's more convenient to store their detailed profiles separately. Queries like "show me the full profile of author X" will be more efficient in a document or relational DB.

### 4. Negative Knowledge Base

*   **Database Type:** **Key-Value Store** or **Document Database**
    *   *Examples: Redis, MongoDB.*

*   **Structure and Purpose:**
    This is the repository for agent "James Randy." It needs a fast way to check for red flags.
    *   **What it stores:** Patterns of pseudoscience, lists of retracted articles, names of scientists with poor reputations, questionable journals. The structure can be simple: a key (e.g., `retracted_doi:10.1234/journal.123`) and a value (`true` or a description of the reason).

*   **Why this type?**
    The speed of key-based lookups is more important here than complex relationships.

### 5. Consensus Base

*   **Database Type:** **Hybrid: Document DB + Vector DB**
    *   *Examples: MongoDB Atlas (which has built-in vector search).*

*   **Structure and Purpose:**
    This is a concentrated summary of knowledge, the "short-term memory" for the "Butler" agent. It needs to be both structured and accessible for semantic search.
    *   **Document Database Component:** Stores JSON documents that are the answers to the Orchestrator's canonical questions.
        ```json
        {
          "topic": "Key Senolytic Agents",
          "consensus_summary": "The most studied senolytics are Dasatinib + Quercetin (D+Q), Fisetin, and Navitoclax...",
          "key_papers": ["pub_dq_1", "pub_fisetin_1"],
          "level_of_evidence": "Preclinical strong, Human preliminary",
          "last_updated": "2025-07-24"
        }
        ```
    *   **Vector Database Component:** Each `consensus_summary` is vectorized. This allows the "Butler" to instantly find the most relevant section of the Consensus Base to answer a user's query, even if the phrasing doesn't match the `topic`.

### Summary: Database Architecture

| # | Database Name             | Recommended Type                           | Primary Purpose                                                                  |
|---|---------------------------|--------------------------------------------|----------------------------------------------------------------------------------|
| 1 | **Publication Graph**     | **Graph DB** (Neo4j, ArangoDB)             | Citation analysis, finding relationships between authors/works, foundation for Graph RAG. |
| 2 | **Knowledge Base**        | **Hybrid: Vector + Document** (Pinecone + MongoDB) | Storing and semantically searching for ideas, facts, and conclusions from sources. |
| 3 | **Author Database**       | **Document DB** (MongoDB)                  | Storing complete, structured profiles of researchers.                            |
| 4 | **Negative Knowledge Base**| **Key-Value** or **Document DB** (Redis)   | Quickly checking for signs of pseudoscience and bad data.                         |
| 5 | **Consensus Base**        | **Hybrid: Document + Vector** (MongoDB Atlas) | Storing consensus knowledge for the "Butler's" fast and accurate responses.     |