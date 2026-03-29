import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { HomePage } from "@/pages/HomePage";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

function renderWithProviders(ui: React.ReactElement) {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>,
  );
}

describe("HomePage", () => {
  it("renders title and upload zone", () => {
    renderWithProviders(<HomePage />);

    expect(screen.getByText("P&ID Inteligente")).toBeInTheDocument();
    expect(
      screen.getByText(/Arrastra un archivo P&ID aqui/i),
    ).toBeInTheDocument();
  });

  it("renders accepted formats text", () => {
    renderWithProviders(<HomePage />);

    expect(
      screen.getByText(/Formatos soportados/i),
    ).toBeInTheDocument();
  });
});
