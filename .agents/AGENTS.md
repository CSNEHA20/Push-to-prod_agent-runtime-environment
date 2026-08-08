# Code Generation Protocol

Before implementing any code, the agent MUST perform the following 8-step review process:

1. **Architecture Review**: Analyze system architecture, component boundaries, state flow, and structural impact.
2. **API Review**: Verify endpoint schemas, request/response signatures, data models, contracts, and error handling.
3. **Dependency Review**: Audit external & internal dependencies, version constraints, imports, and cross-package references.
4. **Runtime Review**: Evaluate execution environment, concurrency, async behavior, state persistence, and lifecycle.
5. **Security Review**: Check authentication, authorization, data validation, sanitization, secrets handling, and vulnerability vectors.
6. **SDK Review**: Review SDK surface area, client interfaces, backwards compatibility, typing completeness, and developer ergonomics.
7. **Performance Review**: Check compute efficiency, memory overhead, DB/network calls, caching opportunities, and scalability bottlenecks.
8. **DX Review**: Evaluate developer experience, error messages, logging clarity, code cleanliness, readability, and documentation.

Only AFTER completing all 8 reviews and achieving complete understanding of the system architecture will code implementation begin.
