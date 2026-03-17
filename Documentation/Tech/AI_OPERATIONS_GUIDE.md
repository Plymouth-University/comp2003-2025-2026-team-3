# AI System Operations Guide

This guide covers the practical aspects of running, maintaining, and extending the AI services.

## Running the AI System

The primary script for processing tickets is `scripts/predict_categories.py`.

### Batch Processing Tickets

To run the AI categorization on a batch of tickets:

1.  **Place Ticket Files**: Ensure the raw ticket data (in JSON format) is located in `backend/data/tickets.json`.
2.  **Execute the Script**: Run the main prediction script from the `backend` directory.

    ```bash
    # Navigate to the backend directory
    cd backend

    # Run the prediction process
    python scripts/predict_categories.py
    ```

3.  **Check the Output**: The script will process each ticket and save the enriched output to `backend/data/generated_categories.json`. The console will show progress.

### Generating Category Embeddings

The `predict_categories.py` script now handles the entire pipeline, including generating embeddings for tickets and clustering them. If you modify the categories in `data/generated_categories.json`, you must regenerate them by re-running the script.

## Performance & Optimization

The system includes several features to ensure efficient operation.

-   **Embedding Caching**: The `sentence-transformers` library automatically caches downloaded models. The script itself does not implement further caching, but this could be added for very large datasets.
-   **Performance Logging**: The script prints progress to the console, but detailed performance metrics are not currently logged to a separate file. This could be added by wrapping key functions with timing decorators.
-   **Metrics Summary**: At the end of each run, a summary is printed to the console, showing the discovered categories and their distribution.

## Future Expansion & Model Management

The current architecture is modular and designed for future enhancements.

### Integrating New Models

To replace the sentence-transformer model or the clustering logic:

1.  **Target `predict_categories.py`**: This script contains the core prediction logic.
    - The model is loaded in `app/services/ai/config.py`. You can change the model name there.
    - The clustering logic (KMeans) is in the `find_optimal_clusters` and `cluster_tickets` functions. This could be swapped for other algorithms like DBSCAN or hierarchical clustering.
2.  **Consider a Model Abstraction**: For greater flexibility, a future refactor could introduce a "Model Provider" class. This would create an abstraction layer, allowing different embedding models (e.g., from Hugging Face, OpenAI) to be swapped out with only a configuration change.

### Expanding AI Capabilities

The current structure makes it easy to add new AI-driven features:

-   **Sentiment Analysis**: A new function could be added to `predict_categories.py` to calculate sentiment for each ticket's text and add it to the final output.
-   **Language Detection**: A language detection library could be used to identify the ticket's language, allowing for routing to different models or teams.

The key is to encapsulate each new capability in its own function or module and integrate it into the main workflow within `predict_categories.py`.
