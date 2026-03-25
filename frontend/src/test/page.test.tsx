/**
 * Core chat UI tests.
 *
 * These tests mount the Home page against a mocked axios so no real network
 * calls are made. They cover the three most critical user flows:
 *   1. The welcome message is shown on initial load.
 *   2. The user can send a message and see the AI reply.
 *   3. A toast is shown when the backend is unreachable.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import axios from "axios";

// Mock axios before importing the component so all calls are intercepted.
vi.mock("axios");
const mockedAxios = vi.mocked(axios, true);

// next/navigation and crypto are unavailable in jsdom — stub them.
vi.stubGlobal("crypto", {
  randomUUID: () => "test-uuid-1234",
});

// Stub localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    clear: () => {
      store = {};
    },
  };
})();
Object.defineProperty(window, "localStorage", { value: localStorageMock });

// Import after mocks are in place
import Home from "../app/page";

describe("Home (chat UI)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.clear();

    // Default: sessions and history return empty arrays
    mockedAxios.get = vi.fn().mockResolvedValue({ data: [] });
    mockedAxios.post = vi
      .fn()
      .mockResolvedValue({ data: { reply: "Hello from AI!" } });
    mockedAxios.delete = vi.fn().mockResolvedValue({ data: {} });
  });

  it("shows the welcome message on first load", async () => {
    render(<Home />);
    await waitFor(() => {
      expect(
        screen.getByText(/Hello! I'm your personal AI assistant/i),
      ).toBeInTheDocument();
    });
  });

  it("sends a message and displays the AI reply", async () => {
    render(<Home />);

    const input = await screen.findByPlaceholderText(/Ask me anything/i);
    fireEvent.change(input, { target: { value: "What is 2+2?" } });

    const sendButton = screen.getByRole("button", { name: "" }); // send icon button
    fireEvent.submit(sendButton.closest("form")!);

    await waitFor(() => {
      expect(screen.getByText("What is 2+2?")).toBeInTheDocument();
      expect(screen.getByText("Hello from AI!")).toBeInTheDocument();
    });
  });

  it("shows an error toast when the backend is unreachable", async () => {
    mockedAxios.get = vi.fn().mockRejectedValue(new Error("Network Error"));
    render(<Home />);

    await waitFor(() => {
      expect(
        screen.getByText(/Could not load conversations/i),
      ).toBeInTheDocument();
    });
  });
});
