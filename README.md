## PM - Kaban Board

The project is originally forked from [ED's PM project](https://github.com/ed-donner/pm).  The instructor, Ed, put together AGENTS.MD that serves project requirements and coding standards and docs/PLAN.md which is 10-part execution plan. Then students built on our own.  Co-pilot and gpt-5.3-CODEX did the first draft then I switched to Claude code. Claude code init, created CLAUDE.md and docs/REVIEW.md. It implemented tasks of High and Medium severity in docs/REVIEW.md. I gradually understood how the backend app work and keep myself engaged to add more improvement, including change FastAPI endpoint functions `ai_chat` and `ai_test` to be async. I let Claude code fix `test_ai.py` due to this change and wrap up the project

#### We should know what we want to do and let coding agents to produce it rather than let the coding agent to figure out what to do and run its own.

That's the key point in [I spent a year burning money on AI and finally decided to do something about it](https://generativeai.pub/i-spent-a-year-burning-money-on-ai-and-finally-decided-to-do-something-about-it-61854d738d4a).  That's exactly what Ed's AGENTS.md and docs/PLAN.md are about. That's how we can keep Claude Code cost down.  A lot of people feel layback with codinng agents' help.  I feel that there is a lot of responsibility and work to be a planner.   Often, requirements are ambiguous at the beginning. Execution plan become more clear as the project goes.  A late discovery can lead to the last-minute change. The author suggest to use an agent of a cheaper model if we need to have lot of conversations with a coding agent for brainstorming in the exploration phase.

#### Make best of Claude code commands for efficiency and cost management

* /init is only need when we start a new project and want to create a new CLAUDE.md: I as many beginner have a wrong impression: always /init when starting a new session.  Wrong, that will override the existing CLAUDE.md. Claude always read CLAUDE.md when we start a new session anyway. For a simple task like fixing backened tests due to my async endpoint change, going straight to give instructions is more efficient and cost effective.  Writing instructions as writing prompts should follow the principle of journalism writing in order of priority. Instruct first and context can be provided as needed.  Always ask Claude to keep CLAUDE.md up to day.
* /context, /compact, and /clear are our friends. /context keep us informed of free context window space.  Use /clear if we want to start a new task and old spamming conversation is not helpful. /clear is considered a good pratice for a clean- slate start. /conpact is to compact and summarize old onversation. Claude always keep CLAUDE.md in its memory regardless.

#### Being a knowlegeable and active participant 
so that we can easily do some minor improvements if needed. Knowing how to rebuild with changes maded and re-run all tests or individual tests and how to reset with DB etc.  I learned those and the project overview from reading CLAUDE.md and deep project knowledge from the reading docs/REVIEW.md.

#### Highlights of some improvements

* I changed functions of FastAPI endpoints: `/api/ai/test` and `/api/ai/chat` to be async using `httpx.AsyncClient` in backend/app/main.py and also changed the supporting backend/app/ai.py accordingly

```
@app.post("/api/ai/chat", response_model=AiChatResponse)
async def ai_chat(
payload: AiChatRequest,
username: str = Query(default="user", min_length=1),
) -> AiChatResponse: 
     :
     try
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            client = OpenRouterClient(config=config, http_client=http_client)
            raw_response = await client.ask_structured_async(
```
  and 4 tests failed in backend/tests/test_ai.py.  The mock/ inject `backend.app.main.httpx.Client` need to be replaced with 
  `backend.app.main.httpx.AsyncClient` because of the code change in main.py.  `_RouteClient` need to be equipped with 
  `__aenter__` and `__aexit__` functions to be a required Async ContextManager in `httpx.AsyncClient` place. The generation function `post` need to be async function. Keep `TestClient`.  FastAPI TestClient was initialized with `app` can access the app functions including those target functions of FastAPI endpoints: `/api/ai/test` and `/api/ai/chat`.  I thought that I need change TestClient to be async so that I used `httpx.AsyncClient` whose constructor does not have the input parameterand cannot access those functions to be a fully functional FastAPI TestClient. I banged my head 3 hours and figured out the Async ContextManager and mock/ inject changes but replaced `TestClient` with `httpx.AsyncClient`. Of course, all assertions failed.  It only took Claude Code 10 - 15 minutes to fix those 4 tests in test_ai.py. Cannot beat AI on that.
```
class _RouteClient:
        async def __aenter__(self) -> "_RouteClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

        async def post(self, *_args, **_kwargs) -> _FakeResponse:
            return _FakeResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": '{"assistant_response":"No board changes needed.","board_update":null}'
                            }
                        }
                    ]
                }
            )

    monkeypatch.setattr("backend.app.main.httpx.AsyncClient", lambda *args, **kwargs: _RouteClient())

    app = create_app(db_path=tmp_path / "app.db")
    client = TestClient(app)

```
* SQLite `with connection` context only automatically commit and rollback but does not close the connection.  I suggest
  to wrap the connection with `contextlib.closing`. However, without explicit the inner `with connection` context, 
  it will lose `automatically commit and rollback` part plus manual commit won't take care of connect.rollback part. 
```
 def save_board(self, username: str, board: BoardPayload) -> BoardPayload:
        with closing(self._connect()) as conn:
            with conn:
            :
            // no need to conn.commit()
```
Claude suggests to add  CORSMiddleware, allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], to take care 
the issue that `npm run dev` (localhost:3000) cannot access 0.0.0.0.:8000 FastAPI server.  Claude Code did make that changes.
However, `npm run dev` is different from `npm run build`.  It did not export static out. Therefore, `npm run dev` is 
technically incomplete deployment.  That's why Dockerfile is using `RUN npm run build`.  By the way, 
`docker compose up -d` won't reflect the change just made. `docker compose up --build -d`  will re-build the docker
image and is required in this case.

Everyone can have his/ her judgement if the 3-4 extra hours to have a better grip of the entire system and make his/ her
async changes is worthwhile.   