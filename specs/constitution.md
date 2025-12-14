# Project Constitution: Hackathon-Todo

## Article I: The Quality Mandate
- **Spec-First:** No feature is implemented without a corresponding specification in the `specs/` directory.
- **Type Safety:** Strict TypeScript for the frontend and SQLModel/Strawberry for the backend are mandatory.
- **Auditability:** Every state change must be traceable via the Audit Service (Phase 3+).

## Article II: Intelligence & Transparency
- **Rationale Summary:** AI Agents must provide a 1-2 sentence `rationale_summary` for every tool call.
- **Privacy:** User data must be strictly isolated by `user_id` across all microservices and vector indices.
- **Drafting:** AI-generated content defaults to a "Pending" status in the `todo_drafts` table until user approval.
- **Chat Integration:** All chat functionality must utilize ChatKit-Plus for enhanced conversational AI experiences.

## Article III: Architectural Evolution
- **Phase Transitions:** Development must proceed sequentially through the defined phases to ensure a stable foundation for the event-driven transition.
- **Microservices:** Inter-service communication must eventually transition to Dapr-mediated service invocation and Pub/Sub.
- **Kafka Integrity:** Event schemas are immutable. Any versioning changes must be backward-compatible.

## Governance
- **Ratification Date:** 2025-12-14
- **Version:** 1.0.0
- **Amendment Process:** Changes to this constitution require explicit approval from project maintainers.
- **Compliance Review:** Regular reviews should ensure all development activities align with these principles.