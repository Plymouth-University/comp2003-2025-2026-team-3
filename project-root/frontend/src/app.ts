// Import a helper function for creating DOM elements
import { el } from "./lib/dom.js";
// Import screen components
import { Dashboard } from "./screens/Dashboard.js";
import { ActiveTickets } from "./screens/ActiveTickets.js";
import { TicketDetail } from "./screens/TicketDetail.js";

// Define a TypeScript type for the possible routes in the app
// "dashboard" is the main page, "active-tickets" is the page for all active tickets etc. 
type Route =
  | { name: "dashboard" }
  | { name: "active-tickets"}
  | { name: "closed-tickets"}
  | { name: "settings" }
  | { name: "account" }
  | { name: "ticket"; id: string };

// Reads the URL hash (after #) and returns the current route as a Route object
function parseHash(): Route {
  const h = location.hash.replace(/^#/, ""); // Remove the #
  if (!h || h === "/") return { name: "dashboard" }; // Default route
  const parts = h.split("/").filter(Boolean); // Split by /
  if (parts[0] === "ticket" && parts[1]) return { name: "ticket", id: parts[1] }; //if ticket id provided, then coming from ticket detail page
  return { name: "active-tickets" }; //fallback to active tickets 
}

// Changes the URL hash to match the given route
function setHash(route: Route) {
  if (route.name === "dashboard") location.hash = "#/";
  if (route.name === "ticket") location.hash = `#/ticket/${encodeURIComponent(route.id)}`;
  if (route.name === "active-tickets") location.hash = "#/active-tickets";
  if (route.name === "closed-tickets") location.hash = "#/closed-tickets";
  if (route.name === "settings") location.hash = "#/settings";
  if (route.name === "account") location.hash = "#/account";
}

// Sidebar component: returns a sidebar navigation element
function Sidebar(setRoute: (route: Route) => void): HTMLElement {
  //aside element with tailwind classes 
  const nav = el("aside", { className: "w-64 hidden md:block bg-white border-r border-slate-200" });
  // Inner container for sidebar content
  const inner = el("div", { className: "p-4" });
  //add title and buttons for all page options
  inner.append(
    el("div", { className: "font-bold text-lg mb-4", text: "Global4 - Ticket Interface" }),
    el("button", {
      className: "w-full text-left px-3 py-2 rounded hover:bg-slate-50",
      attrs: { type: "button" },
      text: "Dashboard",
    }),
    el("button", {
      className: "w-full text-left px-3 py-2 rounded hover:bg-slate-50",
      attrs: { type: "button" },
      text: "Active Tickets",
    }),
    el("button", {
      className: "w-full text-left px-3 py-2 rounded hover:bg-slate-50",
      attrs: { type: "button" },
      text: "Closed Tickets",
    }),
    el("button", {
      className: "w-full text-left px-3 py-2 rounded hover:bg-slate-50",
      attrs: { type: "button" },
      text: "Settings",
    }),
    el("button", {
      className: "w-full text-left px-3 py-2 rounded hover:bg-slate-50",
      attrs: { type: "button" },
      text: "Account",
    }),
  );
  
  // Wire up sidebar button navigation
  const buttons = inner.querySelectorAll("button");
  buttons[0].addEventListener("click", () => setRoute({ name: "dashboard" }));
  buttons[1].addEventListener("click", () => setRoute({ name: "active-tickets" }));
  buttons[2].addEventListener("click", () => setRoute({ name: "closed-tickets" }));
  buttons[3].addEventListener("click", () => setRoute({ name: "settings" }));
  buttons[4].addEventListener("click", () => setRoute({ name: "account" }));
  
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
      el("div", { className: "font-semibold text-lg", text: "Tickets" }),
      el("div", { className: "font-mono font-semibold text-lg text-slate-700", text: "GLOBAL 4" }),
    ])
  );
  return hdr;
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

  // Track current route state
  let currentRoute: Route = parseHash();

  // Function to update route and re-render
  const setRoute = (route: Route) => {
    currentRoute = route;
    setHash(route);
    renderRoute();
  };

  // Function to render the current route
  const renderRoute = () => {
    const r = currentRoute;
    content.innerHTML = ""; // Clear content
    
    if (r.name === "dashboard") {
      content.append(Dashboard());
    } else if (r.name === "active-tickets") {
      content.append(ActiveTickets((id) => setRoute({ name: "ticket", id })));
    } else if (r.name === "ticket") {
      content.append(TicketDetail(r.id, () => setRoute({ name: "active-tickets" })));
    } else {
      // Default for other routes like closed-tickets, settings, account
      content.append(
        el("div", { className: "text-center py-8 text-slate-500", text: `${r.name} page coming soon` })
      );
    }
  };

  // Listen for hash changes (URL changes) to update the view
  window.addEventListener("hashchange", () => {
    currentRoute = parseHash();
    renderRoute();
  });

  // Build the page layout: header, sidebar, and content
  mainCol.append(TopHeader(), content);
  shell.append(Sidebar(setRoute), mainCol);
  root.append(shell);

  // Render the initial route
  renderRoute();
}
