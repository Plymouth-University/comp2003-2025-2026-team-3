// Import a helper function for creating DOM elements
import { el } from "./lib/dom.js";
// Import the TicketListContainer component (renders the ticket list)
import { TicketListContainer } from "./components/TicketListContainer.js";

// Define a TypeScript type for the possible routes in the app
// "dashboard" is the main page, "ticket" is the detail page for a specific ticket
type Route =
  | { name: "dashboard" }
  | { name: "ticket"; id: string };

// Reads the URL hash (after #) and returns the current route as a Route object
function parseHash(): Route {
  const h = location.hash.replace(/^#/, ""); // Remove the #
  if (!h || h === "/") return { name: "dashboard" }; // Default route
  const parts = h.split("/").filter(Boolean); // Split by /
  if (parts[0] === "ticket" && parts[1]) return { name: "ticket", id: parts[1] };
  return { name: "dashboard" }; // Fallback to dashboard
}

// Changes the URL hash to match the given route
function setHash(route: Route) {
  if (route.name === "dashboard") location.hash = "#/";
  if (route.name === "ticket") location.hash = `#/ticket/${encodeURIComponent(route.id)}`;
}

// Sidebar component: returns a sidebar navigation element
function Sidebar(): HTMLElement {
  // Create an <aside> element with Tailwind classes for styling
  const nav = el("aside", { className: "w-64 hidden md:block bg-white border-r border-slate-200" });
  // Inner container for sidebar content
  const inner = el("div", { className: "p-4" });
  // Add a title and a dashboard button
  inner.append(
    el("div", { className: "font-bold text-lg mb-4", text: "My UI" }),
    el("button", {
      className: "w-full text-left px-3 py-2 rounded hover:bg-slate-50",
      attrs: { type: "button" },
      text: "Dashboard",
    })
  );
  // Add a click event to the dashboard button to change the route
  inner.querySelector("button")!.addEventListener("click", () => setHash({ name: "dashboard" }));
  nav.append(inner);
  return nav;
}

// TopHeader component: returns a header bar for the app
function TopHeader(): HTMLElement {
  // Create a <header> element
  const hdr = el("header", { className: "bg-white border-b border-slate-200" });
  // Add a flex container with a title and a subtitle
  hdr.append(
    el("div", { className: "px-4 py-3 flex items-center justify-between" }, [
      el("div", { className: "font-semibold", text: "Tickets" }),
      el("div", { className: "text-sm text-slate-500", text: "Vanilla TS + Tailwind (no React/Vite)" }),
    ])
  );
  return hdr;
}

// TicketDetail component: shows details for a single ticket
// id: the ticketID to display
function TicketDetail(id: string): HTMLElement {
  // Create a wrapper div with styling
  const wrap = el("div", { className: "bg-white rounded-xl shadow p-6 border border-slate-200" });

  // Add a header with ticket ID and a back button
  wrap.append(
    el("div", { className: "flex items-center justify-between gap-3" }, [
      el("div", {}, [
        el("div", { className: "text-xs text-slate-500", text: id }),
        el("h2", { className: "text-xl font-bold", text: "Ticket Details" }),
      ]),
      el("button", {
        className: "px-3 py-2 rounded bg-slate-900 text-white hover:bg-slate-800",
        attrs: { type: "button" },
        text: "Back",
      }),
    ])
  );

  // Add a click event to the back button to return to dashboard
  (wrap.querySelector("button") as HTMLButtonElement).addEventListener("click", () => setHash({ name: "dashboard" }));

  // Add ticket details
  wrap.append(
    el("div", { className: "mt-4 text-sm text-slate-700 space-y-2" }, [
      el("div", { text: `Ticket ID: ${id}` }),
      el("div", { className: "pt-2 text-slate-500", text: "Detailed ticket view coming soon." }),
    ])
  );

  return wrap;
}

// Main App function: renders the whole application into the given root element
// root: the HTML element where the app will be mounted
export function App(root: HTMLElement) {
  root.innerHTML = ""; // Clear any existing content

  // Create the main shell: a flex container for sidebar and main content
  const shell = el("div", { className: "min-h-screen flex" });
  // Main column for header and page content
  const mainCol = el("div", { className: "flex-1 flex flex-col" });

  // Main content area
  const content = el("main", { className: "p-4 md:p-6" });

  // Function to render the current route (dashboard or ticket detail)
  const renderRoute = () => {
    const r = parseHash(); // Get current route from URL hash
    content.innerHTML = ""; // Clear content
    if (r.name === "dashboard") {
      // Show the ticket list, pass a callback to open ticket detail
      content.append(
        TicketListContainer((id) => setHash({ name: "ticket", id }))
      );
    } else {
      // Show the ticket detail page
      content.append(TicketDetail(r.id));
    }
  };

  // Listen for hash changes (URL changes) to update the view
  window.addEventListener("hashchange", renderRoute);

  // Build the page layout: header, sidebar, and content
  mainCol.append(TopHeader(), content);
  shell.append(Sidebar(), mainCol);
  root.append(shell);

  // Render the initial route
  renderRoute();
}
