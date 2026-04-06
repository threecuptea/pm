# AI Integration

## Endpoint

- `GET /api/ai/test?prompt=...`
  - Purpose: lightweight connectivity check to OpenRouter.
  - Response: `{ "model": "...", "prompt": "...", "response": "..." }`

- `POST /api/ai/chat?username=user`
  - Purpose: send Kanban context and chat history to AI, receive structured output, and optionally persist board updates.

## Request schema for `/api/ai/chat`

```json
{
  "question": "How should I prioritize this week?",
  "history": [
    { "role": "user", "content": "I need help with planning." },
    { "role": "assistant", "content": "I can help with that." }
  ]
}
```

Notes:
- `question` is required.
- `history` is optional and defaults to an empty list.
- `role` supports `user` and `assistant`.

## Structured AI response contract

The backend requests JSON-schema-constrained output from OpenRouter.

Expected object:

```json
{
  "assistant_response": "Human-readable assistant reply",
  "board_update": null
}
```

or

```json
{
  "assistant_response": "I moved two cards into In Progress.",
  "board_update": {
    "columns": [ ... ],
    "cards": { ... }
  }
}
```

Rules:
- `assistant_response` is required.
- `board_update` is optional (`null` or a full valid board payload).
- If `board_update` is present, backend validates it and persists it for the user.

## Backend behavior

For every `/api/ai/chat` call, backend sends:
- Current board JSON for the requested user.
- Conversation history from request payload.
- The current user question.

Then backend:
- Validates structured output.
- Returns `502` if structured output is invalid.
- Persists `board_update` when present.

## `/api/ai/chat` response shape

```json
{
  "model": "openai/gpt-oss-120b",
  "assistant_response": "...",
  "board_updated": false,
  "board": {
    "columns": [ ... ],
    "cards": { ... }
  }
}
```

## Error handling

- Missing `OPENROUTER_API_KEY`: `503`
- Upstream OpenRouter HTTP/connectivity errors: `502`
- Invalid structured payload from model: `502`
