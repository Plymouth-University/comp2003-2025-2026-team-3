# AI System Operations Guide

This guide covers the practical aspects of running, maintaining, and extending the AI services.

## Running the AI System

The primary script for processing tickets is `predict_categories.py`.

### Batch Processing Tickets

To run the AI categorization on a batch of tickets:

1.  **Place Ticket Files**: Ensure the raw ticket data (in JSON format) is located in `project-root/backend/data/Unprocessed Tickets/`.
2.  **Execute the Script**: Run the main prediction script from the `backend` directory.

    ```powershell
    # Navigate to the backend directory
    cd project-root/backend

    # Run the prediction process
    python predict_categories.py
    ```

3.  **Check the Output**: The script will process each ticket and save the enriched output to `project-root/backend/data/Unprocessed Tickets/categorized/`. The console will show progress, and detailed logs are available in `project-root/backend/logs/ai_services/`.

### Generating Category Embeddings

If you modify the categories in `data/generated_categories.json`, you must regenerate their embeddings. This is done by running the `category_generator.py` script.

```powershell
# Navigate to the backend directory
cd project-root/backend

# Run the category generator
python -m app.services.ai.category_generator
```

This will update the embedding file used for semantic matching.

## Performance & Optimization

The system includes several features to ensure efficient operation.

-   **Embedding Caching**: The `embedding_cache.py` module saves sentence-transformer model outputs to disk (`.cache/embeddings_cache.pkl`). This avoids costly re-computation of embeddings for identical text, providing a significant speed-up during large batch runs.
-   **Performance Logging**: Detailed timing metrics for every critical operation are logged to `logs/ai_services/ai_services_performance.log`. This data is essential for identifying bottlenecks.
-   **Metrics Summary**: At the end of each run, a full performance summary is printed to the console and main log file, showing aggregate statistics (min, max, average) for each measured operation.

## Future Expansion & Model Management

The current architecture is modular and designed for future enhancements.

### Integrating New Models

To replace the sentence-transformer model or the logic for categorization:

1.  **Target `categorizer.py`**: This module contains the core prediction logic. The `predict_category_hybrid()` function is the primary place to modify the semantic search or keyword matching approach.
2.  **Update `embedding_cache.py`**: If you switch to a different embedding model, the logic here may need to be updated to handle the new model's API.
3.  **Consider a Model Abstraction**: For greater flexibility, a future refactor could introduce a "Model Provider" class. This would create an abstraction layer, allowing different embedding models (e.g., from Hugging Face, OpenAI) to be swapped out with only a configuration change.

### Expanding AI Capabilities

The current structure makes it easy to add new AI-driven features:

-   **Sentiment Analysis**: A new module, `sentiment_analyzer.py`, could be created and called from `categorizer.py` to add sentiment data to the processed ticket.
-   **Language Detection**: A `language_detector.py` module could identify the ticket's language, allowing for routing to different models or teams.

The key is to encapsulate each new capability in its own module and integrate it into the main workflow within `categorizer.py` or `processor.py`.
