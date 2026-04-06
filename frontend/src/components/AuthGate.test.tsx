import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthGate } from "@/components/AuthGate";

describe("AuthGate", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
  });

  it("shows the login form when unauthenticated", () => {
    render(
      <AuthGate>
        <div>Board</div>
      </AuthGate>
    );

    expect(
      screen.getByRole("heading", { name: /sign in to kanban studio/i })
    ).toBeInTheDocument();
    expect(screen.queryByText("Board")).not.toBeInTheDocument();
  });

  it("shows an error for invalid credentials", async () => {
    render(
      <AuthGate>
        <div>Board</div>
      </AuthGate>
    );

    await userEvent.type(screen.getByLabelText(/username/i), "wrong");
    await userEvent.type(screen.getByLabelText(/password/i), "credentials");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Invalid username or password."
    );
    expect(screen.queryByText("Board")).not.toBeInTheDocument();
  });

  it("signs in and logs out", async () => {
    render(
      <AuthGate>
        <div>Board</div>
      </AuthGate>
    );

    await userEvent.type(screen.getByLabelText(/username/i), "user");
    await userEvent.type(screen.getByLabelText(/password/i), "password");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(screen.getByText("Board")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /log out/i })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /log out/i }));

    expect(
      screen.getByRole("heading", { name: /sign in to kanban studio/i })
    ).toBeInTheDocument();
    expect(screen.queryByText("Board")).not.toBeInTheDocument();
  });
});
