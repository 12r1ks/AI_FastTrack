# Stage 3: Process Confirmed Reservation by Using MCP Server

**Not Started**
Starts Jun 4, 2026 — Ends Jun 18, 2026 (14 days)

## Tasks

- Use any open-source MCP server that provides functionality to write data to file. Alternatively, develop a simple MCP server using Python + FastAPI to process confirmed reservations.
- In case MCP server is not possible to implement, use tool/function call for writing data into file.
- Once the administrator (second agent) approves the reservation, the server should write the reservation details to a text file.
- File entry format: `Name | Car Number | Reservation Period | Approval Time`
- Ensure the server is secure and resistant to unauthorized access, while ensuring reliable service.

## Outcome

- A fully functional MCP server integrated with the previous agents.
- The server processes reservation data and saves it in storage.

## Providing the Result

Please provide a link to your GitHub or EPAM GitLab repository in the answer field.

You can earn extra points if you provide the following artifacts:
- A PowerPoint presentation explaining how the solution works, including relevant screenshots
- A README file with clear project documentation (setup, usage, structure, etc.)
- Automated test cases are implemented using pytest or unittest (at least 2 tests per module)
- CI/CD automation and/or Infrastructure as Code (e.g., Terraform)

If the code is poor quality, or too basic to be practical, and includes critical errors, the grade may be reduced.
