# Stage 4: Orchestrating All Components via LangGraph

**Not Started**
Starts Jun 4, 2026 — Ends Jun 18, 2026 (14 days)

## Tasks

- Implement orchestration of all components using LangGraph.
- Ensure complete integration of all stages:
  - The chatbot (RAG agent) interacts with users.
  - The system escalates reservation requests to the administrator via a human-in-the-loop agent (second agent).
  - The MCP server processes data after confirmation.
- Implement the workflow logic for the entire pipeline:
  - Example graph structure:
    - Node for user interaction (context of RAG and chatbot).
    - Node for administrator approval.
    - Node for data recording.
- Conduct testing of the entire system workflow.

## Outcome

- A unified system where all components seamlessly interact with each other.
- Stable operation of the entire pipeline.

## Additional Details

### System Testing

Conduct load tests to evaluate the performance of each component:
- Chatbot in interactive dialogue mode.
- Administrator confirmation functionality.
- MCP server recording and storage process.

Perform integration testing of all steps during orchestration.

### Documentation

Prepare documentation for system usage:
- Architecture description.
- Agent and server logic.
- Setup and deployment guidelines.

## Providing the Result

Please provide a link to your GitHub or EPAM GitLab repository in the answer field.

You can earn extra points if you provide the following artifacts:
- A PowerPoint presentation explaining how the solution works, including relevant screenshots
- A README file with clear project documentation (setup, usage, structure, etc.)
- Automated test cases are implemented using pytest or unittest (at least 2 tests per module)
- CI/CD automation and/or Infrastructure as Code (e.g., Terraform)

If the code is poor quality, or too basic to be practical, and includes critical errors, the grade may be reduced.
