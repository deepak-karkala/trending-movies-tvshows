# Project Requirements Document

##
### Section 3.1: Project Overview & Requirements Recap (Finalizing the Menu and Diner Experience)

Before laying out the technical infrastructure, we must ensure absolute clarity on *what* we're building and *for whom*. This section consolidates the decisions made in Chapter 1 and presents them as formal project documents.

*   **3.1.1 Presenting the Finalized Product Requirement Document (PRD)**
    The PRD serves as the single source of truth for what the "Trending Now" application will do. It details the project's purpose, features, users, and success criteria.

    **Product Requirement Document: "Trending Now" Movies/TV Shows App**

    1.  **Introduction & Purpose:**
        *   To create an application that provides users with up-to-date information on newly released movies and TV shows, featuring LLM-generated genre classifications, review summaries, vibe-based scores, and relevant tags.
        *   To serve as a comprehensive, educational MLOps project within this study guide.
    2.  **Target Audience:**
        *   End-Users: Movie/TV show enthusiasts looking for new content across multiple OTT platforms.
        *   Learners (of this guide): Individuals seeking to understand practical MLOps implementation.
    3.  **Core Features:**
        *   **Data Ingestion:** Regularly scrape/fetch new movie/TV show releases and user reviews from specified sources.
        *   **Genre Classification (Educational Model):** Train an XGBoost/BERT model to classify content genre based on plot/reviews. (This is primarily for demonstrating MLOps training pipelines).
        *   **LLM-Powered Content Enrichment (Production Inference Path):**
            *   Generate concise summaries of aggregated user reviews.
            *   Generate a "vibe score" (1-10) based on review sentiment and content.
            *   Generate descriptive "vibe tags" for intuitive content discovery.
            *   (Production Path) Classify genre using an LLM.
        *   **Homepage Visualization:** Interactive D3.js bubble chart displaying movies/shows.
            *   Bubbles sized by LLM-generated score.
            *   Default view: All recent shows, potentially loosely clustered by overall rating.
            *   Interactive Buttons:
                *   Group by OTT platform.
                *   Group by Genre (primary LLM-generated genre).
                *   Group by Vibe Tags (most prominent tags).
                *   Re-cluster by Score buckets.
        *   **Hover Interaction:** Popup card on bubble hover showing title, primary genre, score, OTT platform.
        *   **Detail Page:** Dedicated page per movie/TV show displaying:
            *   Title, poster, plot summary (scraped).
            *   LLM-generated genre(s).
            *   LLM-generated review summary.
            *   LLM-generated vibe score.
            *   LLM-generated vibe tags.
            *   Links to source reviews.
    4.  **Success Metrics (from Chapter 1 Project Section):**
        *   *App User Engagement (Conceptual for Guide):* (e.g., DAU, Session Duration)
        *   *Genre Accuracy (LLM Path - User Perception):* High user satisfaction with assigned genres.
        *   *Review Summary Quality:* High user satisfaction with clarity and conciseness.
        *   *Vibe Score & Tag Relevance:* High user satisfaction and utility for discovery.
        *   *Educational XGBoost/BERT Model Metrics:* Macro F1 > X%, Precision/Recall per genre > Y%.
        *   *MLOps System Metrics:* Pipeline reliability, data freshness, monitoring effectiveness.
    5.  **Non-Goals (for this phase of the project):**
        *   User accounts and personalization (beyond basic vibe search).
        *   Real-time streaming of new reviews (batch ingestion is sufficient).
        *   Complex recommendation algorithms (focus is on presentation of LLM-enriched data).
        *   Perfect, production-grade scraping (best effort for educational purposes).

*   **3.1.2 Presenting the App/User Flow Diagrams**
    Visualizing how users will navigate the application helps solidify requirements and identify potential UX issues early.

    **"Trending Now" App User Flow**
    <img src="../../_static/mlops/problem_framing/user_flow.svg"/>

    *This flow diagram outlines the primary interactions, focusing on data discovery through the bubble chart and accessing detailed, LLM-enriched information.*

---
