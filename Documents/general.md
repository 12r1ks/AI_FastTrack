# Technical Specification: Development of a Chatbot for Parking Space Reservation

## General Requirements

- **Programming Language:** Python
- **Frameworks:** LangChain, LangGraph
- **Architecture:** Based on Retrieval-Augmented Generation (RAG)
- **Vector database:** Recommended options include Milvus, Pinecone, or Weaviate

## General Features

- The chatbot provides information (general information, working hours, prices, availability of parking spaces, location).
- The reservation process is based on interactive collection of user data, including name, surname, car number, and reservation period.
- The system should prevent exposure of sensitive data (e.g., private information stored in the vector database).
- Evaluation of system performance (e.g., request latency, information retrieval accuracy).

## Providing the Result

For each task, please provide a link to your GitHub or EPAM GitLab repository in the answer field.

You can earn extra points if you provide the following artifacts:
- A PowerPoint presentation explaining how the solution works, including relevant screenshots
- A README file with clear project documentation (setup, usage, structure, etc.)
- Automated test cases are implemented using pytest or unittest (at least 2 tests per module)
- CI/CD automation and/or Infrastructure as Code (e.g., Terraform)

If the code is poor quality, or too basic to be practical, and includes critical errors, the grade may be reduced.
