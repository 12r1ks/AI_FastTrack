# Stage 1: Creation of a RAG System and Chatbot

**Not Started**
Starts Jun 4, 2026 — Ends Jun 18, 2026 (14 days)

## What Should Be Done

1. Implement the basic architecture of the chatbot using Retrieval-Augmented Generation to interact with users.

2. Integrate a vector database for storing information.

   *(Optional)* Solution can be improved by splitting source data into 2 data types: dynamic data (e.g. space availability, working hours, prices) and static data (e.g. general information, parking details, location, booking process). Store static data in vector database but dynamic data in SQL database.

3. Implement interactive features:
   - Provide information to users.
   - Collect user inputs for reservations.

4. Implement guard rails mechanism. Add a filtering to prevent exposure of sensitive data (e.g., using pre-trained NLP models for text analysis).

5. Perform evaluation of the RAG system:
   - Performance testing.
   - Response accuracy measurement (e.g., using metrics like Recall@K and Precision).

## Outcome

- Working chatbot capable of providing basic information and interacting with users.
- Data protection functionality.
- Evaluation report on system performance.

## Providing the Result

Please provide a link to your GitHub or EPAM GitLab repository in the answer field.

You can earn extra points if you provide the following artifacts:
- A PowerPoint presentation explaining how the solution works, including relevant screenshots
- A README file with clear project documentation (setup, usage, structure, etc.)
- Automated test cases are implemented using pytest or unittest (at least 2 tests per module)
- CI/CD automation and/or Infrastructure as Code (e.g., Terraform)

If the code is poor quality, or too basic to be practical, and includes critical errors, the grade may be reduced.
