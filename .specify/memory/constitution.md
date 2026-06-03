# Task Board Constitution

## Code Quality
- Enforce TypeScript strict mode throughout the application. Explicit `any` types are strictly prohibited.
- Architecture must utilize functional components with React hooks exclusively; legacy class components are banned.
- Maintain modularity by enforcing a maximum threshold of 50 lines of execution logic per function.

## Testing
- Maintain a mandatory minimum threshold of 80% automated code coverage before merge approval.
- Execute isolated unit testing via Vitest for all complex drag-and-drop state transitions and column array sorting logic.
- Implement end-to-end (E2E) testing suites via Playwright to validate critical user pathways (card creation, deletion, and cross-column movement).

## UX & Accessibility
- Ensure strict compliance with WCAG 2.1 AA accessibility guidelines, specifically establishing full keyboard-interactable focus states for grid movement.
- Provide fluid drag-and-drop feedback utilizing a visual "ghost card" element tracking user cursor position seamlessly.
- Implement empty-state UI boundaries: Unpopulated grid columns must display a descriptive "Drop cards here" placeholder state.

## Security
- Enforce secure token-based authentication handshakes prior to opening active board sessions or rendering API resource endpoints.
- Apply rigorous input sanitization protocols on all free-text input variables (card titles, descriptions) to eliminate cross-site scripting (XSS) injection vectors.

## Real-Time Collaboration
- Establish dynamic, persistent server connections via modern WebSocket protocols to broadcast multi-user board state updates instantly without complete page document refetches.
- WebSocket state management systems must implement transparent, silent reconnection logic to preserve unsaved local canvas drift during unexpected connection disruptions.
- Conflict Resolution Engine: Concurrent mutations to an individual data record will resolve using a Last-Write-Wins (LWW) protocol, generating an immediate visual notification to the superseded client session.
