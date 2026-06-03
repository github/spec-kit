# Specification: Card CRUD (Slice 2)

## Feature: Card Content Management

### Description
Provides users with the capabilities to create, read, update, and delete individual task cards within board columns to manage daily item workflows.

### User Stories
- US-01: As a user, I want to create a card inside a column so I can document a new task.
- US-02: As a user, I want to view a card's full details so I can read detailed context descriptions.
- US-03: As a user, I want to modify card details so I can keep task descriptions up to date.
- US-04: As a user, I want to delete a card so I can permanently remove redundant work items.

### Acceptance Criteria
- AC-01: Clicking "Add Card" opens an inline input field; pressing Enter or clicking "Save" creates the card instantly at the bottom of that column.
- AC-02: Clicking a card title triggers a modal canvas window displaying the full title and markdown-supported description fields.
- AC-03: Editing titles or descriptions triggers an auto-save loop after 500ms of typing inactivity, displaying a "Saved" status indicator.
- AC-04: Clicking the "Delete" action button prompts an explicit confirmation modal window before executing permanent document data erasure.

### Edge Cases
- EC-01: Submit empty title input field → Reverts field line and highlights container border in red with "Title cannot be blank" validation text.
- EC-02: Lose network connection while editing description field → Freezes editor input box and displays a prominent offline retry banner indicator.
- EC-03: [ADDED FOR EXERCISE] A card is deleted by User A while currently being viewed inside a details modal window by User B → Close User B's open modal panel instantly, clear the element record from their active display view, and trigger a floating toast warning notification stating: "This card has been deleted by another team member."

### Data Requirements
- Card Input Payload: { title: String, description: MarkdownString, columnId: UUID }
- Card Visual State: { isEditing: Boolean, isModalOpen: Boolean }

### Non-goals
- No background color formatting customizable per individual card element.
- No historical log archiving or data field revision undo/redo tracking inside the card canvas.
- No file attachment or asset upload support within descriptions.
