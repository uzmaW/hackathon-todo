# Feature: Authentication (Better Auth)

## User Stories
- As a user, I can sign up with email & password (or 3rd party)
- As a user, I can log in and receive a JWT
- As a user, I can refresh tokens if implemented
- As a user, I can view my profile

## Acceptance Criteria
- /api/auth/signup: Accepts email & password, returns user id
- /api/auth/login: Returns JWT for subsequent requests
- Passwords are hashed using a secure algorithm
- Auth middleware enforces JWT on protected endpoints

## Notes for Implementation
- In phase2, integrate with Better Auth or an equivalent auth provider
- Keep user model minimal: id, email, name, created_at