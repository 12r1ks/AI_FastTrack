# Stage 2: Implementation of Human-in-the-Loop Agent

**Not Started**
Starts Jun 4, 2026 — Ends Jun 18, 2026 (14 days)

## Tasks

- Create the second agent using LangChain to interact with the administrator.
- Chat bot should be able to send a reservation request to administrator and get confirm/refuse response from him (e.g. via email server, messenger, rest api).
- Organize the integration with the first agent so that the reservation request is escalated to the human administrator after collecting details from the user.

## Key Features

- Generating and sending reservation confirmation requests to the administrator.
- Receiving responses from the administrator.
- Maintaining communication between the first and second agents.

## Outcome

- Automated system that connects an administrator for reservation approval.

## Providing the Result

Please provide a link to your GitHub or EPAM GitLab repository in the answer field.

You can earn extra points if you provide the following artifacts:
- A PowerPoint presentation explaining how the solution works, including relevant screenshots
- A README file with clear project documentation (setup, usage, structure, etc.)
- Automated test cases are implemented using pytest or unittest (at least 2 tests per module)
- CI/CD automation and/or Infrastructure as Code (e.g., Terraform)

If the code is poor quality, or too basic to be practical, and includes critical errors, the grade may be reduced.
